"""Ejecución del banco de evaluación y métricas (módulo K, `eval/README.md` §6).

Convierte cada ``EvalCase`` (mensaje ficticio + etiqueta) en un mensaje del
pipeline, ejecuta el análisis y compara con lo esperado. **Solo** para el
conjunto de desarrollo durante el desarrollo; el conjunto sellado se ejecuta
una vez, con autorización (D-40).
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID

from antifraude.analysis.ingest import build_message, make_sender
from antifraude.app.pipeline import AnalysisOutcome, AnalysisPipeline
from antifraude.contracts.ai import AiFailureReason
from antifraude.contracts.checks import CheckStatus
from antifraude.contracts.common import RiskLevel
from antifraude.contracts.evaluation import EvalCase
from antifraude.contracts.messages import Channel

EVAL_USER = UUID("00000000-0000-4000-8000-0000000e7a1d")
_ALERT = {RiskLevel.MEDIUM, RiskLevel.HIGH}


def load_cases(paths: Iterable[Path]) -> list[EvalCase]:
    cases: list[EvalCase] = []
    for p in paths:
        cases += [EvalCase.model_validate_json(line) for line in Path(p).read_text(encoding="utf-8").splitlines()
                  if line.strip()]
    return cases


def run_case(case: EvalCase, pipeline: AnalysisPipeline) -> AnalysisOutcome:
    m = case.message
    ingested = build_message(
        user_id=EVAL_USER,
        channel=Channel.MANUAL,
        body_text=m.body_text,
        body_html=m.body_html,
        subject=m.subject,
        sender=make_sender(m.sender.display_name, m.sender.address, m.sender.auth),
        reply_to=make_sender(None, m.reply_to) if m.reply_to else None,
        received_at=m.received_at,
    )
    return pipeline.run(ingested)


@dataclass
class CaseResult:
    case_id: str
    expected: RiskLevel
    acceptable: list[RiskLevel]
    obtained: RiskLevel
    must_alert: bool
    alerted: bool
    latency_ms: int
    origin: str
    medium: str = "unknown"
    partial: bool = False
    expected_quotes: int = 0
    matched_quotes: int = 0

    @property
    def level_ok(self) -> bool:
        return self.obtained in self.acceptable


@dataclass
class Metrics:
    n: int
    tp: int
    fp: int
    fn: int
    tn: int
    inconclusive: int
    level_ok: int
    latencies_ms: list[int] = field(default_factory=list)
    #: Casos etiquetados NO CONCLUYENTE: no son «legítimos» ni «fraude»; se excluyen de
    #: precisión/recall/FP y se informan aparte (revisión de etiquetas, sesión 6).
    ambiguous_n: int = 0
    ambiguous_level_ok: int = 0
    ambiguous_alerted: int = 0

    @property
    def precision(self) -> float | None:
        return self.tp / (self.tp + self.fp) if (self.tp + self.fp) else None

    @property
    def recall(self) -> float | None:
        return self.tp / (self.tp + self.fn) if (self.tp + self.fn) else None

    @property
    def f1(self) -> float | None:
        denominator = 2 * self.tp + self.fp + self.fn
        return 2 * self.tp / denominator if denominator else None

    @property
    def false_positive_rate(self) -> float | None:
        return self.fp / (self.fp + self.tn) if (self.fp + self.tn) else None

    def percentile(self, q: float) -> int | None:
        if not self.latencies_ms:
            return None
        s = sorted(self.latencies_ms)
        return s[min(len(s) - 1, max(0, math.ceil(q * len(s)) - 1))]


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    """Intervalo de confianza de Wilson al 95 % para una proporción."""
    if n == 0:
        return None
    p = successes / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centre - half), min(1.0, centre + half)


def _case_result(case: EvalCase, out: AnalysisOutcome) -> CaseResult:
    level = out.assessment.risk_level
    quotes = [e.quote for e in out.assessment.evidence if e.quote]
    expected = case.expected.expected_quotes
    return CaseResult(case.case_id, case.expected.risk_level, list(case.expected.acceptable_levels), level,
                      case.expected.must_alert, level in _ALERT, out.latency_ms, case.origin.value,
                      case.message.medium.value, out.assessment.is_partial, len(expected),
                      sum(any(q in actual for actual in quotes) for q in expected))


def evaluate(cases: Iterable[EvalCase], pipeline: AnalysisPipeline) -> tuple[list[CaseResult], Metrics]:
    results = [_case_result(c, run_case(c, pipeline)) for c in cases]
    return _metrics_from(results)


def _fmt(value: float | None) -> str:
    return "n/d" if value is None else f"{value:.2f}"


def report(results: list[CaseResult], m: Metrics) -> str:
    """Informe en texto. Las cifras de desarrollo NO son una evaluación del sistema."""
    pos, neg = m.tp + m.fn, m.fp + m.tn
    lines = [
        "INFORME DE DESARROLLO — conjunto dev (casos sintéticos, la mayoría redactados con IA).",
        "AVISO: el motor se ha ajustado con estos mismos casos; estas cifras NO son una evaluación",
        "independiente ni deben presentarse como rendimiento real. Sin IA (solo reglas + enlaces).",
        f"Casos: {m.n} (deben alertar: {pos}; legítimos: {neg}; ambiguos NO CONCLUYENTE, aparte: {m.ambiguous_n})",
        f"Ambiguos: nivel aceptable {m.ambiguous_level_ok}/{m.ambiguous_n}; con alerta {m.ambiguous_alerted}"
        " (no cuentan como falsos positivos)",
        f"VP={m.tp} FP={m.fp} FN={m.fn} VN={m.tn} | NO CONCLUYENTE={m.inconclusive} | nivel aceptable={m.level_ok}/{m.n}",
        f"Precision={_fmt(m.precision)}  Recall={_fmt(m.recall)}  F1={_fmt(m.f1)}  Tasa FP={_fmt(m.false_positive_rate)}",
    ]
    ci = wilson(m.tp, pos)
    if ci:
        lines.append(f"Recall IC95% Wilson: [{ci[0]:.2f}, {ci[1]:.2f}] (n={pos})")
    ci = wilson(m.fp, neg)
    if ci:
        lines.append(f"Tasa FP IC95% Wilson: [{ci[0]:.2f}, {ci[1]:.2f}] (n={neg})")
    lines.append(f"Latencia del análisis (local, sin IA): p50={m.percentile(0.5)} ms  p95={m.percentile(0.95)} ms")
    lines.append("Coste por mensaje: no medido (sin llamadas a la API de Claude; requiere presupuesto autorizado).")
    lines.append("Casos fuera de lo aceptable: " + (", ".join(r.case_id for r in results if not r.level_ok) or "ninguno"))
    return "\n".join(lines)


_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = _ROOT / "eval" / "results"  # ignorado por Git


@dataclass
class ConfigRun:
    name: str
    results: list[CaseResult]
    metrics: Metrics
    cost_usd: float | None = 0.0
    ai_calls: int | None = 0
    ai_failures: int | None = 0
    ai_blocked: int = 0
    ai_reused: int = 0
    usage_missing: int = 0


def _request_counter(pipeline: AnalysisPipeline) -> int | None:
    # Este contador aumenta justo antes del transporte, después de reservar presupuesto.
    # No se deducen solicitudes pagadas a partir de un resultado que también puede venir de caché.
    from antifraude.ai.base import DisabledAi
    from antifraude.ai.claude import ClaudeAnalyzer
    if isinstance(pipeline.ai, DisabledAi):
        return 0
    if isinstance(pipeline.ai, ClaudeAnalyzer):
        return pipeline.ai.guard.requests_sent
    return None  # el protocolo genérico no promete telemetría de transporte


def evaluate_config(name: str, cases: list[EvalCase], pipeline: AnalysisPipeline) -> ConfigRun:
    """Mide transportes enviados y usage nuevo; caché/bloqueos no duplican consumo."""
    results: list[CaseResult] = []
    cost, calls, failures, blocked, reused, missing = 0.0, 0, 0, 0, 0, 0
    telemetry_known = True
    local_blocks = {AiFailureReason.BUDGET_BLOCKED, AiFailureReason.LIMIT_EXCEEDED, AiFailureReason.BUSY}
    for c in cases:
        before = _request_counter(pipeline)
        out = run_case(c, pipeline)
        after = _request_counter(pipeline)
        results.append(_case_result(c, out))
        if out.ai is not None and out.ai.failure_reason in local_blocks:
            blocked += 1
        if before is None or after is None or after < before:
            telemetry_known = False
            continue
        sent = after - before
        calls += sent
        if not sent:
            if out.ai is not None and (out.ai.status is CheckStatus.DONE
                                       or out.ai.failure_reason is AiFailureReason.REFUSAL):
                reused += 1
            continue
        failures += sent if out.ai is not None and out.ai.status is CheckStatus.FAILED else 0
        usage = out.ai.usage if out.ai is not None else None
        if usage is not None and usage.cost_usd is not None:
            cost += usage.cost_usd
            missing += max(0, sent - 1)
        else:
            missing += sent
    _, metrics = _metrics_from(results)
    return ConfigRun(name, results, metrics, round(cost, 6) if telemetry_known else None,
                     calls if telemetry_known else None, failures if telemetry_known else None,
                     blocked, reused, missing)


def _metrics_from(results: list[CaseResult]) -> tuple[list[CaseResult], Metrics]:
    m = Metrics(n=len(results), tp=0, fp=0, fn=0, tn=0, inconclusive=0, level_ok=0,
                latencies_ms=[r.latency_ms for r in results])
    for r in results:
        m.inconclusive += r.obtained is RiskLevel.INCONCLUSIVE
        m.level_ok += r.level_ok
        if r.expected is RiskLevel.INCONCLUSIVE:
            m.ambiguous_n += 1
            m.ambiguous_level_ok += r.level_ok
            m.ambiguous_alerted += r.alerted
            continue
        if r.must_alert and r.alerted:
            m.tp += 1
        elif not r.must_alert and r.alerted:
            m.fp += 1
        elif r.must_alert and not r.alerted:
            m.fn += 1
        else:
            m.tn += 1
    return results, m


def _quality_metrics(results: list[CaseResult], m: Metrics) -> dict[str, object]:
    pos, neg = m.tp + m.fn, m.fp + m.tn
    expected_quotes = sum(r.expected_quotes for r in results)
    matched_quotes = sum(r.matched_quotes for r in results)
    return {
        "casos": m.n, "deben_alertar": pos, "legitimos": neg, "ambiguos": m.ambiguous_n,
        "vp": m.tp, "fp": m.fp, "fn": m.fn, "vn": m.tn, "no_concluyente": m.inconclusive,
        "tasa_no_concluyente": m.inconclusive / m.n if m.n else None,
        "nivel_aceptable": m.level_ok,
        "ambiguos_nivel_aceptable": m.ambiguous_level_ok, "ambiguos_con_alerta": m.ambiguous_alerted,
        "precision": m.precision, "recall": m.recall, "f1": m.f1, "tasa_fp": m.false_positive_rate,
        "precision_ic95_wilson": wilson(m.tp, m.tp + m.fp),
        "recall_ic95_wilson": wilson(m.tp, pos), "tasa_fp_ic95_wilson": wilson(m.fp, neg),
        "latencia_ms_p50": m.percentile(0.5), "latencia_ms_p95": m.percentile(0.95),
        "analisis_parciales": sum(r.partial for r in results),
        "citas_esperadas": expected_quotes, "citas_esperadas_cubiertas": matched_quotes,
        "cobertura_citas_esperadas": matched_quotes / expected_quotes if expected_quotes else None,
    }


def metrics_dict(run: ConfigRun) -> dict[str, object]:
    data = {"configuracion": run.name, **_quality_metrics(run.results, run.metrics),
            "llamadas_ia": run.ai_calls, "fallos_ia": run.ai_failures,
            "analisis_ia_bloqueados": run.ai_blocked, "respuestas_ia_reutilizadas": run.ai_reused,
            "coste_real_usd": run.cost_usd if not run.usage_missing else None,
            "coste_con_usage_usd": run.cost_usd,
            "solicitudes_sin_coste_usage": run.usage_missing if run.ai_calls is not None else None,
            "nota_coste": ("suma del usage de transportes nuevos, no una factura; caché excluida. "
                           "Coste total null si falta usage o telemetría. Los errores sin usage mantienen "
                           "el cargo pesimista en el libro de gasto."),
            "nota_llamadas_ia": ("Contador de transportes CostGuard; sin inferir solicitudes de los hallazgos. "
                                 "null para un adaptador sin telemetría verificable.")}
    for field, key in (("origin", "por_origen"), ("medium", "por_medio")):
        groups = {}
        for value in sorted({getattr(r, field) for r in run.results}):
            subset = [r for r in run.results if getattr(r, field) == value]
            _, metrics = _metrics_from(subset)
            groups[value] = _quality_metrics(subset, metrics)
        data[key] = groups
    return data


def _git_commit() -> str | None:
    import subprocess
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=_ROOT, capture_output=True, text=True,
                           timeout=10)
        return r.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _git_dirty() -> bool | None:
    import subprocess
    try:
        result = subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=normal"],
                                cwd=_ROOT, capture_output=True, text=True, timeout=10)
        return bool(result.stdout.strip()) if result.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def _sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(_ROOT)
        return True
    except ValueError:
        return False


def build_report(kind: str, runs: list[ConfigRun], *, model: str | None, sealed_sha256: str | None) -> dict[str, object]:
    """Informe reproducible (JSON). Sin textos de mensajes; en modo sellado, sin identificadores de casos."""
    from datetime import datetime, timezone
    import platform
    import sys

    from antifraude.ai.prompt import PROMPT_VERSION
    from antifraude.analysis.rules import RULE_VERSION

    report_: dict[str, object] = {
        "tipo": kind,
        "aviso": ("Conjunto de DESARROLLO: el motor se ajustó con estos casos; NO es una evaluación independiente."
                  if kind == "desarrollo" else
                  "Conjunto con huella declarada, métricas solo agregadas. La custodia, independencia "
                  "y congelación del commit requieren verificación humana; el comando no las acredita."),
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "commit": _git_commit(), "arbol_trabajo_sucio": _git_dirty(),
        "python": sys.version.split()[0], "plataforma": platform.platform(),
        "requirements_lock_sha256": _sha256(_ROOT / "requirements.lock")
        if (_ROOT / "requirements.lock").is_file() else None,
        "rule_version": RULE_VERSION, "prompt_version": PROMPT_VERSION,
        "modelo_ia": model, "sha256_conjunto": sealed_sha256,
        "configuraciones": [metrics_dict(r) for r in runs],
    }
    if kind == "desarrollo" and len(runs) == 2:  # comparación caso a caso (solo identificadores y niveles)
        a, b = runs
        report_["diferencias"] = [
            {"case_id": x.case_id, "esperado": x.expected.value, a.name: x.obtained.value, b.name: y.obtained.value}
            for x, y in zip(a.results, b.results) if x.obtained is not y.obtained]
    elif kind == "desarrollo":
        report_["casos"] = [{"case_id": r.case_id, "esperado": r.expected.value, "obtenido": r.obtained.value,
                             "aceptable": r.level_ok} for r in runs[0].results]
    return report_


def main(argv: list[str] | None = None) -> int:
    """``python -m antifraude.evaluation`` (desde ``backend``). Ver ``eval/EJECUCION.md``."""
    import argparse
    import json

    from antifraude.ai.claude import ClaudeAnalyzer
    from antifraude.ai.budget import worst_case_cost
    from antifraude.core.config import Settings
    from antifraude.intel.entities import EntityDirectory

    ap = argparse.ArgumentParser(prog="python -m antifraude.evaluation")
    ap.add_argument("--modo", choices=["reglas", "ia", "ambos"], default="reglas")
    ap.add_argument("--sellado", type=Path, help="Conjunto sellado (FUERA del repositorio).")
    ap.add_argument("--sha256", help="Huella esperada del conjunto sellado (eval/SELLADO.md).")
    ap.add_argument("--salida", type=Path, help="Informe JSON (por defecto, eval/results/).")
    ap.add_argument("--confirmar-gasto", action="store_true", help="Necesario para cualquier modo con IA.")
    args = ap.parse_args(argv)

    analyzer = None
    policy = None
    model = None
    if args.modo in ("ia", "ambos"):
        settings = Settings.from_env()
        key = settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else None
        analyzer = ClaudeAnalyzer(policy=settings.ai_policy(), api_key=key)
        if not analyzer.configured:
            print(f"IA no disponible: {analyzer.blocked_reason} No se ha gastado nada.")
            return 3
        if not args.confirmar_gasto:
            print("Peor caso estimado: pendiente de validar el número de casos. "
                  "Falta --confirmar-gasto: no se lee ningún conjunto ni se envía ninguna solicitud.")
            return 3
        policy = settings.ai_policy()
        model = policy.model

    kind = "desarrollo"
    sha = None
    if args.sellado is not None:
        path = args.sellado
        if _inside_repo(path):
            print("ERROR: el conjunto sellado debe estar FUERA del repositorio (D-40).")
            return 2
        if not path.is_file() or not args.sha256:
            print("ERROR: falta el archivo sellado o su huella (--sha256).")
            return 2
        sha = _sha256(path)
        if sha != args.sha256.strip().lower():
            print("ERROR: la huella SHA-256 no coincide: el conjunto ha cambiado o no es el registrado.")
            return 2
        marker = RESULTS_DIR / f"sellado_{sha[:16]}.ejecutado"
        if marker.exists():
            print("ERROR: este conjunto sellado ya se ejecutó una vez (D-40). No se repite.")
            return 2
        kind = "sellado"
        cases = load_cases([path])
        # La marca se escribe ANTES de ejecutar: si el proceso cae a mitad, el conjunto no puede repetirse (D-40).
        marker.parent.mkdir(parents=True, exist_ok=True)
        try:
            with marker.open("x", encoding="utf-8") as opened:
                opened.write("en curso")
        except FileExistsError:
            print("ERROR: este conjunto sellado ya está reservado para una ejecución (D-40).")
            return 2
    else:
        cases = load_cases(sorted((_ROOT / "eval" / "datasets" / "dev").glob("*.jsonl")))

    directory = EntityDirectory.load_default(include_fictitious=True)
    runs: list[ConfigRun] = []
    if args.modo in ("reglas", "ambos"):
        runs.append(evaluate_config("reglas", cases, AnalysisPipeline(directory)))
    if analyzer is not None:
        assert policy is not None and model is not None
        requests = min(len(cases), policy.max_requests)
        worst = worst_case_cost(model, policy.max_input_tokens, policy.max_output_tokens) * requests
        print(f"Peor caso estimado: {worst} USD para {len(cases)} casos (límite autorizado {policy.budget_usd} USD; "
              f"máx. {policy.max_requests} solicitudes).")
        if worst > policy.budget_usd:
            print("AVISO: el presupuesto autorizado no cubre el peor caso de todos los casos: la IA se detendrá al "
                  "agotarlo y los casos restantes figurarán como «IA no disponible» (análisis parcial).")
        runs.append(evaluate_config("reglas_ia", cases, AnalysisPipeline(directory, analyzer)))

    rep = build_report(kind, runs, model=model, sealed_sha256=sha)
    out = args.salida or RESULTS_DIR / f"informe_{kind}_{rep['fecha_utc'].replace(':', '').replace('-', '')[:15]}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    if kind == "sellado":
        (RESULTS_DIR / f"sellado_{sha[:16] if sha else 'x'}.ejecutado").write_text(str(rep["fecha_utc"]),
                                                                                     encoding="utf-8")  # completado
        for c in rep["configuraciones"]:  # type: ignore[union-attr]
            print(json.dumps(c, ensure_ascii=False, default=str))
    else:
        for r in runs:
            print(f"== {r.name} ==")
            if r.name == "reglas":
                print(report(r.results, r.metrics))
            else:  # con IA: el texto de report() describe el modo sin IA; se muestran las métricas tal cual
                print(json.dumps(metrics_dict(r), ensure_ascii=False, default=str))
            if r.ai_calls:
                print(f"Llamadas a la IA: {r.ai_calls} (fallidas {r.ai_failures}); coste real registrado: "
                      f"{r.cost_usd} USD")
    print(f"Informe JSON: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

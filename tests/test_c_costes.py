"""Misión 3, tarea A: control de gasto de la API de Claude. TODO SIMULADO: ninguna llamada real ni de pago."""

from __future__ import annotations

import json
import logging
import threading
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from antifraude.ai.budget import (OPUS, PLANNED_INITIAL_BUDGET_USD, SONNET, AiPolicy, BudgetBlocked, CostGuard,
                                  SpendLedger, cost_usd, estimate_input_tokens, worst_case_cost)
from antifraude.ai.claude import ClaudeAnalyzer
from antifraude.analysis.ingest import from_manual_text
from antifraude.app.pipeline import AnalysisPipeline
from antifraude.contracts import RiskLevel
from antifraude.contracts.checks import CheckStatus
from antifraude.core.config import Settings
from antifraude.intel.entities import EntityDirectory

USER = uuid4()
SECRETO = "Introduzca su contraseña MARCADOR-PRIVADO-7731"


def resp(stop: str = "end_turn", usage: dict[str, int] | None = None, texto: str | None = None) -> dict[str, Any]:
    data = texto if texto is not None else json.dumps(
        {"claimed_entity": None, "tactics": [], "inconsistencies": [], "financial_request": None,
         "injection_attempt": False, "uncertainties": [], "suggested_level": None})
    r: dict[str, Any] = {"model": SONNET, "stop_reason": stop, "content": [{"type": "text", "text": data}]}
    r["usage"] = usage if usage is not None else {"input_tokens": 1000, "output_tokens": 500}
    return r


class Transporte:
    """Doble SIMULADO: cuenta las llamadas (cada llamada sería una solicitud de pago)."""

    def __init__(self, respuesta: Any = None) -> None:
        self.respuesta = respuesta if respuesta is not None else resp()
        self.llamadas = 0

    def __call__(self, params: Any) -> Any:
        self.llamadas += 1
        if isinstance(self.respuesta, BaseException):
            raise self.respuesta
        return self.respuesta


def politica(tmp_path: Path, **kw: Any) -> AiPolicy:
    base: dict[str, Any] = {"enabled": True, "model": SONNET, "budget_usd": "0.50",
                            "ledger_path": tmp_path / "gasto.json"}
    base.update(kw)
    return AiPolicy(**base)


def ia(tmp_path: Path, t: Transporte, **kw: Any) -> ClaudeAnalyzer:
    return ClaudeAnalyzer(policy=politica(tmp_path, **kw), api_key=None, transport=t)


def msg(texto: str = SECRETO) -> Any:
    return from_manual_text(texto, USER).message


def gastado(tmp_path: Path) -> Decimal:
    return SpendLedger(tmp_path / "gasto.json").spent()


# --- Política por defecto: todo cerrado ----------------------------------------------------------
def test_por_defecto_ia_desactivada_y_cero_usd_autorizados() -> None:
    s = Settings.from_env({})
    p = s.ai_policy()
    assert not p.enabled and p.budget_usd == 0 and not p.allow_expensive and p.model is None
    assert p.blocked_reason() is not None
    assert PLANNED_INITIAL_BUDGET_USD == Decimal("0.50")  # previsto, NO autorizado


def test_activar_sin_presupuesto_sigue_bloqueado(tmp_path: Path) -> None:
    t = Transporte()
    a = ia(tmp_path, t, budget_usd="0")
    assert not a.configured and "0 USD" in (a.blocked_reason or "")
    assert a.analyze(msg(), []).status is CheckStatus.NOT_CONFIGURED and t.llamadas == 0


def test_variables_de_entorno_de_gasto() -> None:
    s = Settings.from_env({"AI_ENABLED": "1", "CLAUDE_MODEL": SONNET, "AI_BUDGET_USD": "0,50",
                           "AI_MAX_INPUT_TOKENS": "3000", "AI_MAX_OUTPUT_TOKENS": "1500", "AI_MAX_REQUESTS": "5",
                           "AI_THINKING": "off", "AI_EFFORT": "LOW"})
    p = s.ai_policy()
    assert p.enabled and p.budget_usd == Decimal("0.50") and p.max_input_tokens == 3000
    assert p.max_output_tokens == 1500 and p.max_requests == 5 and p.thinking == "off" and p.effort == "low"
    assert p.blocked_reason() is None


@pytest.mark.parametrize("var,valor", [("AI_BUDGET_USD", "50"), ("AI_BUDGET_USD", "-1"),
                                       ("AI_MAX_OUTPUT_TOKENS", "100000"), ("AI_THINKING", "max")])
def test_valores_fuera_de_rango_se_rechazan(var: str, valor: str) -> None:
    with pytest.raises(ValidationError) as exc:
        Settings.from_env({var: valor})
    assert valor not in str(exc.value)  # nunca se repite el valor recibido


def test_opus_bloqueado_salvo_permiso_expreso(tmp_path: Path) -> None:
    assert "Opus" in (politica(tmp_path, model=OPUS).blocked_reason() or "")
    assert politica(tmp_path, model=OPUS, allow_expensive=True).blocked_reason() is None
    assert politica(tmp_path, model=OPUS, allow_expensive=True, thinking="off").blocked_reason() is not None


def test_modelo_no_permitido(tmp_path: Path) -> None:
    assert politica(tmp_path, model="claude-cualquiera").blocked_reason() is not None


# --- Estimación y coste ---------------------------------------------------------------------------
def test_coste_segun_tarifa_publicada() -> None:
    # Sonnet 5.5: 2 USD/M entrada, 10 USD/M salida, 2,50 escritura de caché, 0,10 lectura de caché.
    assert cost_usd(SONNET, input_tokens=1000, output_tokens=500) == Decimal("0.007")
    assert cost_usd(SONNET, input_tokens=0, output_tokens=0, cache_creation_tokens=1_000_000,
                    cache_read_tokens=1_000_000) == Decimal("2.6")
    assert cost_usd(OPUS, input_tokens=1000, output_tokens=500) == Decimal("0.014")


def test_peor_caso_cubre_el_coste_real() -> None:
    est = estimate_input_tokens("x" * 4000)
    assert est >= 4000 / 4  # estimación por exceso
    assert worst_case_cost(SONNET, est, 4000) >= cost_usd(SONNET, input_tokens=est, output_tokens=4000)


# --- Registro del gasto real ----------------------------------------------------------------------
def test_gasto_real_registrado_sin_contenido(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    t = Transporte(resp(usage={"input_tokens": 1000, "output_tokens": 500, "cache_read_input_tokens": 200}))
    r = ia(tmp_path, t).analyze(msg(), [])
    assert r.status is CheckStatus.DONE and r.usage and r.usage.cost_usd == pytest.approx(0.00702)
    assert gastado(tmp_path) == Decimal("0.00702")
    libro = (tmp_path / "gasto.json").read_text(encoding="utf-8")
    assert "MARCADOR-PRIVADO" not in libro and "contraseña" not in libro
    entrada = json.loads(libro)["entries"][0]
    assert entrada["status"] == "ok" and entrada["usage"]["cache_read_input_tokens"] == 200
    assert "MARCADOR-PRIVADO" not in caplog.text and "coste_usd=" in caplog.text


def test_presupuesto_acumulado_persistente(tmp_path: Path) -> None:
    ia(tmp_path, Transporte()).analyze(msg("Mensaje uno: introduzca su clave"), [])
    ia(tmp_path, Transporte()).analyze(msg("Mensaje dos: introduzca su clave"), [])  # otra sesión, mismo libro
    assert gastado(tmp_path) == Decimal("0.014")


def test_presupuesto_insuficiente_para_el_peor_caso_bloquea_sin_enviar(tmp_path: Path) -> None:
    t = Transporte()
    r = ia(tmp_path, t, budget_usd="0.01").analyze(msg(), [])  # peor caso ≈ 0,04 USD > 0,01
    assert r.status is CheckStatus.FAILED and r.failure_reason and r.failure_reason.value == "budget_blocked"
    assert t.llamadas == 0 and gastado(tmp_path) == 0


def test_bloqueo_al_agotar_el_presupuesto(tmp_path: Path) -> None:
    t = Transporte(resp(usage={"input_tokens": 1000, "output_tokens": 3000}))  # 0,032 USD por solicitud
    a = ia(tmp_path, t, budget_usd="0.10", max_output_tokens=4000)
    estados = [a.analyze(msg(f"Mensaje {i}: introduzca su clave"), []).failure_reason for i in range(5)]
    assert t.llamadas < 5 and estados[-1] is not None and estados[-1].value == "budget_blocked"
    assert gastado(tmp_path) <= Decimal("0.10")


def test_limite_de_solicitudes_por_sesion(tmp_path: Path) -> None:
    t = Transporte()
    a = ia(tmp_path, t, max_requests=2)
    r = [a.analyze(msg(f"Mensaje {i}: introduzca su clave"), []) for i in range(3)]
    assert t.llamadas == 2 and r[2].failure_reason and r[2].failure_reason.value == "limit_exceeded"


def test_limite_de_tokens_de_entrada(tmp_path: Path) -> None:
    t = Transporte()
    r = ia(tmp_path, t, max_input_tokens=500).analyze(msg("palabra " * 2000), [])
    assert r.failure_reason and r.failure_reason.value == "limit_exceeded" and t.llamadas == 0


def test_mismo_mensaje_no_se_paga_dos_veces(tmp_path: Path) -> None:
    t = Transporte()
    a = ia(tmp_path, t)
    assert a.analyze(msg(), ["x"]) == a.analyze(msg(), ["x"])
    assert t.llamadas == 1 and gastado(tmp_path) == Decimal("0.007")


# --- Errores y respuestas incompletas ---------------------------------------------------------------
def test_tiempo_agotado_mantiene_el_cargo_pesimista(tmp_path: Path) -> None:
    from antifraude.ai.claude import AiTimeout
    r = ia(tmp_path, Transporte(AiTimeout("x"))).analyze(msg(), [])
    assert r.failure_reason and r.failure_reason.value == "timeout"
    assert gastado(tmp_path) > Decimal("0.03")  # pudo facturarse: se cuenta el peor caso


def test_error_http_4xx_no_cuenta_gasto(tmp_path: Path) -> None:
    class ErrorApi(Exception):
        status_code = 400
    r = ia(tmp_path, Transporte(ErrorApi("bad request"))).analyze(msg(), [])
    assert r.failure_reason and r.failure_reason.value == "api_error" and gastado(tmp_path) == 0


def test_respuesta_sin_usage_cuenta_el_peor_caso(tmp_path: Path) -> None:
    sin_usage = {"model": SONNET, "stop_reason": "end_turn", "content": [{"type": "text", "text": "{}"}]}
    ia(tmp_path, Transporte(sin_usage)).analyze(msg(), [])
    assert gastado(tmp_path) > Decimal("0.03")


@pytest.mark.parametrize("stop", ["max_tokens", "pause_turn", "tool_use", None])
def test_respuesta_incompleta_falla_pero_registra_el_gasto(tmp_path: Path, stop: str | None) -> None:
    r = ia(tmp_path, Transporte(resp(stop=stop))).analyze(msg(), [])  # type: ignore[arg-type]
    assert r.status is CheckStatus.FAILED and r.failure_reason and r.failure_reason.value == "invalid_output"
    assert gastado(tmp_path) == Decimal("0.007")


def test_libro_danado_no_gasta_ni_se_sobrescribe(tmp_path: Path) -> None:
    (tmp_path / "gasto.json").write_text("{roto", encoding="utf-8")
    t = Transporte()
    r = ia(tmp_path, t).analyze(msg(), [])
    assert r.failure_reason and r.failure_reason.value == "budget_blocked" and t.llamadas == 0
    assert (tmp_path / "gasto.json").read_text(encoding="utf-8") == "{roto"


# --- Concurrencia ---------------------------------------------------------------------------------
def test_una_sola_solicitud_en_curso(tmp_path: Path) -> None:
    dentro, salir = threading.Event(), threading.Event()

    def lento(params: Any) -> Any:
        dentro.set()
        salir.wait(5)
        return resp()

    p = politica(tmp_path)
    guard = CostGuard(p, wait_s=0.05)
    a = ClaudeAnalyzer(policy=p, api_key=None, transport=lento, guard=guard)
    resultados: list[Any] = []
    hilo = threading.Thread(target=lambda: resultados.append(a.analyze(msg("Uno: introduzca su clave"), [])))
    hilo.start()
    assert dentro.wait(5)
    segundo = a.analyze(msg("Dos: introduzca su clave"), [])
    salir.set()
    hilo.join(5)
    assert segundo.failure_reason and segundo.failure_reason.value == "busy"
    assert resultados[0].status is CheckStatus.DONE


def test_bloqueo_entre_procesos(tmp_path: Path) -> None:
    (tmp_path / "gasto.lock").write_text("", encoding="utf-8")  # otro proceso tiene una solicitud en curso
    t = Transporte()
    r = ia(tmp_path, t).analyze(msg(), [])
    assert r.failure_reason and r.failure_reason.value == "busy" and t.llamadas == 0


def test_guard_lanza_bloqueo_si_la_politica_no_permite(tmp_path: Path) -> None:
    with pytest.raises(BudgetBlocked):
        CostGuard(politica(tmp_path, enabled=False)).run(10, lambda: None, lambda _: (None, "x", None))


# --- Integración con el análisis: sin IA por presupuesto → parcial, nunca BAJO ---------------------
def test_presupuesto_agotado_da_analisis_parcial(tmp_path: Path) -> None:
    t = Transporte()
    a = ia(tmp_path, t, budget_usd="0.001")
    p = AnalysisPipeline(EntityDirectory.load_default(include_fictitious=True), a)
    out = p.run(from_manual_text("Hola, mira esto https://acort.test/x", USER))
    assert t.llamadas == 0 and out.assessment.is_partial and out.assessment.risk_level is not RiskLevel.LOW


def test_la_app_por_defecto_no_activa_la_ia() -> None:
    from antifraude.app.main import create_app
    app = create_app(Settings.from_env({"ANTHROPIC_API_KEY": "clave-de-prueba-no-real", "CLAUDE_MODEL": SONNET}),
                     issue_initial_code=False)
    assert app.state.ai_configured is False  # falta AI_ENABLED y presupuesto (y el SDK no está instalado)


# --- Regresiones de la revisión independiente del control de gasto (misión 3) -----------------------------
def test_borrar_el_libro_no_reinicia_el_presupuesto(tmp_path: Path) -> None:
    ia(tmp_path, Transporte()).analyze(msg("Uno: introduzca su clave"), [])
    (tmp_path / "gasto.json").unlink()  # queda la copia .bak
    assert gastado(tmp_path) == Decimal("0.007")


def test_libro_borrado_durante_la_solicitud_sigue_apuntando_el_coste(tmp_path: Path) -> None:
    def borra_y_responde(params: Any) -> Any:
        for f in tmp_path.glob("gasto.json*"):
            f.unlink()
        return resp()
    ClaudeAnalyzer(policy=politica(tmp_path), api_key=None, transport=borra_y_responde).analyze(msg(), [])
    assert gastado(tmp_path) == Decimal("0.007")


@pytest.mark.parametrize("valor", ["-1000", "NaN", "Infinity"])
def test_gasto_negativo_o_no_finito_bloquea(tmp_path: Path, valor: str) -> None:
    (tmp_path / "gasto.json").write_text(json.dumps({"version": 1, "spent_usd": valor, "entries": []}),
                                         encoding="utf-8")
    t = Transporte()
    r = ia(tmp_path, t).analyze(msg(), [])
    assert r.failure_reason and r.failure_reason.value == "budget_blocked" and t.llamadas == 0


def test_estimacion_por_exceso_con_emojis_y_otros_alfabetos() -> None:
    assert estimate_input_tokens("😀" * 5000) >= 10_000  # 4 bytes por emoji → ≥ 2 tokens estimados
    assert estimate_input_tokens("ñ" * 1000) >= 1000


def test_libro_dentro_del_repositorio_se_rechaza(tmp_path: Path) -> None:
    dentro = Path(__file__).resolve().parents[1] / "gasto_prueba.json"
    assert "fuera del repositorio" in (politica(tmp_path, ledger_path=dentro).blocked_reason() or "")


def test_bloqueo_ocupado_en_windows_no_rompe(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import antifraude.ai.budget as b

    real_open = b.os.open

    def abrir(path: Any, flags: int, *a: Any) -> int:
        if str(path).endswith(".lock"):
            raise PermissionError("pendiente de borrado")
        return real_open(path, flags, *a)

    monkeypatch.setattr(b.os, "open", abrir)
    t = Transporte()
    r = ia(tmp_path, t).analyze(msg(), [])
    assert r.failure_reason and r.failure_reason.value == "busy" and t.llamadas == 0


def test_mismo_mensaje_en_dos_hilos_se_paga_una_vez(tmp_path: Path) -> None:
    barrera = threading.Barrier(2)
    llamadas: list[int] = []

    def transporte(params: Any) -> Any:
        llamadas.append(1)
        return resp()

    a = ClaudeAnalyzer(policy=politica(tmp_path), api_key=None, transport=transporte)

    def tarea() -> None:
        barrera.wait()
        a.analyze(msg(), ["x"])

    hilos = [threading.Thread(target=tarea) for _ in range(2)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(10)
    assert len(llamadas) == 1


@pytest.mark.parametrize("codigo,cobra", [(400, False), (429, False), (408, True), (500, True)])
def test_errores_http_facturables_y_no_facturables(tmp_path: Path, codigo: int, cobra: bool) -> None:
    class ErrorApi(Exception):
        status_code = codigo
    ia(tmp_path, Transporte(ErrorApi("x"))).analyze(msg(), [])
    assert (gastado(tmp_path) > 0) is cobra


def test_fallo_al_liquidar_tras_pagar_conserva_la_respuesta(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import antifraude.ai.budget as b

    def falla(*a: Any, **k: Any) -> Any:
        raise b.LedgerError("disco lleno")

    monkeypatch.setattr(b.SpendLedger, "settle", falla)
    r = ia(tmp_path, Transporte()).analyze(msg(), [])
    assert r.status is CheckStatus.DONE  # la respuesta ya pagada se usa
    assert gastado(tmp_path) > Decimal("0.03")  # y el cargo pesimista reservado sigue apuntado

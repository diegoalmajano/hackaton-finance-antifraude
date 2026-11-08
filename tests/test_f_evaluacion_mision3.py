"""Misión 3, tarea F: ejecución reproducible de la evaluación. Sin IA real; ningún conjunto sellado real.

El «conjunto sellado» de estas pruebas es un archivo FALSO creado en una carpeta temporal a partir de casos dev:
sirve solo para comprobar el mecanismo (fuera del repositorio, huella, una sola ejecución, solo agregados).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

import antifraude.evaluation as ev
from antifraude.ai.budget import AiPolicy
from antifraude.ai.claude import ClaudeAnalyzer
from antifraude.app.pipeline import AnalysisPipeline
from antifraude.intel.entities import EntityDirectory

ROOT = Path(__file__).resolve().parents[1]
DEV = ROOT / "eval" / "datasets" / "dev" / "casos_dev.jsonl"


@pytest.fixture()
def resultados(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    d = tmp_path / "results"
    monkeypatch.setattr(ev, "RESULTS_DIR", d)
    for var in ("AI_ENABLED", "CLAUDE_MODEL", "AI_BUDGET_USD", "ANTHROPIC_API_KEY", "AI_LEDGER_PATH"):
        monkeypatch.delenv(var, raising=False)
    return d


def sellado_falso(tmp_path: Path) -> tuple[Path, str]:
    lineas = DEV.read_text(encoding="utf-8").splitlines()[:5]
    f = tmp_path / "fuera_del_repo" / "conjunto.jsonl"
    f.parent.mkdir()
    f.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return f, hashlib.sha256(f.read_bytes()).hexdigest()


def test_dev_por_defecto_genera_informe_json(resultados: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert ev.main([]) == 0
    salida = capsys.readouterr().out
    assert "NO son una evaluación" in salida
    informe = json.loads(next(resultados.glob("informe_desarrollo_*.json")).read_text(encoding="utf-8"))
    assert informe["tipo"] == "desarrollo" and "NO es una evaluación independiente" in informe["aviso"]
    assert informe["rule_version"] and informe["configuraciones"][0]["coste_real_usd"] == 0.0
    assert all("texto" not in c and "body" not in json.dumps(c) for c in informe["casos"])


def test_sellado_dentro_del_repo_se_rechaza(resultados: Path) -> None:
    assert ev.main(["--sellado", str(DEV), "--sha256", "0" * 64]) == 2


def test_sellado_con_huella_distinta_se_rechaza(resultados: Path, tmp_path: Path) -> None:
    f, _ = sellado_falso(tmp_path)
    assert ev.main(["--sellado", str(f), "--sha256", "0" * 64]) == 2


def test_sellado_solo_agregados_y_una_sola_vez(resultados: Path, tmp_path: Path,
                                               capsys: pytest.CaptureFixture[str]) -> None:
    f, sha = sellado_falso(tmp_path)
    assert ev.main(["--sellado", str(f), "--sha256", sha]) == 0
    salida = capsys.readouterr().out
    assert "dev-0" not in salida  # nunca identificadores ni textos de casos en pantalla
    informe = json.loads(next(resultados.glob("informe_sellado_*.json")).read_text(encoding="utf-8"))
    assert informe["sha256_conjunto"] == sha and "casos" not in informe and "diferencias" not in informe
    assert ev.main(["--sellado", str(f), "--sha256", sha]) == 2  # segunda ejecución: rechazada


def test_modo_ia_sin_configurar_no_gasta(resultados: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert ev.main(["--modo", "ambos"]) == 3
    assert "No se ha gastado nada" in capsys.readouterr().out


def test_modo_ia_exige_confirmar_el_gasto(resultados: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                          capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("AI_ENABLED", "1")
    monkeypatch.setenv("CLAUDE_MODEL", "claude-sonnet-5-5")
    monkeypatch.setenv("AI_BUDGET_USD", "0.50")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "clave-de-prueba-no-real")
    monkeypatch.setenv("AI_LEDGER_PATH", str(tmp_path / "gasto.json"))
    assert ev.main(["--modo", "ia"]) == 3
    salida = capsys.readouterr().out
    assert "Peor caso estimado" in salida and "--confirmar-gasto" in salida
    assert not (tmp_path / "gasto.json").exists()  # ninguna reserva ni solicitud


def test_comparacion_reglas_frente_a_ia_simulada(tmp_path: Path) -> None:
    """SIMULADO: un transporte falso «responde» como Claude para comprobar el informe comparativo."""
    def transporte(params: Any) -> dict[str, Any]:
        datos = {"claimed_entity": None, "tactics": [], "inconsistencies": [], "financial_request": None,
                 "injection_attempt": False, "uncertainties": [], "suggested_level": None}
        return {"model": "claude-sonnet-5-5", "stop_reason": "end_turn",
                "content": [{"type": "text", "text": json.dumps(datos)}],
                "usage": {"input_tokens": 1000, "output_tokens": 200}}

    casos = ev.load_cases([DEV])
    d = EntityDirectory.load_default(include_fictitious=True)
    ia = ClaudeAnalyzer(policy=AiPolicy(enabled=True, model="claude-sonnet-5-5", budget_usd="0.50",
                                        max_requests=100, ledger_path=tmp_path / "gasto.json"),
                        api_key=None, transport=transporte)
    reglas = ev.evaluate_config("reglas", casos, AnalysisPipeline(d))
    con_ia = ev.evaluate_config("reglas_ia", casos, AnalysisPipeline(d, ia))
    informe = ev.build_report("desarrollo", [reglas, con_ia], model="claude-sonnet-5-5", sealed_sha256=None)
    assert con_ia.ai_calls > 0 and con_ia.cost_usd == pytest.approx(0.004 * con_ia.ai_calls)
    assert {c["configuracion"] for c in informe["configuraciones"]} == {"reglas", "reglas_ia"}  # type: ignore[union-attr]
    assert isinstance(informe["diferencias"], list)
    # La IA (aquí sin hallazgos) completa el análisis: los casos parciales sin IA dejan de serlo.
    assert con_ia.metrics.inconclusive <= reglas.metrics.inconclusive


def test_sellado_marcado_antes_de_ejecutar(resultados: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    f, sha = sellado_falso(tmp_path)

    def cae(*a: Any, **k: Any) -> Any:
        raise RuntimeError("corte de luz")

    monkeypatch.setattr(ev, "evaluate_config", cae)
    with pytest.raises(RuntimeError):
        ev.main(["--sellado", str(f), "--sha256", sha])
    monkeypatch.undo()
    monkeypatch.setattr(ev, "RESULTS_DIR", resultados)
    assert ev.main(["--sellado", str(f), "--sha256", sha]) == 2  # no se puede repetir aunque cayera a mitad

"""Pruebas de F0-08: formato y coherencia del banco de evaluación (sin detector)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from antifraude.contracts import RiskLevel
from antifraude.contracts.evaluation import CaseOrigin, EvalCase, EvalSplit
from conftest import gitignore_ignora

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "eval"
DEV_DIR = EVAL / "datasets" / "dev"
DEMO = DEV_DIR / "demo.jsonl"

RESERVED_SUFFIXES = (".example", ".test", ".invalid", "example.com", "example.org", "example.net")


def load(path: Path) -> list[EvalCase]:
    return [EvalCase.model_validate_json(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def all_dev_cases() -> list[EvalCase]:
    return [c for f in sorted(DEV_DIR.glob("*.jsonl")) for c in load(f)]


def raw_demo() -> list[dict[str, Any]]:
    return [json.loads(line) for line in DEMO.read_text(encoding="utf-8").splitlines() if line.strip()]


def textos(c: EvalCase) -> str:
    m = c.message
    partes = [m.sender.address, m.sender.display_name or "", m.reply_to or "", m.subject or "", m.body_text,
              m.body_html or ""]
    return "\n".join(partes)


# --- Formato y particiones -------------------------------------------------------
def test_todos_los_casos_dev_son_validos_y_unicos() -> None:
    casos = all_dev_cases()
    assert casos, "no hay casos de desarrollo"
    ids = [c.case_id for c in casos]
    assert len(ids) == len(set(ids))
    assert all(c.split is EvalSplit.DEV and c.case_id.startswith("dev-") for c in casos)


def test_tres_casos_de_demo_en_orden() -> None:
    demo = sorted((c for c in load(DEMO) if c.demo_order), key=lambda c: c.demo_order or 0)
    assert [c.demo_order for c in demo] == [1, 2, 3]
    legitimo, evidente, sofisticado = demo
    assert legitimo.expected.risk_level is RiskLevel.LOW and not legitimo.expected.must_alert
    assert evidente.expected.risk_level is RiskLevel.HIGH and evidente.expected.must_alert
    assert sofisticado.expected.must_alert
    assert RiskLevel.LOW not in sofisticado.expected.acceptable_levels
    assert "urgencia" not in sofisticado.tags and "sin_urgencia" in sofisticado.tags  # no depende del tono


def test_origen_sintetico_etiquetado() -> None:
    for c in load(DEMO):
        assert c.is_synthetic is True
        assert c.origin in (CaseOrigin.SYNTHETIC_AI, CaseOrigin.SYNTHETIC_HUMAN)
        assert "sintética" in c.author


def test_casos_sin_resultados_del_detector() -> None:
    prohibidos = {"result", "results", "prediction", "predicted", "detector_output", "score", "assessment"}
    for caso in raw_demo():
        assert not prohibidos & set(caso)
        assert not prohibidos & set(caso["expected"])


def test_citas_esperadas_literales() -> None:
    for c in load(DEMO):
        visible = (c.message.subject or "") + "\n" + c.message.body_text
        for q in c.expected.expected_quotes:
            assert q in visible


def test_caso_sofisticado_tiene_enlace_con_texto_y_destino_distintos() -> None:
    c = next(c for c in load(DEMO) if c.demo_order == 3)
    html = c.message.body_html or ""
    m = re.search(r'<a href="([^"]+)">([^<]+)</a>', html)
    assert m, "falta el enlace en HTML"
    href, visible = m.groups()
    host = re.sub(r"^https?://", "", href).split("/")[0]
    assert visible == "www.bancoficticio.example" and not host.endswith("bancoficticio.example")
    assert c.message.reply_to and not c.message.reply_to.endswith("@bancoficticio.example")


# --- Datos ficticios ----------------------------------------------------------------
def test_solo_dominios_reservados() -> None:
    for c in all_dev_cases():
        t = textos(c)
        dominios = set(re.findall(r"@([a-z0-9.\-]+\.[a-z]+)", t))
        dominios |= {u.split("/")[0] for u in re.findall(r"(?:https?://|www\.)([a-z0-9.\-]+\.[a-z]+[^\s\"<]*)", t)}
        dominios |= set(re.findall(r"\b([a-z0-9\-]+(?:\.[a-z0-9\-]+)*\.(?:es|com|net|org|eu|info|io|co|me|ly|link))\b", t))
        for d in dominios:
            d = d.removeprefix("www.").rstrip(".")
            assert d.endswith(RESERVED_SUFFIXES), f"{c.case_id}: dominio no reservado {d}"


def _iban_valido(iban: str) -> bool:
    s = iban.replace(" ", "")
    s = s[4:] + s[:4]
    return int("".join(str(int(ch, 36)) for ch in s)) % 97 == 1


def test_sin_datos_personales() -> None:
    for c in all_dev_cases():
        t = textos(c)
        assert not re.search(r"(?<!\d)[6-9]\d{8}(?!\d)", t), "teléfono español"
        assert not re.search(r"\+\d{2}\s?\d", t), "teléfono internacional"
        assert not re.search(r"\b\d{8}[A-HJ-NP-TV-Z]\b", t), "DNI"
        assert not re.search(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b", t), "número de tarjeta"
        for iban in re.findall(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){4,7}\b", t):
            assert not _iban_valido(iban), "IBAN con dígitos de control válidos"


# --- Coherencia del contrato ------------------------------------------------------
def _caso(**cambios: Any) -> dict[str, Any]:
    base = raw_demo()[1]  # phishing evidente
    for ruta, valor in cambios.items():
        destino = base
        *partes, ultima = ruta.split(".")
        for p in partes:
            destino = destino[p]
        destino[ultima] = valor
    return base


@pytest.mark.parametrize("cambios", [
    {"expected.risk_level": "low"},                                   # BAJO con categorías y alerta
    {"expected.must_alert": False},                                    # ALTO sin alerta
    {"expected.acceptable_levels": ["medium"]},                        # nivel fuera de aceptables
    {"expected.acceptable_levels": ["low", "high"]},                   # alerta que acepta BAJO
    {"expected.fraud_categories": []},                                 # ALTO sin categorías
    {"expected.expected_quotes": ["texto que no está en el mensaje"]},  # cita no literal
    {"expected.key_signals": []},                                      # sin justificación
    {"case_id": "test-0002"},                                          # prefijo ≠ partición
    {"is_synthetic": False},                                           # sintético sin marcar
    {"message.received_at": "2026-11-03T22:41:00"},                    # fecha sin zona horaria
    {"origin": "real_customer"},                                       # origen no permitido
    {"expected.detector_level": "high"},                               # campo inventado
])
def test_casos_incoherentes_rechazados(cambios: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        EvalCase.model_validate(_caso(**cambios))


def test_caso_sellado_valido_en_formato_pero_no_en_el_repo() -> None:
    sellado = _caso(case_id="test-0001", split="sealed_test")
    assert EvalCase.model_validate(sellado).split is EvalSplit.SEALED_TEST
    en_repo = [c for f in EVAL.rglob("*.jsonl") for c in load(f)]
    assert all(c.split is EvalSplit.DEV for c in en_repo)


# --- Conjunto sellado fuera del repositorio -----------------------------------------
def test_no_existe_conjunto_sellado_en_el_repo() -> None:
    assert not (EVAL / "datasets" / "test_sealed").exists()
    assert not (EVAL / "sealed").exists()
    assert not list(ROOT.rglob("*.sealed.jsonl"))


@pytest.mark.parametrize("ruta", ["eval/datasets/test_sealed/casos.jsonl", "eval/sealed/x.jsonl",
                                  "eval/datasets/dev/final.sealed.jsonl", "eval/results/run.json"])
def test_gitignore_bloquea_rutas_selladas_y_resultados(ruta: str) -> None:
    assert gitignore_ignora(ruta), ruta


def test_casos_dev_versionables() -> None:
    assert not gitignore_ignora("eval/datasets/dev/demo.jsonl")


def test_documentacion_de_metricas() -> None:
    texto = (EVAL / "README.md").read_text(encoding="utf-8")
    for termino in ["Precision", "Recall", "F1", "Falsos positivos", "Latencia", "Coste por mensaje", "Wilson"]:
        assert termino.lower() in texto.lower(), termino
    assert "NO creado" in (EVAL / "SELLADO.md").read_text(encoding="utf-8")

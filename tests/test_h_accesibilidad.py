"""Correcciones de accesibilidad y claridad de la verificación del 09-11-2026.

axe-core marcó un ``<aside>`` dentro de otro punto de referencia en la portada; el historial repetía el
nivel («ALTO — ALTO: …»); dos frases casi idénticas en «Por qué» (remitente y enlace). La parte de navegador
real (axe, teclado, zoom 200 %, contraste forzado) está en ``docs/VERIFICACION_ACCESIBILIDAD_2026-11-09.md``.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from conftest import BASE_URL, ORIGIN, CodeCapture, FakeClock, Harness

from antifraude.analysis.ingest import build_message
from antifraude.app.main import create_app
from antifraude.app.pipeline import AnalysisPipeline
from antifraude.contracts import Channel
from antifraude.core.config import Settings
from antifraude.intel.entities import EntityDirectory

CSS = (Path(__file__).resolve().parents[1] / "backend/antifraude/app/static/css/app.css").read_text(encoding="utf-8")


@pytest.fixture
def demo() -> Harness:
    clock, codes = FakeClock(), CodeCapture()
    app = create_app(Settings.from_env({"APP_DEMO_MODE": "1"}), clock=clock, code_sink=codes)
    h = Harness(client=TestClient(app, base_url=BASE_URL), clock=clock, codes=codes)
    h.pair()
    return h


def analizar_ejemplo(h: Harness, n: int = 2) -> str:
    cab = {"Origin": ORIGIN, "HX-Request": "true", "X-CSRF-Token": h.csrf()}
    r = h.client.post(f"/analizar/ejemplo/{n}", headers=cab)
    assert r.status_code == 200, r.text
    return r.text


def test_portada_sin_aside_anidado(harness: Harness) -> None:
    html = harness.client.get("/").text
    assert "<aside" not in html
    assert 'class="portada-guia" role="group" aria-label="Cómo le ayuda el asistente"' in html


def test_historial_no_repite_el_nivel(demo: Harness) -> None:
    html = analizar_ejemplo(demo)
    assert "ALTO</strong> — ALTO:" not in html
    assert "ALTO</strong> — probable estafa" in html


def test_frases_de_remitente_y_enlace_distinguibles() -> None:
    p = AnalysisPipeline(EntityDirectory.load_default(include_fictitious=True))
    m = build_message(user_id=uuid4(), channel=Channel.MANUAL, body_html=None,
                      body_text="Acceda a https://bancoficticio-seguro.example/login para verificar su cuenta.")
    textos = [s.description_user for u in p.run(m).url_analyses for s in u.findings]
    assert "La dirección web del enlace se parece a la de una entidad, pero no es la oficial." in textos


def test_escudo_visible_en_contraste_forzado() -> None:
    bloque = CSS[CSS.rindex("@media (forced-colors: active)"):]
    assert "forced-color-adjust: none" in bloque.split("}")[0] + bloque.split("}")[1]

"""Regresiones de la revisión de accesibilidad (lo verificable sin navegador ni lector de pantalla)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from conftest import Harness

JS = (Path(__file__).resolve().parents[1] / "backend/antifraude/app/static/js/app.js").read_text(encoding="utf-8")
CSS = (Path(__file__).resolve().parents[1] / "backend/antifraude/app/static/css/app.css").read_text(encoding="utf-8")


def panel(h: Harness) -> str:
    h.pair()
    return h.client.get("/panel").text


def test_region_de_estado_unica_y_sin_anuncios_duplicados(harness: Harness) -> None:
    html = panel(harness)
    assert '<p id="estado-sr" class="sr-solo" role="status"></p>' in html
    assert not re.search(r'id="resultado"[^>]*aria-live', html)
    assert not re.search(r'id="lista-alertas"[^>]*aria-live', html)
    assert 'role="alert" aria-live' not in html  # sin duplicar alert + assertive


def test_mensajes_no_ocultos_con_hidden(harness: Harness) -> None:
    html = panel(harness)
    assert not re.search(r'id="(mensaje-analisis|aviso-global)"[^>]*\bhidden\b', html)
    assert ".mensaje:empty { display: none; }" in CSS


def test_foco_y_anuncio_tras_el_resultado() -> None:
    assert "htmx:afterSettle" in JS and 'getElementById("t-resultado")' in JS and ".focus()" in JS
    assert "Resultado listo: riesgo" in JS and "Analizando el mensaje, espere por favor." in JS


def test_botones_de_analisis_no_pierden_el_foco(harness: Harness) -> None:
    html = panel(harness)
    form = re.search(r'<form id="form-analizar".*?</form>', html, re.S)
    assert form and "hx-disabled-elt" not in form.group(0) and 'hx-sync="this:replace"' in form.group(0)


def test_tiempo_maximo_y_mensaje(harness: Harness) -> None:
    html = harness.client.get("/").text
    cfg = json.loads(re.search(r'<meta name="htmx-config" content=\'([^\']+)\'>', html).group(1))  # type: ignore[union-attr]
    assert cfg["timeout"] == 60000 and "htmx:timeout" in JS


def test_iconos_dinamicos_ocultos_y_tipo_en_palabras() -> None:
    assert 'setAttribute("aria-hidden", "true")' in JS
    assert '"Error: "' in JS and '"Aviso: "' in JS


def test_listas_con_semantica_y_separador(harness: Harness) -> None:
    html = panel(harness)
    assert '<ul class="niveles" role="list">' in html and '<ul class="lista-estados" role="list">' in html
    assert '<span class="nivel-nombre">BAJO</span><span class="sr-solo">. </span>' in html


def test_reflujo_sin_desbordamiento() -> None:
    assert "overflow-wrap: anywhere" in CSS and "::file-selector-button" in CSS


def test_lenguaje_mas_llano(harness: Harness) -> None:
    html = panel(harness)
    assert "archivo .eml" in html and "Si pega un texto y además elige un archivo" in html
    assert "Detalles técnicos" not in html

"""Etapa D: análisis manual desde la interfaz, ejemplos de demo, historial y seguridad."""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from antifraude.app.main import create_app
from antifraude.core.config import Settings
from conftest import BASE_URL, ORIGIN, CodeCapture, FakeClock, Harness

PHISHING = ("URGENTE: su cuenta será bloqueada. Introduzca su usuario y contraseña en "
            "http://bancoficticio-seguro.example/login")


def cabeceras(h: Harness) -> dict[str, str]:
    return {"Origin": ORIGIN, "HX-Request": "true", "X-CSRF-Token": h.csrf()}


def analizar(h: Harness, texto: str) -> str:
    r = h.client.post("/analizar", data={"texto": texto}, headers=cabeceras(h))
    assert r.status_code == 200, r.text
    return r.text


@pytest.fixture
def demo() -> Harness:
    clock, codes = FakeClock(), CodeCapture()
    app = create_app(Settings.from_env({"APP_DEMO_MODE": "1"}), clock=clock, code_sink=codes)
    h = Harness(client=TestClient(app, base_url=BASE_URL), clock=clock, codes=codes)
    h.pair()
    return h


def test_analizar_exige_sesion_y_csrf(harness: Harness) -> None:
    assert harness.client.post("/analizar", data={"texto": "x"}, headers={"Origin": ORIGIN}).status_code == 401
    harness.pair()
    assert harness.client.post("/analizar", data={"texto": "x"}, headers={"Origin": ORIGIN}).status_code == 403
    r = harness.client.post("/analizar", data={"texto": "x"},
                            headers={"Origin": "http://evil.example", "X-CSRF-Token": harness.csrf()})
    assert r.status_code == 403


def test_phishing_resultado_alto_explicado(harness: Harness) -> None:
    harness.pair()
    html = analizar(harness, PHISHING)
    assert "Aviso preventivo" in html and 'data-nivel="alto"' in html
    assert '<span class="nivel-nombre">ALTO</span>' in html
    assert "Qué le recomendamos" in html and "Por qué" in html
    assert "Lo que no hemos podido comprobar" in html
    assert "Análisis parcial" in html  # sin IA configurada (ADR-0015)
    assert "inteligencia artificial no está configurado" in html


def test_legitimo_bajo_sin_aviso_preventivo(harness: Harness) -> None:
    harness.pair()
    html = analizar(harness, "Su pedido llegará mañana entre las 9 y las 14. No tiene que pagar nada.")
    assert 'data-nivel="bajo"' in html and "Aviso preventivo" not in html


def test_contenido_hostil_se_escapa(harness: Harness) -> None:
    harness.pair()
    html = analizar(harness, '<script>alert(1)</script> Introduzca su contraseña en http://x.test/"onmouseover="a')
    assert "<script>alert(1)" not in html and 'onmouseover="a' not in html


def test_texto_vacio_y_archivo_no_eml(harness: Harness) -> None:
    harness.pair()
    r = harness.client.post("/analizar", data={"texto": "   "}, headers=cabeceras(harness))
    assert r.status_code == 400 and "Pegue el texto" in r.json()["detail"]
    r = harness.client.post("/analizar", files={"archivo": ("x.exe", b"MZ", "application/octet-stream")},
                            headers=cabeceras(harness))
    assert r.status_code == 400 and ".eml" in r.json()["detail"]


def test_importar_eml(harness: Harness) -> None:
    harness.pair()
    eml = (b"From: Banco Ficticio <a@bancoficticio-x.example>\r\nSubject: Aviso\r\n"
           b"Content-Type: text/plain; charset=utf-8\r\n\r\nIntroduzca su clave en http://bancoficticio-x.example/l\r\n")
    r = harness.client.post("/analizar", files={"archivo": ("correo.eml", eml, "message/rfc822")},
                            headers=cabeceras(harness))
    assert r.status_code == 200 and "Riesgo" in r.text


def test_historial_sin_texto_del_mensaje(harness: Harness) -> None:
    harness.pair()
    secreto = "Mi vecina Rosalía me debe 37 euros"
    analizar(harness, secreto)
    html = analizar(harness, PHISHING)
    assert 'hx-swap-oob="innerHTML"' in html and "Análisis manual" in html
    panel = harness.client.get("/panel").text
    assert "BAJO" in panel and "ALTO" in panel
    assert secreto not in panel and "Rosalía" not in panel


def test_historial_se_borra_al_cerrar_sesion(harness: Harness) -> None:
    harness.pair()
    analizar(harness, PHISHING)
    harness.client.post("/session/logout", headers=cabeceras(harness))
    harness.clock.advance(31)  # el código ya se usó: una sesión nueva requiere pedir otro
    harness.client.post("/pairing/code", headers={"Origin": ORIGIN})
    harness.pair()
    assert "Todavía no ha analizado ningún mensaje" in harness.client.get("/panel").text


def test_ejemplos_solo_en_modo_demo(harness: Harness) -> None:
    harness.pair()
    r = harness.client.post("/analizar/ejemplo/1", headers=cabeceras(harness))
    assert r.status_code == 404
    assert "MODO DEMOSTRACIÓN" not in harness.client.get("/panel").text


@pytest.mark.parametrize("n,nivel", [(1, "bajo"), (2, "alto"), (3, "alto")])
def test_ejemplos_de_demo_etiquetados(demo: Harness, n: int, nivel: str) -> None:
    r = demo.client.post(f"/analizar/ejemplo/{n}", headers=cabeceras(demo))
    assert r.status_code == 200
    assert "EJEMPLO SINTÉTICO" in r.text and f'data-nivel="{nivel}"' in r.text
    assert "MODO DEMOSTRACIÓN" in demo.client.get("/panel").text


def test_ejemplo_inexistente(demo: Harness) -> None:
    assert demo.client.post("/analizar/ejemplo/9", headers=cabeceras(demo)).status_code == 404


def test_html_del_resultado_compatible_con_csp(harness: Harness) -> None:
    harness.pair()
    html = analizar(harness, PHISHING)
    assert not re.search(r"<script|\sstyle=|\son[a-z]+=", html)

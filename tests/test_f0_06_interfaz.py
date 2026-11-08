"""Pruebas de F0-06: interfaz web accesible (Jinja + htmx local) sobre la seguridad de F0-05."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from antifraude.app.main import VENDOR_HTMX_DIR
from antifraude.app.security.policy import SESSION_ABSOLUTE_TIMEOUT_S, SESSION_COOKIE_NAME
from conftest import ORIGIN, Harness

PAGINAS_PUBLICAS = ["/", "/emparejar"]
HTMX_HEADERS = {"Origin": ORIGIN, "HX-Request": "true"}


def html_de(harness: Harness, ruta: str) -> str:
    r = harness.client.get(ruta)
    assert r.headers["content-type"].startswith("text/html")
    return r.text


def todas_las_paginas(harness: Harness) -> list[str]:
    paginas = [html_de(harness, p) for p in PAGINAS_PUBLICAS]
    paginas.append(harness.client.get("/panel").text)  # 401 con pantalla de emparejamiento
    harness.pair()
    paginas.append(html_de(harness, "/panel"))
    paginas.append(html_de(harness, "/"))
    return paginas


# --- Páginas y flujo -----------------------------------------------------------
def test_bienvenida_sin_sesion(harness: Harness) -> None:
    r = harness.client.get("/")
    assert r.status_code == 200
    assert '<html lang="es">' in r.text
    assert "Le ayudamos a reconocer mensajes" in r.text
    assert 'href="/emparejar"' in r.text and 'href="/panel"' not in r.text
    assert "todavía no está disponible" in r.text  # estado honesto


def test_bienvenida_con_sesion_ofrece_panel(harness: Harness) -> None:
    harness.pair()
    assert 'href="/panel"' in harness.client.get("/").text


def test_pantalla_de_emparejamiento(harness: Harness) -> None:
    r = harness.client.get("/emparejar")
    assert r.status_code == 200
    assert 'hx-post="/pairing"' in r.text and 'name="code"' in r.text
    assert 'for="codigo"' in r.text  # etiqueta asociada al campo
    assert 'hx-post="/pairing/code"' in r.text


def test_el_codigo_nunca_aparece_en_la_pagina(harness: Harness) -> None:
    code = harness.codes.last
    for ruta in PAGINAS_PUBLICAS + ["/panel"]:
        texto = harness.client.get(ruta).text
        assert code not in texto and f"{code[:4]}-{code[4:]}" not in texto


def test_panel_sin_sesion_muestra_emparejamiento(harness: Harness) -> None:
    r = harness.client.get("/panel")
    assert r.status_code == 401
    assert r.headers["content-type"].startswith("text/html")
    assert "primero conecte este navegador" in r.text
    assert 'hx-post="/pairing"' in r.text
    assert "Su panel de protección" not in r.text


def test_panel_con_sesion_caducada(harness: Harness) -> None:
    harness.pair()
    harness.clock.advance(SESSION_ABSOLUTE_TIMEOUT_S)
    r = harness.client.get("/panel")
    assert r.status_code == 401
    assert "ha caducado" in r.text
    assert f'{SESSION_COOKIE_NAME}=""' in r.headers.get("set-cookie", "")


def test_panel_con_sesion(harness: Harness) -> None:
    harness.pair()
    r = harness.client.get("/panel")
    assert r.status_code == 200
    t = r.text
    assert "Estado de protección" in t
    assert "Pendiente de implementación" in t
    assert "No hay alertas" in t  # sin resultados inventados
    assert 'hx-post="/session/logout"' in t and "Cerrar sesión" in t
    assert "Protección automática:</strong> todavía no está activa" in t
    for nivel in ["BAJO", "MEDIO", "ALTO", "NO CONCLUYENTE"]:
        assert f'<span class="nivel-nombre">{nivel}</span>' in t
    assert 'data-autenticado="1"' in t


def test_panel_no_contiene_secretos(harness: Harness) -> None:
    harness.pair()
    t = harness.client.get("/panel").text
    token = harness.csrf()
    cookie = harness.client.cookies.get(SESSION_COOKIE_NAME) or ""
    assert token not in t and cookie and cookie not in t
    assert "csrf" not in t.lower()


def test_emparejar_con_sesion_redirige_al_panel(harness: Harness) -> None:
    harness.pair()
    r = harness.client.get("/emparejar", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/panel"


def test_flujo_htmx_emparejar_y_cerrar_sesion(harness: Harness) -> None:
    r = harness.client.post("/pairing", data={"code": harness.codes.last}, headers=HTMX_HEADERS)
    assert r.status_code == 204 and r.headers["HX-Redirect"] == "/panel"
    assert harness.client.get("/panel").status_code == 200
    token = harness.csrf()
    r = harness.client.post("/session/logout", headers={**HTMX_HEADERS, "X-CSRF-Token": token})
    assert r.status_code == 204 and r.headers["HX-Redirect"] == "/"
    assert harness.client.get("/panel").status_code == 401


def test_sin_htmx_no_hay_hx_redirect(harness: Harness) -> None:
    r = harness.client.post("/pairing", data={"code": harness.codes.last}, headers={"Origin": ORIGIN})
    assert r.status_code == 204 and "HX-Redirect" not in r.headers


def test_error_de_emparejamiento_es_json_legible(harness: Harness) -> None:
    r = harness.client.post("/pairing", data={"code": "AAAAAAAA"}, headers=HTMX_HEADERS)
    assert r.status_code == 401 and "Código incorrecto" in r.json()["detail"]
    assert "HX-Redirect" not in r.headers


def test_logout_htmx_sin_csrf_rechazado(harness: Harness) -> None:
    harness.pair()
    r = harness.client.post("/session/logout", headers=HTMX_HEADERS)
    assert r.status_code == 403 and "HX-Redirect" not in r.headers


# --- Seguridad de las páginas ----------------------------------------------------
@pytest.mark.parametrize("ruta", ["/", "/emparejar", "/panel", "/static/css/app.css", "/vendor/htmx/htmx.min.js"])
def test_host_no_permitido_tambien_en_la_interfaz(harness: Harness, ruta: str) -> None:
    assert harness.client.get(ruta, headers={"Host": "evil.example"}).status_code == 400


def test_origin_ajeno_en_pagina(harness: Harness) -> None:
    harness.pair()
    assert harness.client.get("/panel", headers={"Origin": "http://evil.example"}).status_code == 403


def test_csp_estricta_en_paginas(harness: Harness) -> None:
    for ruta in PAGINAS_PUBLICAS:
        csp = harness.client.get(ruta).headers["content-security-policy"]
        assert "script-src 'self'" in csp and "style-src 'self'" in csp
        assert "unsafe-inline" not in csp and "unsafe-eval" not in csp


def test_html_compatible_con_csp_y_sin_recursos_externos(harness: Harness) -> None:
    for html in todas_las_paginas(harness):
        assert not re.search(r"<script(?![^>]*\bsrc=)[^>]*>", html), "script en línea"
        assert not re.search(r"<style\b", html), "estilo en línea"
        assert not re.search(r"\sstyle=", html), "atributo style"
        assert not re.search(r"\son[a-z]+=", html), "manejador en línea"
        assert not re.search(r"\shx-on", html), "hx-on usa eval"
        assert not re.search(r"(src|href|action)=\"(https?:)?//", html), "recurso externo"
        for ruta in re.findall(r"(?:src|href)=\"([^\"]+)\"", html):
            assert ruta.startswith(("/", "#")), ruta


def test_configuracion_htmx_segura(harness: Harness) -> None:
    html = harness.client.get("/").text
    m = re.search(r'<meta name="htmx-config" content=\'([^\']+)\'>', html)
    assert m, "falta la configuración de htmx"
    cfg = json.loads(m.group(1))
    assert cfg["includeIndicatorStyles"] is False  # evita <style> en línea
    assert cfg["allowEval"] is False and cfg["allowScriptTags"] is False
    assert cfg["historyEnabled"] is False and cfg["historyCacheSize"] == 0  # nada en sessionStorage
    assert cfg["selfRequestsOnly"] is True


def test_recursos_servidos_localmente(harness: Harness) -> None:
    html = harness.client.get("/").text
    assert 'src="/vendor/htmx/htmx.min.js"' in html
    assert 'src="/static/js/app.js"' in html and 'href="/static/css/app.css"' in html
    r = harness.client.get("/vendor/htmx/htmx.min.js")
    assert r.status_code == 200 and "javascript" in r.headers["content-type"]
    assert r.content == (VENDOR_HTMX_DIR / "htmx.min.js").read_bytes()
    for ruta, tipo in [("/static/js/app.js", "javascript"), ("/static/css/app.css", "text/css")]:
        r = harness.client.get(ruta)
        assert r.status_code == 200 and tipo in r.headers["content-type"]
        assert "content-security-policy" in r.headers


def test_app_js_no_usa_almacenamiento_ni_eval() -> None:
    js = (Path(__file__).parents[1] / "backend/antifraude/app/static/js/app.js").read_text(encoding="utf-8")
    codigo = re.sub(r"/\*.*?\*/", "", js, flags=re.S)  # sin comentarios
    for prohibido in ["localStorage", "sessionStorage", "document.cookie", "eval(", "new Function", "innerHTML"]:
        assert prohibido not in codigo, prohibido


@pytest.mark.parametrize("ruta", ["/static/..%2F..%2Fcore%2Fconfig.py", "/vendor/htmx/..%2F..%2Frequirements.txt",
                                  "/static/js/no-existe.js"])
def test_estaticos_sin_salir_de_su_carpeta(harness: Harness, ruta: str) -> None:
    assert harness.client.get(ruta).status_code == 404


def test_sse_sigue_protegido(harness: Harness) -> None:
    assert harness.client.get("/events").status_code == 401

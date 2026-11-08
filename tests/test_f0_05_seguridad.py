"""Pruebas de F0-05: seguridad de la API local (ADR-0013, D-30, D-39)."""

from __future__ import annotations

import logging
import re

import pytest

from antifraude.app.security.pairing import (
    IssueOutcome,
    PairingManager,
    VerifyOutcome,
    generate_code,
    normalize_code,
)
from antifraude.app.security.policy import (
    PAIRING_ALPHABET,
    PAIRING_CODE_TTL_S,
    SESSION_ABSOLUTE_TIMEOUT_S,
    SESSION_COOKIE_NAME,
    SESSION_IDLE_TIMEOUT_S,
)
from antifraude.app.security.sessions import SessionStore
from conftest import ORIGIN, FakeClock, Harness

EVIL = "http://evil.example"
OTHER_LOCAL_APP = "http://127.0.0.1:8765"  # otra aplicación local: mismo sitio, distinto origen


def wrong(code: str) -> str:
    """Un código válido en formato pero distinto del correcto."""
    first = "A" if code[0] != "A" else "B"
    return first + code[1:]


# --- Acceso sin sesión --------------------------------------------------------
@pytest.mark.parametrize("ruta", ["/session", "/events"])
def test_acceso_sin_sesion_rechazado(harness: Harness, ruta: str) -> None:
    r = harness.client.get(ruta)
    assert r.status_code == 401
    assert "sesión" in r.json()["detail"].lower()


def test_sse_sin_sesion_rechazado_y_con_sesion_permitido(harness: Harness) -> None:
    assert harness.client.get("/events").status_code == 401
    harness.pair()
    r = harness.client.get("/events")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    assert "event: ready" in r.text


def test_cookie_falsa_o_malformada(harness: Harness) -> None:
    for valor in ["x", "A" * 43, "../../etc", "a" * 500]:
        harness.client.cookies.set(SESSION_COOKIE_NAME, valor)
        assert harness.client.get("/session").status_code == 401


def test_health_publico_y_sin_datos(harness: Harness) -> None:
    r = harness.client.get("/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


# --- Emparejamiento -----------------------------------------------------------
def test_emparejamiento_correcto_crea_cookie_segura(harness: Harness) -> None:
    r = harness.client.post("/pairing", data={"code": harness.codes.last}, headers={"Origin": ORIGIN})
    assert r.status_code == 204
    cookie = r.headers["set-cookie"]
    assert cookie.startswith(f"{SESSION_COOKIE_NAME}=")
    assert "HttpOnly" in cookie and "SameSite=strict" in cookie and "Path=/" in cookie
    assert f"Max-Age={SESSION_ABSOLUTE_TIMEOUT_S}" in cookie
    assert harness.client.get("/session").status_code == 200


def test_formato_flexible_del_codigo(harness: Harness) -> None:
    code = harness.codes.last
    harness.pair(f" {code[:4].lower()}-{code[4:].lower()} ")


def test_emparejamiento_incorrecto(harness: Harness) -> None:
    r = harness.client.post("/pairing", data={"code": wrong(harness.codes.last)}, headers={"Origin": ORIGIN})
    assert r.status_code == 401
    assert "Le quedan 4 intentos" in r.json()["detail"]
    assert SESSION_COOKIE_NAME not in r.headers.get("set-cookie", "")


def test_codigo_reutilizado(harness: Harness) -> None:
    code = harness.codes.last
    harness.pair(code)
    r = harness.client.post("/pairing", data={"code": code}, headers={"Origin": ORIGIN})
    assert r.status_code == 401 and "ya se ha utilizado" in r.json()["detail"]


def test_codigo_caducado(harness: Harness) -> None:
    code = harness.codes.last
    harness.clock.advance(PAIRING_CODE_TTL_S)
    r = harness.client.post("/pairing", data={"code": code}, headers={"Origin": ORIGIN})
    assert r.status_code == 401 and "caducado" in r.json()["detail"]


def test_nuevo_codigo_tras_caducar(harness: Harness) -> None:
    old = harness.codes.last
    harness.clock.advance(PAIRING_CODE_TTL_S)
    r = harness.client.post("/pairing/code", headers={"Origin": ORIGIN})
    assert r.status_code == 202
    assert harness.codes.last != old
    assert harness.codes.last not in r.text  # el código nunca viaja por HTTP
    harness.pair()


def test_no_se_emite_codigo_si_hay_uno_vigente(harness: Harness) -> None:
    r = harness.client.post("/pairing/code", headers={"Origin": ORIGIN})
    assert r.status_code == 409 and len(harness.codes.codes) == 1


def test_limite_de_intentos_y_espera(harness: Harness) -> None:
    code = harness.codes.last
    bad = wrong(code)
    esperas = []
    for intento in range(1, 5):
        r = harness.client.post("/pairing", data={"code": bad}, headers={"Origin": ORIGIN})
        assert r.status_code == 401
        espera = int(r.headers["Retry-After"])
        esperas.append(espera)
        # Durante la espera, ni siquiera el código correcto se evalúa
        r = harness.client.post("/pairing", data={"code": code}, headers={"Origin": ORIGIN})
        assert r.status_code == 429
        harness.clock.advance(espera)
    assert esperas == [1, 2, 4, 8]
    r = harness.client.post("/pairing", data={"code": bad}, headers={"Origin": ORIGIN})
    assert r.status_code == 403 and "bloqueado" in r.json()["detail"]
    # Bloqueado: ni el código correcto ni pedir uno nuevo sirven
    harness.clock.advance(3600)
    assert harness.client.post("/pairing", data={"code": code}, headers={"Origin": ORIGIN}).status_code == 403
    assert harness.client.post("/pairing/code", headers={"Origin": ORIGIN}).status_code == 403


def test_pedir_codigos_nuevos_no_reinicia_los_intentos() -> None:
    clock = FakeClock()
    codes: list[str] = []
    pm = PairingManager(clock=clock, sink=lambda c, t: codes.append(c))
    assert pm.issue_code() is IssueOutcome.ISSUED
    for _ in range(4):
        r = pm.verify(wrong(codes[-1]))
        assert r.outcome is VerifyOutcome.INVALID
        clock.advance(PAIRING_CODE_TTL_S)  # el código caduca y se pide otro
        assert pm.issue_code() is IssueOutcome.ISSUED
    assert pm.verify(wrong(codes[-1])).outcome is VerifyOutcome.LOCKED


def test_limite_de_codigos_por_ejecucion() -> None:
    clock = FakeClock()
    pm = PairingManager(clock=clock, sink=lambda c, t: None)
    emitidos = 0
    for _ in range(20):
        if pm.issue_code() is IssueOutcome.ISSUED:
            emitidos += 1
        clock.advance(PAIRING_CODE_TTL_S)
    assert emitidos == 10
    assert pm.issue_code() is IssueOutcome.LIMIT_REACHED


def test_intervalo_minimo_entre_codigos() -> None:
    clock = FakeClock()
    codes: list[str] = []
    pm = PairingManager(clock=clock, sink=lambda c, t: codes.append(c))
    pm.issue_code()
    assert pm.verify(codes[-1]).outcome is VerifyOutcome.SUCCESS
    assert pm.issue_code() is IssueOutcome.TOO_SOON


def test_codigo_aleatorio_formato() -> None:
    muestras = {generate_code() for _ in range(200)}
    assert len(muestras) == 200
    assert all(len(c) == 8 and set(c) <= set(PAIRING_ALPHABET) for c in muestras)
    assert not set("IL O01") & set(PAIRING_ALPHABET)
    assert normalize_code(" abcd-efgh ") == "ABCDEFGH"


def test_codigo_demasiado_largo_no_se_evalua(harness: Harness) -> None:
    r = harness.client.post("/pairing", data={"code": "A" * 100}, headers={"Origin": ORIGIN})
    assert r.status_code == 422
    assert "A" * 100 not in r.text  # no se refleja lo enviado
    # y no consume intentos
    r = harness.client.post("/pairing", data={"code": wrong(harness.codes.last)}, headers={"Origin": ORIGIN})
    assert "Le quedan 4 intentos" in r.json()["detail"]


# --- Expiración de sesión -----------------------------------------------------
def test_sesion_caduca_por_inactividad(harness: Harness) -> None:
    harness.pair()
    harness.clock.advance(SESSION_IDLE_TIMEOUT_S - 1)
    assert harness.client.get("/session").status_code == 200  # renueva la actividad
    harness.clock.advance(SESSION_IDLE_TIMEOUT_S - 1)
    assert harness.client.get("/session").status_code == 200
    harness.clock.advance(SESSION_IDLE_TIMEOUT_S)
    r = harness.client.get("/session")
    assert r.status_code == 401 and "caducado" in r.json()["detail"]


def test_sesion_caduca_por_duracion_absoluta() -> None:
    clock = FakeClock()
    store = SessionStore(clock=clock)
    raw, _ = store.create()
    paso = SESSION_IDLE_TIMEOUT_S - 60
    while clock.now - 1_000.0 + paso < SESSION_ABSOLUTE_TIMEOUT_S:
        clock.advance(paso)
        assert store.get(raw) is not None  # activa todo el tiempo
    clock.advance(paso)
    assert store.get(raw) is None


def test_sesion_guarda_solo_hash() -> None:
    store = SessionStore(clock=FakeClock())
    raw, _ = store.create()
    assert raw not in repr(store.__dict__)


def test_maximo_de_sesiones_activas() -> None:
    clock = FakeClock()
    store = SessionStore(clock=clock)
    ids = []
    for _ in range(4):
        ids.append(store.create()[0])
        clock.advance(1)
    assert store.get(ids[0]) is None and store.active_count == 3


def test_respuesta_401_borra_la_cookie(harness: Harness) -> None:
    harness.pair()
    harness.clock.advance(SESSION_ABSOLUTE_TIMEOUT_S)
    r = harness.client.get("/session")
    assert r.status_code == 401
    assert f'{SESSION_COOKIE_NAME}=""' in r.headers.get("set-cookie", "")


# --- Host / Origin / Sec-Fetch-Site --------------------------------------------
@pytest.mark.parametrize("host", ["evil.example", "127.0.0.1", "127.0.0.1:9999", "192.168.1.10:8790",
                                  "localhost.evil.example:8790", "0.0.0.0:8790"])
def test_host_no_permitido(harness: Harness, host: str) -> None:
    r = harness.client.get("/health", headers={"Host": host})
    assert r.status_code == 400


def test_host_localhost_permitido(harness: Harness) -> None:
    assert harness.client.get("/health", headers={"Host": "localhost:8790"}).status_code == 200


@pytest.mark.parametrize("origin", [EVIL, OTHER_LOCAL_APP, "null", "http://localhost:8791"])
def test_origin_no_permitido_en_post(harness: Harness, origin: str) -> None:
    r = harness.client.post("/pairing", data={"code": harness.codes.last}, headers={"Origin": origin})
    assert r.status_code == 403
    assert harness.client.get("/session").status_code == 401  # no se creó sesión


def test_post_sin_origin_rechazado(harness: Harness) -> None:
    r = harness.client.post("/pairing", data={"code": harness.codes.last})
    assert r.status_code == 403


def test_origin_no_permitido_en_get_protegido(harness: Harness) -> None:
    harness.pair()
    assert harness.client.get("/events", headers={"Origin": EVIL}).status_code == 403


@pytest.mark.parametrize("site", ["cross-site", "same-site"])
def test_sec_fetch_site_ajeno(harness: Harness, site: str) -> None:
    harness.pair()
    assert harness.client.get("/session", headers={"Sec-Fetch-Site": site}).status_code == 403


def test_sin_cors(harness: Harness) -> None:
    r = harness.client.options("/session", headers={"Origin": ORIGIN, "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in r.headers


# --- CSRF -----------------------------------------------------------------------
def test_logout_sin_token_csrf(harness: Harness) -> None:
    harness.pair()
    r = harness.client.post("/session/logout", headers={"Origin": ORIGIN})
    assert r.status_code == 403
    assert harness.client.get("/session").status_code == 200  # la sesión sigue


def test_logout_con_token_csrf_invalido(harness: Harness) -> None:
    harness.pair()
    r = harness.client.post("/session/logout", headers={"Origin": ORIGIN, "X-CSRF-Token": "x" * 43})
    assert r.status_code == 403


def test_logout_con_token_csrf_valido(harness: Harness) -> None:
    harness.pair()
    token = harness.csrf()
    r = harness.client.post("/session/logout", headers={"Origin": ORIGIN, "X-CSRF-Token": token})
    assert r.status_code == 204
    assert harness.client.get("/session").status_code == 401


def test_csrf_sin_sesion_es_401(harness: Harness) -> None:
    r = harness.client.post("/session/logout", headers={"Origin": ORIGIN, "X-CSRF-Token": "x"})
    assert r.status_code == 401


# --- Límites, cabeceras y errores ----------------------------------------------
def test_cuerpo_demasiado_grande(harness: Harness) -> None:
    r = harness.client.post("/pairing", headers={"Origin": ORIGIN, "Content-Length": str(7 * 1024 * 1024),
                                                 "Content-Type": "application/x-www-form-urlencoded"},
                            content=b"code=AAAA")
    assert r.status_code == 413


def test_cabeceras_de_seguridad_en_todas_las_respuestas(harness: Harness) -> None:
    for r in [harness.client.get("/health"), harness.client.get("/session"),
              harness.client.get("/health", headers={"Host": "evil.example"})]:
        assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
        assert "script-src 'self'" in r.headers["content-security-policy"]
        assert r.headers["x-content-type-options"] == "nosniff"
        assert r.headers["cache-control"] == "no-store"
        assert r.headers["referrer-policy"] == "no-referrer"


def test_errores_sin_detalles_tecnicos(harness: Harness) -> None:
    r = harness.client.get("/no-existe")
    assert r.status_code == 404 and r.json() == {"detail": "No encontrado."}
    r = harness.client.put("/session", headers={"Origin": ORIGIN})
    assert r.status_code == 405 and "Traceback" not in r.text


def test_rutas_sin_tokens_en_url(harness: Harness) -> None:
    rutas = [getattr(r, "path", "") for r in harness.client.app.routes]  # type: ignore[attr-defined]
    assert not any(re.search(r"\{.*(token|code|session).*\}", p, re.I) for p in rutas)


def test_no_se_registran_codigos_ni_sesiones(harness: Harness, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    code = harness.codes.last
    harness.client.post("/pairing", data={"code": wrong(code)}, headers={"Origin": ORIGIN})
    harness.clock.advance(1)
    harness.pair(code)
    token = harness.csrf()
    cookie = harness.client.cookies.get(SESSION_COOKIE_NAME) or ""
    registros = caplog.text
    for secreto in [code, wrong(code), token, cookie]:
        assert secreto and secreto not in registros

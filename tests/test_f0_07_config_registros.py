"""Pruebas de F0-07: configuración reproducible y privacidad de los registros."""

from __future__ import annotations

import logging
import re
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI

from antifraude.__main__ import CONFIG_HELP, load_settings
from antifraude.app.security.pairing import generate_code
from antifraude.core.config import DEFAULT_PORT, Settings
from antifraude.core.logging import REDACTED, RedactingFilter, build_log_config, redact
from conftest import ORIGIN, Harness

ROOT = Path(__file__).resolve().parents[1]
ENV_EXAMPLE = ROOT / ".env.example"
CONFIG_SRC = ROOT / "backend/antifraude/core/config.py"
SECRETO = "Su clave 4821 y el IBAN ES9121000418450200051332"


def parse_env_example() -> dict[str, str]:
    valores: dict[str, str] = {}
    for linea in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        clave, _, valor = linea.partition("=")
        valores[clave.strip()] = valor.strip()
    return valores


# --- .env.example ---------------------------------------------------------------
def test_env_example_cubre_todas_las_variables_leidas() -> None:
    leidas = set(re.findall(r'"([A-Z][A-Z0-9_]+)" in env', CONFIG_SRC.read_text(encoding="utf-8")))
    assert leidas == {"APP_PORT", "APP_LOG_LEVEL", "ANTHROPIC_API_KEY", "CLAUDE_MODEL"}
    assert set(parse_env_example()) == leidas


def test_env_example_sin_secretos_ni_modelo_decidido() -> None:
    valores = parse_env_example()
    assert valores["ANTHROPIC_API_KEY"] == ""
    assert valores["CLAUDE_MODEL"] == ""  # elección pendiente (D-24, D-32)
    texto = ENV_EXAMPLE.read_text(encoding="utf-8")
    assert not re.search(r"sk-ant-[A-Za-z0-9]", texto)


def test_env_example_documenta_cada_variable() -> None:
    texto = ENV_EXAMPLE.read_text(encoding="utf-8")
    for clave in parse_env_example():
        bloque = texto.split(f"\n{clave}=")[0].rsplit("\n\n", 1)[-1]
        assert bloque.strip().startswith("#"), f"{clave} sin comentario explicativo"


def test_env_example_produce_configuracion_valida_por_defecto() -> None:
    s = Settings.from_env(parse_env_example())
    assert s.port == DEFAULT_PORT and s.log_level == "INFO"
    assert s.anthropic_api_key is None and s.claude_model is None


def test_gitignore_excluye_env_pero_no_el_ejemplo() -> None:
    def ignorado(ruta: str) -> bool:
        r = subprocess.run(["git", "check-ignore", "-q", ruta], cwd=ROOT, capture_output=True)
        return r.returncode == 0
    assert ignorado(".env") and ignorado(".env.local")
    assert not ignorado(".env.example")


# --- Errores de configuración comprensibles -------------------------------------
@pytest.mark.parametrize("env,variable", [
    ({"APP_PORT": "80"}, "APP_PORT"),
    ({"APP_PORT": "no-es-numero"}, "APP_PORT"),
    ({"APP_LOG_LEVEL": "VERBOSO"}, "APP_LOG_LEVEL"),
])
def test_configuracion_invalida_explicada_sin_valores(env: dict[str, str], variable: str,
                                                      capsys: pytest.CaptureFixture[str]) -> None:
    env = {**env, "ANTHROPIC_API_KEY": "clave-de-prueba-no-real"}
    assert load_settings(env) is None
    err = capsys.readouterr().err
    assert "configuración del asistente no es válida" in err and variable in err
    assert "clave-de-prueba-no-real" not in err and "Traceback" not in err
    for valor in env.values():
        if valor not in ("80",):  # «80» aparece en el texto de ayuda («65535», «8790»)
            assert valor not in err


def test_ayuda_para_todos_los_ajustes() -> None:
    assert set(CONFIG_HELP) == set(Settings.model_fields)


def test_arranque_con_configuracion_invalida_sale_con_codigo_2() -> None:
    import os
    entorno = {"APP_PORT": "abc", "PYTHONIOENCODING": "utf-8", "SYSTEMROOT": os.environ.get("SYSTEMROOT", "")}
    r = subprocess.run([sys.executable, "-m", "antifraude"], cwd=ROOT / "backend", env=entorno,
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 2
    assert "APP_PORT debe ser un número entero" in r.stderr and "Traceback" not in r.stderr


# --- Filtro de registros --------------------------------------------------------
def test_redact_oculta_secretos() -> None:
    token = "A" * 20 + "b-c_" + "d" * 19  # 43 caracteres URL-safe
    code = generate_code()
    clave_falsa = "sk-" + "ant-" + "prueba-no-real_123"  # construida para no dejar un literal con forma de clave
    casos = {
        f"cookie af_session={token}; Path=/": token,
        f"X-CSRF-Token: {token}": token,
        "Authorization: Bearer abc.def.ghi": "abc.def.ghi",
        f"clave {clave_falsa}": clave_falsa,
        f"código {code} recibido": code,
        f"código {code[:4]}-{code[4:]} recibido": code[:4],
        f"token suelto {token}": token,
    }
    for texto, secreto in casos.items():
        resultado = redact(texto)
        assert secreto not in resultado and REDACTED in resultado, texto


def test_redact_no_altera_mensajes_normales() -> None:
    for texto in ["Uvicorn running on http://127.0.0.1:8790 (Press CTRL+C to quit)",
                  "Application startup complete.", "Started server process [1234]",
                  "Error interno no controlado: tipo=ValueError, origen=x.py:10, ruta=/panel"]:
        assert redact(texto) == texto


def test_filtro_elimina_trazas_y_argumentos() -> None:
    try:
        raise ValueError(SECRETO)
    except ValueError:
        record = logging.LogRecord("x", logging.ERROR, __file__, 1, "fallo %s", (SECRETO,), sys.exc_info())
    assert RedactingFilter().filter(record) is True
    assert record.exc_info is None and record.exc_text is None and record.args is None
    assert "ValueError" in record.getMessage()
    # El argumento se ha formateado antes de filtrar: el filtro protege la forma, no el contenido arbitrario.
    assert "traza de excepción" in record.getMessage()


def test_configuracion_de_registros() -> None:
    cfg = build_log_config("INFO")
    assert all("redact" in h.get("filters", []) for h in cfg["handlers"].values())
    assert cfg["loggers"]["uvicorn.access"]["handlers"] == []
    assert cfg["loggers"]["uvicorn.access"]["propagate"] is False
    assert cfg["formatters"]["default"]["use_colors"] is False
    logging.config.dictConfig(build_log_config("INFO"))  # la configuración es válida


# --- Errores internos sin datos ---------------------------------------------------
def _app_con_error(harness: Harness) -> FastAPI:
    app: FastAPI = harness.client.app  # type: ignore[assignment]

    def falla() -> None:
        raise ValueError(SECRETO)

    app.add_api_route("/__prueba_error", falla, methods=["GET"])
    return app


def test_error_interno_generico_y_registro_sin_contenido(harness: Harness,
                                                         caplog: pytest.LogCaptureFixture) -> None:
    _app_con_error(harness)
    caplog.set_level(logging.DEBUG)
    r = harness.client.get("/__prueba_error")
    assert r.status_code == 500
    assert r.json() == {"detail": "Se ha producido un error interno. Inténtelo de nuevo."}
    assert SECRETO not in r.text and "Traceback" not in r.text
    assert "content-security-policy" in r.headers  # también con cabeceras de seguridad
    assert "tipo=ValueError" in caplog.text and "ruta=/__prueba_error" in caplog.text
    assert SECRETO not in caplog.text
    assert all(rec.exc_info is None for rec in caplog.records)


def test_flujo_completo_sin_secretos_en_registros(harness: Harness, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    code = harness.codes.last
    harness.client.post("/pairing", data={"code": "AAAAAAAA"}, headers={"Origin": ORIGIN})
    harness.clock.advance(1)
    harness.pair(code)
    token = harness.csrf()
    cookie = harness.client.cookies.get("af_session") or ""
    harness.client.get("/panel")
    harness.client.post("/session/logout", headers={"Origin": ORIGIN, "X-CSRF-Token": token})
    for secreto in [code, token, cookie]:
        assert secreto and secreto not in caplog.text

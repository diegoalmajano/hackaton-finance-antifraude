"""Pruebas de F0-03: configuración, /health y escucha solo en loopback."""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from antifraude.app.main import create_app
from antifraude.core.config import (
    DEFAULT_PORT,
    LOOPBACK_HOST,
    Settings,
    ensure_loopback_host,
)

PAQUETES = ["connectors", "analysis", "intel", "ai", "risk", "app", "contracts", "core"]


@pytest.mark.parametrize("nombre", PAQUETES)
def test_paquetes_importables(nombre: str) -> None:
    importlib.import_module(f"antifraude.{nombre}")


def test_config_por_defecto_sin_clave_ni_modelo() -> None:
    s = Settings.from_env({})
    assert s.host == LOOPBACK_HOST
    assert s.port == DEFAULT_PORT
    assert s.anthropic_api_key is None
    assert s.claude_model is None


def test_config_valores_vacios_son_none() -> None:
    s = Settings.from_env({"ANTHROPIC_API_KEY": "  ", "CLAUDE_MODEL": ""})
    assert s.anthropic_api_key is None
    assert s.claude_model is None


def test_clave_no_aparece_en_repr() -> None:
    s = Settings.from_env({"ANTHROPIC_API_KEY": "valor-de-prueba-no-real"})
    assert "valor-de-prueba-no-real" not in repr(s)
    assert "valor-de-prueba-no-real" not in str(s.model_dump())


@pytest.mark.parametrize("puerto", ["80", "70000", "abc"])
def test_puerto_invalido(puerto: str) -> None:
    with pytest.raises(ValidationError):
        Settings.from_env({"APP_PORT": puerto})


def test_host_no_configurable() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"host": "0.0.0.0"})


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "192.168.1.10", "localhost", "127.0.0.2", ""])
def test_ensure_loopback_rechaza(host: str) -> None:
    with pytest.raises(ValueError):
        ensure_loopback_host(host)


def test_ensure_loopback_acepta() -> None:
    assert ensure_loopback_host("127.0.0.1") == "127.0.0.1"


def _client() -> TestClient:
    app = create_app(Settings.from_env({}), code_sink=lambda code, ttl: None)
    return TestClient(app, base_url="http://127.0.0.1:8790")


def test_health_minimo() -> None:
    client = _client()
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
    assert r.headers["cache-control"] == "no-store"


def test_puerto_por_defecto_es_8790() -> None:
    assert DEFAULT_PORT == 8790


def test_puerto_ocupado_da_error_claro_en_espanol() -> None:
    import socket

    from antifraude.core.network import PortUnavailableError, ensure_port_available

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ocupado:
        ocupado.bind(("127.0.0.1", 0))
        ocupado.listen(1)
        puerto = ocupado.getsockname()[1]
        with pytest.raises(PortUnavailableError) as exc:
            ensure_port_available("127.0.0.1", puerto)
    texto = str(exc.value)
    assert f"puerto {puerto}" in texto and "APP_PORT" in texto and "ya está en uso" in texto


def test_puerto_libre_no_da_error() -> None:
    import socket

    from antifraude.core.network import ensure_port_available

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        libre = s.getsockname()[1]
    ensure_port_available("127.0.0.1", libre)


@pytest.mark.parametrize("ruta", ["/docs", "/redoc", "/openapi.json"])
def test_documentacion_automatica_desactivada(ruta: str) -> None:
    assert _client().get(ruta).status_code == 404

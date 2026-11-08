"""Arranque local: ``python -m antifraude`` (desde la carpeta ``backend``).

Escucha únicamente en 127.0.0.1 (ADR-0013). La configuración se toma de
variables de entorno (ver ``.env.example`` y ``docs/CONFIGURACION.md``); no se
carga ningún archivo ``.env`` automáticamente.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping

import uvicorn
from pydantic import ValidationError

from antifraude.app.main import create_app
from antifraude.core.config import Settings, ensure_loopback_host
from antifraude.core.logging import build_log_config
from antifraude.core.network import PortUnavailableError, ensure_port_available

#: Explicación de cada ajuste para el usuario. Nunca se muestra el valor recibido.
CONFIG_HELP: dict[str, str] = {
    "port": "APP_PORT debe ser un número entero entre 1024 y 65535 (por defecto, 8790).",
    "log_level": "APP_LOG_LEVEL debe ser DEBUG, INFO, WARNING o ERROR (por defecto, INFO).",
    "anthropic_api_key": "ANTHROPIC_API_KEY no tiene un formato válido.",
    "claude_model": "CLAUDE_MODEL no tiene un formato válido.",
    "demo_mode": "APP_DEMO_MODE debe ser 1 (activado) o 0 (desactivado).",
    "ai_enabled": "AI_ENABLED debe ser 1 (activada) o 0 (desactivada, por defecto).",
    "ai_allow_opus": "AI_ALLOW_OPUS debe ser 1 o 0 (por defecto, 0: Opus bloqueado).",
    "ai_budget_usd": "AI_BUDGET_USD debe ser un importe en USD entre 0 y 10 (por defecto, 0: sin gasto autorizado).",
    "ai_max_input_tokens": "AI_MAX_INPUT_TOKENS debe ser un entero entre 500 y 50000.",
    "ai_max_output_tokens": "AI_MAX_OUTPUT_TOKENS debe ser un entero entre 256 y 16000.",
    "ai_max_requests": "AI_MAX_REQUESTS debe ser un entero entre 0 y 1000.",
    "ai_thinking": "AI_THINKING debe ser «adaptive» u «off» (off solo con Sonnet 5.5).",
    "ai_effort": "AI_EFFORT debe ser low, medium o high.",
    "ai_ledger_path": "AI_LEDGER_PATH debe ser una ruta de archivo válida (fuera del repositorio).",
}


def load_settings(environ: Mapping[str, str] | None = None) -> Settings | None:
    """Carga los ajustes o explica en español qué variable revisar (sin mostrar valores)."""
    try:
        return Settings.from_env(environ)
    except ValidationError as exc:
        print("ERROR: la configuración del asistente no es válida.", file=sys.stderr)
        campos = sorted({str(err["loc"][0]) for err in exc.errors() if err.get("loc")})
        for campo in campos:
            print(f"  - {CONFIG_HELP.get(campo, 'Hay una variable de entorno no válida.')}", file=sys.stderr)
        print("Consulte docs/CONFIGURACION.md.", file=sys.stderr)
        return None


def main() -> int:
    settings = load_settings()
    if settings is None:
        return 2
    host = ensure_loopback_host(settings.host)
    try:
        ensure_port_available(host, settings.port)
    except PortUnavailableError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    uvicorn.run(
        create_app(settings),
        host=host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        log_config=build_log_config(settings.log_level),
        access_log=False,  # sin registro de rutas ni parámetros (logs mínimos)
        proxy_headers=False,  # no confiar en cabeceras X-Forwarded-*
        server_header=False,  # no anunciar el servidor
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

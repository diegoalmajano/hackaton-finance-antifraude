"""Arranque local: ``python -m antifraude`` (desde la carpeta ``backend``).

Escucha únicamente en 127.0.0.1 (ADR-0013).
"""

from __future__ import annotations

import sys

import uvicorn

from antifraude.app.main import create_app
from antifraude.core.config import ensure_loopback_host, get_settings
from antifraude.core.network import PortUnavailableError, ensure_port_available


def main() -> int:
    settings = get_settings()
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
        access_log=False,  # sin registro de rutas ni parámetros (logs mínimos)
        proxy_headers=False,  # no confiar en cabeceras X-Forwarded-*
        server_header=False,  # no anunciar el servidor
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Fábrica de la aplicación FastAPI."""

from __future__ import annotations

import time
from collections.abc import Callable

from fastapi import FastAPI

from antifraude.app.auth_routes import router as auth_router
from antifraude.app.errors import install_error_handlers
from antifraude.app.events import router as events_router
from antifraude.app.health import router as health_router
from antifraude.app.security.deps import SecurityState
from antifraude.app.security.middleware import (
    LocalSecurityMiddleware,
    allowed_hosts_for,
    allowed_origins_for,
)
from antifraude.app.security.pairing import CodeSink, PairingManager, console_code_sink
from antifraude.app.security.sessions import SessionStore
from antifraude.core.config import Settings, get_settings


def create_app(
    settings: Settings | None = None,
    *,
    clock: Callable[[], float] = time.monotonic,
    code_sink: CodeSink = console_code_sink,
    issue_initial_code: bool = True,
) -> FastAPI:
    """Crea la aplicación.

    La documentación automática (``/docs``, ``/redoc``, ``/openapi.json``) está
    desactivada: expondría la superficie de la API y Swagger UI carga recursos
    desde un CDN externo. No se instala CORS.
    """
    settings = settings or get_settings()
    app = FastAPI(
        title="Asistente antifraude (local)",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.settings = settings
    app.state.security = SecurityState(
        pairing=PairingManager(clock=clock, sink=code_sink),
        sessions=SessionStore(clock=clock),
    )
    install_error_handlers(app)
    app.add_middleware(
        LocalSecurityMiddleware,
        allowed_hosts=allowed_hosts_for(settings.port),
        allowed_origins=allowed_origins_for(settings.port),
    )
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(events_router)
    if issue_initial_code:
        app.state.security.pairing.issue_code()
    return app

"""Fábrica de la aplicación FastAPI."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import importlib.util

from antifraude.ai.claude import ClaudeAnalyzer
from antifraude.app.gmail_bridge import GmailBridge
from antifraude.app.gmail_routes import router as gmail_router
from antifraude.connectors.gmail_api import GmailApiClient, build_gmail_service, forget_local_token
from antifraude.app.analysis_routes import router as analysis_router
from antifraude.app.auth_routes import router as auth_router
from antifraude.app.pipeline import AnalysisPipeline
from antifraude.intel.entities import EntityDirectory
from antifraude.app.pages import router as pages_router
from antifraude.app.safe_errors import SafeErrorMiddleware
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

STATIC_DIR = Path(__file__).parent / "static"
#: htmx vendorizado en el repositorio (vendor/htmx), servido localmente sin CDN.
VENDOR_HTMX_DIR = Path(__file__).resolve().parents[3] / "vendor" / "htmx"


def _sdk_available() -> bool:
    """¿Está instalado el SDK oficial de Anthropic? (sin importarlo ni hacer red)."""
    return importlib.util.find_spec("anthropic") is not None


def create_app(
    settings: Settings | None = None,
    *,
    clock: Callable[[], float] = time.monotonic,
    code_sink: CodeSink = console_code_sink,
    issue_initial_code: bool = True,
    gmail_client_factory: Callable | None = None,
    gmail_forget_token: Callable[[], bool] | None = None,
    gmail_simulated: bool = False,
    gmail_interval_s: float = 30.0,
) -> FastAPI:
    """Crea la aplicación.

    La documentación automática (``/docs``, ``/redoc``, ``/openapi.json``) está
    desactivada: expondría la superficie de la API y Swagger UI carga recursos
    desde un CDN externo. No se instala CORS.
    """
    settings = settings or get_settings()
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            yield
        finally:
            app.state.gmail.close()

    app = FastAPI(
        lifespan=lifespan,
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
    # Orden: el último añadido es el más externo. SafeErrorMiddleware queda dentro del
    # middleware de seguridad, así las respuestas 500 también llevan sus cabeceras.
    app.add_middleware(SafeErrorMiddleware)
    app.add_middleware(
        LocalSecurityMiddleware,
        allowed_hosts=allowed_hosts_for(settings.port),
        allowed_origins=allowed_origins_for(settings.port),
    )
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(events_router)
    app.include_router(pages_router)
    app.include_router(analysis_router)
    app.include_router(gmail_router)

    # Pipeline de análisis: entidades ficticias solo en modo demostración (R-54); IA solo si se configura.
    directory = EntityDirectory.load_default(include_fictitious=settings.demo_mode)
    api_key = settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else None
    analyzer = ClaudeAnalyzer(policy=settings.ai_policy(), api_key=api_key)
    app.state.ai_configured = analyzer.configured and _sdk_available()
    # Motivo sin datos sensibles (nunca la clave); lo muestra la consola al arrancar (``__main__``).
    app.state.ai_status_text = ("activado, con control de gasto" if app.state.ai_configured else
                                "desactivado: " + (analyzer.blocked_reason
                                                   or "la librería oficial «anthropic» no está instalada."))
    app.state.pipeline = AnalysisPipeline(directory, analyzer)
    gmail_factory = None
    if settings.gmail_enabled:
        if gmail_client_factory is not None:
            gmail_factory = gmail_client_factory
        elif settings.gmail_client_secret_path is not None:
            def gmail_factory():
                return GmailApiClient(build_gmail_service(settings.gmail_client_secret_path, force_consent=True))
    app.state.gmail = GmailBridge(sessions=app.state.security.sessions,
        pipeline=AnalysisPipeline(directory), client_factory=gmail_factory,
        forget_token=gmail_forget_token or forget_local_token,
        simulated=gmail_simulated, interval_s=gmail_interval_s)
    if not (VENDOR_HTMX_DIR / "htmx.min.js").is_file():
        raise RuntimeError(f"No se encuentra htmx en {VENDOR_HTMX_DIR}; revise la instalación (vendor/htmx).")
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.mount("/vendor/htmx", StaticFiles(directory=VENDOR_HTMX_DIR), name="htmx")
    if issue_initial_code:
        app.state.security.pairing.issue_code()
    return app

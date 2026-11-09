"""Páginas HTML de la interfaz (F0-06): bienvenida, emparejamiento y panel.

Reutilizan el sistema de sesiones de F0-05 (no hay otra autenticación).
Nunca incluyen el código de emparejamiento, el identificador de sesión ni el
token CSRF en el HTML ni en URLs.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from antifraude.app.security.deps import SecurityDep
from antifraude.app.security.policy import SESSION_COOKIE_NAME
from antifraude.app.security.sessions import Session

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)

router = APIRouter()

AVISO_SIN_SESION = "Para ver su panel, primero conecte este navegador con el asistente."
AVISO_CADUCADA = (
    "Su sesión ha caducado por seguridad. Vuelva a conectar este navegador "
    "con un código del asistente."
)


def _session(request: Request, security: SecurityDep) -> Session | None:
    return security.sessions.get(request.cookies.get(SESSION_COOKIE_NAME))


def _render_pairing(request: Request, *, aviso: str | None, status_code: int, borrar_cookie: bool) -> Response:
    response = templates.TemplateResponse(
        request, "emparejar.html", {"aviso": aviso, "autenticado": False}, status_code=status_code
    )
    if borrar_cookie:
        response.delete_cookie(SESSION_COOKIE_NAME, path="/", httponly=True, samesite="strict")
    return response


@router.get("/", response_class=HTMLResponse)
def bienvenida(request: Request, security: SecurityDep) -> Response:
    autenticado = _session(request, security) is not None
    return templates.TemplateResponse(request, "bienvenida.html", {"autenticado": autenticado,
        "gmail_disponible": request.app.state.settings.gmail_enabled})


@router.get("/emparejar", response_class=HTMLResponse)
def emparejar(request: Request, security: SecurityDep) -> Response:
    if _session(request, security) is not None:
        return RedirectResponse("/panel", status_code=303)
    tenia_cookie = SESSION_COOKIE_NAME in request.cookies
    return _render_pairing(
        request,
        aviso=AVISO_CADUCADA if tenia_cookie else None,
        status_code=200,
        borrar_cookie=tenia_cookie,
    )


@router.get("/panel", response_class=HTMLResponse)
def panel(request: Request, security: SecurityDep) -> Response:
    if _session(request, security) is None:
        tenia_cookie = SESSION_COOKIE_NAME in request.cookies
        return _render_pairing(
            request,
            aviso=AVISO_CADUCADA if tenia_cookie else AVISO_SIN_SESION,
            status_code=401,
            borrar_cookie=tenia_cookie,
        )
    session = _session(request, security)
    return templates.TemplateResponse(request, "panel.html", {
        "autenticado": True,
        "demo_mode": request.app.state.settings.demo_mode,
        "ai_configured": request.app.state.ai_configured,
        "gmail": request.app.state.gmail.snapshot(session),
        "historial": session.history if session else [],
    })

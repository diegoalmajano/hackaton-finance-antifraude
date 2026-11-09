"""Control Gmail con sesión/CSRF/Origin; sin rutas de archivos ni tokens en formularios."""
from typing import Annotated
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, Response
from antifraude.app.errors import UserFacingError
from antifraude.app.gmail_bridge import GmailConnectionError
from antifraude.app.pages import templates
from antifraude.app.security.deps import CsrfSessionDep, PassiveSessionDep

router = APIRouter()


def _render(request, session):
    snapshot = request.app.state.gmail.snapshot(session)
    if request.method == "GET" and request.query_params.get("revision") == str(snapshot["revision"]):
        return Response(status_code=204)
    return templates.TemplateResponse(request, "partials/gmail.html", {"gmail": snapshot})


@router.get("/gmail", response_class=HTMLResponse)
def status(request: Request, session: PassiveSessionDep):
    return _render(request, session)


@router.post("/gmail/connect", response_class=HTMLResponse)
def connect(request: Request, session: CsrfSessionDep,
            consent: Annotated[bool, Form()] = False):
    if not consent:
        raise UserFacingError(400, "Marque la autorización para comprobar los mensajes nuevos de la cuenta de pruebas.")
    try:
        request.app.state.gmail.connect(session)
    except GmailConnectionError as exc:
        raise UserFacingError(409, str(exc)) from None
    return _render(request, session)


@router.post("/gmail/disconnect", response_class=HTMLResponse)
def disconnect(request: Request, session: CsrfSessionDep):
    request.app.state.gmail.disconnect(session)
    return _render(request, session)

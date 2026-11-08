"""Endpoints de emparejamiento y sesión (F0-05). Sin interfaz: la UI llega en F0-06."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Form, Request, Response
from pydantic import BaseModel

from antifraude.app.errors import UserFacingError
from antifraude.app.security.deps import CsrfSessionDep, SecurityDep, SessionDep
from antifraude.app.security.pairing import IssueOutcome, VerifyOutcome
from antifraude.app.security.policy import (
    PAIRING_MAX_INPUT_CHARS,
    SESSION_ABSOLUTE_TIMEOUT_S,
    SESSION_COOKIE_NAME,
)

router = APIRouter()


class SessionInfo(BaseModel):
    csrf_token: str


def _set_session_cookie(response: Response, raw_id: str) -> None:
    response.set_cookie(
        SESSION_COOKIE_NAME,
        raw_id,
        max_age=SESSION_ABSOLUTE_TIMEOUT_S,
        path="/",
        httponly=True,
        samesite="strict",
        secure=False,  # contexto http://127.0.0.1 (sin TLS); la cookie nunca sale de loopback
    )


def _is_htmx(request: Request) -> bool:
    return request.headers.get("hx-request") == "true"


@router.post("/pairing", status_code=204)
def pair(
    request: Request,
    code: Annotated[str, Form(max_length=PAIRING_MAX_INPUT_CHARS)],
    response: Response,
    security: SecurityDep,
) -> None:
    """El código llega SOLO en el cuerpo del POST; nunca en la URL ni en la respuesta."""
    result = security.pairing.verify(code)
    if result.outcome is VerifyOutcome.SUCCESS:
        raw_id, _ = security.sessions.create()
        _set_session_cookie(response, raw_id)
        if _is_htmx(request):
            response.headers["HX-Redirect"] = "/panel"  # navegación de la interfaz (F0-06)
        response.status_code = 204
        return
    if result.outcome is VerifyOutcome.INVALID:
        raise UserFacingError(
            401,
            f"Código incorrecto. Le quedan {result.remaining_attempts} intentos.",
            {"Retry-After": str(result.retry_after_s)},
        )
    if result.outcome is VerifyOutcome.WAIT:
        raise UserFacingError(
            429,
            "Por seguridad, espere unos segundos antes de volver a intentarlo.",
            {"Retry-After": str(result.retry_after_s)},
        )
    if result.outcome is VerifyOutcome.LOCKED:
        raise UserFacingError(
            403,
            "Por seguridad se ha bloqueado el emparejamiento tras varios intentos incorrectos. "
            "Cierre y vuelva a abrir el asistente para obtener un código nuevo.",
        )
    raise UserFacingError(401, "El código ha caducado o ya se ha utilizado. Solicite un código nuevo.")


@router.post("/pairing/code", status_code=202)
def request_new_code(security: SecurityDep) -> dict[str, str]:
    """Pide un código nuevo; se muestra SOLO en la consola del asistente."""
    outcome = security.pairing.issue_code()
    if outcome is IssueOutcome.ISSUED:
        return {"detail": "Se ha mostrado un código nuevo en la ventana del asistente."}
    messages = {
        IssueOutcome.ACTIVE_EXISTS: (409, "Ya hay un código vigente. Búsquelo en la ventana del asistente."),
        IssueOutcome.TOO_SOON: (429, "Espere un momento antes de pedir otro código."),
        IssueOutcome.LIMIT_REACHED: (403, "Se han solicitado demasiados códigos. Cierre y vuelva a abrir el asistente."),
        IssueOutcome.LOCKED: (403, "El emparejamiento está bloqueado por seguridad. Cierre y vuelva a abrir el asistente."),
    }
    status, message = messages[outcome]
    raise UserFacingError(status, message)


@router.get("/session", response_model=SessionInfo)
def session_info(session: SessionDep) -> SessionInfo:
    """Token CSRF de la sesión (legible solo desde el mismo origen; nunca va en URLs)."""
    return SessionInfo(csrf_token=session.csrf_token)


@router.post("/session/logout", status_code=204)
def logout(request: Request, response: Response, _: CsrfSessionDep, security: SecurityDep) -> None:
    security.sessions.revoke(request.cookies.get(SESSION_COOKIE_NAME))
    response.delete_cookie(SESSION_COOKIE_NAME, path="/", httponly=True, samesite="strict")
    if _is_htmx(request):
        response.headers["HX-Redirect"] = "/"
    response.status_code = 204

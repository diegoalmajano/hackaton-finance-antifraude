"""Dependencias FastAPI de autenticación y CSRF, y estado de seguridad de la app."""

from __future__ import annotations

import hmac
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request

from antifraude.app.security.pairing import PairingManager
from antifraude.app.security.policy import CSRF_HEADER_NAME, SESSION_COOKIE_NAME
from antifraude.app.security.sessions import Session, SessionStore


@dataclass(frozen=True)
class SecurityState:
    pairing: PairingManager
    sessions: SessionStore


class SessionRequired(Exception):
    """No hay sesión válida (inexistente, caducada o revocada)."""


class CsrfFailed(Exception):
    """Falta el token CSRF o no coincide."""


def get_security(request: Request) -> SecurityState:
    state: SecurityState = request.app.state.security
    return state


def require_session(request: Request, security: Annotated[SecurityState, Depends(get_security)]) -> Session:
    session = security.sessions.get(request.cookies.get(SESSION_COOKIE_NAME))
    if session is None:
        raise SessionRequired
    return session


def require_passive_session(request: Request, security: Annotated[SecurityState, Depends(get_security)]) -> Session:
    """Las actualizaciones automáticas no cuentan como actividad humana."""
    session = security.sessions.get(request.cookies.get(SESSION_COOKIE_NAME), touch=False)
    if session is None:
        raise SessionRequired
    return session


def require_csrf(request: Request, session: Annotated[Session, Depends(require_session)]) -> Session:
    token = request.headers.get(CSRF_HEADER_NAME)
    if not token or not hmac.compare_digest(token.encode(), session.csrf_token.encode()):
        raise CsrfFailed
    return session


SessionDep = Annotated[Session, Depends(require_session)]
CsrfSessionDep = Annotated[Session, Depends(require_csrf)]
SecurityDep = Annotated[SecurityState, Depends(get_security)]

PassiveSessionDep = Annotated[Session, Depends(require_passive_session)]

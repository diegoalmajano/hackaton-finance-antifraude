"""Gestión de errores: mensajes en español, sin detalles técnicos ni eco de datos enviados."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from antifraude.app.security.deps import CsrfFailed, SessionRequired
from antifraude.app.security.policy import SESSION_COOKIE_NAME

MSG_SESSION = "Su sesión no es válida o ha caducado. Vuelva a introducir el código de emparejamiento."
MSG_CSRF = "No se ha podido verificar la solicitud. Recargue la página e inténtelo de nuevo."
MSG_VALIDATION = "Los datos enviados no son válidos."
MSG_INTERNAL = "Se ha producido un error interno. Inténtelo de nuevo."

_GENERIC_BY_STATUS = {
    404: "No encontrado.",
    405: "Operación no permitida.",
}


class UserFacingError(Exception):
    """Error con mensaje ya redactado para el usuario (en español)."""

    def __init__(self, status_code: int, message: str, headers: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.headers = headers or {}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(SessionRequired)
    async def _session(_: Request, __: SessionRequired) -> JSONResponse:
        response = JSONResponse({"detail": MSG_SESSION}, status_code=401)
        response.delete_cookie(SESSION_COOKIE_NAME, path="/", httponly=True, samesite="strict")
        return response

    @app.exception_handler(CsrfFailed)
    async def _csrf(_: Request, __: CsrfFailed) -> JSONResponse:
        return JSONResponse({"detail": MSG_CSRF}, status_code=403)

    @app.exception_handler(UserFacingError)
    async def _user(_: Request, exc: UserFacingError) -> JSONResponse:
        return JSONResponse({"detail": exc.message}, status_code=exc.status_code, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, __: RequestValidationError) -> JSONResponse:
        # No se devuelve el detalle de Pydantic: podría reflejar lo enviado (p. ej. un código).
        return JSONResponse({"detail": MSG_VALIDATION}, status_code=422)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        message = _GENERIC_BY_STATUS.get(exc.status_code, "Solicitud no válida.")
        return JSONResponse({"detail": message}, status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def _internal(_: Request, __: Exception) -> JSONResponse:
        return JSONResponse({"detail": MSG_INTERNAL}, status_code=500)

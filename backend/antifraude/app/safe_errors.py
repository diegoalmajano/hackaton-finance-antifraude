"""Captura de errores no controlados sin filtrar datos (F0-07).

Sin esto, Starlette responde 500 pero vuelve a lanzar la excepción y Uvicorn
escribe la traza completa —incluido el mensaje de la excepción, que podría
contener contenido de un mensaje— en los registros.

Aquí se responde con un mensaje genérico en español y se registra solo el
**tipo** de excepción, el archivo y la línea de origen, y la ruta (sin
parámetros). Nunca el mensaje de la excepción.
"""

from __future__ import annotations

import logging
import traceback
from pathlib import Path

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from antifraude.app.errors import MSG_INTERNAL

logger = logging.getLogger("antifraude.errores")

_MAX_PATH_CHARS = 120


def _origin(exc: BaseException) -> str:
    frames = traceback.extract_tb(exc.__traceback__)
    if not frames:
        return "desconocido"
    last = frames[-1]
    return f"{Path(last.filename).name}:{last.lineno}"


class SafeErrorMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started = False

        async def tracking_send(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, receive, tracking_send)
        except Exception as exc:
            path = str(scope.get("path", "?"))[:_MAX_PATH_CHARS]
            logger.error(
                "Error interno no controlado: tipo=%s, origen=%s, ruta=%s",
                type(exc).__name__, _origin(exc), path,
            )
            if not started:
                await JSONResponse({"detail": MSG_INTERNAL}, status_code=500)(scope, receive, send)

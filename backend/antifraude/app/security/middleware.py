"""Middleware ASGI de seguridad (ADR-0013). Se aplica a TODAS las peticiones HTTP.

1. ``Host`` debe ser exactamente ``127.0.0.1:<puerto>`` o ``localhost:<puerto>``
   (defensa frente a DNS rebinding).
2. Métodos que cambian estado: ``Origin`` obligatorio y de la lista permitida.
3. Cualquier método: si llega ``Origin`` debe estar permitido; si llega
   ``Sec-Fetch-Site`` debe ser ``same-origin`` o ``none`` (otra aplicación en
   otro puerto de 127.0.0.1 es *same-site* pero NO *same-origin*: se rechaza).
4. Cuerpo limitado por ``Content-Length``; peticiones que cambian estado sin
   ``Content-Length`` se rechazan.
5. Cabeceras de seguridad en todas las respuestas (CSP estricta, no-store…).
Sin CORS: no se añade ``Access-Control-Allow-Origin`` en ningún caso.
Mensajes al usuario en español y sin detalles técnicos.
"""

from __future__ import annotations

from collections.abc import Iterable

from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from antifraude.app.security.policy import MAX_REQUEST_BODY_BYTES, SAFE_METHODS

SECURITY_HEADERS: dict[str, str] = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; "
        "connect-src 'self'; font-src 'self'; form-action 'self'; frame-ancestors 'none'; "
        "base-uri 'none'; object-src 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
}

_MSG_HOST = "Solicitud no permitida."
_MSG_ORIGIN = "Solicitud no permitida desde este origen."
_MSG_TOO_LARGE = "El contenido enviado es demasiado grande."
_MSG_LENGTH = "Solicitud no válida."


def allowed_hosts_for(port: int) -> frozenset[str]:
    return frozenset({f"127.0.0.1:{port}", f"localhost:{port}"})


def allowed_origins_for(port: int) -> frozenset[str]:
    return frozenset({f"http://127.0.0.1:{port}", f"http://localhost:{port}"})


class LocalSecurityMiddleware:
    def __init__(self, app: ASGIApp, *, allowed_hosts: Iterable[str], allowed_origins: Iterable[str]) -> None:
        self.app = app
        self.allowed_hosts = frozenset(h.lower() for h in allowed_hosts)
        self.allowed_origins = frozenset(o.lower() for o in allowed_origins)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "websocket":  # no hay WebSockets en esta aplicación
            await send({"type": "websocket.close", "code": 1008})
            return
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        rejection = self._check(scope)
        if rejection is not None:
            status, message = rejection
            response = JSONResponse({"detail": message}, status_code=status)
            await response(scope, receive, self._with_security_headers(send))
            return
        await self.app(scope, receive, self._with_security_headers(send))

    def _check(self, scope: Scope) -> tuple[int, str] | None:
        headers = Headers(scope=scope)
        if len(headers.getlist("host")) != 1 or headers.get("host", "").lower() not in self.allowed_hosts:
            return 400, _MSG_HOST

        method = scope["method"].upper()
        origin = headers.get("origin")
        if method not in SAFE_METHODS:
            if origin is None or origin.lower() not in self.allowed_origins:
                return 403, _MSG_ORIGIN
        elif origin is not None and origin.lower() not in self.allowed_origins:
            return 403, _MSG_ORIGIN

        fetch_site = headers.get("sec-fetch-site")
        if fetch_site is not None and fetch_site.lower() not in ("same-origin", "none"):
            return 403, _MSG_ORIGIN

        length = headers.get("content-length")
        if length is not None:
            if not length.isdigit():
                return 400, _MSG_LENGTH
            if int(length) > MAX_REQUEST_BODY_BYTES:
                return 413, _MSG_TOO_LARGE
        elif method not in SAFE_METHODS:
            return 411, _MSG_LENGTH
        if "transfer-encoding" in headers:
            return 400, _MSG_LENGTH
        return None

    @staticmethod
    def _with_security_headers(send: Send) -> Send:
        async def wrapped(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in SECURITY_HEADERS.items():
                    headers[name] = value
                for name in ("access-control-allow-origin", "access-control-allow-credentials"):
                    if name in headers:
                        del headers[name]
            await send(message)

        return wrapped

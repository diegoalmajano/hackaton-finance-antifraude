"""Canal SSE protegido.

Comprueba la autenticación al conectar y **revalida la sesión antes de cada evento** (R-35): si la sesión
caduca o se cierra, el flujo termina. Hoy solo envía un evento ``ready`` y termina; las alertas en
tiempo real (Gmail) usarán ``revalidating_stream`` con la misma garantía. No transmite contenido.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from antifraude.app.security.deps import SecurityDep, SessionDep
from antifraude.app.security.policy import SESSION_COOKIE_NAME

router = APIRouter()


def revalidating_stream(events: Iterable[str], is_valid: Callable[[], bool]) -> Iterator[str]:
    """Emite ``events`` solo mientras ``is_valid()`` sea cierto; lo comprueba ANTES de cada evento."""
    for event in events:
        if not is_valid():
            return
        yield event


@router.get("/events")
def events(request: Request, _: SessionDep, security: SecurityDep) -> StreamingResponse:
    raw_id = request.cookies.get(SESSION_COOKIE_NAME)

    def still_valid() -> bool:
        # touch=False: mantener abierto el canal no alarga la sesión por inactividad.
        return security.sessions.get(raw_id, touch=False) is not None

    base = ["retry: 15000\n\n", "event: ready\ndata: {}\n\n"]
    return StreamingResponse(revalidating_stream(base, still_valid), media_type="text/event-stream")

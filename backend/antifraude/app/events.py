"""Canal SSE protegido (esqueleto F0-05).

Solo comprueba la autenticación y envía un evento ``ready``; no transmite
contenido. Las alertas reales llegan en la fase e. Pendiente para entonces:
revalidar la sesión periódicamente durante conexiones largas.
"""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from antifraude.app.security.deps import SessionDep

router = APIRouter()


@router.get("/events")
def events(_: SessionDep) -> StreamingResponse:
    def stream() -> Iterator[str]:
        yield "retry: 15000\n\n"
        yield "event: ready\ndata: {}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")

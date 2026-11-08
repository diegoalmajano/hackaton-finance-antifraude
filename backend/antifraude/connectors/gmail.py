"""Conector de Gmail por consulta periódica de ``history.list`` (ADR-0004). Etapa E.

Estado: **lógica implementada y probada con un Gmail SIMULADO**. La conexión
real está **bloqueada** hasta disponer de (1) un proyecto de Google Cloud con
cliente OAuth «Desktop» y una cuenta de pruebas (B-04) y (2) autorización para
instalar ``google-auth-oauthlib``, ``google-api-python-client`` y ``keyring``.

El conector no analiza nada: entrega ``RawMessage`` (RFC 822) al pipeline común.
Solo lectura: no marca como leído ni modifica etiquetas. Incluye SPAM.
Un error de red o de autorización se señala en ``status``; nunca se presenta
como «sin mensajes nuevos».
"""

from __future__ import annotations

import base64
from collections.abc import Sequence
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Protocol

from antifraude.contracts.common import MAX_RAW_BYTES
from antifraude.contracts.input_adapter import InputAdapter
from antifraude.contracts.messages import Channel, RawFormat, RawMessage

#: 40 × 60 unidades (messages.get raw) + 2 (history.list), dos veces por minuto = 4 804 < 6 000 unidades/min/usuario.
MAX_MESSAGES_PER_POLL = 40
#: Memoria de identificadores ya entregados (evita duplicados sin crecer sin límite).
MAX_SEEN_IDS = 10_000
#: Mensajes pendientes para la siguiente consulta (por el máximo por consulta o por errores transitorios).
MAX_PENDING = 1_000
#: Intentos de descarga de un mismo mensaje antes de comunicarlo como «no se pudo analizar».
MAX_FETCH_ATTEMPTS = 3
RESYNC_RECENT = 20


class GmailHistoryExpired(Exception):
    """``startHistoryId`` demasiado antiguo (la API responde 404): hay que resincronizar."""


class GmailAuthError(Exception):
    """Credenciales caducadas o revocadas (p. ej. refresh token de 7 días en modo Testing)."""


class GmailClient(Protocol):
    """Subconjunto de la API de Gmail que usa el conector (implementación real pendiente)."""

    def get_profile_history_id(self) -> str: ...

    def list_history_message_ids(self, start_history_id: str) -> tuple[list[str], str]:
        """IDs de mensajes añadidos desde ``start_history_id`` (todas las páginas) y el nuevo historyId."""
        ...

    def list_recent_message_ids(self, max_results: int) -> list[str]: ...

    def get_raw_message(self, message_id: str) -> tuple[bytes, datetime | None]:
        """Mensaje en formato RFC 822 (``format=raw``, ya decodificado) y su fecha interna."""
        ...


class ConnectorStatus(StrEnum):
    NOT_STARTED = "not_started"
    OK = "ok"
    AUTH_ERROR = "auth_error"
    ERROR = "error"


@dataclass
class GmailState:
    history_id: str | None = None
    seen_ids: set[str] = field(default_factory=set)
    _order: deque[str] = field(default_factory=deque, repr=False)
    #: El historyId ya avanzó: lo que no se descargó en esta consulta se guarda aquí para no perderlo.
    pending: list[str] = field(default_factory=list)
    attempts: dict[str, int] = field(default_factory=dict)

    def mark_seen(self, message_id: str) -> None:
        if message_id in self.seen_ids:
            return
        self.seen_ids.add(message_id)
        self._order.append(message_id)
        while len(self._order) > MAX_SEEN_IDS:
            self.seen_ids.discard(self._order.popleft())


class GmailConnector(InputAdapter):
    channel = Channel.GMAIL

    def __init__(self, client: GmailClient, state: GmailState | None = None) -> None:
        self.client = client
        self.state = state or GmailState()
        self.status = ConnectorStatus.NOT_STARTED
        self.last_error: str | None = None
        #: Mensajes recibidos que NO se pueden analizar (vacíos o demasiado grandes): nunca se descartan en
        #: silencio; el sondeo los comunica para mostrar un aviso «no se pudo analizar» (revisión de seguridad A2).
        self.unanalyzable: list[str] = []

    def _collect(self) -> list[str]:
        if self.state.history_id is None:
            # Primera ejecución: no se analiza el buzón antiguo, solo lo que llegue desde ahora.
            self.state.history_id = self.client.get_profile_history_id()
            return []
        try:
            ids, new_history = self.client.list_history_message_ids(self.state.history_id)
            self.state.history_id = new_history
            return ids
        except GmailHistoryExpired:
            ids = self.client.list_recent_message_ids(RESYNC_RECENT)
            self.state.history_id = self.client.get_profile_history_id()
            return ids

    def _defer(self, ids: list[str]) -> None:
        _defer_into(self.state, ids, self.unanalyzable)

    def fetch_new(self) -> Sequence[RawMessage]:
        try:
            ids = self._collect()
        except GmailAuthError:
            self.status, self.last_error = ConnectorStatus.AUTH_ERROR, "Hay que volver a autorizar la cuenta de Gmail."
            return []
        except Exception:
            self.status, self.last_error = ConnectorStatus.ERROR, "No se pudo consultar Gmail."
            return []
        queue = self.state.pending + [m for m in ids if m not in self.state.pending]
        self.state.pending = []
        out: list[RawMessage] = []
        for i, mid in enumerate(queue):
            if mid in self.state.seen_ids:
                continue
            if len(out) >= MAX_MESSAGES_PER_POLL:
                self._defer(queue[i:])  # el resto, en la siguiente consulta (antes se perdía)
                break
            try:
                raw, received = self.client.get_raw_message(mid)
            except GmailAuthError:
                self._defer(queue[i:])
                self.status, self.last_error = ConnectorStatus.AUTH_ERROR, "Hay que volver a autorizar la cuenta de Gmail."
                return out
            except Exception:
                self.state.attempts[mid] = self.state.attempts.get(mid, 0) + 1
                if self.state.attempts[mid] >= MAX_FETCH_ATTEMPTS:
                    self.state.attempts.pop(mid, None)
                    self.state.mark_seen(mid)
                    self.unanalyzable.append(mid[:256])  # se comunica; no se reintenta para siempre
                else:
                    self._defer([mid])
                continue
            self.state.attempts.pop(mid, None)
            self.state.mark_seen(mid)
            if not raw or len(raw) > MAX_RAW_BYTES:
                self.unanalyzable.append(mid[:256])
                continue
            out.append(RawMessage(channel=Channel.GMAIL, raw_format=RawFormat.RFC822, payload=raw,
                                  received_at=received or datetime.now(timezone.utc),
                                  source_message_id=mid[:256]))
        self.status, self.last_error = ConnectorStatus.OK, None
        return out


def _defer_into(state: GmailState, ids: list[str], unanalyzable: list[str]) -> None:
    for mid in ids:
        if mid in state.seen_ids or mid in state.pending:
            continue
        if len(state.pending) >= MAX_PENDING:
            state.mark_seen(mid)
            unanalyzable.append(mid[:256])  # desbordamiento: se avisa en vez de perderlo en silencio
        else:
            state.pending.append(mid)


def decode_gmail_raw(raw_b64url: str) -> bytes:
    """Decodifica el campo ``raw`` de Gmail (base64url sin relleno)."""
    padded = raw_b64url + "=" * (-len(raw_b64url) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))

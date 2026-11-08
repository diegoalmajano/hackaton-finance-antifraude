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
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Protocol

from antifraude.contracts.common import MAX_RAW_BYTES
from antifraude.contracts.input_adapter import InputAdapter
from antifraude.contracts.messages import Channel, RawFormat, RawMessage

MAX_MESSAGES_PER_POLL = 50
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


class GmailConnector(InputAdapter):
    channel = Channel.GMAIL

    def __init__(self, client: GmailClient, state: GmailState | None = None) -> None:
        self.client = client
        self.state = state or GmailState()
        self.status = ConnectorStatus.NOT_STARTED
        self.last_error: str | None = None

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

    def fetch_new(self) -> Sequence[RawMessage]:
        try:
            ids = self._collect()
        except GmailAuthError:
            self.status, self.last_error = ConnectorStatus.AUTH_ERROR, "Hay que volver a autorizar la cuenta de Gmail."
            return []
        except Exception:
            self.status, self.last_error = ConnectorStatus.ERROR, "No se pudo consultar Gmail."
            return []
        out: list[RawMessage] = []
        for mid in ids:
            if mid in self.state.seen_ids or len(out) >= MAX_MESSAGES_PER_POLL:
                continue
            try:
                raw, received = self.client.get_raw_message(mid)
            except GmailAuthError:
                self.status, self.last_error = ConnectorStatus.AUTH_ERROR, "Hay que volver a autorizar la cuenta de Gmail."
                return out
            except Exception:
                continue  # se reintentará en la siguiente consulta (no se marca como visto)
            self.state.seen_ids.add(mid)
            if not raw or len(raw) > MAX_RAW_BYTES:
                continue
            out.append(RawMessage(channel=Channel.GMAIL, raw_format=RawFormat.RFC822, payload=raw,
                                  received_at=received or datetime.now(timezone.utc),
                                  source_message_id=mid[:256]))
        self.status, self.last_error = ConnectorStatus.OK, None
        return out


def decode_gmail_raw(raw_b64url: str) -> bytes:
    """Decodifica el campo ``raw`` de Gmail (base64url sin relleno)."""
    padded = raw_b64url + "=" * (-len(raw_b64url) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))

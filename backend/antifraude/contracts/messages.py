"""Recepción y normalización de mensajes.

``RawMessage``: lo que entrega un conector (sin analizar).
``IncomingMessage``: mensaje normalizado y minimizado que recorre el pipeline.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from antifraude.contracts.common import (
    MAX_ATTACHMENTS,
    MAX_LIST_ITEMS,
    MAX_RAW_BYTES,
    MAX_SUBJECT_CHARS,
    MAX_URLS_PER_MESSAGE,
    ContractModel,
    DomainName,
    ExternalId,
    Sha256Hex,
    ShortNote,
    UntrustedName,
    UntrustedShortText,
    UntrustedText,
    UntrustedUrl,
    _text,
)

UntrustedSubject = _text(MAX_SUBJECT_CHARS)


class Channel(StrEnum):
    MANUAL = "manual"  # texto pegado o archivo .eml importado (fase a)
    GMAIL = "gmail"  # fase f
    SIMULATED = "simulated"  # siempre etiquetado como SIMULADO (ADR-0015)
    VOICE_TRANSCRIPT = "voice_transcript"  # reservado para la fase 2 (ADR-0010); sin conector


class RawFormat(StrEnum):
    PLAIN_TEXT = "plain_text"  # UTF-8
    RFC822 = "rfc822"  # archivo .eml o Gmail con format=raw


class AuthVerdict(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    SOFTFAIL = "softfail"
    NEUTRAL = "neutral"
    NONE = "none"
    TEMPERROR = "temperror"
    PERMERROR = "permerror"
    UNKNOWN = "unknown"


class SenderAuth(ContractModel):
    """Resultados de autenticación tal como los declara la cabecera (no verificados por nosotros)."""

    spf: AuthVerdict = AuthVerdict.UNKNOWN
    dkim: AuthVerdict = AuthVerdict.UNKNOWN
    dmarc: AuthVerdict = AuthVerdict.UNKNOWN
    header_present: bool = False


class Sender(ContractModel):
    display_name: UntrustedName | None = None
    address: UntrustedName | None = None  # sin validar formato: un remitente malformado es una señal
    domain: DomainName | None = None
    auth: SenderAuth = SenderAuth()


class UrlLocation(StrEnum):
    BODY_TEXT = "body_text"
    HTML_HREF = "html_href"
    SUBJECT = "subject"


class ExtractedUrl(ContractModel):
    url_id: UUID
    raw: UntrustedUrl
    location: UrlLocation
    display_text: UntrustedShortText | None = None  # texto visible del enlace (HTML)
    normalized: UntrustedUrl | None = None
    host: DomainName | None = None
    registrable_domain: DomainName | None = None


class AttachmentMeta(ContractModel):
    """Solo metadatos: los adjuntos nunca se abren en el MVP."""

    filename: UntrustedName
    mime_type: UntrustedName
    size_bytes: int = Field(ge=0)


class RawMessage(ContractModel):
    """Entrada sin procesar entregada por un ``InputAdapter``."""

    channel: Channel
    raw_format: RawFormat
    payload: bytes = Field(min_length=1, max_length=MAX_RAW_BYTES)
    received_at: AwareDatetime
    source_message_id: ExternalId | None = None  # id de Gmail; None en entrada manual
    is_simulated: bool = False

    @model_validator(mode="after")
    def _simulated_matches_channel(self) -> RawMessage:
        _check_simulated(self.channel, self.is_simulated)
        return self


class IncomingMessage(ContractModel):
    """Mensaje normalizado y **minimizado** (ADR-0008, `13` §10)."""

    id: UUID
    user_id: UUID
    channel: Channel
    received_at: AwareDatetime
    source_message_id: ExternalId | None = None
    sender: Sender = Sender()
    reply_to: Sender | None = None
    subject: UntrustedSubject | None = None
    text: UntrustedText
    urls: list[ExtractedUrl] = Field(default_factory=list, max_length=MAX_URLS_PER_MESSAGE)
    attachments: list[AttachmentMeta] = Field(default_factory=list, max_length=MAX_ATTACHMENTS)
    thread_id: ExternalId | None = None
    content_hash: Sha256Hex
    parse_warnings: list[ShortNote] = Field(default_factory=list, max_length=MAX_LIST_ITEMS)
    is_simulated: bool = False

    @model_validator(mode="after")
    def _invariants(self) -> IncomingMessage:
        _check_simulated(self.channel, self.is_simulated)
        ids = [u.url_id for u in self.urls]
        if len(ids) != len(set(ids)):
            raise ValueError("url_id repetido en el mismo mensaje")
        return self


def _check_simulated(channel: Channel, is_simulated: bool) -> None:
    if is_simulated != (channel is Channel.SIMULATED):
        raise ValueError("is_simulated debe ser True si y solo si el canal es 'simulated'")

"""Ingesta: texto pegado o archivo .eml → ``IncomingMessage`` (fase a). Sin red.

- Limpia el texto (invisibles, controles), lo **minimiza** y extrae los
  enlaces del texto y del HTML (texto visible + destino).
- Del .eml toma remitente, Reply-To, asunto, resultados de autenticación
  declarados en ``Authentication-Results`` y solo **metadatos** de adjuntos.
- Los datos se truncan a los límites del contrato y se anotan avisos.
"""

from __future__ import annotations

import email
import email.policy
import hashlib
import hmac
import re
import secrets
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import parseaddr, parsedate_to_datetime
from uuid import UUID, uuid4

from pydantic import ValidationError

from antifraude.analysis.html_text import html_to_text_and_anchors
from antifraude.analysis.text import clean_text, fold, has_mixed_script, minimize
from antifraude.contracts.common import (
    MAX_ATTACHMENTS,
    MAX_RAW_BYTES,
    MAX_SUBJECT_CHARS,
    MAX_TEXT_CHARS,
    MAX_URL_CHARS,
    MAX_URLS_PER_MESSAGE,
)
from antifraude.contracts.messages import (
    AttachmentMeta,
    AuthVerdict,
    Channel,
    ExtractedUrl,
    IncomingMessage,
    RawFormat,
    RawMessage,
    Sender,
    SenderAuth,
    UrlLocation,
)
from antifraude.intel.urls import split_url, url_id_for

#: Dominios de primer nivel aceptados para dominios «desnudos» sin esquema ni barra (p. ej. «banco-seguro.com»).
_BARE_TLDS = (
    "com|es|net|org|eu|info|biz|io|co|me|ly|xyz|top|online|site|shop|store|app|link|click|live|vip|"
    "club|cloud|digital|support|help|services|security|bank|cat|gal|eus|pt|fr|de|it|uk|us|ru|cn|tk|ml|ga|cf|gq|"
    "test|example|invalid"
)
_URL_RE = re.compile(
    r"(?:(?:https?|hxxps?)://[^\s<>\"'«»]+|www\.[^\s<>\"'«»]+"
    r"|(?<![@\w.\-])[a-z0-9][a-z0-9\-]*(?:\.[a-z0-9\-]+)*\.[a-z]{2,24}/[^\s<>\"'«»]*"
    r"|(?<![@\w.\-])[a-z0-9][a-z0-9\-]*(?:\.[a-z0-9\-]+)*\.(?:" + _BARE_TLDS + r")(?![\w\-@]))",
    re.IGNORECASE,
)
_TRAILING = ".,;:!?)]}»"
_HASH_KEY = secrets.token_bytes(32)
#: Máximo de partes MIME de un .eml (protección frente a denegación de servicio).
MAX_MIME_PARTS = 200
_QUERY = re.compile(r"[?#].*$", re.DOTALL)


class IngestError(ValueError):
    """El contenido no se puede procesar (vacío o demasiado grande)."""


@dataclass
class IngestResult:
    message: IncomingMessage
    invisible_chars: int
    raw_text_for_rules: str  # texto limpio y minimizado (igual que message.text) + asunto


def _extract_urls(text: str, location: UrlLocation, message_id: UUID, start: int,
                  warnings: list[str]) -> list[ExtractedUrl]:
    found: list[ExtractedUrl] = []
    # NFKC: los caracteres de ancho completo («ｂａｎｃｏ.example») se convierten a su forma normal.
    for m in _URL_RE.finditer(unicodedata.normalize("NFKC", text)):
        raw = m.group(0).rstrip(_TRAILING)
        if not raw:
            continue
        url = _make_url(raw, location, None, message_id, start + len(found), warnings)
        if url is not None:
            found.append(url)
    return found


def _make_url(raw: str, location: UrlLocation, display: str | None, message_id: UUID, index: int,
              warnings: list[str]) -> ExtractedUrl | None:
    """Crea la URL extraída. Limpia controles/invisibles; recorta las muy largas con aviso; nunca lanza."""
    raw, _ = clean_text(raw)
    raw = raw.replace("\n", "").replace(" ", "")
    if display is not None:
        display = minimize(clean_text(display)[0])[:1000] or None
    if not raw:
        return None
    if len(raw) > MAX_URL_CHARS:
        warnings.append("Un enlace era extraordinariamente largo y se ha recortado para analizarlo.")
        raw = raw[:MAX_URL_CHARS]
    parts = split_url(raw)
    host = parts.host if parts.host and re.fullmatch(r"[a-z0-9.\-]{1,253}", parts.host) else None
    stored = _QUERY.sub("?[parámetros omitidos]", raw) if ("?" in raw or "#" in raw) else raw  # minimización
    try:
        return ExtractedUrl(url_id=url_id_for(index, message_id), raw=stored[:MAX_URL_CHARS], location=location,
                            display_text=display, host=host, registrable_domain=None)
    except ValidationError:
        warnings.append("Se omitió un enlace con un formato no válido.")
        return None


def _dedupe(urls: list[ExtractedUrl]) -> list[ExtractedUrl]:
    seen: set[tuple[str, str | None]] = set()
    out: list[ExtractedUrl] = []
    for u in urls:
        key = (u.raw, u.display_text)
        if key in seen:
            continue
        seen.add(key)
        out.append(u)
    return out


def build_message(
    *,
    user_id: UUID,
    channel: Channel,
    body_text: str,
    body_html: str | None = None,
    subject: str | None = None,
    sender: Sender | None = None,
    reply_to: Sender | None = None,
    received_at: datetime | None = None,
    attachments: list[AttachmentMeta] | None = None,
    source_message_id: str | None = None,
    is_simulated: bool = False,
) -> IngestResult:
    warnings: list[str] = []
    message_id = uuid4()

    html_text, anchors = ("", [])
    if body_html:
        html_text, anchors = html_to_text_and_anchors(body_html, warnings)
    base_text = body_text if body_text.strip() else html_text
    # Un correo con texto plano inocente y HTML distinto: se analizan ambos (evasión clásica de filtros).
    if body_text.strip() and html_text.strip():
        plain_words = set(fold(body_text).split())
        extra = [w for w in fold(html_text).split() if w not in plain_words]
        if len(extra) >= 2:  # cualquier contenido HTML que no esté en el texto plano se analiza
            base_text = body_text + "\n\n" + html_text
            warnings.append("El correo contenía en su versión HTML texto distinto del texto plano; se han analizado ambos.")
    cleaned, invisibles = clean_text(base_text)
    if not cleaned:
        raise IngestError("El mensaje está vacío.")
    if invisibles:
        warnings.append(f"Se eliminaron {invisibles} caracteres invisibles.")
    if has_mixed_script((subject or "") + " " + cleaned):
        warnings.append("Texto oculto: hay palabras que mezclan letras de distintos alfabetos para disimularse.")
    text = minimize(cleaned)  # minimizar ANTES de recortar: la máscara puede alargar el texto
    if len(text) > MAX_TEXT_CHARS:
        text = text[:MAX_TEXT_CHARS]
        warnings.append("El texto se ha recortado por su longitud.")

    subj_clean = None
    if subject:
        subj_clean, sub_inv = clean_text(subject)
        invisibles += sub_inv
        subj_clean = minimize(subj_clean)[:MAX_SUBJECT_CHARS] or None

    urls = _extract_urls(subj_clean or "", UrlLocation.SUBJECT, message_id, 0, warnings)
    urls += _extract_urls(cleaned, UrlLocation.BODY_TEXT, message_id, len(urls), warnings)
    for a in anchors:
        href = clean_text(a.href)[0].replace(" ", "")
        if not href or href.lower().startswith(("mailto:", "tel:", "#", "javascript:", "data:")):
            continue
        url = _make_url(href, UrlLocation.HTML_HREF, a.text or None, message_id, len(urls), warnings)
        if url is not None:
            urls.append(url)
    urls = _dedupe(urls)
    if len(urls) > MAX_URLS_PER_MESSAGE:
        urls = urls[:MAX_URLS_PER_MESSAGE]
        warnings.append("Hay demasiados enlaces; solo se analizan los primeros.")

    # HMAC con clave local por ejecución: sirve para deduplicar sin permitir adivinar el contenido (p. ej. un OTP).
    content_hash = hmac.new(_HASH_KEY, (subject or "").encode() + b"\x00" + base_text.encode(),
                            hashlib.sha256).hexdigest()
    msg = IncomingMessage(
        id=message_id,
        user_id=user_id,
        channel=channel,
        received_at=received_at or datetime.now(timezone.utc),
        source_message_id=source_message_id,
        sender=sender or Sender(),
        reply_to=reply_to,
        subject=subj_clean,
        text=text,
        urls=urls,
        attachments=(attachments or [])[:MAX_ATTACHMENTS],
        content_hash=content_hash,
        parse_warnings=[w[:500] for w in warnings][:50],
        is_simulated=is_simulated,
    )
    return IngestResult(message=msg, invisible_chars=invisibles, raw_text_for_rules=((subj_clean or "") + "\n" + text))


# --- Remitentes y autenticación -------------------------------------------------
def make_sender(display_name: str | None, address: str | None, auth: SenderAuth | None = None) -> Sender:
    domain = None
    if address and "@" in address:
        candidate = address.rsplit("@", 1)[1].strip().strip(">").lower().rstrip(".")
        try:
            candidate = candidate.encode("idna").decode("ascii") if not candidate.isascii() else candidate
        except UnicodeError:
            candidate = ""
        if re.fullmatch(r"[a-z0-9.\-]{1,253}", candidate or ""):
            domain = candidate
    return Sender(
        display_name=(display_name or None) and clean_text(display_name)[0][:256] or None,
        address=(address or None) and address.strip()[:256],
        domain=domain,
        auth=auth or SenderAuth(),
    )


_AUTH_RE = {k: re.compile(rf"\b{k}\s*=\s*([a-z]+)", re.IGNORECASE) for k in ("spf", "dkim", "dmarc")}


def parse_auth_results(values: list[str]) -> SenderAuth:
    if not values:
        return SenderAuth()
    joined = " ; ".join(values)
    verdicts: dict[str, AuthVerdict] = {}
    for key, rx in _AUTH_RE.items():
        m = rx.search(joined)
        if m:
            try:
                verdicts[key] = AuthVerdict(m.group(1).lower())
            except ValueError:
                verdicts[key] = AuthVerdict.UNKNOWN
    return SenderAuth(header_present=True, **verdicts)


# --- Entrada manual y .eml -------------------------------------------------------
def from_manual_text(text: str, user_id: UUID) -> IngestResult:
    if len(text.encode("utf-8", errors="ignore")) > MAX_RAW_BYTES:
        raise IngestError("El texto es demasiado largo.")
    return build_message(user_id=user_id, channel=Channel.MANUAL, body_text=text)


def from_raw(raw: RawMessage, user_id: UUID) -> IngestResult:
    """Entrada común para cualquier conector (``InputAdapter``)."""
    if raw.raw_format is RawFormat.RFC822:
        result = from_eml(raw.payload, user_id, channel=raw.channel, source_message_id=raw.source_message_id,
                          is_simulated=raw.is_simulated)
    else:
        result = build_message(user_id=user_id, channel=raw.channel,
                               body_text=raw.payload.decode("utf-8", errors="replace"),
                               received_at=raw.received_at, source_message_id=raw.source_message_id,
                               is_simulated=raw.is_simulated)
    return result


def _part_text(part: EmailMessage) -> str:
    try:
        return str(part.get_content())
    except Exception:
        payload = part.get_payload(decode=True) or b""
        return payload.decode("utf-8", errors="replace") if isinstance(payload, bytes) else str(payload)


def from_eml(raw: bytes, user_id: UUID, *, channel: Channel = Channel.MANUAL, source_message_id: str | None = None,
             is_simulated: bool = False) -> IngestResult:
    if not raw or len(raw) > MAX_RAW_BYTES:
        raise IngestError("El archivo está vacío o es demasiado grande.")
    # Pre-comprobación lineal: miles de partes MIME harían el análisis muy lento (revisión de seguridad).
    if raw.count(b"\n--") > MAX_MIME_PARTS * 2 + 10:
        raise IngestError("El correo tiene demasiadas partes para analizarlo con seguridad.")
    msg = email.message_from_bytes(raw, policy=email.policy.default)
    assert isinstance(msg, EmailMessage)
    text_parts: list[str] = []
    html_parts: list[str] = []
    attachments: list[AttachmentMeta] = []
    for n, part in enumerate(msg.walk()):
        if n > MAX_MIME_PARTS:
            raise IngestError("El correo tiene demasiadas partes para analizarlo con seguridad.")
        if part.is_multipart():
            continue
        disposition = part.get_content_disposition()
        ctype = part.get_content_type()
        if disposition == "attachment" or (part.get_filename() and disposition != "inline"):
            payload = part.get_payload(decode=True) or b""
            attachments.append(AttachmentMeta(filename=(part.get_filename() or "sin_nombre")[:256],
                                              mime_type=ctype[:256], size_bytes=len(payload)))
        elif ctype == "text/plain":
            text_parts.append(_part_text(part))
        elif ctype == "text/html":
            html_parts.append(_part_text(part))
    name, addr = parseaddr(str(msg.get("From", "")))
    _, reply = parseaddr(str(msg.get("Reply-To", ""))) if msg.get("Reply-To") else ("", "")
    auth = parse_auth_results([str(v) for v in msg.get_all("Authentication-Results", [])])
    received_at = None
    if msg.get("Date"):
        try:
            received_at = parsedate_to_datetime(str(msg["Date"]))
            if received_at.tzinfo is None:
                received_at = received_at.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            received_at = None
    return build_message(
        user_id=user_id,
        channel=channel,
        source_message_id=source_message_id,
        is_simulated=is_simulated,
        body_text="\n".join(text_parts),
        body_html="\n".join(html_parts) or None,
        subject=str(msg.get("Subject", "")) or None,
        sender=make_sender(name, addr, auth),
        reply_to=make_sender(None, reply) if reply else None,
        received_at=received_at,
        attachments=attachments,
    )

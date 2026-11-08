"""Tipos base, enumeraciones compartidas y límites de tamaño de los contratos.

Todo el contenido de mensajes y enlaces es **dato no confiable**: los textos se
acotan en longitud y no admiten el carácter NUL. La normalización (quitar
caracteres invisibles, recortar, etc.) es responsabilidad de la ingesta; aquí
solo se garantiza que los datos que circulan están acotados y bien tipados.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Final

from pydantic import AfterValidator, BaseModel, ConfigDict, StringConstraints

# --- Límites (contenido no confiable) ---------------------------------------
MAX_RAW_BYTES: Final[int] = 5 * 1024 * 1024  # mensaje original (.eml / RFC 822 / texto)
MAX_TEXT_CHARS: Final[int] = 100_000  # cuerpo normalizado y minimizado
MAX_SUBJECT_CHARS: Final[int] = 1_000
MAX_URL_CHARS: Final[int] = 8_192
MAX_URLS_PER_MESSAGE: Final[int] = 200
MAX_ATTACHMENTS: Final[int] = 50
MAX_QUOTE_CHARS: Final[int] = 500
MAX_LIST_ITEMS: Final[int] = 50
MAX_USER_TEXT_CHARS: Final[int] = 2_000  # textos que mostramos al usuario


def _reject_nul(value: str) -> str:
    if "\x00" in value:
        raise ValueError("el texto no puede contener el carácter NUL")
    return value


def _text(max_length: int, min_length: int = 0) -> object:
    return Annotated[
        str,
        StringConstraints(min_length=min_length, max_length=max_length),
        AfterValidator(_reject_nul),
    ]


# Textos procedentes del mensaje (no confiables)
UntrustedText = _text(MAX_TEXT_CHARS)
UntrustedShortText = _text(1_000)
UntrustedName = _text(256)
UntrustedUrl = _text(MAX_URL_CHARS, min_length=1)
Quote = _text(MAX_QUOTE_CHARS, min_length=1)
# Textos generados por el sistema (para el usuario o técnicos)
UserText = _text(MAX_USER_TEXT_CHARS, min_length=1)
ShortNote = _text(500, min_length=1)
# Identificadores
Code = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_.]{1,63}$")]
ExternalId = Annotated[str, StringConstraints(min_length=1, max_length=256, pattern=r"^[\x21-\x7e]+$")]
DomainName = Annotated[
    str, StringConstraints(min_length=1, max_length=253, pattern=r"^[a-z0-9.\-]+$")
]  # en minúsculas y en forma ASCII (punycode); la ingesta normaliza
Sha256Hex = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Version = Annotated[str, StringConstraints(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._\-]+$")]


class ContractModel(BaseModel):
    """Base de todos los contratos: inmutables, sin campos desconocidos y sin
    reproducir los datos de entrada en los errores (evita que contenido de
    mensajes acabe en trazas o registros)."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True, hide_input_in_errors=True)


# --- Enumeraciones compartidas ----------------------------------------------
class RiskLevel(StrEnum):
    """Los cuatro niveles aprobados (D-14). Sin porcentajes."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    INCONCLUSIVE = "inconclusive"

    @property
    def label_es(self) -> str:
        return _RISK_LABELS_ES[self]


_RISK_LABELS_ES: Final[dict[RiskLevel, str]] = {
    RiskLevel.LOW: "BAJO",
    RiskLevel.MEDIUM: "MEDIO",
    RiskLevel.HIGH: "ALTO",
    RiskLevel.INCONCLUSIVE: "NO CONCLUYENTE",
}


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def rank(self) -> int:
        return _SEVERITY_RANK[self]


_SEVERITY_RANK: Final[dict[Severity, int]] = {
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}


class FraudCategory(StrEnum):
    CREDENTIAL_THEFT = "credential_theft"
    PAYMENT_FRAUD = "payment_fraud"
    BANK_IMPERSONATION = "bank_impersonation"
    PHISHING_LINK = "phishing_link"
    INVESTMENT_SCAM = "investment_scam"
    ACCOUNT_TAKEOVER = "account_takeover"
    OTHER = "other"

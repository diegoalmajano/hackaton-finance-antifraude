"""Directorio de entidades financieras: esquema (F0-09).

Reglas de seguridad expresadas en el propio esquema:
- Solo una entidad ``verified`` (con fuente oficial y fecha) puede tener
  dominios oficiales reales.
- Una entidad ``pending_verification`` **no puede** tener dominios: un
  dominio sin comprobar nunca se tratará como oficial.
- Una entidad ``fictitious`` (pruebas y demo) solo puede usar dominios
  reservados (RFC 2606/6761) y nunca se carga por defecto.
Los datos del directorio NUNCA se construyen a partir de lo que dicen los
mensajes (`11` §9).
"""

from __future__ import annotations

import re
from datetime import date
from enum import StrEnum
from typing import Annotated

from pydantic import AfterValidator, Field, field_validator, model_validator

from antifraude.contracts.common import ContractModel, ShortNote, _text

RESERVED_SUFFIXES: tuple[str, ...] = (
    ".example", ".test", ".invalid", ".localhost",
    "example.com", "example.net", "example.org",
)

_LABEL_RE = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")
_TLD_RE = re.compile(r"^(?:[a-z]{2,63}|xn--[a-z0-9-]{1,59})$")


def is_reserved_domain(domain: str) -> bool:
    """True si el dominio es (o cuelga de) un nombre reservado para documentación o pruebas."""
    d = domain.lower().rstrip(".")
    for suffix in RESERVED_SUFFIXES:
        base = suffix.lstrip(".")
        if d == base or d.endswith("." + base):
            return True
    return False


def _valid_domain(value: str) -> str:
    """Dominio en minúsculas, ASCII (punycode si es IDN), sin esquema, puerto, ruta ni comodines."""
    if value != value.strip() or value != value.lower():
        raise ValueError("el dominio debe estar en minúsculas y sin espacios")
    if len(value) > 253 or "." not in value:
        raise ValueError("el dominio debe tener al menos dos etiquetas")
    if not value.isascii():
        raise ValueError("el dominio debe estar en ASCII (punycode para dominios internacionales)")
    labels = value.split(".")
    if not all(_LABEL_RE.fullmatch(lbl) for lbl in labels):
        raise ValueError("etiqueta de dominio no válida (sin esquema, puerto, ruta, comodines ni guiones extremos)")
    if not _TLD_RE.fullmatch(labels[-1]):
        raise ValueError("dominio de primer nivel no válido")
    return value


DomainStrict = Annotated[str, AfterValidator(_valid_domain)]
EntityId = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]{1,40}$")]
EntityName = _text(200, min_length=2)
AliasName = _text(100, min_length=2)


class VerificationStatus(StrEnum):
    VERIFIED = "verified"
    PENDING = "pending_verification"
    FICTITIOUS = "fictitious"


class DomainUsage(StrEnum):
    WEB = "web"
    EMAIL = "email"


class EntityType(StrEnum):
    BANK = "bank"
    OTHER = "other"


class OfficialDomain(ContractModel):
    domain: DomainStrict
    #: Si True, también son oficiales los subdominios reales (``*.dominio``). Nunca coincidencias parciales.
    include_subdomains: bool = False
    usage: list[DomainUsage] = Field(min_length=1, max_length=2)


class VerificationRecord(ContractModel):
    source_description: ShortNote  # p. ej. «Web oficial de la entidad» / «Registro de entidades del Banco de España»
    source_url: str | None = Field(default=None, max_length=500)
    checked_on: date
    checked_by: ShortNote

    @field_validator("source_url")
    @classmethod
    def _https(cls, value: str | None) -> str | None:
        if value is not None and (not value.startswith("https://") or not value.isascii() or " " in value):
            raise ValueError("source_url debe ser una URL https en ASCII")
        return value

    @field_validator("checked_on")
    @classmethod
    def _not_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("checked_on no puede ser una fecha futura")
        return value


class FinancialEntity(ContractModel):
    entity_id: EntityId
    official_name: EntityName
    aliases: list[AliasName] = Field(default_factory=list, max_length=20)
    entity_type: EntityType = EntityType.BANK
    country: str = Field(default="ES", pattern=r"^[A-Z]{2}$")
    verification_status: VerificationStatus
    official_domains: list[OfficialDomain] = Field(default_factory=list, max_length=30)
    verification: VerificationRecord | None = None
    notes: list[ShortNote] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def _rules(self) -> FinancialEntity:
        domains = [d.domain for d in self.official_domains]
        if len(domains) != len(set(domains)):
            raise ValueError("dominio repetido en la misma entidad")
        names = [_fold(n) for n in [self.official_name, *self.aliases]]
        if len(names) != len(set(names)):
            raise ValueError("nombre o alias repetido en la misma entidad")

        status = self.verification_status
        if status is VerificationStatus.PENDING:
            if domains:
                raise ValueError("una entidad pendiente de verificación no puede tener dominios oficiales")
        elif status is VerificationStatus.VERIFIED:
            if not domains:
                raise ValueError("una entidad verificada debe tener al menos un dominio oficial")
            if self.verification is None or self.verification.source_url is None:
                raise ValueError("una entidad verificada exige fuente oficial (source_url) y fecha")
            if any(is_reserved_domain(d) for d in domains):
                raise ValueError("una entidad real verificada no puede usar dominios reservados")
            if self.entity_id.startswith("ficticio"):
                raise ValueError("los identificadores 'ficticio*' están reservados a entidades ficticias")
        else:  # FICTITIOUS
            if not self.entity_id.startswith("ficticio"):
                raise ValueError("una entidad ficticia debe tener un entity_id que empiece por 'ficticio'")
            if not all(is_reserved_domain(d) for d in domains):
                raise ValueError("una entidad ficticia solo puede usar dominios reservados (.example, .test…)")
            if self.verification is None:
                raise ValueError("una entidad ficticia debe documentar su origen en verification")
        return self


class EntityFile(ContractModel):
    schema_version: str = Field(pattern=r"^1$")
    description: ShortNote
    entities: list[FinancialEntity] = Field(max_length=500)


def _fold(name: str) -> str:
    """Normaliza un nombre para comparaciones exactas (sin distinguir mayúsculas, acentos ni espacios repetidos)."""
    import unicodedata

    text = unicodedata.normalize("NFKD", name)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.casefold().split())

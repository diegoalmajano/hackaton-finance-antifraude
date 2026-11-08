"""Resultado del análisis **pasivo** de un enlace (ADR-0005, ADR-0009)."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field, model_validator

from antifraude.contracts.checks import CheckResult
from antifraude.contracts.common import (
    MAX_LIST_ITEMS,
    Code,
    ContractModel,
    DomainName,
    ShortNote,
    UntrustedUrl,
)
from antifraude.contracts.screening import Signal, SignalSource


class DomainComparison(StrEnum):
    OFFICIAL = "official"  # dominio oficial de la entidad declarada (no garantiza legitimidad)
    LOOKALIKE = "lookalike"  # parecido a un dominio oficial del directorio
    UNRELATED = "unrelated"
    UNKNOWN = "unknown"


class UrlAnalysis(ContractModel):
    url_id: UUID
    normalized_url: UntrustedUrl | None = None
    registrable_domain: DomainName | None = None  # None si no se pudo determinar
    claimed_entity_id: Code | None = None  # entidad del directorio que el mensaje dice ser
    comparison: DomainComparison = DomainComparison.UNKNOWN
    lookalike_of: DomainName | None = None
    display_href_mismatch: bool = False
    is_shortener: bool = False  # el destino NO se resuelve (incertidumbre)
    punycode_or_confusable: bool = False
    domain_age_days: int | None = Field(default=None, ge=0)  # RDAP, complementario
    findings: list[Signal] = Field(default_factory=list, max_length=MAX_LIST_ITEMS)
    checks: list[CheckResult] = Field(default_factory=list, max_length=MAX_LIST_ITEMS)
    limitations: list[ShortNote] = Field(default_factory=list, max_length=MAX_LIST_ITEMS)

    @model_validator(mode="after")
    def _invariants(self) -> UrlAnalysis:
        if (self.comparison is DomainComparison.LOOKALIKE) != (self.lookalike_of is not None):
            raise ValueError("lookalike_of es obligatorio solo cuando comparison='lookalike'")
        if any(f.source is not SignalSource.THREAT_INTEL for f in self.findings):
            raise ValueError("los hallazgos de un enlace deben tener source='threat_intel'")
        return self

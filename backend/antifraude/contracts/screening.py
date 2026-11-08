"""Señales y resultado del filtro preliminar por reglas (nivel 1)."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field, model_validator

from antifraude.contracts.checks import CheckStatus
from antifraude.contracts.common import (
    MAX_LIST_ITEMS,
    Code,
    ContractModel,
    Severity,
    UserText,
    Version,
)


class SignalFamily(StrEnum):
    CONTENT = "content"
    SENDER = "sender"
    URL = "url"
    CONTEXT = "context"


class SignalSource(StrEnum):
    RULE = "rule"  # filtro por reglas
    THREAT_INTEL = "threat_intel"  # análisis técnico de enlaces/dominios


class TextSpan(ContractModel):
    start: int = Field(ge=0)
    end: int = Field(gt=0)

    @model_validator(mode="after")
    def _ordered(self) -> TextSpan:
        if self.end <= self.start:
            raise ValueError("span.end debe ser mayor que span.start")
        return self


class Signal(ContractModel):
    code: Code
    family: SignalFamily
    severity: Severity
    source: SignalSource
    description_user: UserText
    description_tech: UserText
    span: TextSpan | None = None


class ScreeningResult(ContractModel):
    message_id: UUID
    status: CheckStatus  # done | failed
    signals: list[Signal] = Field(default_factory=list, max_length=MAX_LIST_ITEMS)
    max_severity: Severity | None = None  # None si no hay señales
    needs_deep_analysis: bool
    preliminary_alert_required: bool
    rule_version: Version
    latency_ms: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _invariants(self) -> ScreeningResult:
        if self.status not in (CheckStatus.DONE, CheckStatus.FAILED):
            raise ValueError("el filtro solo puede estar 'done' o 'failed'")
        expected = max((s.severity for s in self.signals), key=lambda s: s.rank, default=None)
        if self.max_severity != expected:
            raise ValueError("max_severity debe coincidir con la señal más grave (o None sin señales)")
        if self.preliminary_alert_required and not self.needs_deep_analysis:
            raise ValueError("una alerta preventiva exige análisis profundo y alerta definitiva")
        if self.status is CheckStatus.FAILED and not self.needs_deep_analysis:
            raise ValueError("si el filtro falla, el mensaje debe pasar a análisis profundo")
        return self

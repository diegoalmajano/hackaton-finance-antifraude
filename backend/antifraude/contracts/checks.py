"""Estado de cada comprobación (ADR-0006).

Se distinguen expresamente ``done`` (completada), ``failed`` (fallida) y
``not_configured`` (no configurada). Una comprobación obligatoria que no está
completada impide el nivel BAJO (ver ``FraudAssessment``).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from antifraude.contracts.common import Code, ContractModel, ShortNote


class CheckStatus(StrEnum):
    DONE = "done"
    FAILED = "failed"
    NOT_CONFIGURED = "not_configured"
    SKIPPED = "skipped"
    NOT_APPLICABLE = "not_applicable"


class CheckResult(ContractModel):
    name: Code  # p. ej. "screening.rules", "intel.url_passive", "intel.rdap", "ai.analysis"
    required: bool
    status: CheckStatus
    detail: ShortNote | None = None  # nunca contenido del mensaje ni secretos
    duration_ms: int | None = Field(default=None, ge=0)

    @property
    def is_complete(self) -> bool:
        """Completada o no aplicable (p. ej. análisis de URLs sin URLs)."""
        return self.status in (CheckStatus.DONE, CheckStatus.NOT_APPLICABLE)

    @property
    def is_unverified(self) -> bool:
        """No se pudo comprobar: debe declararse como incertidumbre."""
        return self.status in (CheckStatus.FAILED, CheckStatus.NOT_CONFIGURED, CheckStatus.SKIPPED)

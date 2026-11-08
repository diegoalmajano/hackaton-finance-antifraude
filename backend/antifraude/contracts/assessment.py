"""Evidencias y evaluación final del riesgo (ADR-0006, D-14, D-29).

Nivel, evidencias verificadas, incertidumbres y recomendaciones son campos
separados. No hay porcentajes ni puntuaciones. Las invariantes de este módulo
son una **red de seguridad**: el motor de riesgo (fase c) aplica las reglas
completas, pero ningún objeto puede expresar «BAJO» con comprobaciones
obligatorias sin completar ni con evidencias de riesgo relevantes.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import AwareDatetime, Field, computed_field, model_validator

from antifraude.contracts.ai import AiUsage
from antifraude.contracts.checks import CheckResult
from antifraude.contracts.common import (
    MAX_LIST_ITEMS,
    Code,
    ContractModel,
    FraudCategory,
    Quote,
    RiskLevel,
    Severity,
    ShortNote,
    UserText,
    Version,
)


class EvidenceSource(StrEnum):
    RULE = "rule"
    THREAT_INTEL = "threat_intel"
    AI = "ai"
    USER_PROFILE = "user_profile"
    CORRELATION = "correlation"


class EvidenceKind(StrEnum):
    RISK = "risk"
    LEGITIMACY = "legitimacy"


class Evidence(ContractModel):
    """Evidencia **verificada**. Las citas de IA no verificadas nunca llegan aquí."""

    evidence_id: UUID
    source: EvidenceSource
    kind: EvidenceKind
    severity: Severity
    category: FraudCategory | None = None
    description_user: UserText
    description_tech: UserText
    quote: Quote | None = None  # cita literal verificada como subcadena del mensaje
    ref_url_id: UUID | None = None

    @model_validator(mode="after")
    def _ai_requires_quote(self) -> Evidence:
        if self.source is EvidenceSource.AI and self.quote is None:
            raise ValueError("una evidencia de IA exige una cita literal verificada")
        return self


#: Categorías incompatibles con BAJO aunque la evidencia sea de severidad baja (D-29).
_NEVER_LOW_CATEGORIES = frozenset(
    {FraudCategory.CREDENTIAL_THEFT, FraudCategory.PAYMENT_FRAUD, FraudCategory.ACCOUNT_TAKEOVER}
)


class Recommendation(ContractModel):
    code: Code
    text_user: UserText


class FraudAssessment(ContractModel):
    assessment_id: UUID
    message_id: UUID
    user_id: UUID
    risk_level: RiskLevel
    fraud_categories: list[FraudCategory] = Field(default_factory=list, max_length=len(FraudCategory))
    evidence: list[Evidence] = Field(default_factory=list, max_length=MAX_LIST_ITEMS)
    uncertainties: list[ShortNote] = Field(default_factory=list, max_length=MAX_LIST_ITEMS)
    recommendations: list[Recommendation] = Field(default_factory=list, max_length=MAX_LIST_ITEMS)
    checks: list[CheckResult] = Field(min_length=1, max_length=MAX_LIST_ITEMS)
    explanation_user: UserText  # español llano, sin tecnicismos
    explanation_tech: UserText
    rule_version: Version
    model_id: Version | None = None
    prompt_version: Version | None = None
    ai_usage: AiUsage | None = None
    created_at: AwareDatetime
    is_simulated: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_partial(self) -> bool:
        """Análisis parcial: alguna comprobación **obligatoria** no se completó."""
        return any(c.required and not c.is_complete for c in self.checks)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def unverified_checks(self) -> list[str]:
        """Comprobaciones (obligatorias u opcionales) que no se pudieron realizar.

        Se calculan automáticamente para mostrar al usuario «lo que no se pudo
        comprobar» sin exigir texto adicional. Una opcional no realizada (p. ej.
        RDAP o reputación sin configurar) **no** impide por sí sola el nivel BAJO.
        """
        return [c.name for c in self.checks if c.is_unverified]

    @model_validator(mode="after")
    def _invariants(self) -> FraudAssessment:
        risk_evidence = [e for e in self.evidence if e.kind is EvidenceKind.RISK]
        max_risk_rank = max((e.severity.rank for e in risk_evidence), default=0)

        if self.is_partial and not self.uncertainties:
            raise ValueError("las comprobaciones obligatorias no completadas deben explicarse en uncertainties")

        if self.risk_level is RiskLevel.LOW:
            if self.is_partial:
                raise ValueError("BAJO no es posible con comprobaciones obligatorias sin completar")
            if max_risk_rank >= Severity.MEDIUM.rank:
                raise ValueError("BAJO no es posible con evidencias de riesgo de severidad media o superior")
            if any(e.category in _NEVER_LOW_CATEGORIES for e in risk_evidence):
                raise ValueError(
                    "BAJO no es posible con evidencias de robo de credenciales, fraude de pago "
                    "o toma de cuenta (D-29), sea cual sea su severidad"
                )
            if self.fraud_categories:
                raise ValueError("BAJO no puede declarar categorías de fraude")
        elif self.risk_level is RiskLevel.MEDIUM:
            if not risk_evidence:
                raise ValueError("MEDIO exige al menos una evidencia de riesgo")
        elif self.risk_level is RiskLevel.HIGH:
            if max_risk_rank < Severity.HIGH.rank:
                raise ValueError("ALTO exige al menos una evidencia de riesgo alta o crítica")
        elif self.risk_level is RiskLevel.INCONCLUSIVE:
            if not self.uncertainties:
                raise ValueError("NO CONCLUYENTE exige declarar las incertidumbres")

        if len(set(self.fraud_categories)) != len(self.fraud_categories):
            raise ValueError("fraud_categories no puede tener repetidos")
        return self

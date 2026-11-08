"""Hallazgos del análisis con IA (fase d, ADR-0007).

``AiOutput`` es el esquema estricto que deberá devolver el modelo; sus citas
**aún no están verificadas**. Solo las citas que el motor compruebe como
subcadena literal del mensaje se convertirán en ``Evidence`` (fuente ``ai``).
``AiFindings`` envuelve el resultado con su estado: un fallo nunca produce BAJO.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from antifraude.contracts.checks import CheckStatus
from antifraude.contracts.common import (
    ContractModel,
    FraudCategory,
    Quote,
    RiskLevel,
    ShortNote,
    UntrustedName,
    Version,
)

MAX_AI_ITEMS = 20


class FinancialRequestType(StrEnum):
    CREDENTIALS = "credentials"  # usuario/contraseña
    OTP = "otp"  # código de un solo uso / PIN
    CARD_DATA = "card_data"
    TRANSFER = "transfer"  # transferencia / Bizum
    PAYMENT_DETAILS_CHANGE = "payment_details_change"  # cambio de IBAN / cuenta
    OTHER = "other"


class AiTactic(ContractModel):
    category: FraudCategory
    quote: Quote  # debe ser una cita literal del mensaje (se verifica después)
    explanation: ShortNote


class AiOutput(ContractModel):
    """Salida estructurada del modelo. Datos generados a partir de contenido no confiable."""

    claimed_entity: UntrustedName | None = None
    tactics: list[AiTactic] = Field(default_factory=list, max_length=MAX_AI_ITEMS)
    inconsistencies: list[ShortNote] = Field(default_factory=list, max_length=MAX_AI_ITEMS)
    financial_request: FinancialRequestType | None = None
    injection_attempt: bool = False  # un intento de inyección es evidencia de riesgo
    uncertainties: list[ShortNote] = Field(default_factory=list, max_length=MAX_AI_ITEMS)
    suggested_level: RiskLevel | None = None  # solo orientativo: decide el motor determinista


class AiFailureReason(StrEnum):
    REFUSAL = "refusal"
    TIMEOUT = "timeout"
    INVALID_OUTPUT = "invalid_output"
    API_ERROR = "api_error"
    # Control de gasto (misión 3): la solicitud NO se envió.
    BUDGET_BLOCKED = "budget_blocked"  # presupuesto agotado o política que no permite gastar
    LIMIT_EXCEEDED = "limit_exceeded"  # límite de tokens de entrada o de solicitudes por sesión
    BUSY = "busy"  # ya había una solicitud de pago en curso


class AiUsage(ContractModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cache_creation_input_tokens: int = Field(default=0, ge=0)
    cache_read_input_tokens: int = Field(default=0, ge=0)
    #: Coste calculado con la tarifa publicada (no es la factura; ver docs/CONTROL_COSTES_IA.md).
    cost_usd: float | None = Field(default=None, ge=0)


class AiFindings(ContractModel):
    status: CheckStatus  # done | failed | not_configured
    output: AiOutput | None = None
    failure_reason: AiFailureReason | None = None
    model_id: Version | None = None
    prompt_version: Version | None = None
    usage: AiUsage | None = None

    @model_validator(mode="after")
    def _invariants(self) -> AiFindings:
        allowed = (CheckStatus.DONE, CheckStatus.FAILED, CheckStatus.NOT_CONFIGURED)
        if self.status not in allowed:
            raise ValueError("el análisis IA solo puede estar 'done', 'failed' o 'not_configured'")
        if (self.status is CheckStatus.DONE) != (self.output is not None):
            raise ValueError("output es obligatorio si y solo si status='done'")
        if (self.status is CheckStatus.FAILED) != (self.failure_reason is not None):
            raise ValueError("failure_reason es obligatorio si y solo si status='failed'")
        if self.status is CheckStatus.NOT_CONFIGURED and (self.usage or self.model_id):
            raise ValueError("una IA no configurada no puede tener modelo ni consumo")
        return self

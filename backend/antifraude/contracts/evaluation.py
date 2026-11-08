"""Formato de los casos del banco de evaluación (F0-08).

Un caso describe un mensaje **ficticio** y el resultado **esperado** según la
persona o el agente que lo etiquetó. No contiene resultados del detector.

- Partición ``dev``: puede estar en el repositorio y usarse para desarrollar.
- Partición ``sealed_test``: conjunto final sellado; vive **fuera** del
  repositorio y no se consulta durante el desarrollo (D-40). Este contrato la
  define solo para poder validarla el día de la evaluación.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import AwareDatetime, Field, model_validator

from antifraude.contracts.common import (
    MAX_LIST_ITEMS,
    MAX_SUBJECT_CHARS,
    MAX_TEXT_CHARS,
    ContractModel,
    FraudCategory,
    Quote,
    RiskLevel,
    ShortNote,
    UntrustedName,
    UserText,
    _text,
)
from antifraude.contracts.messages import SenderAuth

CaseText = _text(MAX_TEXT_CHARS, min_length=1)
CaseSubject = _text(MAX_SUBJECT_CHARS, min_length=1)
CaseTitle = _text(120, min_length=1)

_ALERT_LEVELS = frozenset({RiskLevel.MEDIUM, RiskLevel.HIGH})


class EvalSplit(StrEnum):
    DEV = "dev"
    SEALED_TEST = "sealed_test"


class CaseOrigin(StrEnum):
    SYNTHETIC_HUMAN = "synthetic_human"  # escrito por una persona del equipo
    SYNTHETIC_AI = "synthetic_ai"  # generado/redactado con IA (se informa aparte: riesgo R-26)
    ADAPTED_LICENSED = "adapted_licensed"  # adaptado de una fuente con licencia que lo permita


class Medium(StrEnum):
    EMAIL = "email"
    SMS = "sms"


class ReviewStatus(StrEnum):
    PENDING_HUMAN_REVIEW = "pending_human_review"
    REVIEWED = "reviewed"


class EvalSender(ContractModel):
    display_name: UntrustedName | None = None
    address: UntrustedName
    auth: SenderAuth = SenderAuth()


class EvalMessage(ContractModel):
    medium: Medium
    received_at: AwareDatetime
    sender: EvalSender
    reply_to: UntrustedName | None = None
    subject: CaseSubject | None = None
    body_text: CaseText
    body_html: CaseText | None = None  # opcional: para enlaces cuyo texto visible ≠ destino


class ExpectedOutcome(ContractModel):
    """Resultado esperado (etiqueta). Las alertas se consideran MEDIO o ALTO."""

    risk_level: RiskLevel
    acceptable_levels: list[RiskLevel] = Field(min_length=1, max_length=4)
    must_alert: bool
    fraud_categories: list[FraudCategory] = Field(default_factory=list, max_length=len(FraudCategory))
    expected_quotes: list[Quote] = Field(default_factory=list, max_length=MAX_LIST_ITEMS)
    key_signals: list[ShortNote] = Field(min_length=1, max_length=MAX_LIST_ITEMS)

    @model_validator(mode="after")
    def _coherent(self) -> ExpectedOutcome:
        if self.risk_level not in self.acceptable_levels:
            raise ValueError("risk_level debe estar entre los acceptable_levels")
        if len(set(self.acceptable_levels)) != len(self.acceptable_levels):
            raise ValueError("acceptable_levels no puede tener repetidos")
        if self.must_alert != (self.risk_level in _ALERT_LEVELS):
            raise ValueError("must_alert debe ser True si y solo si el nivel esperado es MEDIO o ALTO")
        if self.risk_level is RiskLevel.LOW and self.fraud_categories:
            raise ValueError("un caso esperado BAJO no puede tener categorías de fraude")
        if self.risk_level in _ALERT_LEVELS and not self.fraud_categories:
            raise ValueError("un caso esperado MEDIO o ALTO debe indicar categorías de fraude")
        if self.must_alert and RiskLevel.LOW in self.acceptable_levels:
            raise ValueError("un caso que debe alertar no puede aceptar BAJO")
        return self


class EvalCase(ContractModel):
    case_id: str = Field(pattern=r"^(dev|test)-[0-9]{4}$")
    split: EvalSplit
    title_es: CaseTitle
    origin: CaseOrigin
    is_synthetic: bool
    author: ShortNote
    created: date
    review_status: ReviewStatus
    demo_order: int | None = Field(default=None, ge=1, le=10)
    tags: list[ShortNote] = Field(default_factory=list, max_length=MAX_LIST_ITEMS)
    message: EvalMessage
    expected: ExpectedOutcome
    rationale_es: UserText

    @model_validator(mode="after")
    def _invariants(self) -> EvalCase:
        prefix = "dev-" if self.split is EvalSplit.DEV else "test-"
        if not self.case_id.startswith(prefix):
            raise ValueError("el prefijo de case_id debe coincidir con la partición")
        if self.origin in (CaseOrigin.SYNTHETIC_HUMAN, CaseOrigin.SYNTHETIC_AI) and not self.is_synthetic:
            raise ValueError("un caso de origen sintético debe marcarse is_synthetic=True")
        visible = (self.message.subject or "") + "\n" + self.message.body_text
        for quote in self.expected.expected_quotes:
            if quote not in visible:
                raise ValueError("cada cita esperada debe ser una subcadena literal del asunto o del texto")
        return self

"""Alertas en dos fases (`11` §7).

- **Preventiva**: el filtro detecta indicios; aún no hay nivel ni evaluación.
- **Definitiva**: nivel + evaluación; cierra la preventiva si la hubo.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import AwareDatetime, model_validator

from antifraude.contracts.common import ContractModel, RiskLevel, UserText, _text

AlertTitle = _text(120, min_length=1)


class AlertPhase(StrEnum):
    PREVENTIVE = "preventive"
    FINAL = "final"


class Alert(ContractModel):
    alert_id: UUID
    user_id: UUID
    message_id: UUID
    phase: AlertPhase
    title_user: AlertTitle
    body_user: UserText
    created_at: AwareDatetime
    risk_level: RiskLevel | None = None
    assessment_id: UUID | None = None
    closes_alert_id: UUID | None = None  # alerta preventiva que esta definitiva cierra
    is_partial: bool = False
    is_simulated: bool = False

    @model_validator(mode="after")
    def _invariants(self) -> Alert:
        if self.phase is AlertPhase.PREVENTIVE:
            if self.risk_level is not None or self.assessment_id is not None:
                raise ValueError("una alerta preventiva no tiene nivel ni evaluación")
            if self.closes_alert_id is not None or self.is_partial:
                raise ValueError("closes_alert_id e is_partial solo aplican a la alerta definitiva")
        else:
            if self.risk_level is None or self.assessment_id is None:
                raise ValueError("una alerta definitiva exige nivel y evaluación")
            if self.closes_alert_id == self.alert_id:
                raise ValueError("una alerta no puede cerrarse a sí misma")
        return self

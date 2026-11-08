"""Contratos Pydantic v2: **fuente única y autoritativa** de los datos (ADR-0003).

Cualquier cambio en un contrato se hace primero aquí (con sus tests) y se
revisa antes de adaptar productores y consumidores (protocolo contract-first).
"""

from antifraude.contracts.ai import (
    AiFailureReason,
    AiFindings,
    AiOutput,
    AiTactic,
    AiUsage,
    FinancialRequestType,
)
from antifraude.contracts.alerts import Alert, AlertPhase
from antifraude.contracts.assessment import (
    Evidence,
    EvidenceKind,
    EvidenceSource,
    FraudAssessment,
    Recommendation,
)
from antifraude.contracts.checks import CheckResult, CheckStatus
from antifraude.contracts.common import FraudCategory, RiskLevel, Severity
from antifraude.contracts.input_adapter import InputAdapter
from antifraude.contracts.links import DomainComparison, UrlAnalysis
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
from antifraude.contracts.screening import ScreeningResult, Signal, SignalFamily, SignalSource, TextSpan

CONTRACT_VERSION = "0.1.0"

__all__ = [
    "CONTRACT_VERSION",
    "AiFailureReason",
    "AiFindings",
    "AiOutput",
    "AiTactic",
    "AiUsage",
    "Alert",
    "AlertPhase",
    "AttachmentMeta",
    "AuthVerdict",
    "Channel",
    "CheckResult",
    "CheckStatus",
    "DomainComparison",
    "Evidence",
    "EvidenceKind",
    "EvidenceSource",
    "ExtractedUrl",
    "FinancialRequestType",
    "FraudAssessment",
    "FraudCategory",
    "IncomingMessage",
    "InputAdapter",
    "RawFormat",
    "RawMessage",
    "Recommendation",
    "RiskLevel",
    "ScreeningResult",
    "Sender",
    "SenderAuth",
    "Severity",
    "Signal",
    "SignalFamily",
    "SignalSource",
    "TextSpan",
    "UrlAnalysis",
    "UrlLocation",
]

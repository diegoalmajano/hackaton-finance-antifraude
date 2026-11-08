"""Orquestador del análisis (ADR-0001): ingesta → filtro → enlaces → IA → riesgo → alertas.

Toda la lógica de análisis es común a todos los canales; los conectores
solo entregan mensajes. Sin red salvo, en su caso, el cliente de IA.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from antifraude.ai.base import AiAnalyzer, DisabledAi, verified_quotes
from antifraude.analysis.ingest import IngestResult
from antifraude.analysis.rules import screen
from antifraude.contracts.ai import AiFailureReason, AiFindings
from antifraude.contracts.checks import CheckResult, CheckStatus
from antifraude.contracts.messages import ExtractedUrl
from antifraude.contracts.alerts import Alert, AlertPhase
from antifraude.contracts.assessment import FraudAssessment
from antifraude.contracts.common import RiskLevel, Severity
from antifraude.contracts.links import UrlAnalysis
from antifraude.contracts.messages import IncomingMessage
from antifraude.contracts.screening import ScreeningResult
from antifraude.intel.entities import EntityDirectory
from antifraude.intel.urls import analyze_url
from antifraude.risk.engine import assess

_FINAL_TITLES = {
    RiskLevel.HIGH: "ALTO: probable estafa",
    RiskLevel.MEDIUM: "MEDIO: tenga precaución",
    RiskLevel.INCONCLUSIVE: "NO CONCLUYENTE: compruébelo antes de actuar",
    RiskLevel.LOW: "BAJO: sin indicios de estafa",
}


@dataclass(frozen=True)
class AnalysisOutcome:
    message: IncomingMessage
    screening: ScreeningResult
    url_analyses: list[UrlAnalysis]
    ai: AiFindings | None
    assessment: FraudAssessment
    preventive_alert: Alert | None
    final_alert: Alert
    latency_ms: int


class AnalysisPipeline:
    def __init__(self, directory: EntityDirectory, ai: AiAnalyzer | None = None) -> None:
        self.directory = directory
        self.ai: AiAnalyzer = ai or DisabledAi()

    def _analyze_url(self, url: ExtractedUrl, claimed: str | None) -> UrlAnalysis:
        try:
            return analyze_url(url, self.directory, claimed)
        except Exception:  # un enlace imposible de analizar se declara, no aborta ni da BAJO
            return UrlAnalysis(
                url_id=url.url_id,
                checks=[CheckResult(name="intel.url_passive", required=True, status=CheckStatus.FAILED)],
                limitations=["No se pudo analizar uno de los enlaces."],
            )

    def run(self, ingested: IngestResult) -> AnalysisOutcome:
        t0 = perf_counter()
        message = ingested.message
        screening, entities = screen(message, self.directory)
        claimed = entities[0].entity_id if entities else None
        url_analyses = [self._analyze_url(u, claimed) for u in message.urls]

        ai_findings: AiFindings | None = None
        quotes: set[str] = set()
        url_risky = any(f.severity.rank >= Severity.MEDIUM.rank for ua in url_analyses for f in ua.findings)
        ai_required = screening.needs_deep_analysis or url_risky
        if ai_required:
            technical = [s.code for s in screening.signals] + [f.code for ua in url_analyses for f in ua.findings]
            try:
                ai_findings = self.ai.analyze(message, technical)
            except Exception:  # un fallo de la IA nunca aborta el análisis (D-14): análisis parcial declarado
                ai_findings = AiFindings(status=CheckStatus.FAILED, failure_reason=AiFailureReason.API_ERROR)
            quotes = verified_quotes(ai_findings.output, message)

        assessment = assess(message, screening, url_analyses, ai_findings, ai_required=ai_required,
                            verified_quotes=quotes)
        now = datetime.now(timezone.utc)
        preventive: Alert | None = None
        if screening.preliminary_alert_required:
            preventive = Alert(
                alert_id=uuid4(), user_id=message.user_id, message_id=message.id, phase=AlertPhase.PREVENTIVE,
                title_user="Posible intento de fraude",
                body_user="Hemos encontrado elementos sospechosos en este mensaje. Estamos comprobándolo.",
                created_at=now, is_simulated=message.is_simulated)
        final = Alert(
            alert_id=uuid4(), user_id=message.user_id, message_id=message.id, phase=AlertPhase.FINAL,
            title_user=_FINAL_TITLES[assessment.risk_level], body_user=assessment.explanation_user,
            created_at=now, risk_level=assessment.risk_level, assessment_id=assessment.assessment_id,
            closes_alert_id=preventive.alert_id if preventive else None, is_partial=assessment.is_partial,
            is_simulated=message.is_simulated)
        return AnalysisOutcome(message, screening, url_analyses, ai_findings, assessment, preventive, final,
                               int((perf_counter() - t0) * 1000))

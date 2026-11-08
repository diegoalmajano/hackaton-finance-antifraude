"""Motor de riesgo determinista (fase c, ADR-0006, D-29).

Fusiona las señales de reglas, el análisis pasivo de enlaces y, si existen,
los hallazgos de IA **con citas verificadas**, y decide el nivel:

- **ALTO**: evidencia crítica (dominio que imita a una entidad o marca en un
  subdominio ajeno), o petición de credenciales/OTP/tarjeta o de cambio de
  cuenta corroborada por otra fuente (enlace no oficial, remitente que se
  hace pasar por una entidad, DMARC fallido, respuesta a otro dominio, texto
  de enlace engañoso), o evidencia de IA de robo de credenciales/pago
  corroborada por otra fuente, o dos señuelos graves a la vez. Varias
  evidencias altas que describen el mismo hecho (p. ej. remitente ajeno que usa
  el nombre del banco + enlace a su propio dominio) NO bastan por sí solas:
  así se evita marcar como ALTO a proveedores legítimos (revisión adversarial A13/P5).
- **MEDIO**: ≥1 evidencia alta, ≥2 medias de fuentes distintas, o cualquier
  petición de credenciales/OTP/tarjeta (D-29: nunca es segura).
- **BAJO**: solo si todas las comprobaciones obligatorias se completaron y no
  hay evidencias de riesgo de severidad media o superior.
- **NO CONCLUYENTE**: en el resto de casos (hay indicios débiles o falta una
  comprobación obligatoria y las evidencias no alcanzan otro nivel).
Un error nunca produce BAJO (lo garantiza además el contrato).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4, uuid5

from antifraude.analysis.rules import RULE_VERSION
from antifraude.contracts.ai import AiFindings, FinancialRequestType
from antifraude.contracts.assessment import Evidence, EvidenceKind, EvidenceSource, FraudAssessment, Recommendation
from antifraude.contracts.checks import CheckResult, CheckStatus
from antifraude.contracts.common import FraudCategory, RiskLevel, Severity
from antifraude.contracts.links import DomainComparison, UrlAnalysis
from antifraude.contracts.messages import AuthVerdict, IncomingMessage
from antifraude.contracts.screening import ScreeningResult, Signal, SignalSource

_CATEGORY_BY_CODE: dict[str, FraudCategory] = {
    "content.credential_request": FraudCategory.CREDENTIAL_THEFT,
    "content.otp_request": FraudCategory.ACCOUNT_TAKEOVER,
    "content.card_request": FraudCategory.CREDENTIAL_THEFT,
    "content.payment_request": FraudCategory.PAYMENT_FRAUD,
    "content.payment_details_change": FraudCategory.PAYMENT_FRAUD,
    "content.investment_promise": FraudCategory.INVESTMENT_SCAM,
    "content.remote_access": FraudCategory.ACCOUNT_TAKEOVER,
    "content.family_new_number": FraudCategory.OTHER,
    "content.prize_or_refund": FraudCategory.OTHER,
    "content.injection_attempt": FraudCategory.OTHER,
    "content.unrecognized_charge_lure": FraudCategory.PAYMENT_FRAUD,
    "content.dangerous_attachment": FraudCategory.OTHER,
    "sender.brand_mismatch": FraudCategory.BANK_IMPERSONATION,
    "sender.body_brand_mismatch": FraudCategory.BANK_IMPERSONATION,
    "content.otp_share": FraudCategory.ACCOUNT_TAKEOVER,
    "content.credential_request_en": FraudCategory.CREDENTIAL_THEFT,
    "content.obfuscation": FraudCategory.OTHER,
    "content.identity_data_request": FraudCategory.CREDENTIAL_THEFT,
    "content.credential_expiry": FraudCategory.CREDENTIAL_THEFT,
    "content.safe_account_lure": FraudCategory.PAYMENT_FRAUD,
    "content.call_lure": FraudCategory.OTHER,
    "content.secrecy": FraudCategory.OTHER,
    "url.unparseable": FraudCategory.PHISHING_LINK,
    "url.brand_in_subdomain": FraudCategory.PHISHING_LINK,
    "url.lookalike_domain": FraudCategory.PHISHING_LINK,
    "url.display_mismatch": FraudCategory.PHISHING_LINK,
    "url.not_official_for_claimed": FraudCategory.PHISHING_LINK,
    "url.ip_literal": FraudCategory.PHISHING_LINK,
    "url.userinfo": FraudCategory.PHISHING_LINK,
    "url.punycode": FraudCategory.PHISHING_LINK,
}

#: Peticiones que nunca son seguras (D-29).
_SENSITIVE_REQUESTS = {"content.credential_request", "content.otp_request", "content.card_request",
                       "content.otp_share", "content.credential_request_en", "content.identity_data_request"}
_PAYMENT_REQUESTS = {"content.payment_details_change", "content.payment_request"}
#: Señuelos graves: con una corroboración de otra señal, el nivel es ALTO (ADR-0006, regla 1).
_LURES = _SENSITIVE_REQUESTS | {
    "content.payment_details_change", "content.investment_promise", "content.remote_access",
    "content.unrecognized_charge_lure", "content.family_new_number", "content.credential_expiry",
    "content.safe_account_lure",
}
#: Señales que corroboran un señuelo (canal no fiable, presión o petición de dinero).
_CORROBORATORS = {
    "url.brand_in_subdomain", "url.lookalike_domain", "url.display_mismatch", "url.not_official_for_claimed",
    "url.ip_literal", "url.userinfo", "url.punycode", "url.shortener", "url.unofficial_link",
    "sender.brand_mismatch", "sender.body_brand_mismatch", "sender.dmarc_fail", "sender.reply_to_mismatch",
    "content.account_threat",
    "content.urgency", "content.injection_attempt", "content.payment_request",
    "content.obfuscation", "content.invisible_chars", "url.unparseable",
    "content.call_lure", "content.secrecy",
}
_CRITICAL_ALONE = {"url.brand_in_subdomain", "url.lookalike_domain"}


@dataclass(frozen=True)
class _Ev:
    code: str
    severity: Severity
    source: EvidenceSource
    user: str
    tech: str
    quote: str | None = None
    category: FraudCategory | None = None


def _from_signal(s: Signal) -> _Ev:
    src = EvidenceSource.THREAT_INTEL if s.source is SignalSource.THREAT_INTEL else EvidenceSource.RULE
    return _Ev(s.code, s.severity, src, s.description_user, s.description_tech,
               category=_CATEGORY_BY_CODE.get(s.code))


def _ai_evidence(ai: AiFindings | None, verified_quotes: set[str]) -> list[_Ev]:
    if ai is None or ai.output is None:
        return []
    out: list[_Ev] = []
    for tactic in ai.output.tactics:
        if tactic.quote not in verified_quotes:
            continue  # cita no verificada → se descarta
        severity = Severity.HIGH if tactic.category in (FraudCategory.CREDENTIAL_THEFT, FraudCategory.PAYMENT_FRAUD,
                                                        FraudCategory.ACCOUNT_TAKEOVER) else Severity.MEDIUM
        out.append(_Ev(f"ai.{tactic.category.value}", severity, EvidenceSource.AI,
                       tactic.explanation, f"IA: {tactic.category.value}", quote=tactic.quote, category=tactic.category))
    if ai.output.injection_attempt:
        out.append(_Ev("ai.injection_attempt", Severity.HIGH, EvidenceSource.AI,
                       "El análisis detectó instrucciones ocultas dirigidas a programas de IA.",
                       "IA: injection_attempt", category=FraudCategory.OTHER))
    return out


def _decide(evs: Sequence[_Ev], partial: bool) -> RiskLevel:
    level = _decide_raw(evs, partial)
    if level is RiskLevel.HIGH and not any(e.severity.rank >= Severity.HIGH.rank for e in evs):
        return RiskLevel.MEDIUM  # el contrato exige una evidencia alta para ALTO: nunca se rompe el análisis
    return level


def _decide_raw(evs: Sequence[_Ev], partial: bool) -> RiskLevel:
    risk = [e for e in evs if e.severity.rank >= Severity.LOW.rank]
    codes = {e.code for e in risk}
    n_high = sum(1 for e in risk if e.severity.rank >= Severity.HIGH.rank)
    sources_medium = {e.source for e in risk if e.severity.rank >= Severity.MEDIUM.rank}
    n_medium = sum(1 for e in risk if e.severity.rank >= Severity.MEDIUM.rank)
    sensitive = bool(codes & _SENSITIVE_REQUESTS) or any(
        e.source is EvidenceSource.AI and e.category in (FraudCategory.CREDENTIAL_THEFT, FraudCategory.ACCOUNT_TAKEOVER)
        for e in risk)
    payment = bool(codes & _PAYMENT_REQUESTS)
    lures = codes & _LURES
    ai_high = [e for e in risk if e.source is EvidenceSource.AI and e.severity.rank >= Severity.HIGH.rank]
    non_ai_medium = [e for e in risk if e.source is not EvidenceSource.AI and e.severity.rank >= Severity.MEDIUM.rank]

    if codes & _CRITICAL_ALONE:
        return RiskLevel.HIGH
    if lures and (codes - lures) & _CORROBORATORS:
        return RiskLevel.HIGH
    if len(lures) >= 2:
        return RiskLevel.HIGH
    if ai_high and non_ai_medium:
        return RiskLevel.HIGH
    # ALTO solo por combinaciones críticas (ADR-0006), nunca por mera acumulación de señales.
    # Evidencias solo de severidad baja (p. ej. «http», enlace no oficial) no impiden BAJO.
    if sensitive or payment or n_high >= 1 or (n_medium >= 2 and len(sources_medium) >= 2) or n_medium >= 3:
        return RiskLevel.MEDIUM
    if n_medium >= 1 or partial:
        return RiskLevel.INCONCLUSIVE
    return RiskLevel.LOW


_RECOMMENDATIONS: dict[str, str] = {
    "do_not_share": "No facilite contraseñas, claves, PIN ni códigos que le lleguen por SMS. Su banco nunca se los pedirá.",
    "do_not_click": "No pulse los enlaces de este mensaje ni descargue nada.",
    "do_not_pay": "No haga pagos, transferencias ni Bizum a partir de este mensaje.",
    "verify_official": "Si tiene dudas, llame a su banco al teléfono de siempre (el de su tarjeta o su app), no al que aparece en el mensaje.",
    "delete_report": "Puede borrar el mensaje. Si ya facilitó algún dato, avise a su banco cuanto antes.",
    "verify_family": "Llame a su familiar a su número de siempre antes de enviar dinero.",
    "stay_alert": "No hemos visto señales de estafa, pero ante cualquier petición de datos o pagos, compruébelo por un canal oficial.",
    "check_carefully": "Hay detalles que no hemos podido comprobar. Antes de actuar, verifíquelo por un canal oficial.",
}


def _recommendations(level: RiskLevel, codes: set[str]) -> list[Recommendation]:
    keys: list[str]
    if level is RiskLevel.LOW:
        keys = ["stay_alert"]
    elif level is RiskLevel.INCONCLUSIVE:
        keys = ["check_carefully", "verify_official"]
    else:
        keys = []
        if codes & (_SENSITIVE_REQUESTS | {"ai.credential_theft", "ai.account_takeover"}):
            keys.append("do_not_share")
        if any(c.startswith("url.") for c in codes):
            keys.append("do_not_click")
        if codes & (_PAYMENT_REQUESTS | {"content.investment_promise", "content.safe_account_lure", "ai.payment_fraud"}):
            keys.append("do_not_pay")
        if "content.family_new_number" in codes:
            keys.append("verify_family")
        keys += ["verify_official", "delete_report"]
    return [Recommendation(code="rec." + k, text_user=_RECOMMENDATIONS[k]) for k in dict.fromkeys(keys)]


_HEADLINE = {
    RiskLevel.HIGH: "Hay señales claras de que este mensaje es una estafa.",
    RiskLevel.MEDIUM: "Este mensaje tiene señales que piden precaución.",
    RiskLevel.INCONCLUSIVE: "No hemos podido comprobarlo todo: no podemos decir si es seguro.",
    RiskLevel.LOW: "No hemos encontrado indicios de estafa en este mensaje.",
}


def assess(
    message: IncomingMessage,
    screening: ScreeningResult,
    url_analyses: Sequence[UrlAnalysis],
    ai: AiFindings | None,
    *,
    ai_required: bool,
    verified_quotes: set[str] | None = None,
    now: datetime | None = None,
) -> FraudAssessment:
    """Evaluación final determinista. ``verified_quotes``: citas de IA comprobadas como subcadenas literales."""
    evs: list[_Ev] = [_from_signal(s) for s in screening.signals]
    for ua in url_analyses:
        evs += [_from_signal(s) for s in ua.findings]
        if ua.comparison is not DomainComparison.OFFICIAL:
            evs.append(_Ev("url.unofficial_link", Severity.LOW, EvidenceSource.THREAT_INTEL,
                           "El mensaje incluye un enlace a una web que no es la oficial de ninguna entidad del directorio.",
                           f"enlace no oficial: {ua.registrable_domain or 'dominio desconocido'}"))
    evs += _ai_evidence(ai, verified_quotes or set())
    # una evidencia por código (la más grave)
    best: dict[str, _Ev] = {}
    for e in evs:
        if e.code not in best or e.severity.rank > best[e.code].severity.rank:
            best[e.code] = e
    evs = list(best.values())
    risk_evs = [e for e in evs if not e.code.startswith("context.")]

    # --- comprobaciones ---------------------------------------------------------
    checks: list[CheckResult] = [CheckResult(name="screening.rules", required=True, status=screening.status)]
    if url_analyses:
        url_failed = any(c.name == "intel.url_passive" and c.status is CheckStatus.FAILED
                         for ua in url_analyses for c in ua.checks)
        checks.append(CheckResult(name="intel.url_passive", required=True,
                                  status=CheckStatus.FAILED if url_failed else CheckStatus.DONE))
        checks.append(CheckResult(name="intel.rdap", required=False, status=CheckStatus.NOT_CONFIGURED))
        checks.append(CheckResult(name="intel.reputation", required=False, status=CheckStatus.NOT_CONFIGURED))
    else:
        checks.append(CheckResult(name="intel.url_passive", required=True, status=CheckStatus.NOT_APPLICABLE))
    if ai_required:
        checks.append(CheckResult(name="ai.analysis", required=True,
                                  status=ai.status if ai is not None else CheckStatus.NOT_CONFIGURED))
    else:
        checks.append(CheckResult(name="ai.analysis", required=False, status=CheckStatus.NOT_APPLICABLE))
    partial = any(c.required and not c.is_complete for c in checks)

    level = _decide(risk_evs, partial)

    # --- legitimidad (nunca anula riesgos; D-18) -----------------------------------
    legitimacy: list[Evidence] = []
    auth = message.sender.auth
    if (auth.header_present and auth.dmarc is AuthVerdict.PASS and message.sender.domain
            and not any(e.code == "sender.brand_mismatch" for e in risk_evs)):
        legitimacy.append(Evidence(
            evidence_id=uuid4(), source=EvidenceSource.RULE, kind=EvidenceKind.LEGITIMACY, severity=Severity.LOW,
            description_user="El remitente supera las comprobaciones de autenticidad de su dominio (no garantiza que el contenido sea legítimo).",
            description_tech=f"DMARC pass para {message.sender.domain}"))

    evidence = [
        Evidence(evidence_id=uuid5(message.id, e.code), source=e.source, kind=EvidenceKind.RISK, severity=e.severity,
                 category=e.category, description_user=e.user, description_tech=e.tech, quote=e.quote)
        for e in sorted(risk_evs, key=lambda e: -e.severity.rank)
    ][:50] + legitimacy

    uncertainties: list[str] = []
    for c in checks:
        if c.required and not c.is_complete:
            if c.name == "ai.analysis":
                uncertainties.append("Análisis parcial: el análisis con inteligencia artificial no estaba disponible.")
            else:
                uncertainties.append(f"No se pudo completar la comprobación «{c.name}».")
    for ua in url_analyses:
        uncertainties += [lim for lim in ua.limitations if lim not in uncertainties]
    if any(s.code == "context.non_spanish" for s in screening.signals):
        uncertainties.append("El mensaje no parece estar en español; la revisión del texto está pensada para español.")
    if level is RiskLevel.INCONCLUSIVE and not uncertainties:
        uncertainties.append("Hay indicios débiles que no permiten concluir si el mensaje es seguro.")
    uncertainties = uncertainties[:50]

    categories: list[FraudCategory] = []
    if level is not RiskLevel.LOW:
        for e in risk_evs:
            if e.category and e.category not in categories and e.severity.rank >= Severity.MEDIUM.rank:
                categories.append(e.category)

    codes = {e.code for e in risk_evs}
    top = [e.user for e in sorted(risk_evs, key=lambda e: -e.severity.rank) if e.severity.rank >= Severity.MEDIUM.rank][:3]
    explanation_user = _HEADLINE[level] + (" " + " ".join(top) if top else "")
    if partial:
        explanation_user += " (Análisis parcial: no se han podido hacer todas las comprobaciones.)"

    return FraudAssessment(
        assessment_id=uuid4(),
        message_id=message.id,
        user_id=message.user_id,
        risk_level=level,
        fraud_categories=categories,
        evidence=evidence,
        uncertainties=uncertainties,
        recommendations=_recommendations(level, codes),
        checks=checks,
        explanation_user=explanation_user[:2000],
        explanation_tech=("señales: " + ", ".join(sorted(codes)) if codes else "sin señales")[:2000],
        rule_version=RULE_VERSION,
        model_id=ai.model_id if ai else None,
        prompt_version=ai.prompt_version if ai else None,
        ai_usage=ai.usage if ai else None,
        created_at=now or datetime.now(timezone.utc),
        is_simulated=message.is_simulated,
    )


def credential_like(request: FinancialRequestType | None) -> bool:
    return request in (FinancialRequestType.CREDENTIALS, FinancialRequestType.OTP, FinancialRequestType.CARD_DATA)

"""Regresiones sintéticas de desarrollo; no evaluación independiente."""
from uuid import uuid4
import pytest
from antifraude.analysis.ingest import build_message
from antifraude.app.pipeline import AnalysisPipeline
from antifraude.contracts import Channel, RiskLevel
from antifraude.intel.entities import EntityDirectory


def analyze(text):
    return AnalysisPipeline(EntityDirectory.load_default(include_fictitious=True)).run(
        build_message(user_id=uuid4(), channel=Channel.MANUAL, body_text=text))


@pytest.mark.parametrize("separator", [" ", "\n", "\n\n", "\r\n\r\n", "\n \t\n"])
@pytest.mark.parametrize("template,code", [
    ("Envíe el código{separator}de verificación.", "content.otp_request"),
    ("Confirme el número{separator}secreto.", "content.credential_request"),
    ("ENVÍEME: por favor, el código de{separator}VERIFICACIÓN.", "content.otp_request"),
    ("Facilite sus datos de{separator}acceso.", "content.credential_request"),
])
def test_sensitive_object_layout(separator, template, code):
    out = analyze(template.format(separator=separator))
    assert out.assessment.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)
    assert code in {s.code for s in out.screening.signals}
    assert "rec.do_not_share" in {r.code for r in out.assessment.recommendations}
    assert out.preventive_alert is not None


@pytest.mark.parametrize("text", [
    "No evite facilitar su contraseña.",
    "NO EVITE: facilitar su contraseña.",
    "No evite\n\nfacilitar su contraseña.",
    "No\n\nevite facilitar su contraseña.",
    "No evite facilitar, por favor, su contraseña.",
    "No evite enviarme el código de verificación.",
    "No deje de facilitar su contraseña.",
])
def test_double_negation_is_request(text):
    out = analyze(text)
    assert out.assessment.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)
    assert any(s.code in {"content.credential_request", "content.otp_request"} for s in out.screening.signals)
    assert "rec.do_not_share" in {r.code for r in out.assessment.recommendations}
    assert out.preventive_alert is not None


@pytest.mark.parametrize("text", [
    "Documento firmado con\n\nfirma electrónica; nunca comparta su contraseña.",
    "Documento firmado con\nfirma electrónica; nunca comparta su contraseña.",
    "Documento firmado con firma electrónica; nunca comparta su contraseña.",
    "Documento con\n\nfirma electrónica.",
    "Seguimos con\n\nfirme protección de su contraseña.",
    "Evite: facilitar su contraseña.",
    "Evite:\n\nfacilitar su contraseña.",
    "Mensaje para Te\n\nCleopatra: nunca comparta su contraseña.",
    "Confirme la asistencia; nunca comparta su contraseña.",
    "Envíe el formulario. Nunca comparta su contraseña.",
    "Envíe el formulario del club\n\nLa contraseña de la sala se entrega en recepción.",
    "Evite facilitar su contraseña.",
    "Evite\n\nfacilitar su contraseña.",
    "No\n\nle envíe su contraseña.",
    "Nunca envíe el código\n\nde verificación.",
    "Evite facilitar el número\n\nsecreto.",
    "Nunca comparta sus datos de\n\nacceso.",
    "No evite saludar; nunca comparta su contraseña.",
    "No evite saludar. Evite facilitar su contraseña.",
])
def test_legitimate_advice_has_no_sensitive_request(text):
    out = analyze(text)
    assert out.assessment.risk_level == RiskLevel.LOW
    assert not any(s.code in {"content.credential_request", "content.otp_request", "content.card_request"} for s in out.screening.signals)
    assert "rec.do_not_share" not in {r.code for r in out.assessment.recommendations}
    assert out.preventive_alert is None


@pytest.mark.parametrize("text,code", [
    ("Please enter: your password.", "content.credential_request_en"),
    ("Envíe a nuestro agente: su contraseña.", "content.credential_request"),
    ("Envíe por favor al gestor: el código de verificación.", "content.otp_request"),
    ("Envíe por favor al gestor: el código\n\nde verificación.", "content.otp_request"),
    ("Manda\n\nme su contraseña.", "content.credential_request"),
    ("Comparte\n\nme su contraseña.", "content.credential_request"),
])
def test_separate_review_preserves_requests(text, code):
    out = analyze(text)
    assert code in {s.code for s in out.screening.signals}
    assert out.assessment.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)
    assert "rec.do_not_share" in {r.code for r in out.assessment.recommendations}
    assert out.preventive_alert is not None

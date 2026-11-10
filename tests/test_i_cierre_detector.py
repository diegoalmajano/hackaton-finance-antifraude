"""H1–H4: regresiones sintéticas de cierre, sin API ni evaluación sellada."""
from uuid import uuid4
import socket

import pytest

from antifraude.analysis.ingest import build_message
from antifraude.app.pipeline import AnalysisPipeline
from antifraude.contracts import Channel, RiskLevel
from antifraude.contracts.ai import AiFindings
from antifraude.contracts.checks import CheckStatus
from antifraude.contracts.common import FraudCategory, Severity
from antifraude.intel.entities import EntityDirectory

REVERSE = "content.reverse_payment_request"
REFERENCE = "context.sensitive_reference_request"


@pytest.fixture(autouse=True)
def sin_red(monkeypatch):
    def denied(*args, **kwargs):
        pytest.fail("Esta regresión pasiva no puede usar red ni DNS")
    monkeypatch.setattr(socket, "getaddrinfo", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)


class EspiaSimulada:
    def __init__(self):
        self.calls = []

    def analyze(self, message, technical_findings):
        self.calls.append(list(technical_findings))
        return AiFindings(status=CheckStatus.NOT_CONFIGURED)


def analyze(text, ai=None):
    pipeline = AnalysisPipeline(EntityDirectory.load_default(include_fictitious=True), ai)
    return pipeline.run(build_message(user_id=uuid4(), channel=Channel.MANUAL, body_text=text))


def test_h1_bizum_inverso_solo_explica_pago_y_da_accion_sin_inflar_nivel():
    out = analyze("Acepta la solicitud de Bizum que te he mandado para que te llegue el dinero del alquiler.")
    assert out.assessment.risk_level is RiskLevel.MEDIUM
    evidence = next(e for e in out.assessment.evidence if "PAGAR" in e.description_user)
    assert evidence.category is FraudCategory.PAYMENT_FRAUD
    assert "PAGAR" in evidence.description_user
    advice = next(r for r in out.assessment.recommendations if r.code == "rec.do_not_pay")
    assert "Bizum" in advice.text_user


def test_h1_peticion_inversa_corroboradora_de_otro_senuelo():
    out = analyze("Mamá, este es mi nuevo número. Acepta la solicitud de Bizum que te he mandado para que te llegue el dinero del alquiler.")
    assert REVERSE in {s.code for s in out.screening.signals}
    assert "content.family_new_number" in {s.code for s in out.screening.signals}
    assert out.assessment.risk_level is RiskLevel.HIGH


@pytest.mark.parametrize("text", [
    "Para recibir dinero no debes aceptar ninguna solicitud de pago.",
    "Para recibir dinero no debéis aceptar ninguna solicitud de pago.",
    "Para recibir dinero no debemos aceptar ninguna solicitud de pago.",
    "Para recibir dinero no se debe aceptar ninguna solicitud de pago.",
    "Puede recibir dinero sin necesidad de aceptar una solicitud de pago.",
])
def test_h2_consejo_por_persona_o_impersonal_no_se_convierte_en_pago(text):
    out = analyze(text)
    assert REVERSE not in {s.code for s in out.screening.signals}
    assert out.assessment.risk_level is RiskLevel.LOW


@pytest.mark.parametrize("prefix", [
    "No aceptes otras ofertas. ",
    "No debes aceptar otras ofertas; pero ",
    "No debe aceptar otras ofertas; sin embargo ",
    "No se debe aceptar otras ofertas; aun así ",
])
def test_h2_h4_negativa_ajena_no_suprime_orden_posterior(prefix):
    out = analyze(prefix + "Para recibir dinero acepta la solicitud de Bizum.")
    assert REVERSE in {s.code for s in out.screening.signals}
    assert out.assessment.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)
    assert any(r.code == "rec.do_not_pay" for r in out.assessment.recommendations)


def test_h4_salto_simple_no_oculta_peticion_inversa():
    out = analyze("Para recibir dinero\nacepta la solicitud de Bizum.")
    assert REVERSE in {s.code for s in out.screening.signals}
    assert out.assessment.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)


def test_h4_parrafos_ajenos_no_forman_solicitud_inversa():
    out = analyze("Hay una solicitud de pago para recibir dinero.\n\nAcepte el reglamento del club.")
    assert REVERSE not in {s.code for s in out.screening.signals}
    assert out.assessment.risk_level is RiskLevel.LOW


def test_h4_regla_general_no_inventa_objeto_cruzando_otro_parrafo():
    out = analyze("Envíe el formulario del club\n\nLa contraseña de la sala se entrega en recepción.")
    assert "content.credential_request" not in {s.code for s in out.screening.signals}
    assert out.assessment.risk_level is RiskLevel.LOW


@pytest.mark.parametrize("text", [
    "No comparta su código. Para verificar su identidad, envíelo a nuestro gestor.",
    "Su contraseña es privada. Envíela al agente para terminar.",
    "Su PIN es personal. Compártalo por correo para verificarlo.",
])
def test_h3_referencia_sensible_acotada_activa_adaptador_y_declara_parcial(text):
    ai = EspiaSimulada()
    out = analyze(text, ai)
    assert len(ai.calls) == 1 and REFERENCE in ai.calls[0]
    signal = next(s for s in out.screening.signals if s.code == REFERENCE)
    assert signal.severity is Severity.LOW
    assert out.screening.needs_deep_analysis
    assert out.assessment.risk_level is RiskLevel.INCONCLUSIVE
    assert out.assessment.is_partial
    assert any(c.name == "ai.analysis" and c.required for c in out.assessment.checks)


@pytest.mark.parametrize("text", [
    "Su formulario está listo. Envíelo al gestor.",
    "Su código postal está en la ficha. Envíelo al gestor.",
    "Su código de acceso es personal. No lo envíe al gestor.",
    "Su código de acceso es personal. Introdúzcalo en la app oficial.",
])
def test_h3_no_escala_mensajes_cotidianos_o_consejos_por_ese_disparador(text):
    ai = EspiaSimulada()
    out = analyze(text, ai)
    assert ai.calls == []
    assert REFERENCE not in {s.code for s in out.screening.signals}
    assert out.assessment.risk_level is RiskLevel.LOW


@pytest.mark.parametrize("text,code", [
    ("Introduzca\nsu contraseña para continuar.", "content.credential_request"),
    ("Introduzca su\ncontraseña para continuar.", "content.credential_request"),
    ("Envíame\nel código de verificación.", "content.otp_request"),
])
def test_h4_maquetacion_simple_no_oculta_una_peticion_sensible(text, code):
    out = analyze(text)
    assert code in {s.code for s in out.screening.signals}
    assert out.assessment.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)


def test_h4_solicitud_en_asunto_y_accion_en_cuerpo_conservan_su_contexto():
    pipeline = AnalysisPipeline(EntityDirectory.load_default(include_fictitious=True))
    out = pipeline.run(build_message(user_id=uuid4(), channel=Channel.MANUAL,
        subject="Solicitud de Bizum para recibir dinero", body_text="Acéptela en su app para continuar."))
    assert REVERSE in {s.code for s in out.screening.signals}
    assert out.assessment.risk_level is RiskLevel.MEDIUM
    assert any(r.code == "rec.do_not_pay" for r in out.assessment.recommendations)


@pytest.mark.parametrize("text", [
    "No debes dejar de aceptar la solicitud de Bizum para que te llegue el dinero del alquiler.",
    "Para recibir dinero no debes dejar de aceptar ninguna solicitud de pago.",
])
def test_h2_doble_negacion_no_anula_la_orden_de_aceptar_pago(text):
    out = analyze(text)
    assert REVERSE in {s.code for s in out.screening.signals}
    assert out.assessment.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)
    assert any(r.code == "rec.do_not_pay" for r in out.assessment.recommendations)

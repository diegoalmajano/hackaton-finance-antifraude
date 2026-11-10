"""Regresiones de formato detectadas al comparar las dos ramas para el Council."""
from uuid import uuid4
import pytest
from antifraude.analysis.ingest import build_message
from antifraude.app.pipeline import AnalysisPipeline
from antifraude.contracts import Channel,RiskLevel
from antifraude.intel.entities import EntityDirectory

@pytest.mark.parametrize('text,code',[
    ('Introduzca\n\nsu contraseña.','content.credential_request'),
    ('Introduzca\r\n\rsu contraseña.','content.credential_request'),
    ('Introduzca\n \t\nsu contraseña.','content.credential_request'),
    ('Introduzca\n\nsu\n\ncontraseña.','content.credential_request'),
    ('Envíame\n\nel código de verificación.','content.otp_request'),
    ('Introduzca\n\npor favor su contraseña.','content.credential_request'),
    ('Envíame\n\npor favor el código de verificación.','content.otp_request'),
    ('Intro\nduzca por favor su contraseña.','content.credential_request'),
    ('Enví\n\name por favor el código de verificación.','content.otp_request'),
    ('Introduzca\n\npor\n\nfavor su\n\ncontraseña.','content.credential_request'),
    ('Introduzca\n\nsu PIN.','content.credential_request'),
    ('Introduzca\n\nsu contra\n\nseña.','content.credential_request'),
    ('Introduzca su\n\ncontra\n\nseña.','content.credential_request'),
    ('Facilite\n\npor favor sus credenciales.','content.credential_request'),
    ('No deje de verificarlo: introduzca\n\nsu contraseña.','content.credential_request'),
    ('Introduzca:\n\nsu contraseña.','content.credential_request'),
    ('Introduzca\n\npor favor, su contraseña.','content.credential_request'),
    ('Introduzca,\n\npor favor, su contraseña.','content.credential_request'),
    ('Envíeme:\n\nel código de verificación.','content.otp_request'),
    ('INTRODUZCA:\n\nPOR FAVOR, SU CONTRASEÑA.','content.credential_request'),
    ('Introduzca por favor, su contraseña.','content.credential_request'),
    ('Tec\n\nlee por favor su contraseña.','content.credential_request'),
    ('Tecle\n\náis su contraseña.','content.credential_request'),
    ('Neces\n\nitaría su contraseña.','content.credential_request'),
    ('Tec\n\nléeme su contraseña.','content.credential_request'),
    ('Intro\n\nduzca:\n\npor favor, su contraseña.','content.credential_request'),
])
def test_council_formato_no_oculta_solicitud_sensible(text,code):
    p=AnalysisPipeline(EntityDirectory.load_default(include_fictitious=True))
    out=p.run(build_message(user_id=uuid4(),channel=Channel.MANUAL,body_text=text))
    assert code in {s.code for s in out.screening.signals}
    assert out.assessment.risk_level in (RiskLevel.MEDIUM,RiskLevel.HIGH)
    assert any(r.code=='rec.do_not_share' for r in out.assessment.recommendations)

@pytest.mark.parametrize('text',[
    'No introduzca\n\nsu contraseña.',
    'Nunca envíes\n\nel código de verificación.',
    'No\n\nintroduzca su contraseña.',
    'No\nintroduzca su contraseña.',
    'Nunca\n\nenvíes el código de verificación.',
    'Nunca\nenvíes el código de verificación.',
    'Envíe el formulario del club\n\nLa contraseña de la sala se entrega en recepción.',
    'No intro\n\nduzca por favor su contraseña.',
    'Nunca\n\nenví\name por favor el código de verificación.',
    'No introduzca\n\npor favor su contraseña.',
    'Evite\n\nintroducir por favor su contraseña.',
    'Envíe el formulario del club.\n\nPor favor, la contraseña de la sala se entrega en recepción.',
    'No\n\nle envíe su contraseña.',
    'No\nle envíe su contraseña.',
    'No le envíe su contraseña.',
    'Nunca\n\nle facilite su PIN.',
    'Nunca\nle facilite su PIN.',
    'No\n\nle\n\nenvíe:\n\nsu contraseña.',
    'No\n\nme envíes por favor, el código de verificación.',
    'No\n\nintroduzca:\n\npor favor, su contraseña.',
    'No neces\n\nitaría su contraseña.',
    'Nunca tec\n\nleéis su contraseña.',
    'Mensaje para Te\n\nCleopatra: nunca comparta su contraseña.',
    'Mensaje para Te\nCleopatra: nunca comparta su contraseña.',
    'Mensaje para TÉ\n\nCLEOPATRA: nunca comparta su contraseña.',
    'Envíe el formulario del club\n\nPor favor, la contraseña de la sala se entrega en recepción.',
])
def test_council_consejos_y_parrafos_ajenos_conservan_bajo(text):
    p=AnalysisPipeline(EntityDirectory.load_default(include_fictitious=True))
    out=p.run(build_message(user_id=uuid4(),channel=Channel.MANUAL,body_text=text))
    assert out.assessment.risk_level is RiskLevel.LOW
    assert not any(s.code in {'content.credential_request', 'content.otp_request'}
                   for s in out.screening.signals)
    assert out.preventive_alert is None

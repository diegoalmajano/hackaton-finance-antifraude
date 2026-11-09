"""Regla ``content.reverse_payment_request`` (Bizum inverso), rules-0.3.4.

Hueco encontrado en la verificación independiente del 09-11-2026 (``docs/VERIFICACION_LINUX_2026-11-09.md``):
«le hemos enviado una solicitud de Bizum para recibir el reembolso… acéptela» daba NO CONCLUYENTE.

Ejemplos redactados a partir de la tipología pública (avisos de INCIBE/OSI y del Banco de España sobre el
«Bizum inverso»), NO a partir del conjunto dev, y con variantes de redacción para no ajustar a una frase.
Los legítimos cubren consejos de seguridad y notificaciones reales de Bizum que no deben alertar.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from antifraude.analysis.ingest import build_message
from antifraude.app.pipeline import AnalysisPipeline
from antifraude.contracts import Channel, RiskLevel
from antifraude.intel.entities import EntityDirectory

USER = uuid4()
CODIGO = "content.reverse_payment_request"


@pytest.fixture(scope="module")
def pipeline() -> AnalysisPipeline:
    return AnalysisPipeline(EntityDirectory.load_default(include_fictitious=True))


def analizar(p: AnalysisPipeline, texto: str):
    return p.run(build_message(user_id=USER, channel=Channel.MANUAL, body_text=texto, body_html=None))


ESTAFAS = [
    # el caso del sondeo (cruza una frase)
    "Le hemos enviado una solicitud de Bizum para recibir el reembolso de su compra en Wallapop. Acéptela en su app "
    "para que se le ingrese el dinero.",
    # comprador falso en plataforma de segunda mano
    "Hola, ya te he pagado el artículo. Te llegará una solicitud de Bizum para cobrar los 45 €, solo tienes que "
    "aceptarla y el dinero te entra en la cuenta.",
    # orden invertido: primero el verbo
    "Para completar la devolución, acepte la solicitud de pago de 120 € que le ha llegado para recibir su dinero.",
    "Acepta la solicitud de Bizum que te he mandado para que te llegue el dinero del alquiler.",
    # devolución de un supuesto cargo duplicado
    "Le hemos cobrado dos veces. Para la devolución del importe, autorice la solicitud de dinero que verá en su app.",
    # «aprobar» en lugar de «aceptar»
    "Su reembolso está listo: apruebe la solicitud de cobro en Bizum para recibirlo hoy.",
    # señuelo «no pierda su dinero» (la palabra «no» no es una negación de aceptar)
    "No pierda su reembolso de 89 €: acepte la solicitud de Bizum que le hemos enviado para recibirlo.",
]

LEGITIMOS = [
    # consejos de seguridad del banco o de la OSI: describen la estafa y dicen que NO se acepte
    "Recuerde: si recibe una solicitud de Bizum para cobrar un reembolso, no la acepte. Para recibir dinero nunca "
    "tiene que aceptar nada.",
    "Consejo de seguridad: para recibir un Bizum no es necesario aceptar ninguna solicitud de pago.",
    "Nunca aceptes una solicitud de Bizum de alguien que dice que te va a devolver dinero.",
    "Con Bizum puede recibir dinero sin tener que aceptar ninguna solicitud.",
    # notificaciones reales
    "Has recibido un Bizum de 15,00 EUR de LAURA G. Concepto: cena viernes.",
    "Has enviado un Bizum de 20,00 EUR a PEDRO M. Concepto: regalo.",
    "Tu reembolso de 34,99 € ha sido procesado y lo verás en tu cuenta en 3-5 días hábiles.",
]


@pytest.mark.parametrize("texto", ESTAFAS)
def test_bizum_inverso_alerta(pipeline: AnalysisPipeline, texto: str) -> None:
    out = analizar(pipeline, texto)
    assert CODIGO in {s.code for s in out.screening.signals}, texto
    assert out.assessment.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH), texto


@pytest.mark.parametrize("texto", LEGITIMOS)
def test_consejos_y_notificaciones_no_disparan_la_regla(pipeline: AnalysisPipeline, texto: str) -> None:
    out = analizar(pipeline, texto)
    assert CODIGO not in {s.code for s in out.screening.signals}, texto


@pytest.mark.parametrize("texto", LEGITIMOS[4:])
def test_notificaciones_reales_quedan_en_bajo(pipeline: AnalysisPipeline, texto: str) -> None:
    assert analizar(pipeline, texto).assessment.risk_level is RiskLevel.LOW, texto


def test_no_cruza_saltos_de_linea(pipeline: AnalysisPipeline) -> None:
    texto = "Le enviamos una solicitud de pago por la cuota del club.\n\nAcepte el reglamento para recibir el carné."
    assert CODIGO not in {s.code for s in analizar(pipeline, texto).screening.signals}

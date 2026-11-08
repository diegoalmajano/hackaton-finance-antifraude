"""Regresiones de la revisión independiente de la Etapa B (escenarios verificados por el revisor)."""

from __future__ import annotations

from uuid import uuid4

import pytest

from antifraude.analysis.html_text import html_to_text_and_anchors
from antifraude.analysis.ingest import build_message, from_manual_text, make_sender
from antifraude.app.pipeline import AnalysisPipeline
from antifraude.contracts import Channel, RiskLevel
from antifraude.contracts.ai import AiFindings
from antifraude.contracts.messages import IncomingMessage
from antifraude.intel.entities import EntityDirectory

USER = uuid4()


@pytest.fixture(scope="module")
def pipeline() -> AnalysisPipeline:
    return AnalysisPipeline(EntityDirectory.load_default(include_fictitious=True))


def nivel(p: AnalysisPipeline, texto: str, **kw) -> RiskLevel:  # type: ignore[no-untyped-def]
    return p.run(build_message(user_id=USER, channel=Channel.MANUAL, body_text=texto, **kw)).assessment.risk_level


# 1. Peticiones de credenciales que daban BAJO
@pytest.mark.parametrize("texto", [
    "No le demore: introduzca su contraseña",
    "No te preocupes, introduce tu clave aquí",
    "Para desbloquear su cuenta acceda con su usuario y contraseña en el enlace.",
    "Necesitamos su clave de acceso para verificar su identidad.",
    "Su código de seguridad es 123456, comuníquelo al agente que le llamará",
    "Necesitamos su DNI y la contraseña de su banca online",
])
def test_peticiones_sensibles_nunca_bajo(pipeline: AnalysisPipeline, texto: str) -> None:
    assert nivel(pipeline, texto) in (RiskLevel.MEDIUM, RiskLevel.HIGH)


@pytest.mark.parametrize("texto", [
    "Recuerde: nunca le pediremos sus claves, contraseñas ni códigos por correo.",
    "Jamás le solicitaremos los datos de su tarjeta por SMS.",
    "Tu código es 482913. No lo compartas con nadie.",
])
def test_avisos_legitimos_siguen_bajos(pipeline: AnalysisPipeline, texto: str) -> None:
    assert nivel(pipeline, texto) is RiskLevel.LOW


# 2. NUL e invisibles en enlaces HTML: nunca 500
def test_nul_en_href_no_rompe(pipeline: AnalysisPipeline) -> None:
    out = pipeline.run(build_message(user_id=USER, channel=Channel.MANUAL, body_text="",
                                     body_html='<p>Hola</p><a href="http://a.test/\x00x">ver\x00</a>'))
    assert out.assessment is not None


# 3. La minimización no rompe los límites
def test_minimizacion_no_supera_limites(pipeline: AnalysisPipeline) -> None:
    out = pipeline.run(build_message(user_id=USER, channel=Channel.MANUAL, body_text="pin 1234 " * 20000,
                                     subject="pin 1234 " * 300))
    assert len(out.message.text) <= 100_000 and len(out.message.subject or "") <= 1000


# 4. HTML mal formado
def test_head_sin_cerrar_no_oculta_el_cuerpo() -> None:
    texto, _ = html_to_text_and_anchors("<html><head><title>x<body><p>Introduzca su contraseña</p></body></html>")
    assert "Introduzca su contraseña" in texto


def test_enlace_sin_cerrar_se_registra() -> None:
    _, anclas = html_to_text_and_anchors("<p>Pulse <a href='http://evil.test/x'>aquí <a href='http://evil2.test'>y aquí")
    assert {a.href for a in anclas} == {"http://evil.test/x", "http://evil2.test"}


def test_html_distinto_del_texto_plano_se_analiza(pipeline: AnalysisPipeline) -> None:
    out = pipeline.run(build_message(
        user_id=USER, channel=Channel.MANUAL, body_text="Hola, le enviamos el boletín mensual de noticias.",
        body_html="<p>Su cuenta será bloqueada. Introduzca su contraseña y el código que recibirá por SMS "
                  "en http://falso.test/x antes de 24 horas</p>"))
    assert out.assessment.risk_level is RiskLevel.HIGH


# 5. Dominios desnudos, ancho completo y URL larga
def test_dominio_desnudo_se_extrae() -> None:
    m = from_manual_text("Entre en banco-seguro.com y facilite su clave", USER).message
    assert [u.host for u in m.urls] == ["banco-seguro.com"]


def test_dominio_de_ancho_completo_se_extrae() -> None:
    m = from_manual_text("Acceda a ｂａｎｃｏ-falso.example/login", USER).message
    assert m.urls and m.urls[0].host == "banco-falso.example"


def test_url_muy_larga_se_recorta_con_aviso() -> None:
    m = from_manual_text("http://x.test/" + "a" * 9000, USER).message
    assert m.urls and any("largo" in w for w in m.parse_warnings)


def test_parametros_de_url_no_se_guardan() -> None:
    m = from_manual_text("Pulse https://x.test/login?otp=123456&token=abc", USER).message
    assert "123456" not in m.urls[0].raw and "abc" not in m.urls[0].raw


# 6. Entidad en el cuerpo, remitente ajeno
def test_cuerpo_habla_por_la_entidad_desde_otro_dominio(pipeline: AnalysisPipeline) -> None:
    lvl = nivel(pipeline, "Banco Ficticio le informa: introduzca su clave de acceso para evitar el bloqueo",
                sender=make_sender("Soporte", "x@correo-gratuito.example"))
    assert lvl is RiskLevel.HIGH


# 7. IBAN legítimo con plazo ya no es ALTO
def test_iban_de_factura_no_es_estafa(pipeline: AnalysisPipeline) -> None:
    lvl = nivel(pipeline, "Su factura se cargará en el IBAN ES9121000418450200051332. Plazo de 10 días.")
    assert lvl is not RiskLevel.HIGH


def test_iban_nuevo_si_es_cambio_de_pago(pipeline: AnalysisPipeline) -> None:
    lvl = nivel(pipeline, "Hemos cambiado de banco: a partir de ahora pague al nuevo IBAN ES9121000418450200051332. Urgente.")
    assert lvl is RiskLevel.HIGH


# 8. Fallos de la IA no abortan el análisis
class IaQueFalla:
    def analyze(self, message: IncomingMessage, technical_findings: list[str]) -> AiFindings:
        raise ConnectionError("red caída")


def test_excepcion_de_la_ia_da_analisis_parcial() -> None:
    p = AnalysisPipeline(EntityDirectory.load_default(include_fictitious=True), IaQueFalla())
    out = p.run(from_manual_text("Introduzca su contraseña en http://x.test/a", USER))
    assert out.assessment.is_partial and out.assessment.risk_level is not RiskLevel.LOW


# 12. Marca corta del directorio no produce falsos «parecidos»
def test_marca_contenida_en_otra_palabra_no_es_parecido() -> None:
    from antifraude.contracts.entities import FinancialEntity
    from antifraude.intel.urls import analyze_url
    e = FinancialEntity.model_validate({
        "entity_id": "ficticio_ing", "official_name": "Ing Ficticio", "verification_status": "fictitious",
        "official_domains": [{"domain": "ing.example", "include_subdomains": True, "usage": ["web"]}],
        "verification": {"source_description": "prueba", "checked_on": "2026-11-01", "checked_by": "t"}})
    d = EntityDirectory([e], include_fictitious=True)
    url = from_manual_text("https://booking.example/x", USER).message.urls[0]
    assert analyze_url(url, d).lookalike_of is None

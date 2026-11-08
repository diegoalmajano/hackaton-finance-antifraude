"""Regresiones de la revisión de SEGURIDAD de la Etapa B (pruebas de concepto del revisor)."""

from __future__ import annotations

import time
from uuid import uuid4

import pytest

from antifraude.analysis.html_text import html_to_text_and_anchors
from antifraude.analysis.ingest import IngestError, build_message, from_eml, from_manual_text
from antifraude.analysis.text import minimize
from antifraude.app.pipeline import AnalysisPipeline
from antifraude.contracts import Channel, RiskLevel
from antifraude.intel.entities import EntityDirectory

USER = uuid4()


@pytest.fixture(scope="module")
def pipeline() -> AnalysisPipeline:
    return AnalysisPipeline(EntityDirectory.load_default(include_fictitious=True))


def nivel(p: AnalysisPipeline, texto: str = "", html: str | None = None) -> RiskLevel:
    return p.run(build_message(user_id=USER, channel=Channel.MANUAL, body_text=texto,
                               body_html=html)).assessment.risk_level


# 1–2. Denegación de servicio
@pytest.mark.parametrize("html", ["<a href=x " * 30000, "<!--" * 500000, "<![CDATA[" * 200000])
def test_html_hostil_se_analiza_rapido(html: str) -> None:
    t0 = time.perf_counter()
    html_to_text_and_anchors(html)
    assert time.perf_counter() - t0 < 3.0


def test_multipart_con_miles_de_partes_se_rechaza() -> None:
    partes = b"".join(b"--B\r\nContent-Type: text/plain\r\n\r\nx\r\n" for _ in range(60000))
    eml = b'Content-Type: multipart/mixed; boundary="B"\r\n\r\n' + partes + b"--B--\r\n"
    t0 = time.perf_counter()
    with pytest.raises(IngestError):
        from_eml(eml, USER)
    assert time.perf_counter() - t0 < 2.0


# 3. HTML con texto plano inocente
def test_html_alternativo_se_analiza(pipeline: AnalysisPipeline) -> None:
    lvl = nivel(pipeline, "Hola, mira tu correo",
                "<p>Introduzca su contraseña en <a href='http://evil.test'>Banco Ficticio</a></p>")
    assert lvl in (RiskLevel.MEDIUM, RiskLevel.HIGH)


# 4. Homoglifos, «leet», letras espaciadas, separación larga
@pytest.mark.parametrize("texto", [
    "intrοduzca su cοntraseña en https://evil.test/x",          # «o» griega
    "introduzca su cоntraseña en https://evil.test/x",          # «о» cirílica
    "introduzca su c0ntraseña en https://evil.test",
    "I n t r o d u z c a su c o n t r a s e n a en https://evil.test",
    "introduzca " + "a " * 40 + "su contraseña https://evil.test",
])
def test_evasiones_de_texto_no_dan_bajo(pipeline: AnalysisPipeline, texto: str) -> None:
    assert nivel(pipeline, texto) in (RiskLevel.MEDIUM, RiskLevel.HIGH)


# 5–6. noscript, texto oculto, enlaces con código, host indeterminable
def test_noscript_se_analiza(pipeline: AnalysisPipeline) -> None:
    assert nivel(pipeline, html="<p>Hola</p><noscript>Introduzca su contraseña y su PIN en el banco ya</noscript>") \
        in (RiskLevel.MEDIUM, RiskLevel.HIGH)


def test_texto_oculto_es_senal(pipeline: AnalysisPipeline) -> None:
    out = pipeline.run(build_message(user_id=USER, channel=Channel.MANUAL, body_text="Hola, buenos días.",
                                     body_html="<p>Hola, buenos días.</p><div style='display:none'>"
                                               "introduzca su contraseña en el formulario adjunto ya mismo</div>"))
    assert any("ofuscación" in e.description_tech for e in out.assessment.evidence)
    assert out.assessment.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)


def test_enlace_javascript_es_senal(pipeline: AnalysisPipeline) -> None:
    out = pipeline.run(build_message(user_id=USER, channel=Channel.MANUAL, body_text="",
                                     body_html="<p>Revise su cuenta <a href='JaVaScRiPt:alert(1)'>aquí</a></p>"))
    assert any("ofuscación" in e.description_tech for e in out.assessment.evidence)


def test_host_indeterminable_es_senal(pipeline: AnalysisPipeline) -> None:
    out = pipeline.run(from_manual_text("Acceda: https://evil.test\\.bancoficticio.example/login", USER))
    assert any("indeterminable" in e.description_tech for e in out.assessment.evidence)


# 7. Minimización
@pytest.mark.parametrize("entrada,secreto", [
    ("4111.1111.1111.1111", "1111.1111.1111"), ("4111/1111/1111/1111", "1111/1111"),
    ("ES91-2100-0418-4502-0005-1332", "2100-0418"), ("2100 0418 45 0200051332", "0200051332"),
    ("Su código de verificación de Bizum para la operación es 123456", "123456"),
    ("123456 es su código", "123456"), ("código:\n123456", "123456"), ("cvv 123", "123"),
    ("mi contraseña es hunter2", "hunter2"), ("password is hunter2", "hunter2"),
    ("12345678Z", "12345678"), ("llame al 612 345 678", "612 345 678"),
])
def test_minimizacion_ampliada(entrada: str, secreto: str) -> None:
    assert secreto not in minimize(entrada)


@pytest.mark.parametrize("texto", ["Pedido 12345678 de 3 unidades por 25 euros", "Su cita es el 12 de noviembre a las 10:30",
                                   "En las próximas 24 horas"])
def test_minimizacion_no_toca_datos_normales(texto: str) -> None:
    assert minimize(texto) == texto


def test_huella_de_contenido_no_es_sha256_simple() -> None:
    import hashlib
    m = from_manual_text("Tu código es 4829", USER).message
    assert m.content_hash != hashlib.sha256(b"\x00Tu c\xc3\xb3digo es 4829").hexdigest()


# --- Pendientes de seguridad resueltos en la misión 2 ------------------------------------------
def test_ingles_basico_y_aviso_de_idioma(pipeline: AnalysisPipeline) -> None:
    out = pipeline.run(from_manual_text(
        "Dear customer, please enter your password and PIN at https://evil.test/login to keep your account active.", USER))
    assert out.assessment.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)
    assert any("no parece estar en español" in u for u in out.assessment.uncertainties)


def test_espanol_no_genera_aviso_de_idioma(pipeline: AnalysisPipeline) -> None:
    out = pipeline.run(from_manual_text("Su pedido llegará mañana entre las nueve y las dos. No tiene que pagar nada.", USER))
    assert not any("español" in u for u in out.assessment.uncertainties)


def test_ancho_completo_es_senal_de_ofuscacion(pipeline: AnalysisPipeline) -> None:
    out = pipeline.run(from_manual_text("Acceda a ｂａｎｃｏ-falso.example/login para revisar su cuenta", USER))
    assert any("ofuscación" in e.description_tech for e in out.assessment.evidence)

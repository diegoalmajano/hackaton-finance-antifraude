"""Pendientes P5–P7 y R-64: casos sintéticos; nunca red ni conjunto sellado."""
from uuid import uuid4
import socket
import pytest
from antifraude.analysis.ingest import build_message, make_sender
from antifraude.app.pipeline import AnalysisPipeline
from antifraude.contracts import Channel, RiskLevel
from antifraude.intel.entities import EntityDirectory

@pytest.fixture
def pipeline(monkeypatch):
    def denied(*args, **kwargs):
        pytest.fail("El análisis pasivo no debe usar red ni DNS")
    monkeypatch.setattr(socket, "getaddrinfo", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    return AnalysisPipeline(EntityDirectory.load_default(include_fictitious=True))

def run(pipeline, body, name="Avisos", email="avisos@boletin.example"):
    return pipeline.run(build_message(user_id=uuid4(), channel=Channel.MANUAL,
        body_text=body, sender=make_sender(name, email)))

@pytest.mark.parametrize("suffix", ["apk", "exe", "EXE?version=2#descarga", "%61pk", "msi", "bat", "ps1", "scr", "com"])
@pytest.mark.parametrize("host", ["descargas.example", "bancoficticio.example"])
def test_r64_descarga_ejecutable_requiere_precaucion(pipeline, suffix, host):
    out=run(pipeline, f"Documento disponible: https://{host}/documento.{suffix}")
    assert out.assessment.risk_level is RiskLevel.MEDIUM
    assert out.assessment.is_partial  # IA requerida pero desactivada
    assert any(f.code == "url.executable_download" for u in out.url_analyses for f in u.findings)
    assert any(r.code == "rec.do_not_click" for r in out.assessment.recommendations)
    assert not any("malicioso" in e.description_user for e in out.assessment.evidence)

@pytest.mark.parametrize("path", ["informe.pdf", "foto.png", "programa.exe.txt", "ayuda/exe", "manual?nombre=programa.exe", "pagina#programa.apk", "producto.apk/descripcion"])
def test_r64_no_marca_documentos_ni_extensiones_en_query(pipeline, path):
    out=run(pipeline, f"Documento disponible: https://documentos.example/{path}")
    assert out.assessment.risk_level is RiskLevel.LOW
    assert not any(f.code == "url.executable_download" for u in out.url_analyses for f in u.findings)

def test_r64_un_remitente_oficial_no_anula_peticion_sensible(pipeline):
    out=run(pipeline, "Confirme su contraseña en https://bancoficticio.example/app.apk", "Banco Ficticio", "avisos@bancoficticio.example")
    assert out.assessment.risk_level is RiskLevel.HIGH
    assert out.assessment.is_partial

@pytest.mark.parametrize("name,email,body,expected", [
    ("Banco Ficticio", "avisos@bancoficticio.example", "Banco Ficticio le invita a su encuesta voluntaria: https://encuestas.example/satisfaccion", RiskLevel.MEDIUM),
    ("Revista", "editor@revista.example", "Mi artículo menciona a Banco Ficticio. Puede leerlo en https://revista.example/articulo", RiskLevel.INCONCLUSIVE),
])
def test_p5_p6_sin_confundir_mencion_e_identidad_ni_excepcion_de_confianza(pipeline, name, email, body, expected):
    out=run(pipeline, body, name, email)
    assert out.assessment.risk_level is expected
    assert out.assessment.is_partial
    # Petición sensible añadida: el supuesto remitente legítimo no evita la alerta.
    attack=run(pipeline, body+" Confirme su contraseña para continuar.", name, email)
    assert attack.assessment.risk_level is RiskLevel.HIGH

def test_p7_acortador_desconocido_no_es_seguro_ni_prueba_de_fraude(pipeline):
    out=run(pipeline, "Puede consultar el resumen en https://acort.test/aviso")
    assert out.assessment.risk_level is RiskLevel.INCONCLUSIVE
    assert out.assessment.is_partial
    assert any("acortado" in u for u in out.assessment.uncertainties)


@pytest.mark.parametrize("name,email", [("Revista","editor@revista.example"),("Ana","ana@correo.example"),("Avisos", "avisos@boletin.example")])
def test_p6_mencion_en_tercera_persona_no_inventa_identidad_bancaria(pipeline, name, email):
    out=run(pipeline,"Este artículo menciona a Banco Ficticio. https://revista.example/articulo",name,email)
    assert out.assessment.risk_level is RiskLevel.INCONCLUSIVE
    assert out.assessment.is_partial
    assert all(u.claimed_entity_id is None for u in out.url_analyses)
    assert not any(f.code == "url.not_official_for_claimed" for u in out.url_analyses for f in u.findings)
    assert any(c.name == "ai.analysis" and c.required for c in out.assessment.checks)

@pytest.mark.parametrize("name,email", [("Banco Ficticio","avisos@bancoficticio.example"),("Avisos", "avisos@bancoficticio.example"),("Banco Ficticio", "alertas@intruso.example")])
def test_identidad_de_remitente_se_conserva_sin_anular_peticion_sensible(pipeline, name, email):
    out=run(pipeline,"Confirme su contraseña en https://acceso.example/validar",name,email)
    assert out.assessment.risk_level is RiskLevel.HIGH
    assert out.assessment.is_partial
    assert all(u.claimed_entity_id == "ficticio_banco" for u in out.url_analyses)

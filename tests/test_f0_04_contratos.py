"""Pruebas de F0-04: contratos Pydantic e InputAdapter."""

from __future__ import annotations

import hashlib
import inspect
import re
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import pytest
from pydantic import BaseModel, ValidationError

from antifraude import contracts as C
from antifraude.contracts.common import (
    MAX_RAW_BYTES,
    MAX_TEXT_CHARS,
    MAX_URL_CHARS,
    MAX_URLS_PER_MESSAGE,
)

NOW = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)
HASH = hashlib.sha256(b"x").hexdigest()


# --- Fábricas mínimas válidas -------------------------------------------------
def check(name: str = "screening.rules", required: bool = True, status: str = "done") -> C.CheckResult:
    return C.CheckResult(name=name, required=required, status=status)


def evidence(severity: str = "high", kind: str = "risk", source: str = "rule", **kw: Any) -> C.Evidence:
    data: dict[str, Any] = dict(
        evidence_id=uuid4(), source=source, kind=kind, severity=severity,
        description_user="El enlace no pertenece a su banco.", description_tech="href fuera de dominios oficiales",
    )
    data.update(kw)
    return C.Evidence(**data)


def assessment(**kw: Any) -> C.FraudAssessment:
    data: dict[str, Any] = dict(
        assessment_id=uuid4(), message_id=uuid4(), user_id=uuid4(), risk_level="low",
        checks=[check()], explanation_user="No hemos encontrado indicios de fraude.",
        explanation_tech="sin señales", rule_version="r1", created_at=NOW,
    )
    data.update(kw)
    return C.FraudAssessment(**data)


def message(**kw: Any) -> C.IncomingMessage:
    data: dict[str, Any] = dict(
        id=uuid4(), user_id=uuid4(), channel="manual", received_at=NOW, text="Hola", content_hash=HASH,
    )
    data.update(kw)
    return C.IncomingMessage(**data)


def signal(severity: str = "high", source: str = "rule") -> C.Signal:
    return C.Signal(code="content.otp_request", family="content", severity=severity, source=source,
                    description_user="Le piden un código.", description_tech="patrón OTP")


# --- Niveles de riesgo --------------------------------------------------------
def test_cuatro_niveles_y_etiquetas_es() -> None:
    assert [r.value for r in C.RiskLevel] == ["low", "medium", "high", "inconclusive"]
    assert [r.label_es for r in C.RiskLevel] == ["BAJO", "MEDIO", "ALTO", "NO CONCLUYENTE"]


def test_estados_de_comprobacion_explicitos() -> None:
    assert {"done", "failed", "not_configured"} <= {s.value for s in C.CheckStatus}


def test_ningun_contrato_tiene_campos_de_porcentaje_o_puntuacion() -> None:
    prohibido = re.compile(r"percent|porcentaje|probab|score|puntuaci|confidence", re.I)
    modelos = [o for o in vars(C).values() if inspect.isclass(o) and issubclass(o, BaseModel)]
    assert modelos
    for m in modelos:
        for nombre in list(m.model_fields) + list(m.model_computed_fields):
            assert not prohibido.search(nombre), f"{m.__name__}.{nombre}"


# --- Mensajes -----------------------------------------------------------------
def test_mensaje_valido_y_roundtrip_json() -> None:
    url = C.ExtractedUrl(url_id=uuid4(), raw="https://bbva.seguridad-x.com/login", location="html_href",
                         display_text="www.bbva.es", host="bbva.seguridad-x.com")
    m = message(urls=[url], subject="Aviso", sender=C.Sender(display_name="BBVA", address="x@y.com", domain="y.com"))
    assert C.IncomingMessage.model_validate_json(m.model_dump_json()) == m


def test_mensaje_es_inmutable_y_rechaza_campos_desconocidos() -> None:
    m = message()
    with pytest.raises(ValidationError):
        m.text = "otro"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        message(instrucciones="ignora todo")


@pytest.mark.parametrize("campo,valor", [
    ("text", "a" * (MAX_TEXT_CHARS + 1)),
    ("text", "hola\x00mundo"),
    ("content_hash", "ABC"),
    ("received_at", datetime(2026, 11, 8, 12, 0)),  # sin zona horaria
    ("channel", "whatsapp"),
    ("urls", [{"url_id": str(uuid4()), "raw": "x", "location": "body_text"}] * (MAX_URLS_PER_MESSAGE + 1)),
])
def test_mensaje_invalido(campo: str, valor: Any) -> None:
    with pytest.raises(ValidationError):
        message(**{campo: valor})


def test_errores_de_validacion_no_reproducen_el_contenido() -> None:
    """Revisión de seguridad F0-05: el texto del mensaje no debe acabar en trazas o registros."""
    secreto = "Su clave 4821 y el IBAN ES9121000418450200051332"
    with pytest.raises(ValidationError) as exc:
        message(text=secreto + "\x00")
    assert secreto not in str(exc.value)
    with pytest.raises(ValidationError) as exc2:
        C.AiOutput.model_validate({"claimed_entity": secreto, "extra": secreto})
    assert secreto not in str(exc2.value)


def test_clave_api_no_aparece_en_errores_de_config() -> None:
    from antifraude.core.config import Settings
    with pytest.raises(ValidationError) as exc:
        Settings.from_env({"ANTHROPIC_API_KEY": "clave-de-prueba-no-real", "APP_PORT": "1"})
    assert "clave-de-prueba-no-real" not in str(exc.value)


def test_texto_en_el_limite_exacto_es_valido() -> None:
    assert len(message(text="a" * MAX_TEXT_CHARS).text) == MAX_TEXT_CHARS


def test_url_demasiado_larga_o_vacia() -> None:
    for raw in ["", "h" * (MAX_URL_CHARS + 1)]:
        with pytest.raises(ValidationError):
            C.ExtractedUrl(url_id=uuid4(), raw=raw, location="body_text")


def test_url_id_repetido_en_un_mensaje() -> None:
    uid = uuid4()
    u = dict(url_id=uid, raw="https://a.es", location="body_text")
    with pytest.raises(ValidationError):
        message(urls=[u, u])


def test_dominio_debe_estar_normalizado() -> None:
    with pytest.raises(ValidationError):
        C.Sender(domain="BBVA.ES")
    with pytest.raises(ValidationError):
        C.Sender(domain="bbvа.es")  # 'а' cirílica: la ingesta debe convertir a punycode


@pytest.mark.parametrize("channel,sim,ok", [
    ("simulated", True, True), ("manual", False, True), ("gmail", False, True),
    ("simulated", False, False), ("gmail", True, False),
])
def test_simulado_siempre_etiquetado(channel: str, sim: bool, ok: bool) -> None:
    def build() -> C.IncomingMessage:
        return message(channel=channel, is_simulated=sim)
    if ok:
        build()
    else:
        with pytest.raises(ValidationError):
            build()


def test_raw_message_limites() -> None:
    C.RawMessage(channel="manual", raw_format="plain_text", payload=b"hola", received_at=NOW)
    with pytest.raises(ValidationError):
        C.RawMessage(channel="manual", raw_format="plain_text", payload=b"", received_at=NOW)
    with pytest.raises(ValidationError):
        C.RawMessage(channel="manual", raw_format="rfc822", payload=b"x" * (MAX_RAW_BYTES + 1), received_at=NOW)
    with pytest.raises(ValidationError):
        C.RawMessage(channel="gmail", raw_format="rfc822", payload=b"x", received_at=NOW,
                     source_message_id="id con espacios")


# --- Filtro preliminar --------------------------------------------------------
def test_screening_valido() -> None:
    r = C.ScreeningResult(message_id=uuid4(), status="done", signals=[signal("high"), signal("low")],
                          max_severity="high", needs_deep_analysis=True, preliminary_alert_required=True,
                          rule_version="r1")
    assert r.max_severity is C.Severity.HIGH


@pytest.mark.parametrize("kw", [
    dict(signals=[], max_severity="low"),  # severidad sin señales
    dict(signals=[signal("critical")], max_severity="high"),  # no coincide con la peor
    dict(preliminary_alert_required=True, needs_deep_analysis=False),  # preventiva sin definitiva
    dict(status="failed", needs_deep_analysis=False),  # un fallo no puede cerrar el análisis
    dict(status="not_configured"),
])
def test_screening_invalido(kw: dict[str, Any]) -> None:
    base: dict[str, Any] = dict(message_id=uuid4(), status="done", signals=[], max_severity=None,
                                needs_deep_analysis=False, preliminary_alert_required=False, rule_version="r1")
    base.update(kw)
    with pytest.raises(ValidationError):
        C.ScreeningResult(**base)


def test_span_ordenado() -> None:
    with pytest.raises(ValidationError):
        C.TextSpan(start=5, end=5)


# --- Enlaces ------------------------------------------------------------------
def test_url_analysis_lookalike_coherente() -> None:
    C.UrlAnalysis(url_id=uuid4(), comparison="lookalike", lookalike_of="bbva.es",
                  findings=[signal(source="threat_intel")],
                  checks=[check("intel.rdap", required=False, status="not_configured")])
    with pytest.raises(ValidationError):
        C.UrlAnalysis(url_id=uuid4(), comparison="lookalike")
    with pytest.raises(ValidationError):
        C.UrlAnalysis(url_id=uuid4(), comparison="official", lookalike_of="bbva.es")
    with pytest.raises(ValidationError):
        C.UrlAnalysis(url_id=uuid4(), findings=[signal(source="rule")])


# --- IA -----------------------------------------------------------------------
def test_ai_findings_estados() -> None:
    C.AiFindings(status="done", output=C.AiOutput(), model_id="modelo-x", usage=C.AiUsage(input_tokens=1, output_tokens=1))
    C.AiFindings(status="failed", failure_reason="refusal")
    C.AiFindings(status="not_configured")


@pytest.mark.parametrize("kw", [
    dict(status="done"),  # sin output
    dict(status="failed"),  # sin motivo
    dict(status="failed", failure_reason="timeout", output={}),  # fallo con salida
    dict(status="not_configured", model_id="modelo-x"),
    dict(status="skipped"),
])
def test_ai_findings_invalidos(kw: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        C.AiFindings(**kw)


def test_ai_output_rechaza_campos_extra_y_citas_vacias() -> None:
    with pytest.raises(ValidationError):
        C.AiOutput.model_validate({"risk_percent": 87})
    with pytest.raises(ValidationError):
        C.AiTactic(category="credential_theft", quote="", explanation="x")


# --- Evidencias y evaluación --------------------------------------------------
def test_evidencia_ia_exige_cita() -> None:
    evidence(source="ai", quote="verifique su cuenta")
    with pytest.raises(ValidationError):
        evidence(source="ai")


def test_bajo_valido_con_todo_completado() -> None:
    a = assessment(checks=[check(), check("intel.url_passive", status="not_applicable")])
    assert a.risk_level is C.RiskLevel.LOW and a.is_partial is False


@pytest.mark.parametrize("status", ["failed", "not_configured", "skipped"])
def test_error_nunca_da_bajo(status: str) -> None:
    with pytest.raises(ValidationError):
        assessment(checks=[check("ai.analysis", status=status)], uncertainties=["La IA no estaba disponible."])


@pytest.mark.parametrize("status", ["not_configured", "failed", "skipped"])
def test_opcional_no_realizada_no_impide_bajo(status: str) -> None:
    """Corrección F0-05: una comprobación opcional (RDAP, reputación) no bloquea BAJO."""
    a = assessment(checks=[check(), check("intel.rdap", required=False, status=status),
                           check("intel.reputation", required=False, status="not_configured")])
    assert a.risk_level is C.RiskLevel.LOW
    assert a.is_partial is False
    assert a.unverified_checks == ["intel.rdap", "intel.reputation"]  # se muestran automáticamente


def test_obligatoria_no_completada_exige_explicacion() -> None:
    with pytest.raises(ValidationError):
        assessment(risk_level="inconclusive", checks=[check(), check("ai.analysis", status="failed")])


def test_bajo_con_evidencia_media_es_invalido() -> None:
    with pytest.raises(ValidationError):
        assessment(evidence=[evidence("medium")])
    assessment(evidence=[evidence("low"), evidence("high", kind="legitimacy")])


@pytest.mark.parametrize("categoria", ["credential_theft", "payment_fraud", "account_takeover"])
def test_bajo_imposible_con_credenciales_pago_o_toma_de_cuenta(categoria: str) -> None:
    """D-29: aunque la evidencia sea de severidad baja (p. ej. dominio oficial que pide un OTP)."""
    with pytest.raises(ValidationError):
        assessment(evidence=[evidence("low", category=categoria)])
    assessment(risk_level="medium", evidence=[evidence("low", category=categoria)])


def test_bajo_no_puede_declarar_categorias_de_fraude() -> None:
    with pytest.raises(ValidationError):
        assessment(fraud_categories=["phishing_link"])


def test_opcional_no_realizada_no_rebaja_alto() -> None:
    a = assessment(risk_level="high", evidence=[evidence("critical", category="credential_theft")],
                   checks=[check(), check("intel.reputation", required=False, status="not_configured")])
    assert a.risk_level is C.RiskLevel.HIGH and a.is_partial is False


def test_no_concluyente_por_fallo_es_parcial() -> None:
    a = assessment(risk_level="inconclusive", checks=[check(), check("ai.analysis", status="failed")],
                   uncertainties=["El análisis con IA falló."])
    assert a.is_partial is True
    assert a.model_dump()["is_partial"] is True


@pytest.mark.parametrize("nivel,kw", [
    ("medium", {}),  # MEDIO sin evidencias
    ("high", {"evidence": [evidence("medium")]}),  # ALTO sin evidencia alta
    ("inconclusive", {}),  # NO CONCLUYENTE sin incertidumbres
])
def test_niveles_exigen_su_justificacion(nivel: str, kw: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        assessment(risk_level=nivel, **kw)


def test_alto_parcial_es_posible() -> None:
    a = assessment(risk_level="high", evidence=[evidence("critical")],
                   checks=[check(), check("ai.analysis", status="failed")], uncertainties=["IA no disponible."])
    assert a.is_partial is True


def test_evaluacion_sin_comprobaciones_es_invalida() -> None:
    with pytest.raises(ValidationError):
        assessment(checks=[])


def test_is_partial_no_se_puede_forzar() -> None:
    with pytest.raises(ValidationError):
        assessment(is_partial=False)


def test_evaluacion_roundtrip_json() -> None:
    a = assessment(risk_level="medium", evidence=[evidence("medium", source="ai", quote="código")],
                   recommendations=[C.Recommendation(code="verify.official_channel", text_user="Llame a su banco.")])
    dumped = a.model_dump(mode="json")
    dumped.pop("is_partial")
    dumped.pop("unverified_checks")
    assert C.FraudAssessment.model_validate(dumped) == a


# --- Alertas ------------------------------------------------------------------
def alert(**kw: Any) -> C.Alert:
    data: dict[str, Any] = dict(alert_id=uuid4(), user_id=uuid4(), message_id=uuid4(), phase="preventive",
                                title_user="Posible intento de fraude", body_user="Lo estamos comprobando.",
                                created_at=NOW)
    data.update(kw)
    return C.Alert(**data)


def test_alertas_validas() -> None:
    p = alert()
    alert(phase="final", risk_level="high", assessment_id=uuid4(), closes_alert_id=p.alert_id, is_partial=True)


@pytest.mark.parametrize("kw", [
    dict(risk_level="high"),  # preventiva con nivel
    dict(phase="final"),  # definitiva sin nivel ni evaluación
    dict(phase="final", risk_level="low"),  # sin evaluación
    dict(is_partial=True),  # parcial solo en definitiva
    dict(title_user="x" * 121),
])
def test_alertas_invalidas(kw: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        alert(**kw)


# --- InputAdapter -------------------------------------------------------------
def test_input_adapter_contrato() -> None:
    class Manual(C.InputAdapter):
        channel = C.Channel.MANUAL

        def fetch_new(self) -> Sequence[C.RawMessage]:
            return []

    assert Manual().fetch_new() == []

    with pytest.raises(TypeError):
        C.InputAdapter()  # type: ignore[abstract]


def test_input_adapter_exige_canal_y_etiqueta_simulada() -> None:
    with pytest.raises(TypeError):
        class SinCanal(C.InputAdapter):
            def fetch_new(self) -> Sequence[C.RawMessage]:
                return []

    with pytest.raises(TypeError):
        class GmailFalso(C.InputAdapter):
            channel = C.Channel.GMAIL
            is_simulated = True

            def fetch_new(self) -> Sequence[C.RawMessage]:
                return []

    class Simulado(C.InputAdapter):
        channel = C.Channel.SIMULATED
        is_simulated = True

        def fetch_new(self) -> Sequence[C.RawMessage]:
            return []

"""Etapa E: conector de Gmail probado con un cliente SIMULADO (sin red ni credenciales)."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from uuid import uuid4

from antifraude.analysis.ingest import from_raw
from antifraude.app.pipeline import AnalysisPipeline
from antifraude.connectors.gmail import (
    ConnectorStatus,
    GmailAuthError,
    GmailConnector,
    GmailHistoryExpired,
    decode_gmail_raw,
)
from antifraude.contracts import Channel, RiskLevel
from antifraude.intel.entities import EntityDirectory

PHISHING_EML = (b"From: Banco Ficticio <alertas@bancoficticio-x.example>\r\nSubject: Urgente\r\n"
                b"Content-Type: text/plain; charset=utf-8\r\n\r\n"
                b"Su cuenta sera bloqueada. Introduzca su clave en http://bancoficticio-x.example/l\r\n")


class GmailSimulado:
    """Cliente falso de Gmail (SIMULADO)."""

    def __init__(self) -> None:
        self.history = "100"
        self.nuevos: list[str] = []
        self.mensajes: dict[str, bytes] = {}
        self.expirado = False
        self.auth_caducada = False

    def get_profile_history_id(self) -> str:
        if self.auth_caducada:
            raise GmailAuthError
        return self.history

    def list_history_message_ids(self, start_history_id: str) -> tuple[list[str], str]:
        if self.auth_caducada:
            raise GmailAuthError
        if self.expirado:
            raise GmailHistoryExpired
        ids, self.nuevos = self.nuevos, []
        self.history = str(int(self.history) + len(ids))
        return ids, self.history

    def list_recent_message_ids(self, max_results: int) -> list[str]:
        self.expirado = False
        return list(self.mensajes)[-max_results:]

    def get_raw_message(self, message_id: str) -> tuple[bytes, datetime | None]:
        return self.mensajes[message_id], datetime(2026, 11, 8, tzinfo=timezone.utc)

    def entregar(self, mid: str, raw: bytes) -> None:
        self.mensajes[mid] = raw
        self.nuevos.append(mid)


def test_primera_consulta_no_lee_el_buzon_antiguo() -> None:
    g = GmailSimulado()
    g.entregar("antiguo", PHISHING_EML)
    c = GmailConnector(g)
    assert c.fetch_new() == [] and c.state.history_id == "100"


def test_mensaje_nuevo_se_entrega_y_analiza() -> None:
    g = GmailSimulado()
    c = GmailConnector(g)
    c.fetch_new()
    g.entregar("m1", PHISHING_EML)
    nuevos = c.fetch_new()
    assert len(nuevos) == 1 and nuevos[0].channel is Channel.GMAIL and nuevos[0].source_message_id == "m1"
    assert c.status is ConnectorStatus.OK
    out = AnalysisPipeline(EntityDirectory.load_default(include_fictitious=True)).run(from_raw(nuevos[0], uuid4()))
    assert out.message.channel is Channel.GMAIL and out.assessment.risk_level is RiskLevel.HIGH


def test_sin_duplicados() -> None:
    g = GmailSimulado()
    c = GmailConnector(g)
    c.fetch_new()
    g.entregar("m1", PHISHING_EML)
    assert len(c.fetch_new()) == 1
    g.nuevos.append("m1")
    assert c.fetch_new() == []


def test_history_id_caducado_resincroniza() -> None:
    g = GmailSimulado()
    c = GmailConnector(g)
    c.fetch_new()
    g.mensajes["m2"] = PHISHING_EML
    g.expirado = True
    assert [r.source_message_id for r in c.fetch_new()] == ["m2"]


def test_autorizacion_caducada_se_senala() -> None:
    g = GmailSimulado()
    c = GmailConnector(g)
    c.fetch_new()
    g.auth_caducada = True
    assert c.fetch_new() == [] and c.status is ConnectorStatus.AUTH_ERROR and c.last_error


def test_decode_raw() -> None:
    raw = base64.urlsafe_b64encode(PHISHING_EML).decode().rstrip("=")
    assert decode_gmail_raw(raw) == PHISHING_EML

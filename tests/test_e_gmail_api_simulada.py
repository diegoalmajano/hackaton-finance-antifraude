"""Adaptador de la API de Gmail y sondeo, probados con un servicio SIMULADO que imita googleapiclient."""

from __future__ import annotations

import base64
import time
from typing import Any

import pytest

from antifraude.connectors.gmail import GmailAuthError, GmailConnector, GmailHistoryExpired
from antifraude.connectors.gmail_api import GmailApiClient, GmailPoller
from antifraude.contracts.messages import RawMessage

EML = b"From: x@bancoficticio-x.example\r\nSubject: Aviso\r\n\r\nIntroduzca su clave en http://x.test/l\r\n"


class _Req:
    def __init__(self, resultado: Any) -> None:
        self.resultado = resultado

    def execute(self) -> Any:
        if isinstance(self.resultado, Exception):
            raise self.resultado
        return self.resultado


class HttpErrorFalso(Exception):
    def __init__(self, status: int) -> None:
        super().__init__(status)
        self.resp = type("R", (), {"status": status})()


class ServicioSimulado:
    """Imita la cadena service.users().history().list(...).execute() (SIMULADO)."""

    def __init__(self) -> None:
        self.paginas: list[dict[str, Any]] = []
        self.llamadas: list[dict[str, Any]] = []
        self.error: Exception | None = None

    def users(self) -> "ServicioSimulado":
        return self

    def getProfile(self, userId: str) -> _Req:  # noqa: N802 (nombre de la API de Google)
        return _Req(self.error or {"historyId": "500"})

    def history(self) -> "ServicioSimulado":
        return self

    def messages(self) -> "ServicioSimulado":
        return self

    def list(self, **kw: Any) -> _Req:
        self.llamadas.append(kw)
        if self.error:
            return _Req(self.error)
        if "startHistoryId" in kw:
            return _Req(self.paginas.pop(0))
        return _Req({"messages": [{"id": "r1"}, {"id": "r2"}]})

    def get(self, userId: str, id: str, format: str) -> _Req:  # noqa: A002
        assert format == "raw"
        raw = base64.urlsafe_b64encode(EML).decode().rstrip("=")
        return _Req({"id": id, "raw": raw, "internalDate": "1794150000000"})


def test_paginacion_del_historial_y_mensajes_crudos() -> None:
    s = ServicioSimulado()
    s.paginas = [
        {"history": [{"messagesAdded": [{"message": {"id": "a"}}]}], "nextPageToken": "p2", "historyId": "501"},
        {"history": [{"messagesAdded": [{"message": {"id": "b"}}, {"message": {"id": "a"}}]}], "historyId": "502"},
    ]
    c = GmailApiClient(s)
    assert c.get_profile_history_id() == "500"
    ids, nuevo = c.list_history_message_ids("500")
    assert ids == ["a", "b"] and nuevo == "502"
    assert s.llamadas[1]["pageToken"] == "p2" and s.llamadas[0]["historyTypes"] == ["messageAdded"]
    raw, fecha = c.get_raw_message("a")
    assert raw == EML and fecha is not None and fecha.year >= 2026
    assert c.list_recent_message_ids(5) == ["r1", "r2"]
    assert s.llamadas[-1]["includeSpamTrash"] is True


@pytest.mark.parametrize("status,excepcion", [(404, GmailHistoryExpired), (401, GmailAuthError), (403, GmailAuthError)])
def test_errores_http_se_traducen(status: int, excepcion: type[Exception]) -> None:
    s = ServicioSimulado()
    s.error = HttpErrorFalso(status)
    with pytest.raises(excepcion):
        GmailApiClient(s).list_history_message_ids("1")


def test_conector_completo_sobre_el_adaptador() -> None:
    s = ServicioSimulado()
    s.paginas = [{"history": [{"messagesAdded": [{"message": {"id": "m9"}}]}], "historyId": "600"}]
    con = GmailConnector(GmailApiClient(s))
    assert con.fetch_new() == []  # primera consulta: solo guarda el historyId
    nuevos = con.fetch_new()
    assert [r.source_message_id for r in nuevos] == ["m9"]


def test_sondeo_en_hilo_se_detiene_limpiamente() -> None:
    recibidos: list[RawMessage] = []

    class ConectorFalso:
        def __init__(self) -> None:
            self.n = 0

        def fetch_new(self) -> list[RawMessage]:
            self.n += 1
            return []

    poller = GmailPoller(ConectorFalso(), recibidos.append, interval_s=0.01)  # type: ignore[arg-type]
    poller.start()
    time.sleep(0.1)
    poller.stop()
    assert poller.cycles >= 2 and poller._thread is not None and not poller._thread.is_alive()


def test_un_mensaje_que_falla_no_detiene_el_sondeo() -> None:
    from datetime import datetime, timezone
    from antifraude.contracts.messages import Channel, RawFormat
    raws = [RawMessage(channel=Channel.GMAIL, raw_format=RawFormat.RFC822, payload=EML,
                       received_at=datetime.now(timezone.utc), source_message_id=str(i)) for i in range(3)]

    class ConectorFalso:
        def fetch_new(self) -> list[RawMessage]:
            return raws

    vistos: list[str] = []

    def procesar(r: RawMessage) -> None:
        if r.source_message_id == "1":
            raise RuntimeError("fallo")
        vistos.append(r.source_message_id or "")

    assert GmailPoller(ConectorFalso(), procesar).poll_once() == 3  # type: ignore[arg-type]
    assert vistos == ["0", "2"]

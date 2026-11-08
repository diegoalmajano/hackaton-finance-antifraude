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


# --- Misión 3: duplicados, mensajes no analizables, keyring seguro y desconexión (SIMULADO) ---------
def test_duplicados_no_se_entregan_dos_veces_y_la_memoria_esta_acotada() -> None:
    from antifraude.connectors import gmail as g
    s = ServicioSimulado()
    s.paginas = [{"history": [{"messagesAdded": [{"message": {"id": "m1"}}]}], "historyId": "601"},
                 {"history": [{"messagesAdded": [{"message": {"id": "m1"}}]}], "historyId": "602"}]
    con = GmailConnector(GmailApiClient(s))
    con.fetch_new()
    assert len(con.fetch_new()) == 1 and con.fetch_new() == []  # el mismo id en otra página de historial
    estado = g.GmailState()
    for i in range(g.MAX_SEEN_IDS + 50):
        estado.mark_seen(str(i))
    assert len(estado.seen_ids) == g.MAX_SEEN_IDS and "0" not in estado.seen_ids


def test_mensaje_demasiado_grande_se_comunica_no_se_pierde(monkeypatch: pytest.MonkeyPatch) -> None:
    from antifraude.connectors import gmail as g
    monkeypatch.setattr(g, "MAX_RAW_BYTES", 10)  # el EML de prueba supera 10 bytes
    s = ServicioSimulado()
    s.paginas = [{"history": [{"messagesAdded": [{"message": {"id": "grande"}}]}], "historyId": "700"}]
    con = GmailConnector(GmailApiClient(s))
    con.fetch_new()
    fallos: list[str | None] = []
    poller = GmailPoller(con, lambda raw: None, on_failure=fallos.append)
    assert poller.poll_once() == 0
    assert fallos == ["grande"] and poller.failures == 1 and con.unanalyzable == []


def test_fallo_al_analizar_se_comunica_con_el_id_y_sin_contenido() -> None:
    from datetime import datetime, timezone
    from antifraude.contracts.messages import Channel, RawFormat
    raw = RawMessage(channel=Channel.GMAIL, raw_format=RawFormat.RFC822, payload=EML,
                     received_at=datetime.now(timezone.utc), source_message_id="id-7")

    class ConectorFalso:
        def fetch_new(self) -> list[RawMessage]:
            return [raw]

    def falla(_: RawMessage) -> None:
        raise ValueError("cabecera rota")

    fallos: list[str | None] = []
    GmailPoller(ConectorFalso(), falla, on_failure=fallos.append).poll_once()  # type: ignore[arg-type]
    assert fallos == ["id-7"]


class _KeyringFalso:
    """SIMULADO: imita el módulo keyring con un almacén en memoria."""

    def __init__(self, backend: object, falla_al_borrar: bool = False) -> None:
        self._backend = backend
        self._datos: dict[tuple[str, str], str] = {}
        self._falla = falla_al_borrar

    def get_keyring(self) -> object:
        return self._backend

    def get_password(self, s: str, u: str) -> str | None:
        return self._datos.get((s, u))

    def set_password(self, s: str, u: str, p: str) -> None:
        self._datos[(s, u)] = p

    def delete_password(self, s: str, u: str) -> None:
        if self._falla:
            raise RuntimeError("no se pudo")
        self._datos.pop((s, u), None)


class WinVaultKeyring:
    priority = 5


class PlaintextKeyring:
    priority = 0.5


def test_keyring_inseguro_se_rechaza() -> None:
    from antifraude.connectors.gmail_api import GmailSetupError, ensure_secure_keyring
    ensure_secure_keyring(_KeyringFalso(WinVaultKeyring()))
    with pytest.raises(GmailSetupError):
        ensure_secure_keyring(_KeyringFalso(PlaintextKeyring()))


def test_desconexion_informa_si_no_pudo_borrar_el_token() -> None:
    from antifraude.connectors.gmail_api import KEYRING_SERVICE, KEYRING_USER, forget_local_token
    k = _KeyringFalso(WinVaultKeyring())
    assert forget_local_token(k) is True  # no había token
    k.set_password(KEYRING_SERVICE, KEYRING_USER, "token-de-prueba")
    assert forget_local_token(k) is True and k.get_password(KEYRING_SERVICE, KEYRING_USER) is None
    roto = _KeyringFalso(WinVaultKeyring(), falla_al_borrar=True)
    roto.set_password(KEYRING_SERVICE, KEYRING_USER, "token-de-prueba")
    assert forget_local_token(roto) is False


def test_mensajes_por_encima_del_maximo_no_se_pierden(monkeypatch: pytest.MonkeyPatch) -> None:
    from antifraude.connectors import gmail as g
    monkeypatch.setattr(g, "MAX_MESSAGES_PER_POLL", 2)
    s = ServicioSimulado()
    s.paginas = [{"history": [{"messagesAdded": [{"message": {"id": f"m{i}"}} for i in range(5)]}],
                  "historyId": "800"},
                 {"historyId": "801"}, {"historyId": "802"}]
    con = GmailConnector(GmailApiClient(s))
    con.fetch_new()  # primera consulta: solo historyId
    entregados = [r.source_message_id for r in con.fetch_new()]
    entregados += [r.source_message_id for r in con.fetch_new()]  # el historial ya avanzó: salen de pendientes
    entregados += [r.source_message_id for r in con.fetch_new()]
    assert entregados == ["m0", "m1", "m2", "m3", "m4"]


def test_error_transitorio_se_reintenta_y_luego_se_comunica() -> None:
    from antifraude.connectors import gmail as g

    class ClienteFalso:
        def __init__(self) -> None:
            self.llamadas = 0

        def get_profile_history_id(self) -> str:
            return "1"

        def list_history_message_ids(self, start: str) -> tuple[list[str], str]:
            return (["roto"] if start == "1" else []), "2"

        def list_recent_message_ids(self, n: int) -> list[str]:
            return []

        def get_raw_message(self, mid: str) -> tuple[bytes, None]:
            self.llamadas += 1
            raise RuntimeError("500")

    cli = ClienteFalso()
    con = GmailConnector(cli)  # type: ignore[arg-type]
    con.fetch_new()
    for _ in range(g.MAX_FETCH_ATTEMPTS):
        assert con.fetch_new() == []
    assert cli.llamadas == g.MAX_FETCH_ATTEMPTS and con.unanalyzable == ["roto"] and con.state.pending == []

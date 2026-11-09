"""R-69: errores y recuperación de cuota, servicio SIMULADO sin red/OAuth."""
from __future__ import annotations
import json
import socket
import pytest
from antifraude.connectors.gmail import ConnectorStatus, GmailAuthError, GmailConnector, GmailQuotaError, MAX_FETCH_ATTEMPTS
from antifraude.connectors.gmail_api import GmailApiClient
from test_e_gmail_api_simulada import ServicioSimulado, HttpErrorFalso, _Req

class ErrorConDetalle(HttpErrorFalso):
    def __init__(self, status, reasons=(), content=None):
        super().__init__(status)
        self.content = content if content is not None else json.dumps({"error": {
            "errors": [{"reason": reason} for reason in reasons],
            "message": "detalle remoto que no debe mostrarse"}}).encode()

class ServicioConCuota(ServicioSimulado):
    def __init__(self):
        super().__init__()
        self.raw_error = None
        self.gets = []
    def get(self, userId, id, format):
        self.gets.append(id)
        error = self.error or (self.raw_error if id == "b" else None)
        return _Req(error) if error else super().get(userId, id, format)

@pytest.fixture(autouse=True)
def sin_red(monkeypatch):
    def denied(*args, **kwargs):
        pytest.fail("Esta prueba simulada no puede usar red ni DNS")
    monkeypatch.setattr(socket, "getaddrinfo", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)

QUOTAS = [(403, "dailyLimitExceeded"), (403, "rateLimitExceeded"),
          (403, "userRateLimitExceeded"), (429, None)]

@pytest.mark.parametrize("status,reason", QUOTAS)
@pytest.mark.parametrize("operation", ["profile", "history", "recent", "raw"])
def test_la_cuota_no_se_traduce_como_autorizacion(status, reason, operation):
    service = ServicioConCuota()
    service.error = ErrorConDetalle(status, [reason] if reason else [])
    api = GmailApiClient(service)
    actions = {"profile": api.get_profile_history_id,
               "history": lambda: api.list_history_message_ids("1"),
               "recent": lambda: api.list_recent_message_ids(20),
               "raw": lambda: api.get_raw_message("b")}
    with pytest.raises(GmailQuotaError) as captured:
        actions[operation]()
    assert "detalle remoto" not in str(captured.value)

@pytest.mark.parametrize("status,content", [
    (401, b'{"error":{"errors":[{"reason":"rateLimitExceeded"}]}}'),
    (403, b'no json'), (403, b'[]'), (403, b'{"error":null}'),
    (403, b'{"error":{"errors":[{"reason":"domainPolicy"}]}}'),
    (403, b'{"error":{"errors":[{"reason":"rateLimitExceeded"},{"reason":"authError"}]}}'),
    (403, b'{"error":{"errors":[{"reason":"rateLimitExceeded"},{}]}}'),
    (403, b'x'*70000),
])
def test_autorizacion_y_detalles_desconocidos_no_se_disfrazan_de_cuota(status, content):
    service = ServicioConCuota()
    service.error = ErrorConDetalle(status, content=content)
    with pytest.raises(GmailAuthError):
        GmailApiClient(service).get_profile_history_id()

@pytest.mark.parametrize("status,reason", [(403,"userRateLimitExceeded"),(429,None)])
def test_cuota_inicial_es_error_y_se_recupera_sin_reautorizar(status, reason):
    service = ServicioConCuota()
    service.error = ErrorConDetalle(status,[reason] if reason else [])
    connector = GmailConnector(GmailApiClient(service))
    assert connector.fetch_new() == []
    assert connector.status is ConnectorStatus.ERROR
    assert connector.last_error and "autorizar" not in connector.last_error
    assert "detalle remoto" not in connector.last_error
    assert connector.state.history_id is None
    service.error = None
    assert connector.fetch_new() == []
    assert connector.status is ConnectorStatus.OK
    assert connector.state.history_id == "500"

@pytest.mark.parametrize("status,reason", [(403,"rateLimitExceeded"),(429,None)])
def test_cuota_en_descarga_conserva_lote_y_no_agota_intentos_del_mensaje(status, reason):
    service = ServicioConCuota()
    service.paginas = [{"history":[{"messagesAdded":[{"message":{"id":x}} for x in ("a","b","c")]}],"historyId":"600"}]
    service.paginas += [{"historyId":str(601+i)} for i in range(MAX_FETCH_ATTEMPTS+3)]
    connector = GmailConnector(GmailApiClient(service))
    connector.fetch_new()
    service.raw_error = ErrorConDetalle(status,[reason] if reason else [])
    assert [m.source_message_id for m in connector.fetch_new()] == ["a"]
    assert connector.status is ConnectorStatus.ERROR
    assert connector.state.pending == ["b","c"]
    assert service.gets == ["a","b"]  # se corta el lote al alcanzar la cuota
    for _ in range(MAX_FETCH_ATTEMPTS+1):
        assert connector.fetch_new() == []
        assert connector.status is ConnectorStatus.ERROR
    assert connector.state.seen_ids == {"a"}
    assert connector.state.pending == ["b","c"]
    assert connector.state.attempts == {} and connector.unanalyzable == []
    assert all(mid == "b" for mid in service.gets[2:])
    service.raw_error = None
    assert [m.source_message_id for m in connector.fetch_new()] == ["b","c"]
    assert connector.status is ConnectorStatus.OK and connector.last_error is None
    assert connector.state.pending == [] and connector.state.seen_ids == {"a","b","c"}


@pytest.mark.parametrize("status,reason", [(403,"dailyLimitExceeded"),(429,None)])
def test_cuota_al_consultar_historial_conserva_cursor_y_pendientes(status, reason):
    service = ServicioConCuota()
    connector = GmailConnector(GmailApiClient(service))
    connector.fetch_new()
    connector.state.pending = ["b"]
    service.error = ErrorConDetalle(status, [reason] if reason else [])
    assert connector.fetch_new() == []
    assert connector.status is ConnectorStatus.ERROR
    assert connector.state.history_id == "500"
    assert connector.state.pending == ["b"]
    assert connector.state.seen_ids == set() and connector.state.attempts == {}
    assert service.gets == []
    service.error = None
    service.paginas = [{"historyId":"600"}]
    assert [m.source_message_id for m in connector.fetch_new()] == ["b"]
    assert connector.status is ConnectorStatus.OK
    assert connector.state.history_id == "600" and connector.state.pending == []

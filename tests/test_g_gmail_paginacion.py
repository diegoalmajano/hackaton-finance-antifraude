"""Consentimiento por petición/página: servicio SIMULADO, sin OAuth/SDK/red."""
import socket
import pytest
from antifraude.app.gmail_bridge import _GuardedClient
from antifraude.connectors.gmail import GmailAuthError
from antifraude.connectors.gmail_api import GmailApiClient


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("La prueba simulada no puede acceder a red ni DNS")
    monkeypatch.setattr(socket,"getaddrinfo",forbidden)
    monkeypatch.setattr(socket.socket,"connect",forbidden)


class FakeService:
    def __init__(self, consent, revoke_at=None):
        self.consent=consent
        self.revoke_at=revoke_at
        self.executions=[]
    def users(self):return self
    def history(self):return self
    def messages(self):return self
    def request(self, operation, page=1):
        service=self
        class Request:
            def execute(self):
                service.executions.append((operation,page,service.consent[0]))
                if operation=="history":
                    if page==service.revoke_at:service.consent[0]=False
                    result={"historyId":str(100+page),"history":[{"messagesAdded":[{"message":{"id":str(page)}}]}]}
                    if page<3:result["nextPageToken"]=str(page+1)
                    return result
                if operation=="profile":return {"historyId":"100"}
                if operation=="recent":return {"messages":[{"id":"a"}]}
                return {"raw":"QQ=="}
        return Request()
    def getProfile(self, **kwargs):return self.request("profile")
    def list(self, **kwargs):
        return self.request("history",int(kwargs.get("pageToken",1))) if "startHistoryId" in kwargs else self.request("recent")
    def get(self, **kwargs):return self.request("raw")


@pytest.mark.parametrize("revoke_at",[1,2])
def test_revocar_en_una_pagina_impide_la_siguiente_execute(revoke_at):
    consent=[True];service=FakeService(consent,revoke_at)
    client=GmailApiClient(service)
    setter=getattr(client,"set_read_guard",None)
    if setter is not None:setter(lambda:consent[0])
    guarded=_GuardedClient(client,lambda:consent[0])
    with pytest.raises(GmailAuthError):
        guarded.list_history_message_ids("100")
    assert len(service.executions)==revoke_at
    assert all(active for _,_,active in service.executions)


@pytest.mark.parametrize("operation",["profile","history","recent","raw"])
def test_denegacion_inicial_no_ejecuta_ninguna_lectura(operation):
    consent=[False];service=FakeService(consent);client=GmailApiClient(service)
    client.set_read_guard(lambda:consent[0])
    operations={"profile":client.get_profile_history_id,"history":lambda:client.list_history_message_ids("100"),
                "recent":lambda:client.list_recent_message_ids(20),"raw":lambda:client.get_raw_message("a")}
    with pytest.raises(GmailAuthError):operations[operation]()
    assert service.executions==[]


def test_callback_fallido_no_envia_peticion_ni_expone_su_detalle():
    consent=[True];service=FakeService(consent);client=GmailApiClient(service)
    def failed():raise RuntimeError("detalle interno sintético")
    client.set_read_guard(failed)
    with pytest.raises(GmailAuthError) as captured:client.get_profile_history_id()
    assert service.executions==[]
    assert "detalle interno" not in str(captured.value)


def test_sin_guard_sigue_compatible_y_pagina_sin_duplicados():
    consent=[True];service=FakeService(consent);client=GmailApiClient(service)
    assert client.get_profile_history_id()=="100"
    assert client.list_history_message_ids("100")==(["1","2","3"],"103")
    assert client.list_recent_message_ids(20)==["a"]
    assert client.get_raw_message("a")[0]==b"A"
    assert len(service.executions)==6

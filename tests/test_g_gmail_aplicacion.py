"""Unión Gmail→panel con cliente SIMULADO; nunca OAuth/cuenta real ni red."""
from collections import deque
import threading
import time
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from antifraude.app.main import create_app
from antifraude.app.gmail_bridge import GmailBridge, GmailConnectionError, MAX_GMAIL_ALERTS
from antifraude.app.pipeline import AnalysisPipeline
from antifraude.app.security.sessions import SessionStore
from antifraude.app.security.policy import SESSION_COOKIE_NAME
from antifraude.connectors.gmail import GmailAuthError, GmailQuotaError
from antifraude.core.config import Settings
from antifraude.intel.entities import EntityDirectory
from conftest import FakeClock, CodeCapture, BASE_URL, ORIGIN

EML = (b"From: Banco Ficticio <avisos@bancoficticio.example>\n"
       b"Subject: SINTETICO\nContent-Type: text/plain; charset=utf-8\n\n"
       b"Confirme su contrase" + "ñ".encode() + b"a en https://intruso.example/validar")


class Client:
    def __init__(self):
        self.pending = deque()
        self.payloads = {}
        self.lock = threading.Lock()
        self.error = None
        self.reads = []
        self.closed = False

    def add(self, mid, payload=EML):
        with self.lock:
            self.payloads[mid] = payload
            self.pending.append(mid)

    def get_profile_history_id(self):
        return "100"

    def list_history_message_ids(self, start):
        if self.error:
            raise self.error
        with self.lock:
            ids = list(self.pending)
            self.pending.clear()
        return ids, "101"

    def list_recent_message_ids(self, maximum):
        return []

    def get_raw_message(self, mid):
        self.reads.append(mid)
        return self.payloads[mid], datetime.now(timezone.utc)

    def close(self):
        self.closed = True


def wait_for(condition):
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        value = condition()
        if value:
            return value
        time.sleep(0.005)
    pytest.fail("El flujo simulado no terminó en el tiempo esperado")


@pytest.fixture
def bridge():
    clock = FakeClock()
    sessions = SessionStore(clock=clock)
    _, owner = sessions.create()
    client = Client()
    deleted = []
    service = GmailBridge(sessions=sessions,
        pipeline=AnalysisPipeline(EntityDirectory.load_default(include_fictitious=True)),
        client_factory=lambda: client, forget_token=lambda: deleted.append(True) or True,
        simulated=True, interval_s=0.01)
    yield service, owner, client, sessions, clock, deleted
    service.close()


def test_flujo_simulado_minimizado_con_alerta_explicada_y_deduplicacion(bridge):
    service, owner, client, _, _, _ = bridge
    service.connect(owner)
    wait_for(lambda: service.snapshot(owner)["state"] == "connected")
    client.add("sintetico-1")
    wait_for(lambda: service.snapshot(owner)["analyzed"] == 1)
    snapshot = service.snapshot(owner)
    assert snapshot["simulated"] is True
    assert snapshot["alerts"][0]["risk"] == "high"
    assert snapshot["alerts"][0]["evidence"] and snapshot["alerts"][0]["recommendations"]
    assert snapshot["alerts"][0]["partial"] is True
    assert all(word not in snapshot["alerts"][0] for word in ("body", "text", "subject", "sender", "source_message_id"))
    client.add("sintetico-1")
    time.sleep(0.05)
    assert service.snapshot(owner)["analyzed"] == 1


def test_otro_navegador_no_ve_ni_desconecta_conexion_ajena(bridge):
    service, owner, client, sessions, _, _ = bridge
    _, other = sessions.create()
    service.connect(owner)
    wait_for(lambda: service.snapshot(owner)["state"] == "connected")
    client.add("privado-sintetico")
    wait_for(lambda: service.snapshot(owner)["analyzed"] == 1)
    assert service.snapshot(other)["alerts"] == []
    service.disconnect(other)
    assert service.snapshot(owner)["running"]
    with pytest.raises(GmailConnectionError):
        service.connect(other)


def test_desconexion_borra_alertas_cierra_cliente_y_retira_token(bridge):
    service, owner, client, _, _, deleted = bridge
    service.connect(owner)
    wait_for(lambda: service.snapshot(owner)["state"] == "connected")
    service.disconnect(owner)
    wait_for(lambda: not service.snapshot(owner)["running"])
    assert service.snapshot(owner)["alerts"] == []
    assert client.closed and deleted


def test_caducidad_detiene_y_no_prolonga_sesion(bridge):
    service, owner, client, _, clock, deleted = bridge
    initial_seen = owner.last_seen
    service.connect(owner)
    wait_for(lambda: service.snapshot(owner)["state"] == "connected")
    assert owner.last_seen == initial_seen
    clock.advance(1801)
    wait_for(lambda: not service.snapshot(owner)["running"])
    client.add("posterior")
    assert client.reads == [] and deleted


def test_revocacion_durante_autorizacion_no_inicia_lectura_y_borra_token_tardio():
    clock = FakeClock(); sessions = SessionStore(clock=clock)
    raw_id, owner = sessions.create()
    entered, release = threading.Event(), threading.Event()
    client = Client(); deleted = []
    def factory():
        entered.set(); assert release.wait(2)
        return client
    service = GmailBridge(sessions=sessions, pipeline=AnalysisPipeline(EntityDirectory.load_default()),
        client_factory=factory, forget_token=lambda: deleted.append(True) or True, simulated=True, interval_s=0.01)
    try:
        service.connect(owner); assert entered.wait(1)
        sessions.revoke(raw_id); service.disconnect(owner); release.set()
        wait_for(lambda: not service.snapshot(owner)["running"])
        assert client.reads == [] and deleted and client.closed
    finally:
        release.set(); service.close()


@pytest.mark.parametrize("error,state", [(GmailQuotaError(),"error"),(GmailAuthError(),"auth_error")])
def test_errores_de_cuota_y_autorizacion_visibles_sin_correo_expuesto(bridge, error, state):
    service, owner, client, _, _, _ = bridge
    client.error = error
    service.connect(owner)
    snapshot = wait_for(lambda: (s if (s := service.snapshot(owner))["state"] == state else None))
    assert snapshot["message"] and snapshot["alerts"] == []


def test_fallo_de_ingesta_nunca_bajo(bridge):
    service, owner, client, _, _, _ = bridge
    service.connect(owner)
    wait_for(lambda: service.snapshot(owner)["state"] == "connected")
    client.add("sin-cuerpo", b"Subject: SINTETICO\n\n")
    wait_for(lambda: service.snapshot(owner)["analyzed"] == 1)
    assert service.snapshot(owner)["alerts"][0]["risk"] == "inconclusive"
    assert service.snapshot(owner)["alerts"][0]["failed"] is True


def test_retencion_acotada_y_shutdown(bridge):
    service, owner, client, _, _, deleted = bridge
    service.connect(owner)
    wait_for(lambda: service.snapshot(owner)["state"] == "connected")
    for i in range(MAX_GMAIL_ALERTS+3):
        client.add(str(i))
    wait_for(lambda: service.snapshot(owner)["analyzed"] == MAX_GMAIL_ALERTS+3)
    assert len(service.snapshot(owner)["alerts"]) == MAX_GMAIL_ALERTS
    service.close()
    assert not service.snapshot(owner)["running"] and deleted


@pytest.fixture
def app_gmail():
    clock, codes, client = FakeClock(), CodeCapture(), Client()
    deleted = []
    app = create_app(Settings.from_env({"APP_GMAIL_ENABLED":"1","APP_DEMO_MODE":"1"}),
        clock=clock,code_sink=codes,gmail_client_factory=lambda: client,
        gmail_forget_token=lambda: deleted.append(True) or True,gmail_simulated=True,gmail_interval_s=0.01)
    with TestClient(app, base_url=BASE_URL) as browser:
        assert browser.post("/pairing",data={"code":codes.last},headers={"Origin":ORIGIN}).status_code==204
        token = browser.get("/session").json()["csrf_token"]
        headers={"Origin":ORIGIN,"X-CSRF-Token":token}
        yield app,browser,client,headers,clock,deleted


def test_http_consentimiento_csrf_origin_y_espera_visible(app_gmail):
    app,browser,client,h,_,_=app_gmail
    assert browser.post("/gmail/connect",data={"consent":"1"},headers={"Origin":ORIGIN}).status_code==403
    assert browser.post("/gmail/connect",data={"consent":"1"},headers={**h,"Origin":"https://ajeno.example"}).status_code==403
    assert browser.post("/gmail/connect",headers=h).status_code==400
    assert browser.post("/gmail/connect",data={"consent":"1"},headers=h).status_code==200
    wait_for(lambda: app.state.gmail.snapshot(app.state.gmail._binding.session)["state"]=="connected")
    client.add("uno")
    wait_for(lambda: app.state.gmail.snapshot(app.state.gmail._binding.session)["analyzed"]==1)
    page=browser.get("/gmail")
    assert page.status_code==200 and "SIMULADO" in page.text and "ALTO" in page.text
    assert "Por qué" in page.text and "Qué hacer" in page.text
    assert "Content-Security-Policy" in page.headers
    assert browser.post("/gmail/disconnect",headers=h).status_code==200


def test_http_logout_detiene_recepcion_y_aisla_alertas(app_gmail):
    app,browser,client,h,_,deleted=app_gmail
    browser.post("/gmail/connect",data={"consent":"1"},headers=h)
    wait_for(lambda: app.state.gmail.snapshot(app.state.gmail._binding.session)["state"]=="connected")
    assert browser.post("/session/logout",headers=h).status_code==204
    wait_for(lambda: deleted)
    assert browser.get("/gmail").status_code==401


def test_http_sondeo_no_extiende_sesion(app_gmail):
    _,browser,_,_,clock,_=app_gmail
    for _ in range(4):
        clock.advance(500)
        result=browser.get("/gmail")
    assert result.status_code==401


def test_gmail_apagado_por_defecto_sin_invocar_fabrica():
    called=[]; codes=CodeCapture()
    app=create_app(Settings.from_env({}),code_sink=codes,gmail_client_factory=lambda: called.append(True))
    with TestClient(app,base_url=BASE_URL) as client:
        client.post("/pairing",data={"code":codes.last},headers={"Origin":ORIGIN})
        csrf=client.get("/session").json()["csrf_token"]
        response=client.post("/gmail/connect",data={"consent":"1"},headers={"Origin":ORIGIN,"X-CSRF-Token":csrf})
        assert response.status_code==409 and not called


def test_sesion_ajena_no_reutiliza_credencial_tras_error_de_autorizacion(bridge):
    service, owner, client, sessions, _, _ = bridge
    _, other = sessions.create()
    client.error = GmailAuthError()
    service.connect(owner)
    wait_for(lambda: service.snapshot(owner)["state"] == "auth_error")
    with pytest.raises(GmailConnectionError):
        service.connect(other)
    service.disconnect(owner)
    wait_for(lambda: service.snapshot(owner)["state"] == "disconnected")


def test_fallo_al_borrar_token_se_explica_y_bloquea_otra_sesion(bridge):
    service, owner, client, sessions, _, _ = bridge
    _, other = sessions.create()
    service.forget_token = lambda: False
    service.connect(owner)
    wait_for(lambda: service.snapshot(owner)["state"] == "connected")
    service.disconnect(owner)
    wait_for(lambda: not service.snapshot(owner)["running"])
    snapshot = service.snapshot(owner)
    assert snapshot["state"] == "cleanup_error" and "no se pudo borrar" in snapshot["message"]
    with pytest.raises(GmailConnectionError):
        service.connect(other)


def test_refresco_http_no_reemplaza_controles_sin_cambios(app_gmail):
    app,browser,_,h,_,_=app_gmail
    initial=browser.get("/gmail").text
    assert 'hx-trigger="every 5s"' not in initial
    browser.post("/gmail/connect",data={"consent":"1"},headers=h)
    session=app.state.gmail._binding.session
    wait_for(lambda: app.state.gmail.snapshot(session)["state"]=="connected")
    rev=app.state.gmail.snapshot(session)["revision"]
    assert browser.get(f"/gmail?revision={rev}").status_code==204
    assert 'hx-trigger="every 5s"' in browser.get("/gmail").text


def test_gmail_no_usa_analizador_ia_de_entrada_manual(app_gmail):
    app,_,_,_,_,_=app_gmail
    from antifraude.ai.base import DisabledAi
    assert isinstance(app.state.gmail.pipeline.ai, DisabledAi)


def test_limpieza_pendiente_no_borra_permiso_de_una_nueva_conexion(bridge):
    service, owner, _, _, _, _ = bridge
    service.connect(owner)
    wait_for(lambda: service.snapshot(owner)["state"] == "connected")
    service.disconnect(owner)
    wait_for(lambda: not service.snapshot(owner)["running"])
    entered, release = threading.Event(), threading.Event()
    def blocked_forget():
        entered.set(); assert release.wait(2)
        return True
    service.forget_token = blocked_forget
    cleanup = threading.Thread(target=service.disconnect, args=(owner,))
    cleanup.start()
    try:
        assert entered.wait(1)
        with pytest.raises(GmailConnectionError):
            service.connect(owner)
    finally:
        release.set(); cleanup.join(2)


def test_error_de_autorizacion_se_limpia_al_cerrar(bridge):
    service, owner, client, _, _, deleted = bridge
    client.error = GmailAuthError()
    service.connect(owner)
    wait_for(lambda: service.snapshot(owner)["state"] == "auth_error")
    service.close()
    assert deleted and not service.snapshot(owner)["running"]


def test_aviso_alto_no_desaparece_sin_resumen_por_limite_de_tarjetas(bridge):
    service, owner, client, _, _, _ = bridge
    service.connect(owner)
    wait_for(lambda: service.snapshot(owner)["state"] == "connected")
    client.add("peligroso", EML)
    for i in range(MAX_GMAIL_ALERTS):
        client.add(f"legitimo-{i}", b"Subject: Sintetico\n\nSu pedido llega hoy. No necesita hacer nada.")
    wait_for(lambda: service.snapshot(owner)["analyzed"] == MAX_GMAIL_ALERTS+1)
    snapshot = service.snapshot(owner)
    assert not any(a["risk"] == "high" for a in snapshot["alerts"])
    assert snapshot["risk_counts"]["high"] == 1


def test_configuracion_rechaza_credencial_dentro_del_repo():
    from pathlib import Path
    from pydantic import ValidationError
    inside=Path(__file__).resolve().parents[1]/"client_secret_sintetico.json"
    with pytest.raises(ValidationError):
        Settings.from_env({"APP_GMAIL_CLIENT_SECRET":str(inside)})


def test_error_de_autorizacion_se_limpia_al_caducar_sin_nuevas_lecturas(bridge):
    service, owner, client, _, clock, deleted = bridge
    client.error=GmailAuthError()
    service.connect(owner)
    wait_for(lambda: service.snapshot(owner)["state"]=="auth_error")
    clock.advance(1801)
    wait_for(lambda: deleted)
    assert not client.reads


def test_guard_del_adaptador_se_instala_antes_de_leer(bridge):
    service, owner, client, _, _, _ = bridge
    installed=[]
    client.set_read_guard=lambda callback: installed.append(callback)
    original=client.get_profile_history_id
    def checked():
        assert installed and installed[0]()
        return original()
    client.get_profile_history_id=checked
    service.connect(owner)
    wait_for(lambda: service.snapshot(owner)["state"]=="connected")
    assert installed


def test_permiso_no_borrado_no_se_presta_a_sesion_nueva_tras_caducar(bridge):
    service, owner, _, sessions, clock, _ = bridge
    service.forget_token=lambda: False
    service.connect(owner)
    wait_for(lambda: service.snapshot(owner)["state"]=="connected")
    service.disconnect(owner)
    wait_for(lambda: not service.snapshot(owner)["running"])
    assert service.snapshot(owner)["state"]=="cleanup_error"
    clock.advance(1801)
    _, other=sessions.create()
    with pytest.raises(GmailConnectionError):
        service.connect(other)

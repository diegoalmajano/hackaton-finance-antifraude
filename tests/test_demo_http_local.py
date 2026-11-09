"""Demo contra un servidor Uvicorn real en loopback; sin navegador ni APIs externas."""
from pathlib import Path
import socket
import threading
import time
import httpx
import pytest
import uvicorn
from antifraude.app.main import create_app
from antifraude.core.config import Settings

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def live():
    sock=socket.socket()
    sock.bind(("127.0.0.1",0))
    port=sock.getsockname()[1]
    codes=[]
    app=create_app(Settings.from_env({"APP_PORT":str(port), "APP_DEMO_MODE":"1",
        "AI_ENABLED":"0", "AI_BUDGET_USD":"0", "AI_ALLOW_OPUS":"0"}),
        code_sink=lambda code, ttl: codes.append(code))
    server=uvicorn.Server(uvicorn.Config(app,host="127.0.0.1",port=port,
        log_level="critical",access_log=False,proxy_headers=False,server_header=False))
    thread=threading.Thread(target=server.run,kwargs={"sockets":[sock]},daemon=True)
    thread.start()
    try:
        deadline=time.monotonic()+5
        while not server.started and thread.is_alive() and time.monotonic()<deadline:
            time.sleep(0.01)
        assert server.started, "El servidor local no arrancó"
        base=f"http://127.0.0.1:{port}"
        with httpx.Client(base_url=base,trust_env=False,timeout=5) as client:
            assert client.get("/").status_code==200
            assert "conecte" in client.get("/panel").text.lower()
            assert client.post("/pairing",data={"code":codes[-1]},headers={"Origin":base,"Sec-Fetch-Site":"same-origin"}).status_code==204
            token=client.get("/session").json()["csrf_token"]
            headers={"Origin":base,"Sec-Fetch-Site":"same-origin","X-CSRF-Token":token,"HX-Request":"true"}
            yield client,headers
    finally:
        server.should_exit=True
        thread.join(5)
        sock.close()
        assert not thread.is_alive(), "El servidor de prueba debe cerrarse"

@pytest.mark.parametrize("filename,level",[("01-sintetico.eml","bajo"),("02-sintetico.eml","alto"),("03-sintetico.eml","alto"),("04-ambiguo-sintetico.eml","no-concluyente")])
def test_demo_eml_y_prioridad_sobre_texto(live, filename, level):
    client,headers=live
    raw=(ROOT/"docs/entrega/ejemplos"/filename).read_bytes()
    result=client.post("/analizar",data={"texto":"Confirme su contraseña urgente en https://intruso.example"},files={"archivo":(filename,raw,"message/rfc822")},headers=headers)
    assert result.status_code==200
    assert f'data-nivel="{level}"' in result.text
    assert "inteligencia artificial no está configurado" in result.text
    assert "Content-Security-Policy" in result.headers
    assert "X-Content-Type-Options" in result.headers
    if level!="bajo":
        assert "Lo que no hemos podido comprobar" in result.text
        assert "Análisis parcial" in result.text
    assert "Análisis manual" in client.get("/panel").text

def test_demo_texto_validacion_y_cierre(live):
    client,headers=live
    assert client.post("/analizar",data={"texto":""},headers=headers).status_code==400
    assert client.post("/analizar",files={"archivo":("invalido.txt",b"sintetico","text/plain")},headers=headers).status_code==400
    assert client.post("/analizar",data={"texto":"Su pedido llegará mañana. No tiene que pagar nada."},headers=headers).status_code==200
    assert client.post("/analizar",data={"texto":"x"},headers={"Origin":headers["Origin"]}).status_code==403
    assert client.post("/analizar",data={"texto":"x"},headers={**headers,"Origin":"https://ajeno.example"}).status_code==403
    assert client.post("/session/logout",headers=headers).status_code==204
    assert client.get("/session").status_code==401
    assert "Para ver su panel" in client.get("/panel").text

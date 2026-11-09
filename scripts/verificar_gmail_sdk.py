"""Compatibilidad del SDK Gmail instalado, con OAuth/HTTP/keyring SIMULADOS.

Ejecutar con el intérprete del entorno opcional previamente autorizado:
    <python-del-entorno> -B scripts/verificar_gmail_sdk.py

No conecta cuentas ni accede al almacén personal de credenciales. Bloquea red,
DNS, servidores locales y navegador; carga el discovery incluido en el SDK.
No forma parte de pytest: faltar dependencias es un error explícito, no un skip.
"""
from __future__ import annotations

import base64
from contextlib import ExitStack, contextmanager
import inspect
from importlib.metadata import version
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = {"google-auth-oauthlib": "1.5.0", "google-api-python-client": "2.201.0", "keyring": "25.7.0"}
SDK = None
ADAPTER = None


def denied(*args, **kwargs):
    raise AssertionError("La comprobación del SDK no permite red, navegador ni credenciales reales.")


def load_dependencies():
    # Importar no selecciona ni consulta el backend keyring. Todas sus operaciones
    # se sustituyen antes de ejecutar cualquier constructor del producto.
    import httplib2
    import keyring
    import requests.sessions
    from google.auth.credentials import AnonymousCredentials
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient import discovery, discovery_cache
    from googleapiclient.errors import HttpError
    return SimpleNamespace(httplib2=httplib2, keyring=keyring, requests=requests.sessions,
        AnonymousCredentials=AnonymousCredentials, Credentials=Credentials,
        Flow=InstalledAppFlow, discovery=discovery, discovery_cache=discovery_cache,
        HttpError=HttpError, flow_signature=inspect.signature(InstalledAppFlow.run_local_server),
        versions={name: version(name) for name in VERSIONS})


@contextmanager
def offline_only():
    with ExitStack() as stack:
        for name in ("connect", "connect_ex", "bind", "listen"):
            stack.enter_context(patch.object(socket.socket, name, side_effect=denied))
        for name in ("create_connection", "getaddrinfo", "gethostbyname", "gethostbyname_ex", "gethostbyaddr"):
            stack.enter_context(patch.object(socket, name, side_effect=denied))
        for name in ("open", "open_new", "open_new_tab"):
            stack.enter_context(patch.object(webbrowser, name, side_effect=denied))
        for name in ("get_keyring", "set_keyring", "get_password", "set_password", "delete_password", "get_credential"):
            stack.enter_context(patch.object(SDK.keyring, name, side_effect=denied))
        stack.enter_context(patch.object(SDK.Flow, "from_client_secrets_file", side_effect=denied))
        stack.enter_context(patch.object(SDK.Flow, "run_local_server", side_effect=denied))
        stack.enter_context(patch.object(SDK.Credentials, "refresh", side_effect=denied))
        stack.enter_context(patch.object(SDK.discovery, "build", side_effect=denied))
        stack.enter_context(patch.object(SDK.httplib2.Http, "request", side_effect=denied))
        stack.enter_context(patch.object(SDK.requests.Session, "request", side_effect=denied))
        yield


class SyntheticBackend:
    priority = 1


class SDKCompatibility(unittest.TestCase):
    def test_vetos_activos_sin_ejecutar_red_ni_keyring_real(self):
        with self.assertRaises(AssertionError):
            socket.getaddrinfo("bloqueado.invalid", 443)
        with self.assertRaises(AssertionError):
            webbrowser.open("https://accounts.google.com/")
        with self.assertRaises(AssertionError):
            SDK.keyring.get_password("SINTETICO", "SINTETICO")
        with self.assertRaises(AssertionError):
            SDK.discovery.build("gmail", "v1")

    def static_service(self):
        document = SDK.discovery_cache.get_static_doc("gmail", "v1")
        self.assertIsNotNone(document, "El SDK no contiene discovery estático de Gmail v1.")
        return SDK.discovery.build_from_document(document, credentials=SDK.AnonymousCredentials())

    @contextmanager
    def oauth_doubles(self, *, deletion_fails=False, priority=1):
        # Ninguna de estas funciones delega al keyring real: el token solo vive en este dict.
        store = {"token": "SIMULADO-ANTERIOR-NO-REAL"}
        events = []
        def get_password(*args):
            events.append("get")
            return store.get("token")
        def delete_password(*args):
            events.append("delete")
            if deletion_fails:
                raise RuntimeError("Fallo SINTÉTICO al retirar el permiso")
            store.pop("token", None)
        def set_password(service, user, value):
            events.append("set")
            store["token"] = value
        credentials = SimpleNamespace(refresh_token="SIMULADO-NUEVO-NO-REAL")
        def run_local_server(**kwargs):
            events.append("oauth")
            return credentials
        flow = SimpleNamespace(run_local_server=Mock(side_effect=run_local_server))
        def create_flow(*args, **kwargs):
            events.append("flow")
            return flow
        service = object()
        backend = SyntheticBackend()
        backend.priority = priority
        with ExitStack() as stack:
            stack.enter_context(patch.object(SDK.keyring, "get_keyring", return_value=backend))
            stack.enter_context(patch.object(SDK.keyring, "get_password", side_effect=get_password))
            stack.enter_context(patch.object(SDK.keyring, "delete_password", side_effect=delete_password))
            put = stack.enter_context(patch.object(SDK.keyring, "set_password", side_effect=set_password))
            factory = stack.enter_context(patch.object(SDK.Flow, "from_client_secrets_file", side_effect=create_flow))
            build = stack.enter_context(patch.object(SDK.discovery, "build", return_value=service))
            with tempfile.TemporaryDirectory(prefix="gmail-sdk-sintetico-") as folder:
                secret = Path(folder) / "client_secret_sintetico.json"
                secret.write_text(json.dumps({"installed": {
                    "client_id": "SINTETICO.apps.googleusercontent.com", "client_secret": "SINTETICO-NO-REAL",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token", "redirect_uris": ["http://127.0.0.1"]}}), encoding="utf-8")
                yield SimpleNamespace(store=store, events=events, flow=flow, factory=factory,
                    build=build, put=put, secret=secret, service=service, credentials=credentials)

    def test_versiones_y_forma_de_api_instaladas(self):
        self.assertEqual(SDK.versions, VERSIONS)
        for name in ("host", "bind_addr", "port", "open_browser", "timeout_seconds", "authorization_prompt_message"):
            self.assertIn(name, SDK.flow_signature.parameters)
        self.assertEqual(ADAPTER.SCOPES, ["https://www.googleapis.com/auth/gmail.readonly"])
        service = self.static_service()
        self.assertTrue(callable(service.users().getProfile))
        self.assertTrue(callable(service.users().history().list))
        self.assertTrue(callable(service.users().messages().get))
        self.assertTrue(callable(service.close))
        service.close()

    def test_adaptador_con_sdk_real_y_http_simulado(self):
        service = self.static_service()
        raw = b"From: sintesis@demo.example\nSubject: SINTETICO\n\nMensaje de prueba."
        payloads = iter([
            {"historyId": "100"},
            {"history": [{"messagesAdded": [{"message": {"id": "a"}}]}], "nextPageToken": "pagina2", "historyId": "101"},
            {"history": [{"messagesAdded": [{"message": {"id": "b"}}]}], "historyId": "102"},
            {"messages": [{"id": "a"}]},
            {"raw": base64.urlsafe_b64encode(raw).decode(), "internalDate": "1000"},
        ])
        def synthetic_http(*args, **kwargs):
            return SDK.httplib2.Response({"status": "200"}), json.dumps(next(payloads)).encode()
        with patch.object(service._http, "request", side_effect=synthetic_http) as http:
            client = ADAPTER.GmailApiClient(service)
            self.assertEqual(client.get_profile_history_id(), "100")
            self.assertEqual(client.list_history_message_ids("100"), (["a", "b"], "102"))
            self.assertEqual(client.list_recent_message_ids(20), ["a"])
            result, received = client.get_raw_message("a")
            self.assertEqual(result, raw)
            self.assertEqual(received.timestamp(), 1)
            self.assertEqual(http.call_count, 5)
            requests = [call.args[0] for call in http.call_args_list]
            self.assertIn("pageToken=pagina2", requests[2])
            self.assertIn("format=raw", requests[-1])
            client.close()

    def test_http_errors_reales_generados_por_respuestas_simuladas(self):
        from antifraude.connectors.gmail import GmailAuthError, GmailHistoryExpired, GmailQuotaError
        cases = [(403, "dailyLimitExceeded", GmailQuotaError), (403, "rateLimitExceeded", GmailQuotaError),
                 (403, "userRateLimitExceeded", GmailQuotaError), (429, "rateLimitExceeded", GmailQuotaError),
                 (401, "authError", GmailAuthError), (403, "domainPolicy", GmailAuthError),
                 (404, "notFound", GmailHistoryExpired), (500, "backendError", SDK.HttpError)]
        for status, reason, expected in cases:
            with self.subTest(status=status, reason=reason):
                service = self.static_service()
                body = json.dumps({"error": {"code": status, "message": "Fallo SIMULADO", "errors": [{"reason": reason}]}}).encode()
                with patch.object(service._http, "request", return_value=(SDK.httplib2.Response({"status": str(status)}), body)):
                    with self.assertRaises(expected):
                        ADAPTER.GmailApiClient(service).get_profile_history_id()
                service.close()

    def test_revalida_permiso_antes_de_la_segunda_pagina_del_sdk(self):
        from antifraude.connectors.gmail import GmailAuthError
        service = self.static_service()
        allowed = [True]
        def first_page(*args, **kwargs):
            allowed[0] = False
            return SDK.httplib2.Response({"status": "200"}), b'{"nextPageToken":"pagina2","historyId":"101"}'
        client = ADAPTER.GmailApiClient(service)
        client.set_read_guard(lambda: allowed[0])
        with patch.object(service._http, "request", side_effect=first_page) as http:
            with self.assertRaises(GmailAuthError):
                client.list_history_message_ids("100")
            self.assertEqual(http.call_count, 1)
        service.close()

    def test_force_consent_retira_permiso_simulado_y_solicita_elegir_cuenta(self):
        with self.oauth_doubles() as fake:
            service = ADAPTER.build_gmail_service(fake.secret, force_consent=True)
            self.assertIs(service, fake.service)
            self.assertLess(fake.events.index("delete"), fake.events.index("flow"))
            self.assertLess(fake.events.index("oauth"), fake.events.index("set"))
            self.assertEqual(fake.store["token"], "SIMULADO-NUEVO-NO-REAL")
            fake.factory.assert_called_once_with(str(fake.secret), ADAPTER.SCOPES)
            kwargs = fake.flow.run_local_server.call_args.kwargs
            self.assertEqual(kwargs["host"], "127.0.0.1")
            self.assertEqual(kwargs["bind_addr"], "127.0.0.1")
            self.assertEqual(kwargs["port"], 0)
            self.assertEqual(kwargs["timeout_seconds"], 120)
            self.assertIs(kwargs["open_browser"], True)  # Se comprueba el parámetro; el navegador no se abre.
            self.assertIsNone(kwargs["authorization_prompt_message"])
            self.assertEqual(kwargs["prompt"], "select_account consent")
            # La firma auténtica del SDK acepta los argumentos que recibió el doble.
            SDK.flow_signature.bind(None, **kwargs)
            fake.build.assert_called_once_with("gmail", "v1", credentials=fake.credentials, cache_discovery=False)

    def test_force_consent_no_sigue_si_no_puede_retirar_permiso(self):
        with self.oauth_doubles(deletion_fails=True) as fake:
            with self.assertRaises(ADAPTER.GmailSetupError):
                ADAPTER.build_gmail_service(fake.secret, force_consent=True)
            fake.factory.assert_not_called()
            fake.flow.run_local_server.assert_not_called()
            fake.put.assert_not_called()
            fake.build.assert_not_called()
            self.assertEqual(fake.store["token"], "SIMULADO-ANTERIOR-NO-REAL")

    def test_backend_inseguro_simulado_bloquea_antes_de_oauth(self):
        with self.oauth_doubles(priority=0) as fake:
            with self.assertRaises(ADAPTER.GmailSetupError):
                ADAPTER.build_gmail_service(fake.secret, force_consent=True)
            fake.factory.assert_not_called()
            fake.build.assert_not_called()
            self.assertEqual(fake.events, [])


def main():
    global SDK, ADAPTER
    os.environ.update({name: "0" for name in ("AI_ENABLED", "AI_BUDGET_USD", "AI_ALLOW_OPUS",
        "ANTIFRAUDE_PRUEBAS_REALES", "ANTIFRAUDE_PRUEBAS_REALES_GMAIL", "APP_GMAIL_ENABLED")})
    for name in ("ANTHROPIC_API_KEY", "CLAUDE_MODEL", "APP_GMAIL_CLIENT_SECRET", "GMAIL_CLIENT_SECRET"):
        os.environ.pop(name, None)
    try:
        SDK = load_dependencies()
    except (ImportError, LookupError) as exc:
        print("Faltan dependencias opcionales o metadatos. No se ha ejecutado ninguna comprobación.", file=sys.stderr)
        print("Use el entorno autorizado con las versiones de VERSIONS; no se instala nada automáticamente.", file=sys.stderr)
        print(type(exc).__name__, file=sys.stderr)
        return 2
    sys.path.insert(0, str(ROOT / "backend"))
    print("SDK instalado; OAuth, keyring y respuestas HTTP SIMULADOS. Red/DNS/navegador bloqueados.")
    print("Versiones:", SDK.versions, flush=True)
    with offline_only():
        from antifraude.connectors import gmail_api
        ADAPTER = gmail_api
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(SDKCompatibility)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    print("No se han conectado cuentas, abierto OAuth ni consultado credenciales personales.")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

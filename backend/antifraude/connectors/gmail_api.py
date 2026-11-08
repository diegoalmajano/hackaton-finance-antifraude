"""Adaptador de la API real de Gmail y sondeo periódico (preparado; Etapa E).

Estado:
- ``GmailApiClient`` y ``GmailPoller``: implementados y **probados con un servicio SIMULADO** que imita
  las respuestas de la API (``users.getProfile``, ``users.history.list``, ``users.messages.list/get``).
- ``build_gmail_service`` (OAuth de app de escritorio + token en keyring): implementado pero **NO
  PROBADO**; necesita instalar ``google-auth-oauthlib``, ``google-api-python-client`` y ``keyring``
  (pendiente de autorización) y un cliente OAuth «Desktop» de Google Cloud (B-04).

Solo lectura (scope ``gmail.readonly``). Nada se marca como leído ni se modifica. Ver
``docs/GMAIL_CONFIGURACION.md``.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from antifraude.connectors.gmail import (
    GmailAuthError,
    GmailConnector,
    GmailHistoryExpired,
    decode_gmail_raw,
)
from antifraude.contracts.messages import RawMessage

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
KEYRING_SERVICE = "hackaton-finance-antifraude-gmail"
KEYRING_USER = "refresh-token"


class GmailSetupError(RuntimeError):
    """No se puede preparar Gmail (faltan librerías, credenciales o autorización)."""


def _status_of(exc: Exception) -> int | None:
    """Código HTTP de un ``HttpError`` de googleapiclient sin importar la librería."""
    resp = getattr(exc, "resp", None)
    status = getattr(resp, "status", None) if resp is not None else getattr(exc, "status_code", None)
    try:
        return int(status) if status is not None else None
    except (TypeError, ValueError):
        return None


def _translate(exc: Exception) -> Exception:
    status = _status_of(exc)
    if status == 404:
        return GmailHistoryExpired()
    if status in (401, 403):
        return GmailAuthError()
    return exc


class GmailApiClient:
    """Implementa ``GmailClient`` sobre un objeto ``service`` de googleapiclient (inyectable)."""

    def __init__(self, service: Any, user_id: str = "me") -> None:
        self.service = service
        self.user_id = user_id

    def _users(self) -> Any:
        return self.service.users()

    def get_profile_history_id(self) -> str:
        try:
            return str(self._users().getProfile(userId=self.user_id).execute()["historyId"])
        except Exception as exc:
            raise _translate(exc) from exc

    def list_history_message_ids(self, start_history_id: str) -> tuple[list[str], str]:
        ids: list[str] = []
        page_token: str | None = None
        latest = start_history_id
        try:
            while True:
                kwargs: dict[str, Any] = {"userId": self.user_id, "startHistoryId": start_history_id,
                                          "historyTypes": ["messageAdded"]}
                if page_token:
                    kwargs["pageToken"] = page_token
                resp = self._users().history().list(**kwargs).execute()
                for h in resp.get("history", []):
                    for added in h.get("messagesAdded", []):
                        mid = added.get("message", {}).get("id")
                        if mid and mid not in ids:
                            ids.append(mid)
                latest = str(resp.get("historyId", latest))
                page_token = resp.get("nextPageToken")
                if not page_token:
                    return ids, latest
        except Exception as exc:
            raise _translate(exc) from exc

    def list_recent_message_ids(self, max_results: int) -> list[str]:
        try:
            resp = self._users().messages().list(userId=self.user_id, maxResults=max_results,
                                                 includeSpamTrash=True).execute()
        except Exception as exc:
            raise _translate(exc) from exc
        return [m["id"] for m in resp.get("messages", []) if "id" in m]

    def get_raw_message(self, message_id: str) -> tuple[bytes, datetime | None]:
        try:
            resp = self._users().messages().get(userId=self.user_id, id=message_id, format="raw").execute()
        except Exception as exc:
            raise _translate(exc) from exc
        received = None
        if resp.get("internalDate"):
            try:
                received = datetime.fromtimestamp(int(resp["internalDate"]) / 1000, tz=timezone.utc)
            except (TypeError, ValueError, OverflowError):
                received = None
        return decode_gmail_raw(resp.get("raw", "")), received


def build_gmail_service(client_secret_path: Path) -> Any:  # pragma: no cover - requiere librerías no instaladas
    """OAuth de app de escritorio (redirección loopback) y servicio Gmail. NO PROBADO (ver docstring del módulo)."""
    try:
        import keyring  # type: ignore[import-not-found]
        from google.auth.transport.requests import Request  # type: ignore[import-not-found]
        from google.oauth2.credentials import Credentials  # type: ignore[import-not-found]
        from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore[import-not-found]
        from googleapiclient.discovery import build  # type: ignore[import-not-found]
    except ImportError as exc:
        raise GmailSetupError("Faltan las librerías de Google o keyring (instalación pendiente de autorización).") from exc
    if not client_secret_path.is_file():
        raise GmailSetupError("No se encuentra el archivo del cliente OAuth (client_secret*.json, fuera del repositorio).")
    creds = None
    refresh = keyring.get_password(KEYRING_SERVICE, KEYRING_USER)
    if refresh:
        import json
        info = json.loads(client_secret_path.read_text(encoding="utf-8"))["installed"]
        creds = Credentials(None, refresh_token=refresh, token_uri=info["token_uri"], client_id=info["client_id"],
                            client_secret=info["client_secret"], scopes=SCOPES)
        try:
            creds.refresh(Request())
        except Exception:
            creds = None  # caducado (modo Testing: 7 días) → volver a autorizar
    if creds is None:
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)
        creds = flow.run_local_server(host="localhost", port=0, open_browser=True)
        if creds.refresh_token:
            keyring.set_password(KEYRING_SERVICE, KEYRING_USER, creds.refresh_token)
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def forget_local_token() -> None:  # pragma: no cover - requiere keyring
    """Borra el token local. La revocación en Google se hace desde la cuenta (ver la guía)."""
    try:
        import keyring  # type: ignore[import-not-found]
    except ImportError:
        return
    try:
        keyring.delete_password(KEYRING_SERVICE, KEYRING_USER)
    except Exception:
        pass


class GmailPoller:
    """Consulta periódica en un hilo: entrega cada mensaje nuevo a ``on_message``. Se detiene limpiamente."""

    def __init__(self, connector: GmailConnector, on_message: Callable[[RawMessage], None],
                 interval_s: float = 30.0) -> None:
        self.connector = connector
        self.on_message = on_message
        self.interval_s = interval_s
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.cycles = 0

    def poll_once(self) -> int:
        nuevos = self.connector.fetch_new()
        for raw in nuevos:
            try:
                self.on_message(raw)
            except Exception:
                continue  # un mensaje que falla no detiene el resto; el pipeline ya declara sus errores
        self.cycles += 1
        return len(nuevos)

    def _run(self) -> None:
        while not self._stop.is_set():
            self.poll_once()
            self._stop.wait(self.interval_s)

    def start(self) -> None:
        if self._thread is None:
            self._thread = threading.Thread(target=self._run, name="gmail-poller", daemon=True)
            self._thread.start()

    def stop(self, timeout_s: float = 5.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout_s)

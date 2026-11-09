"""Une el conector Gmail al panel: consentimiento por sesión y alertas solo en memoria.

No abre OAuth al arrancar. La fábrica se invoca únicamente tras el POST consentido.
El cliente real permanece opcional; las pruebas inyectan clientes SIMULADOS.
"""
from __future__ import annotations

import copy
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from antifraude.analysis.ingest import from_raw
from antifraude.app.pipeline import AnalysisPipeline
from antifraude.app.security.sessions import Session, SessionStore
from antifraude.connectors.gmail import ConnectorStatus, GmailAuthError, GmailClient, GmailConnector
from antifraude.connectors.gmail_api import GmailPoller
from antifraude.contracts.messages import Channel, RawMessage

MAX_GMAIL_ALERTS = 20


class GmailConnectionError(Exception):
    """Error apto para mostrar sin información de credenciales ni del correo."""


@dataclass
class _Binding:
    session: Session
    user_id: UUID = field(default_factory=uuid4)
    stop: threading.Event = field(default_factory=threading.Event)
    thread: threading.Thread | None = None
    alerts: deque = field(default_factory=lambda: deque(maxlen=MAX_GMAIL_ALERTS))
    state: str = "connecting"
    message: str = "Complete la autorización en la ventana de Google."
    analyzed: int = 0
    revision: int = 0
    cleaning: bool = False
    risk_counts: dict[str, int] = field(default_factory=dict)


class _GuardedClient:
    """Revalida el consentimiento ANTES de cada operación de lectura externa."""
    def __init__(self, client: GmailClient, allowed: Callable[[], bool]):
        self.client, self.allowed = client, allowed

    def _check(self):
        if not self.allowed():
            raise GmailAuthError()

    def get_profile_history_id(self):
        self._check()
        return self.client.get_profile_history_id()

    def list_history_message_ids(self, start):
        self._check()
        return self.client.list_history_message_ids(start)

    def list_recent_message_ids(self, maximum):
        self._check()
        return self.client.list_recent_message_ids(maximum)

    def get_raw_message(self, message_id):
        self._check()
        return self.client.get_raw_message(message_id)


class GmailBridge:
    def __init__(self, *, sessions: SessionStore, pipeline: AnalysisPipeline,
                 client_factory: Callable[[], GmailClient] | None,
                 forget_token: Callable[[], bool], simulated: bool = False,
                 interval_s: float = 30.0):
        self.sessions, self.pipeline = sessions, pipeline
        self.client_factory, self.forget_token = client_factory, forget_token
        self.simulated, self.interval_s = simulated, interval_s
        self._lock = threading.RLock()
        self._binding: _Binding | None = None
        self._closed = False

    def _allowed(self, binding: _Binding) -> bool:
        return not binding.stop.is_set() and self.sessions.is_active(binding.session)

    def connect(self, session: Session) -> None:
        with self._lock:
            if self._closed or self.client_factory is None:
                raise GmailConnectionError("La conexión con Gmail todavía no está habilitada en este asistente.")
            if not self.sessions.is_active(session):
                raise GmailConnectionError("La sesión ha caducado. Vuelva a conectar el navegador.")
            old = self._binding
            if old and old.state == "cleanup_error":
                raise GmailConnectionError("No se ha podido retirar el permiso anterior. Resuelva el borrado del permiso local antes de volver a conectar.")
            if old and old.session is not session and old.state != "disconnected" and self.sessions.is_active(old.session):
                raise GmailConnectionError("Gmail está reservado a otro navegador. Desconéctelo desde la sesión que lo autorizó.")
            if old and (old.cleaning or old.state == "stopping"):
                raise GmailConnectionError("Espere a que termine la desconexión antes de conectar Gmail de nuevo.")
            if old and old.thread and old.thread.is_alive():
                raise GmailConnectionError("Ya hay una conexión en curso. Desconéctela y espere a que termine.")
            binding = _Binding(session)
            self._binding = binding
            binding.thread = threading.Thread(target=self._run, args=(binding,), name="gmail-session", daemon=True)
            binding.thread.start()

    def _record(self, binding: _Binding, item: dict) -> None:
        with self._lock:
            if self._allowed(binding):
                binding.alerts.appendleft(item)
                binding.analyzed += 1
                binding.revision += 1
                risk = item["risk"]
                binding.risk_counts[risk] = binding.risk_counts.get(risk, 0) + 1

    def _message(self, binding: _Binding, raw: RawMessage) -> None:
        if not self._allowed(binding):
            return
        if self.simulated:
            raw = raw.model_copy(update={"channel": Channel.SIMULATED, "is_simulated": True})
        # La conexión Gmail NO concede permiso de transmisión a IA externa.
        out = self.pipeline.run(from_raw(raw, binding.user_id))
        a = out.assessment
        self._record(binding, {"id": uuid4().hex, "risk": a.risk_level.value,
            "title": out.final_alert.title_user, "explanation": a.explanation_user,
            "recommendations": [r.text_user for r in a.recommendations],
            "evidence": [e.description_user for e in a.evidence],
            "uncertainties": list(a.uncertainties), "partial": a.is_partial,
            "failed": False})
        # No se conserva out/IncomingMessage ni cuerpo, asunto, remitente o id de Gmail.

    def _failure(self, binding: _Binding) -> None:
        self._record(binding, {"id": uuid4().hex, "risk": "inconclusive",
            "title": "NO CONCLUYENTE: no se pudo analizar un correo",
            "explanation": "No ha sido posible completar la comprobación. Revíselo por un canal conocido.",
            "recommendations": ["No abra enlaces ni comparta datos hasta comprobar el mensaje."],
            "evidence": [], "uncertainties": ["El correo no se ha podido analizar."],
            "partial": True, "failed": True})

    def _state(self, binding: _Binding, state: str, message: str) -> None:
        if (binding.state, binding.message) != (state, message):
            binding.state, binding.message = state, message
            binding.revision += 1

    def _run(self, binding: _Binding) -> None:
        client = None
        try:
            if not self._allowed(binding):
                return
            client = self.client_factory()
            setter = getattr(client, "set_read_guard", None)
            if callable(setter):
                setter(lambda: self._allowed(binding))
            guarded = _GuardedClient(client, lambda: self._allowed(binding))
            connector = GmailConnector(guarded)
            poller = GmailPoller(connector, lambda raw: self._message(binding, raw),
                                 on_failure=lambda _: self._failure(binding))
            errors = 0
            while self._allowed(binding):
                try:
                    poller.poll_once()
                    with self._lock:
                        if not self._allowed(binding):
                            break
                        if connector.status is ConnectorStatus.OK:
                            self._state(binding, "connected", "Gmail conectado. Se comprobarán los mensajes nuevos.")
                            errors = 0
                        else:
                            self._state(binding, "auth_error" if connector.status is ConnectorStatus.AUTH_ERROR else "error",
                                        connector.last_error or "No se pudo consultar Gmail.")
                            errors = min(errors + 1, 4)
                    if connector.status is ConnectorStatus.AUTH_ERROR:
                        break
                except Exception:
                    with self._lock:
                        self._state(binding, "error", "No se pudo completar la comprobación de Gmail.")
                    errors = min(errors + 1, 4)
                deadline = time.monotonic() + min(self.interval_s * (2 ** errors), 300.0)
                while self._allowed(binding) and time.monotonic() < deadline:
                    binding.stop.wait(min(0.5, max(0.0, deadline - time.monotonic())))
        except Exception:
            with self._lock:
                self._state(binding, "error", "No se pudo conectar Gmail. Revise la configuración o vuelva a autorizar.")
        finally:
            # Si se requiere reautorizar, se supervisa la sesión sin emitir más lecturas.
            # Así la caducidad/cierre también limpia una conexión que ya falló.
            while self._allowed(binding):
                binding.stop.wait(0.2)
            if client is not None:
                try:
                    close = getattr(client, "close", None)
                    if callable(close):
                        close()
                except Exception:
                    pass
            if not self._allowed(binding):
                # También se elimina un token que haya llegado después de cancelar OAuth.
                self._cleanup(binding)

    def _cleanup(self, binding: _Binding) -> None:
        with self._lock:
            if binding.cleaning:
                return
            binding.cleaning = True
            self._state(binding, "stopping", "Retirando el permiso local de Gmail…")
        try:
            forgotten = self.forget_token()
        except Exception:
            forgotten = False
        with self._lock:
            binding.alerts.clear()
            binding.analyzed = 0
            binding.risk_counts.clear()
            self._state(binding, "disconnected" if forgotten else "cleanup_error",
                "Gmail desconectado. La recepción está detenida." if forgotten
                else "La recepción está detenida, pero no se pudo borrar el permiso local. Revoque el acceso en Google.")
            binding.cleaning = False

    def disconnect(self, session: Session) -> None:
        with self._lock:
            binding = self._binding
            if binding is None or binding.session is not session:
                return
            binding.stop.set()
            binding.alerts.clear()
            binding.analyzed = 0
            binding.risk_counts.clear()
            self._state(binding, "stopping", "Deteniendo Gmail y retirando el permiso local…")
            alive = binding.thread is not None and binding.thread.is_alive()
        if not alive:
            self._cleanup(binding)

    def snapshot(self, session: Session) -> dict:
        with self._lock:
            binding = self._binding
            if binding and not self._allowed(binding):
                binding.stop.set()
                binding.alerts.clear()
            owned = binding is not None and binding.session is session
            return {"enabled": self.client_factory is not None, "simulated": self.simulated,
                "state": binding.state if owned else "disconnected",
                "message": binding.message if owned else "Gmail no está conectado en esta sesión.",
                "alerts": copy.deepcopy(list(binding.alerts)) if owned else [],
                "analyzed": binding.analyzed if owned else 0,
                "revision": binding.revision if owned else 0,
                "risk_counts": dict(binding.risk_counts) if owned else {},
                "running": bool(binding and binding.thread and binding.thread.is_alive()) if owned else False}

    def close(self, timeout_s: float = 5.0) -> None:
        with self._lock:
            self._closed = True
            binding = self._binding
            if binding:
                binding.stop.set()
                binding.alerts.clear()
        if binding and binding.thread:
            binding.thread.join(timeout_s)
            if not binding.thread.is_alive() and binding.state != "disconnected":
                self._cleanup(binding)

"""Sesiones en servidor, en memoria (F0-05).

- Identificador de 256 bits (``secrets.token_urlsafe(32)``); en memoria solo se
  guarda su hash SHA-256, nunca el valor.
- Caducidad por inactividad (30 min) y absoluta (8 h).
- Cada sesión tiene su propio token CSRF.
- Al reiniciar el asistente todas las sesiones se pierden (hay que volver a emparejar).
"""

from __future__ import annotations

import hashlib
import re
import secrets
import threading
from collections.abc import Callable
from dataclasses import dataclass, field

from antifraude.app.security.policy import (
    SESSION_ABSOLUTE_TIMEOUT_S,
    SESSION_IDLE_TIMEOUT_S,
    SESSION_MAX_ACTIVE,
)

Clock = Callable[[], float]
_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{43}$")


def _digest(raw_id: str) -> str:
    return hashlib.sha256(raw_id.encode("ascii")).hexdigest()


@dataclass
class Session:
    csrf_token: str
    created_at: float
    last_seen: float
    #: Historial de la sesión: solo nivel, título y hora; NUNCA el texto del mensaje. Se pierde al cerrar.
    history: list[dict[str, str]] = field(default_factory=list)


class SessionStore:
    def __init__(
        self,
        *,
        clock: Clock,
        idle_timeout_s: int = SESSION_IDLE_TIMEOUT_S,
        absolute_timeout_s: int = SESSION_ABSOLUTE_TIMEOUT_S,
        max_active: int = SESSION_MAX_ACTIVE,
    ) -> None:
        self._clock = clock
        self._idle = idle_timeout_s
        self._absolute = absolute_timeout_s
        self._max_active = max_active
        self._lock = threading.Lock()
        self._sessions: dict[str, Session] = {}

    def _is_expired(self, s: Session, now: float) -> bool:
        return now - s.last_seen >= self._idle or now - s.created_at >= self._absolute

    def _purge(self, now: float) -> None:
        for key in [k for k, s in self._sessions.items() if self._is_expired(s, now)]:
            del self._sessions[key]

    def create(self) -> tuple[str, Session]:
        """Crea una sesión y devuelve el identificador en claro (solo para la cookie)."""
        with self._lock:
            now = self._clock()
            self._purge(now)
            while len(self._sessions) >= self._max_active:  # expulsa la más antigua
                oldest = min(self._sessions, key=lambda k: self._sessions[k].created_at)
                del self._sessions[oldest]
            raw_id = secrets.token_urlsafe(32)
            session = Session(csrf_token=secrets.token_urlsafe(32), created_at=now, last_seen=now)
            self._sessions[_digest(raw_id)] = session
            return raw_id, session

    def get(self, raw_id: str | None, *, touch: bool = True) -> Session | None:
        """Devuelve la sesión válida o ``None`` (inexistente, malformada o caducada)."""
        if not raw_id or not _SESSION_ID_RE.fullmatch(raw_id):
            return None
        with self._lock:
            now = self._clock()
            key = _digest(raw_id)
            session = self._sessions.get(key)
            if session is None:
                return None
            if self._is_expired(session, now):
                del self._sessions[key]
                return None
            if touch:
                session.last_seen = now
            return session

    def revoke(self, raw_id: str | None) -> None:
        if not raw_id or not _SESSION_ID_RE.fullmatch(raw_id):
            return
        with self._lock:
            self._sessions.pop(_digest(raw_id), None)

    @property
    def active_count(self) -> int:
        with self._lock:
            self._purge(self._clock())
            return len(self._sessions)

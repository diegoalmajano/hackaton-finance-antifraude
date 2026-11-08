"""Emparejamiento manual con código aleatorio de un solo uso (D-39).

- El código se muestra en la consola del asistente (nunca en la web ni en URLs)
  y el usuario lo teclea en la interfaz.
- Un solo uso, caducidad de 5 minutos.
- Máximo 5 intentos incorrectos **en total** (no se reinician al pedir un código
  nuevo); tras cada fallo hay una espera creciente y al quinto el emparejamiento
  queda bloqueado hasta reiniciar el asistente.
- Número de códigos por ejecución limitado.
"""

from __future__ import annotations

import hmac
import secrets
import sys
import threading
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from antifraude.app.security.policy import (
    PAIRING_ALPHABET,
    PAIRING_CODE_LENGTH,
    PAIRING_CODE_TTL_S,
    PAIRING_MAX_CODES_PER_RUN,
    PAIRING_MAX_FAILURES,
    PAIRING_MIN_REISSUE_INTERVAL_S,
    pairing_wait_after_failure,
)

Clock = Callable[[], float]
CodeSink = Callable[[str, int], None]


def console_code_sink(code: str, ttl_s: int) -> None:
    """Muestra el código en la consola local. No usa ``logging`` (no queda en registros)."""
    pretty = f"{code[:4]}-{code[4:]}"
    sys.stdout.write(
        "\n============================================================\n"
        f"  Código de emparejamiento del asistente: {pretty}\n"
        f"  Escríbalo en la ventana del asistente. Caduca en {ttl_s // 60} minutos\n"
        "  y solo sirve una vez. No lo comparta con nadie.\n"
        "============================================================\n\n"
    )
    sys.stdout.flush()


def generate_code() -> str:
    return "".join(secrets.choice(PAIRING_ALPHABET) for _ in range(PAIRING_CODE_LENGTH))


def normalize_code(raw: str) -> str:
    return raw.replace("-", "").replace(" ", "").strip().upper()


class VerifyOutcome(StrEnum):
    SUCCESS = "success"
    INVALID = "invalid"
    NO_ACTIVE_CODE = "no_active_code"  # caducado, ya usado o nunca emitido
    WAIT = "wait"
    LOCKED = "locked"


class IssueOutcome(StrEnum):
    ISSUED = "issued"
    ACTIVE_EXISTS = "active_exists"
    TOO_SOON = "too_soon"
    LIMIT_REACHED = "limit_reached"
    LOCKED = "locked"


@dataclass(frozen=True)
class VerifyResult:
    outcome: VerifyOutcome
    remaining_attempts: int
    retry_after_s: int = 0


@dataclass
class _ActiveCode:
    value: str
    expires_at: float


class PairingManager:
    def __init__(
        self,
        *,
        clock: Clock,
        sink: CodeSink = console_code_sink,
        code_ttl_s: int = PAIRING_CODE_TTL_S,
        max_failures: int = PAIRING_MAX_FAILURES,
        max_codes: int = PAIRING_MAX_CODES_PER_RUN,
        min_reissue_interval_s: int = PAIRING_MIN_REISSUE_INTERVAL_S,
    ) -> None:
        self._clock = clock
        self._sink = sink
        self._ttl = code_ttl_s
        self._max_failures = max_failures
        self._max_codes = max_codes
        self._min_interval = min_reissue_interval_s
        self._lock = threading.Lock()
        self._active: _ActiveCode | None = None
        self._failures = 0
        self._next_attempt_at = 0.0
        self._codes_issued = 0
        self._last_issued_at: float | None = None

    # --- estado ---------------------------------------------------------------
    @property
    def locked(self) -> bool:
        return self._failures >= self._max_failures

    @property
    def remaining_attempts(self) -> int:
        return max(0, self._max_failures - self._failures)

    def _expire_if_needed(self, now: float) -> None:
        if self._active is not None and now >= self._active.expires_at:
            self._active = None

    # --- emisión --------------------------------------------------------------
    def issue_code(self) -> IssueOutcome:
        with self._lock:
            now = self._clock()
            self._expire_if_needed(now)
            if self.locked:
                return IssueOutcome.LOCKED
            if self._active is not None:
                return IssueOutcome.ACTIVE_EXISTS
            if self._codes_issued >= self._max_codes:
                return IssueOutcome.LIMIT_REACHED
            if self._last_issued_at is not None and now - self._last_issued_at < self._min_interval:
                return IssueOutcome.TOO_SOON
            code = generate_code()
            self._active = _ActiveCode(value=code, expires_at=now + self._ttl)
            self._codes_issued += 1
            self._last_issued_at = now
        self._sink(code, self._ttl)
        return IssueOutcome.ISSUED

    # --- verificación ---------------------------------------------------------
    def verify(self, submitted: str) -> VerifyResult:
        with self._lock:
            now = self._clock()
            self._expire_if_needed(now)
            if self.locked:
                return VerifyResult(VerifyOutcome.LOCKED, 0)
            if now < self._next_attempt_at:
                wait = max(1, int(self._next_attempt_at - now + 0.999))
                return VerifyResult(VerifyOutcome.WAIT, self.remaining_attempts, wait)
            if self._active is None:
                return VerifyResult(VerifyOutcome.NO_ACTIVE_CODE, self.remaining_attempts)

            candidate = normalize_code(submitted)
            if hmac.compare_digest(candidate.encode(), self._active.value.encode()):
                self._active = None  # un solo uso
                self._failures = 0
                self._next_attempt_at = 0.0
                return VerifyResult(VerifyOutcome.SUCCESS, self.remaining_attempts)

            self._failures += 1
            if self.locked:
                self._active = None
                return VerifyResult(VerifyOutcome.LOCKED, 0)
            wait = pairing_wait_after_failure(self._failures)
            self._next_attempt_at = now + wait
            return VerifyResult(VerifyOutcome.INVALID, self.remaining_attempts, wait)

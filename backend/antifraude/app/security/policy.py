"""Parámetros de seguridad aprobados (F0-05). No configurables por entorno."""

from __future__ import annotations

from typing import Final

# Emparejamiento (D-39 / aprobación F0-05)
PAIRING_CODE_LENGTH: Final[int] = 8
#: Alfabeto sin caracteres ambiguos (sin I, L, O, 0, 1): 31 símbolos → ~39,6 bits.
PAIRING_ALPHABET: Final[str] = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
PAIRING_CODE_TTL_S: Final[int] = 5 * 60
PAIRING_MAX_FAILURES: Final[int] = 5  # al quinto fallo: bloqueo hasta reiniciar el asistente
PAIRING_MAX_CODES_PER_RUN: Final[int] = 10  # no se pueden generar códigos ilimitados
PAIRING_MIN_REISSUE_INTERVAL_S: Final[int] = 30
PAIRING_MAX_INPUT_CHARS: Final[int] = 32

# Sesión
SESSION_COOKIE_NAME: Final[str] = "af_session"
SESSION_IDLE_TIMEOUT_S: Final[int] = 30 * 60
SESSION_ABSOLUTE_TIMEOUT_S: Final[int] = 8 * 60 * 60
SESSION_MAX_ACTIVE: Final[int] = 3

# CSRF
CSRF_HEADER_NAME: Final[str] = "x-csrf-token"

# Peticiones
SAFE_METHODS: Final[frozenset[str]] = frozenset({"GET", "HEAD", "OPTIONS"})
#: Tamaño máximo del cuerpo de una petición (mensaje original 5 MiB + margen de formulario).
MAX_REQUEST_BODY_BYTES: Final[int] = 6 * 1024 * 1024


def pairing_wait_after_failure(failures: int) -> int:
    """Espera de seguridad (s) tras ``failures`` fallos consecutivos: 1, 2, 4, 8…"""
    return 0 if failures <= 0 else 2 ** (failures - 1)

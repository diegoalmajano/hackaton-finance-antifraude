"""Registros con privacidad (F0-07).

Principio: el código del asistente **no registra** códigos de emparejamiento,
cookies, tokens, claves ni contenido de mensajes. Este módulo añade una
**segunda línea de defensa**: un filtro que oculta valores con forma de
secreto en cualquier registro que pase por los manejadores configurados, y
que descarta las trazas de excepción (pueden contener datos).

El código de emparejamiento se muestra en la consola con ``sys.stdout`` (no
con ``logging``) a propósito: el usuario necesita verlo (riesgo R-32).
"""

from __future__ import annotations

import logging
import re
from typing import Any, Final

REDACTED: Final[str] = "[OCULTO]"

#: (patrón, sustitución). Orden: de lo más específico a lo más general.
_PATTERNS: Final[list[tuple[re.Pattern[str], str]]] = [
    # Cookie de sesión (af_session=...)
    (re.compile(r"(af_session=)[^;\s\"',]+", re.IGNORECASE), r"\1" + REDACTED),
    # Cabeceras sensibles con su valor
    (re.compile(r"((?:x-csrf-token|cookie|set-cookie|authorization|x-api-key)[\"']?\s*[:=]\s*[\"']?)[^\r\n\"']+",
                re.IGNORECASE), r"\1" + REDACTED),
    # Claves de Anthropic
    (re.compile(r"sk-ant-[A-Za-z0-9_\-]+"), REDACTED),
    # Tokens de 43 caracteres URL-safe (sesión y CSRF: secrets.token_urlsafe(32))
    (re.compile(r"(?<![A-Za-z0-9_\-])[A-Za-z0-9_\-]{43}(?![A-Za-z0-9_\-])"), REDACTED),
    # Códigos de emparejamiento (alfabeto sin I, L, O, 0, 1), con o sin guion
    (re.compile(r"(?<![A-Za-z0-9])[A-HJKMNP-Z2-9]{4}-?[A-HJKMNP-Z2-9]{4}(?![A-Za-z0-9])"), REDACTED),
]


def redact(text: str) -> str:
    """Oculta valores con forma de secreto en ``text``."""
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class RedactingFilter(logging.Filter):
    """Filtro para manejadores: oculta secretos y elimina trazas de excepción."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:  # formato roto: no arriesgar
            message = str(record.msg)
        if record.exc_info:
            exc_type = record.exc_info[0]
            name = exc_type.__name__ if exc_type else "desconocida"
            message += f" [traza de excepción {name} omitida por privacidad]"
        record.msg = redact(message)
        record.args = None
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        record.__dict__.pop("color_message", None)  # formato alternativo de Uvicorn
        return True


def build_log_config(level: str) -> dict[str, Any]:
    """Configuración de ``logging`` para Uvicorn y la aplicación, con el filtro en todos los manejadores."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"redact": {"()": "antifraude.core.logging.RedactingFilter"}},
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(levelprefix)s %(message)s",
                "use_colors": False,
            }
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stderr",
                "filters": ["redact"],
            }
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": level, "propagate": False},
            "uvicorn.error": {"level": level},
            # Sin registro de accesos (rutas, IP, cabeceras): además access_log=False.
            "uvicorn.access": {"handlers": [], "level": "CRITICAL", "propagate": False},
            "antifraude": {"handlers": ["default"], "level": level, "propagate": False},
        },
        "root": {"handlers": ["default"], "level": "WARNING"},
    }

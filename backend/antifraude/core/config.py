"""Configuración centralizada a partir de variables de entorno (F0-03).

- La dirección de escucha es fija: solo ``127.0.0.1`` (ADR-0013). No se puede
  cambiar por configuración.
- No hay claves de API ni modelo de Claude por defecto (ADR-0007, D-24).
- No se carga ningún archivo ``.env`` automáticamente: no hay dependencia
  autorizada para ello. Las variables se toman del entorno del proceso.
"""

from __future__ import annotations

import ipaddress
import os
from collections.abc import Mapping
from functools import lru_cache
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

#: Única dirección de escucha permitida (loopback IPv4).
LOOPBACK_HOST: Final[str] = "127.0.0.1"

#: Puerto por defecto de la aplicación local (D-42). Configurable con APP_PORT.
DEFAULT_PORT: Final[int] = 8790

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]


def ensure_loopback_host(host: str) -> str:
    """Devuelve ``host`` solo si es exactamente la dirección loopback permitida.

    Rechaza ``0.0.0.0``, ``::``, direcciones de red y nombres de host
    (``localhost`` podría resolverse a otra dirección).
    """
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError("La dirección de escucha debe ser una IP literal") from exc
    if str(address) != LOOPBACK_HOST:
        raise ValueError(f"Solo se permite escuchar en {LOOPBACK_HOST}")
    return LOOPBACK_HOST


class Settings(BaseModel):
    """Ajustes de la aplicación. Inmutables una vez creados."""

    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    port: int = Field(default=DEFAULT_PORT, ge=1024, le=65535)
    log_level: LogLevel = "INFO"
    # Fase d. Opcional: sin clave, la IA queda «no configurada» (ADR-0015).
    anthropic_api_key: SecretStr | None = None
    # Fase d. Sin valor por defecto: la elección está pendiente (D-24, D-32).
    claude_model: str | None = None

    @property
    def host(self) -> str:
        """Dirección de escucha; siempre loopback."""
        return LOOPBACK_HOST

    @field_validator("anthropic_api_key", "claude_model", mode="before")
    @classmethod
    def _empty_as_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("claude_model")
    @classmethod
    def _strip_model(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Settings:
        """Construye los ajustes a partir de variables de entorno."""
        env = os.environ if environ is None else environ
        raw: dict[str, object] = {}
        if "APP_PORT" in env:
            raw["port"] = env["APP_PORT"]
        if "APP_LOG_LEVEL" in env:
            raw["log_level"] = env["APP_LOG_LEVEL"].strip().upper()
        if "ANTHROPIC_API_KEY" in env:
            raw["anthropic_api_key"] = env["ANTHROPIC_API_KEY"]
        if "CLAUDE_MODEL" in env:
            raw["claude_model"] = env["CLAUDE_MODEL"]
        return cls.model_validate(raw)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Ajustes del proceso (se leen una sola vez)."""
    return Settings.from_env()

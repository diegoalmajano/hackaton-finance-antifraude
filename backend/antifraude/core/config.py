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
from decimal import Decimal
from pathlib import Path
from functools import lru_cache
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from antifraude.ai.budget import (DEFAULT_MAX_INPUT_TOKENS, DEFAULT_MAX_OUTPUT_TOKENS, DEFAULT_MAX_REQUESTS,
                                  HARD_BUDGET_CAP_USD, AiPolicy)

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
    # Modo demostración: carga la entidad ficticia y los ejemplos sintéticos (siempre etiquetados).
    demo_mode: bool = False
    # Control de gasto de la IA (misión 3). TODO cerrado por defecto: IA desactivada y 0 USD autorizados.
    ai_enabled: bool = False
    ai_allow_opus: bool = False
    ai_budget_usd: Decimal = Field(default=Decimal("0"), ge=0, le=HARD_BUDGET_CAP_USD)
    ai_max_input_tokens: int = Field(default=DEFAULT_MAX_INPUT_TOKENS, ge=500, le=50_000)
    ai_max_output_tokens: int = Field(default=DEFAULT_MAX_OUTPUT_TOKENS, ge=256, le=16_000)
    ai_max_requests: int = Field(default=DEFAULT_MAX_REQUESTS, ge=0, le=1000)
    ai_thinking: Literal["adaptive", "off"] = "adaptive"
    ai_effort: Literal["low", "medium", "high"] = "low"
    ai_ledger_path: Path | None = None

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

    def ai_policy(self) -> AiPolicy:
        """Política de gasto de la IA derivada de la configuración (sin la clave)."""
        return AiPolicy(enabled=self.ai_enabled, model=self.claude_model, allow_expensive=self.ai_allow_opus,
                        budget_usd=self.ai_budget_usd, max_input_tokens=self.ai_max_input_tokens,
                        max_output_tokens=self.ai_max_output_tokens, max_requests=self.ai_max_requests,
                        thinking=self.ai_thinking, effort=self.ai_effort, ledger_path=self.ai_ledger_path)

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
        if "APP_DEMO_MODE" in env:
            raw["demo_mode"] = _flag(env["APP_DEMO_MODE"])
        for var, field in (("AI_ENABLED", "ai_enabled"), ("AI_ALLOW_OPUS", "ai_allow_opus")):
            if var in env:
                raw[field] = _flag(env[var])
        for var, field in (("AI_BUDGET_USD", "ai_budget_usd"), ("AI_MAX_INPUT_TOKENS", "ai_max_input_tokens"),
                           ("AI_MAX_OUTPUT_TOKENS", "ai_max_output_tokens"), ("AI_MAX_REQUESTS", "ai_max_requests"),
                           ("AI_LEDGER_PATH", "ai_ledger_path")):
            if env.get(var, "").strip():
                raw[field] = env[var].strip().replace(",", ".") if var == "AI_BUDGET_USD" else env[var].strip()
        for var, field in (("AI_THINKING", "ai_thinking"), ("AI_EFFORT", "ai_effort")):
            if env.get(var, "").strip():
                raw[field] = env[var].strip().lower()
        return cls.model_validate(raw)


def _flag(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "si", "sí", "yes")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Ajustes del proceso (se leen una sola vez)."""
    return Settings.from_env()

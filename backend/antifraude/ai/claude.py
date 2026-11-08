"""Cliente de Claude para el análisis contextual (fase d, ADR-0007, ADR-0015).

- Usa el **SDK oficial** ``anthropic`` si está instalado; si no lo está (su
  instalación está pendiente de autorización), la IA queda «no configurada»
  y el sistema funciona en modo degradado etiquetado. No hay HTTP propio.
- Solo se activa si el usuario define ``ANTHROPIC_API_KEY`` **y** elige un
  modelo en ``CLAUDE_MODEL`` (la elección está pendiente, D-24/D-32).
- El transporte es inyectable: las pruebas usan respuestas simuladas y
  **nunca** hacen llamadas de pago.
- Errores, rechazos (``stop_reason: refusal``), cortes por ``max_tokens``,
  JSON inválido o tiempos de espera → ``AiFindings(status=failed)``; el motor
  determinista nunca convierte un fallo en BAJO.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any

from pydantic import ValidationError

from antifraude.ai.prompt import PROMPT_VERSION, SYSTEM_PROMPT, build_user_content, output_schema
from antifraude.contracts.ai import AiFailureReason, AiFindings, AiOutput, AiUsage
from antifraude.contracts.checks import CheckStatus
from antifraude.contracts.messages import IncomingMessage

#: Modelos candidatos aprobados para la comparativa (D-24). Ninguno es el predeterminado.
ALLOWED_MODELS = frozenset({"claude-opus-5-5", "claude-sonnet-5-5"})
#: Esfuerzo inicial para clasificación (se ajustará con la comparativa medida).
DEFAULT_EFFORT = "low"
#: Auditoría: el razonamiento (siempre activo en Opus 5.5) consume tokens de salida; 16 000 es el valor
#: recomendado para peticiones sin streaming. Solo se factura lo que realmente se genera.
MAX_TOKENS = 16000
FALLBACK_BETA = "server-side-fallback-2026-07-01"
REQUEST_TIMEOUT_S = 60.0

Transport = Callable[[Mapping[str, Any]], Mapping[str, Any]]


class AiUnavailable(RuntimeError):
    """El SDK oficial no está instalado o no hay credenciales."""


class AiTimeout(RuntimeError):
    """La llamada superó el tiempo máximo."""


def sdk_transport(api_key: str, timeout_s: float = REQUEST_TIMEOUT_S) -> Transport:
    """Transporte con el SDK oficial (import diferido). Lanza ``AiUnavailable`` si no está instalado."""
    try:
        import anthropic  # type: ignore[import-not-found]
    except ImportError as exc:  # instalación pendiente de autorización
        raise AiUnavailable("La librería oficial «anthropic» no está instalada.") from exc

    client = anthropic.Anthropic(api_key=api_key, timeout=timeout_s, max_retries=1)

    def send(params: Mapping[str, Any]) -> Mapping[str, Any]:
        kwargs = dict(params)
        try:
            try:
                response = client.beta.messages.create(**kwargs)
            except TypeError:
                # Auditoría: si la versión del SDK no acepta «fallbacks» como argumento, se envía por extra_body.
                if "fallbacks" not in kwargs:
                    raise
                extra = {"fallbacks": kwargs.pop("fallbacks")}
                response = client.beta.messages.create(**kwargs, extra_body=extra)
        except anthropic.APITimeoutError as exc:
            raise AiTimeout("tiempo de espera agotado") from exc
        result: Mapping[str, Any] = response.to_dict()
        return result

    return send


def build_request(model: str, message: IncomingMessage, technical_findings: list[str], *,
                  effort: str = DEFAULT_EFFORT, use_fallbacks: bool = True) -> dict[str, Any]:
    user_content, _ = build_user_content(message, technical_findings)
    request: dict[str, Any] = {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "system": [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": user_content}],
        "output_config": {"effort": effort, "format": {"type": "json_schema", "schema": output_schema()}},
    }
    if use_fallbacks:
        request["betas"] = [FALLBACK_BETA]
        request["fallbacks"] = "default"
    return request


def _clip(value: Any, limit: int) -> Any:
    return value[:limit] if isinstance(value, str) else value


def _sanitize(data: Any) -> Any:
    """Acota longitudes y número de elementos antes de validar (sin inventar contenido)."""
    if not isinstance(data, dict):
        return data
    tactics = []
    for t in data.get("tactics") or []:
        if isinstance(t, dict) and isinstance(t.get("quote"), str) and t["quote"].strip():
            tactics.append({**t, "quote": _clip(t["quote"], 500), "explanation": _clip(t.get("explanation"), 500)})
    data["tactics"] = tactics[:20]
    for key in ("inconsistencies", "uncertainties"):
        items = data.get(key) or []
        data[key] = [_clip(i, 500) for i in items if isinstance(i, str) and i.strip()][:20]
    data["claimed_entity"] = _clip(data.get("claimed_entity"), 256) or None
    return data


def parse_response(response: Mapping[str, Any], requested_model: str) -> AiFindings:
    """Convierte la respuesta de la API en ``AiFindings`` validados (o en un fallo explícito)."""
    model_id = str(response.get("model") or requested_model)[:64]
    usage_raw = response.get("usage") or {}
    usage = None
    if isinstance(usage_raw, Mapping):
        try:
            usage = AiUsage(input_tokens=int(usage_raw.get("input_tokens") or 0),
                            output_tokens=int(usage_raw.get("output_tokens") or 0))
        except (TypeError, ValueError):
            usage = None

    def failed(reason: AiFailureReason) -> AiFindings:
        return AiFindings(status=CheckStatus.FAILED, failure_reason=reason, model_id=model_id,
                          prompt_version=PROMPT_VERSION, usage=usage)

    stop = response.get("stop_reason")
    if stop == "refusal":
        return failed(AiFailureReason.REFUSAL)
    if stop == "max_tokens":
        return failed(AiFailureReason.INVALID_OUTPUT)
    texts = [b.get("text", "") for b in (response.get("content") or [])
             if isinstance(b, Mapping) and b.get("type") == "text"]
    if not texts:
        return failed(AiFailureReason.INVALID_OUTPUT)
    try:
        data = _sanitize(json.loads("".join(texts)))
        output = AiOutput.model_validate(data)
    except (json.JSONDecodeError, ValidationError, TypeError):
        return failed(AiFailureReason.INVALID_OUTPUT)
    return AiFindings(status=CheckStatus.DONE, output=output, model_id=model_id,
                      prompt_version=PROMPT_VERSION, usage=usage)


class ClaudeAnalyzer:
    """``AiAnalyzer`` con Claude. Sin clave/modelo/SDK → ``not_configured``."""

    def __init__(self, *, model: str | None, api_key: str | None, transport: Transport | None = None,
                 effort: str = DEFAULT_EFFORT, use_fallbacks: bool = True) -> None:
        self.model = model if model in ALLOWED_MODELS else None
        self._api_key = api_key
        self._transport = transport
        self.effort = effort
        self.use_fallbacks = use_fallbacks

    @property
    def configured(self) -> bool:
        return bool(self.model and (self._transport or self._api_key))

    def _get_transport(self) -> Transport:
        if self._transport is None:
            if not self._api_key:
                raise AiUnavailable("Falta la clave de la API.")
            self._transport = sdk_transport(self._api_key)
        return self._transport

    def analyze(self, message: IncomingMessage, technical_findings: list[str]) -> AiFindings:
        if not self.configured or self.model is None:
            return AiFindings(status=CheckStatus.NOT_CONFIGURED)
        try:
            transport = self._get_transport()
        except AiUnavailable:
            return AiFindings(status=CheckStatus.NOT_CONFIGURED)
        request = build_request(self.model, message, technical_findings, effort=self.effort,
                                use_fallbacks=self.use_fallbacks)
        try:
            response = transport(request)
        except AiTimeout:
            return AiFindings(status=CheckStatus.FAILED, failure_reason=AiFailureReason.TIMEOUT,
                              model_id=self.model, prompt_version=PROMPT_VERSION)
        except Exception:  # cualquier error de red o de la API: nunca se propaga ni se registra el contenido
            return AiFindings(status=CheckStatus.FAILED, failure_reason=AiFailureReason.API_ERROR,
                              model_id=self.model, prompt_version=PROMPT_VERSION)
        return parse_response(response, self.model)

"""Cliente de Claude para el análisis contextual (fase d, ADR-0007, ADR-0015; control de gasto, misión 3).

- Usa el **SDK oficial** ``anthropic`` si está instalado; si no lo está (instalación pendiente de
  autorización), la IA queda «no configurada». No hay HTTP propio.
- **Desactivada por defecto.** Solo se usa si la política lo permite (``AiPolicy``: ``AI_ENABLED=1``,
  modelo explícito, Opus solo con permiso expreso, presupuesto autorizado > 0) y hay clave.
- **Cada solicitud pasa por ``CostGuard``**: estimación del peor caso, reserva en el libro de gasto,
  límite de tokens y de solicitudes, una solicitud a la vez y registro del coste real (sin contenido).
- **Sin gastos duplicados:** sin reintentos automáticos del SDK (``max_retries=0``), sin *fallback* a
  otros modelos y con memoria de resultados por mensaje (el mismo mensaje no se paga dos veces).
- Errores, rechazos, cortes por ``max_tokens``, ``stop_reason`` inesperados, JSON inválido o tiempos
  de espera → ``AiFindings(status=failed)``; el motor determinista nunca convierte un fallo en BAJO.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
import secrets
from collections import OrderedDict
from collections.abc import Callable, Mapping
from decimal import Decimal
from typing import Any

from pydantic import ValidationError

from antifraude.ai.budget import PRICES, AiPolicy, BudgetBlocked, CostGuard, LedgerError, cost_usd, \
    estimate_input_tokens
from antifraude.ai.prompt import PROMPT_VERSION, SYSTEM_PROMPT, build_user_content, output_schema
from antifraude.contracts.ai import AiFailureReason, AiFindings, AiOutput, AiUsage
from antifraude.contracts.checks import CheckStatus
from antifraude.contracts.messages import IncomingMessage

#: Modelos candidatos aprobados para la comparativa (D-24). Ninguno es el predeterminado.
ALLOWED_MODELS = frozenset(PRICES)
REQUEST_TIMEOUT_S = 60.0
_CACHE_SIZE = 256

log = logging.getLogger("antifraude.ai")

Transport = Callable[[Mapping[str, Any]], Mapping[str, Any]]


class AiUnavailable(RuntimeError):
    """El SDK oficial no está instalado o no hay credenciales."""


class AiTimeout(RuntimeError):
    """La llamada superó el tiempo máximo (pudo llegar a facturarse)."""


#: Parámetros recientes de la API que se envían en ``extra_body`` para no depender de la versión del SDK.
_EXTRA_BODY_KEYS = ("output_config", "thinking")


def sdk_transport(api_key: str, timeout_s: float = REQUEST_TIMEOUT_S) -> Transport:
    """Transporte con el SDK oficial (import diferido). Lanza ``AiUnavailable`` si no está instalado."""
    try:
        import anthropic  # type: ignore[import-not-found]
    except ImportError as exc:  # instalación pendiente de autorización
        raise AiUnavailable("La librería oficial «anthropic» no está instalada.") from exc

    # max_retries=0: un reintento automático podría pagar dos veces la misma solicitud.
    client = anthropic.Anthropic(api_key=api_key, timeout=timeout_s, max_retries=0)

    def send(params: Mapping[str, Any]) -> Mapping[str, Any]:
        kwargs = {k: v for k, v in params.items() if k not in _EXTRA_BODY_KEYS}
        extra = {k: params[k] for k in _EXTRA_BODY_KEYS if k in params}
        try:
            response = client.messages.create(**kwargs, extra_body=extra) if extra else \
                client.messages.create(**kwargs)
        except anthropic.APITimeoutError as exc:
            raise AiTimeout("tiempo de espera agotado") from exc
        result: Mapping[str, Any] = response.to_dict()
        return result

    return send


def build_request(model: str, message: IncomingMessage, technical_findings: list[str], *,
                  max_tokens: int, effort: str = "low", thinking: str = "adaptive") -> dict[str, Any]:
    """Petición a la API de mensajes. Sin herramientas, sin ``fallbacks`` y sin parámetros de muestreo."""
    user_content, _ = build_user_content(message, technical_findings)
    request: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "system": [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": user_content}],
        "output_config": {"effort": effort, "format": {"type": "json_schema", "schema": output_schema()}},
    }
    if thinking == "off":  # solo Sonnet 5.5 (lo garantiza AiPolicy): sin razonamiento extendido
        request["thinking"] = {"type": "between_tools"}
    return request


def _clip(value: Any, limit: int) -> Any:
    return value[:limit] if isinstance(value, str) else value


#: Contactos en el texto LIBRE de la IA (explicaciones): una inyección podría hacer que la IA «recomiende»
#: un teléfono, web o correo del estafador con el sello del asistente. Se eliminan antes de mostrarlo (M3).
_CONTACT = re.compile(
    r"(https?://\S+|www\.\S+|[\w.+-]+@[\w-]+(\.[\w-]+)+|\+?\d[\d\s.\-]{6,}\d|"
    r"\b[\w-]+(\.[\w-]+)*\.(com|es|net|org|info|io|app|xyz|top|online|site|test|example|eu)\b\S*)",
    re.IGNORECASE)


def _scrub(value: Any) -> Any:
    return _CONTACT.sub("[dato omitido]", value) if isinstance(value, str) else value


def _sanitize(data: Any) -> Any:
    """Acota longitudes y número de elementos y quita contactos del texto libre (sin inventar contenido).

    Las citas (``quote``) NO se tocan: deben coincidir literalmente con el mensaje.
    """
    if not isinstance(data, dict):
        return data
    tactics = []
    for t in data.get("tactics") or []:
        if isinstance(t, dict) and isinstance(t.get("quote"), str) and t["quote"].strip():
            tactics.append({**t, "quote": _clip(t["quote"], 500),
                            "explanation": _clip(_scrub(t.get("explanation")), 500)})
    data["tactics"] = tactics[:20]
    for key in ("inconsistencies", "uncertainties"):
        items = data.get(key) or []
        data[key] = [_clip(_scrub(i), 500) for i in items if isinstance(i, str) and i.strip()][:20]
    data["claimed_entity"] = _clip(data.get("claimed_entity"), 256) or None
    return data


def _int(raw: Mapping[str, Any], key: str) -> int:
    value = raw.get(key)
    return int(value) if isinstance(value, (int, float)) and value >= 0 else 0


def parse_usage(response: Mapping[str, Any], model: str) -> AiUsage | None:
    """``usage`` de la respuesta con su coste calculado según la tarifa publicada (``None`` si falta)."""
    raw = response.get("usage")
    if not isinstance(raw, Mapping) or "input_tokens" not in raw or "output_tokens" not in raw:
        return None
    try:
        tokens = {k: _int(raw, k) for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens",
                                            "cache_read_input_tokens")}
    except (TypeError, ValueError):
        return None
    cost = None
    if model in PRICES:
        cost = float(cost_usd(model, input_tokens=tokens["input_tokens"], output_tokens=tokens["output_tokens"],
                              cache_creation_tokens=tokens["cache_creation_input_tokens"],
                              cache_read_tokens=tokens["cache_read_input_tokens"]))
    return AiUsage(**tokens, cost_usd=cost)


def parse_response(response: Mapping[str, Any], requested_model: str) -> AiFindings:
    """Convierte la respuesta de la API en ``AiFindings`` validados (o en un fallo explícito)."""
    model_id = str(response.get("model") or requested_model)[:64]
    usage = parse_usage(response, model_id if model_id in PRICES else requested_model)

    def failed(reason: AiFailureReason) -> AiFindings:
        return AiFindings(status=CheckStatus.FAILED, failure_reason=reason, model_id=model_id,
                          prompt_version=PROMPT_VERSION, usage=usage)

    stop = response.get("stop_reason")
    if stop == "refusal":
        return failed(AiFailureReason.REFUSAL)
    if stop != "end_turn":  # max_tokens (respuesta incompleta), pause_turn u otros: no se usa la salida
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


_BLOCK_REASONS = {"budget": AiFailureReason.BUDGET_BLOCKED, "policy": AiFailureReason.BUDGET_BLOCKED,
                  "input_limit": AiFailureReason.LIMIT_EXCEEDED, "request_limit": AiFailureReason.LIMIT_EXCEEDED,
                  "busy": AiFailureReason.BUSY}


def _settle(model: str) -> Callable[[Any], tuple[Decimal | None, str, dict[str, int] | None]]:
    """Coste final de una solicitud. ``None`` = desconocido → se mantiene el cargo pesimista reservado."""

    def settle(outcome: Any) -> tuple[Decimal | None, str, dict[str, int] | None]:
        if isinstance(outcome, BaseException):
            status_code = getattr(outcome, "status_code", None)
            if isinstance(status_code, int) and 400 <= status_code < 500:
                return Decimal("0"), f"error_http_{status_code}", None  # la API rechaza sin generar
            return None, "error_posible_cargo", None  # tiempo agotado / red / 5xx: puede haberse facturado
        usage = parse_usage(outcome, model) if isinstance(outcome, Mapping) else None
        if usage is None or usage.cost_usd is None:
            return None, "sin_usage", None
        tokens = usage.model_dump(exclude={"cost_usd"})
        return Decimal(str(usage.cost_usd)), "ok", tokens

    return settle


class ClaudeAnalyzer:
    """``AiAnalyzer`` con Claude, siempre detrás de ``CostGuard``. Sin política/clave/SDK → ``not_configured``."""

    def __init__(self, *, policy: AiPolicy, api_key: str | None, transport: Transport | None = None,
                 guard: CostGuard | None = None) -> None:
        self.policy = policy
        self._api_key = api_key
        self._transport = transport
        self._guard = guard
        self._cache: OrderedDict[str, AiFindings] = OrderedDict()
        self._cache_key = secrets.token_bytes(32)  # HMAC por proceso: la memoria no sirve de diccionario

    @property
    def model(self) -> str | None:
        return self.policy.model if self.policy.model in ALLOWED_MODELS else None

    @property
    def blocked_reason(self) -> str | None:
        reason = self.policy.blocked_reason()
        if reason:
            return reason
        if not (self._transport or self._api_key):
            return "Falta la clave de la API (ANTHROPIC_API_KEY)."
        return None

    @property
    def configured(self) -> bool:
        return self.blocked_reason is None

    @property
    def guard(self) -> CostGuard:
        if self._guard is None:
            self._guard = CostGuard(self.policy)
        return self._guard

    def _get_transport(self) -> Transport:
        if self._transport is None:
            if not self._api_key:
                raise AiUnavailable("Falta la clave de la API.")
            self._transport = sdk_transport(self._api_key)
        return self._transport

    def _key(self, message: IncomingMessage, technical_findings: list[str]) -> str:
        p = self.policy
        material = json.dumps([p.model, p.effort, p.thinking, p.max_output_tokens, PROMPT_VERSION,
                               message.subject, message.text, message.sender.address,
                               sorted(technical_findings)], ensure_ascii=False, default=str)
        return hmac.new(self._cache_key, material.encode("utf-8"), hashlib.sha256).hexdigest()

    def analyze(self, message: IncomingMessage, technical_findings: list[str]) -> AiFindings:
        if not self.configured or self.model is None:
            return AiFindings(status=CheckStatus.NOT_CONFIGURED)
        key = self._key(message, technical_findings)
        if key in self._cache:  # mismo mensaje y mismos parámetros: no se paga dos veces
            self._cache.move_to_end(key)
            return self._cache[key]
        try:
            transport = self._get_transport()
        except AiUnavailable:
            return AiFindings(status=CheckStatus.NOT_CONFIGURED)
        model = self.model
        request = build_request(model, message, technical_findings, max_tokens=self.policy.max_output_tokens,
                                effort=self.policy.effort, thinking=self.policy.thinking)
        estimated = estimate_input_tokens(SYSTEM_PROMPT, request["messages"][0]["content"],
                                          json.dumps(output_schema()))

        def fail(reason: AiFailureReason) -> AiFindings:
            return AiFindings(status=CheckStatus.FAILED, failure_reason=reason, model_id=model,
                              prompt_version=PROMPT_VERSION)

        try:
            response = self.guard.run(estimated, lambda: transport(request), _settle(model))
        except BudgetBlocked as exc:
            log.warning("IA no usada: %s", exc)  # texto fijo, sin contenido del mensaje
            return fail(_BLOCK_REASONS.get(exc.code, AiFailureReason.BUDGET_BLOCKED))
        except LedgerError as exc:
            log.error("IA no usada: %s", exc)
            return fail(AiFailureReason.BUDGET_BLOCKED)
        except AiTimeout:
            return fail(AiFailureReason.TIMEOUT)
        except Exception:  # cualquier error de red o de la API: nunca se propaga ni se registra el contenido
            return fail(AiFailureReason.API_ERROR)
        findings = parse_response(response, model)
        if findings.usage is not None:
            log.info("IA: modelo=%s entrada=%d salida=%d cache_w=%d cache_r=%d coste_usd=%s",
                     findings.model_id, findings.usage.input_tokens, findings.usage.output_tokens,
                     findings.usage.cache_creation_input_tokens, findings.usage.cache_read_input_tokens,
                     findings.usage.cost_usd)
        if findings.status is CheckStatus.DONE or findings.failure_reason is AiFailureReason.REFUSAL:
            self._cache[key] = findings
            while len(self._cache) > _CACHE_SIZE:
                self._cache.popitem(last=False)
        return findings

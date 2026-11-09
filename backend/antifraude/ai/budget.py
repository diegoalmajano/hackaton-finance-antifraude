"""Control de gasto de la API de Claude (misión 3, tarea A). Sin red.

Objetivo: que activar la IA nunca pueda gastar más de lo autorizado por el usuario.

- **Política** (``AiPolicy``): IA desactivada por defecto; modelo explícito; Opus bloqueado salvo permiso
  expreso; presupuesto autorizado 0 USD por defecto (el previsto de 0,50 USD NO está autorizado);
  límites de tokens de entrada y salida y de solicitudes por sesión.
- **Estimación previa** del coste en el peor caso (entrada estimada por exceso + ``max_tokens`` completos).
- **Libro de gasto** (``SpendLedger``) persistente en disco y **fuera del repositorio**: antes de cada
  solicitud se apunta el peor caso como «en curso»; al terminar se sustituye por el coste real calculado
  con el ``usage`` de la respuesta. Si el proceso muere a mitad, el cargo pesimista se queda apuntado
  (falla de forma segura). Nunca guarda texto de mensajes, citas ni claves: solo modelo, tokens y coste.
- **Concurrencia**: una sola solicitud a la vez (cerrojo en el proceso + archivo de bloqueo entre procesos),
  para que dos análisis simultáneos no consuman a la vez el mismo margen.

Esto es un **límite preventivo local**. El límite efectivo de facturación lo fija Anthropic Console
(límites de gasto de la organización); ver ``docs/CONTROL_COSTES_IA.md``.
"""

from __future__ import annotations

import json
import math
import os
import tempfile
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import ROUND_CEILING, Decimal
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

#: Precios en USD por millón de tokens (página oficial de precios de Anthropic, consultada el 2026-11-08):
#: https://platform.claude.com/docs/en/about-claude/pricing — revisar antes de cada campaña de pruebas.
PRICES_SOURCE = "https://platform.claude.com/docs/en/about-claude/pricing (consultado el 2026-11-08)"
SONNET = "claude-sonnet-5-5"
OPUS = "claude-opus-5-5"


@dataclass(frozen=True)
class ModelPrice:
    input: Decimal
    cache_write_5m: Decimal
    cache_read: Decimal
    output: Decimal


PRICES: dict[str, ModelPrice] = {
    SONNET: ModelPrice(Decimal("2.00"), Decimal("2.50"), Decimal("0.10"), Decimal("10.00")),
    OPUS: ModelPrice(Decimal("4.00"), Decimal("5.00"), Decimal("0.20"), Decimal("20.00")),
}
#: Modelos que exigen un permiso adicional explícito (más caros).
EXPENSIVE_MODELS = frozenset({OPUS})
#: Presupuesto PREVISTO para las primeras pruebas. No está autorizado: el autorizado por defecto es 0.
PLANNED_INITIAL_BUDGET_USD = Decimal("0.50")
#: Tope duro contra errores de tecleo (p. ej. «50» en vez de «0.50»).
HARD_BUDGET_CAP_USD = Decimal("10")
DEFAULT_MAX_INPUT_TOKENS = 6000
DEFAULT_MAX_OUTPUT_TOKENS = 4000
DEFAULT_MAX_REQUESTS = 20
_MTOK = Decimal(1_000_000)
_MAX_ENTRIES = 500
_LOCK_STALE_S = 300.0


_REPO_ROOT = Path(__file__).resolve().parents[3]


def _inside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(_REPO_ROOT)
        return True
    except ValueError:
        return False


def default_ledger_path() -> Path:
    """``%LOCALAPPDATA%\\antifraude\\gasto_ia.json`` (o ``~/.antifraude``): siempre fuera del repositorio."""
    base = os.environ.get("LOCALAPPDATA")
    root = Path(base) / "antifraude" if base else Path.home() / ".antifraude"
    return root / "gasto_ia.json"


class AiPolicy(BaseModel):
    """Qué se permite gastar. Inmutable; se construye desde la configuración (``Settings.ai_policy``)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = False
    model: str | None = None
    allow_expensive: bool = False
    budget_usd: Decimal = Field(default=Decimal("0"), ge=0, le=HARD_BUDGET_CAP_USD)
    max_input_tokens: int = Field(default=DEFAULT_MAX_INPUT_TOKENS, ge=500, le=50_000)
    max_output_tokens: int = Field(default=DEFAULT_MAX_OUTPUT_TOKENS, ge=256, le=16_000)
    max_requests: int = Field(default=DEFAULT_MAX_REQUESTS, ge=0, le=1000)
    thinking: Literal["adaptive", "off"] = "adaptive"
    effort: Literal["low", "medium", "high"] = "low"
    ledger_path: Path | None = None

    def blocked_reason(self) -> str | None:
        """Motivo (en español, sin datos sensibles) por el que la IA no puede usarse; ``None`` si puede."""
        if not self.enabled:
            return "La IA está desactivada (AI_ENABLED no está activado)."
        if not self.model:
            return "No se ha elegido modelo (CLAUDE_MODEL)."
        if self.model not in PRICES:
            return "El modelo indicado no está permitido."
        if self.model in EXPENSIVE_MODELS and not self.allow_expensive:
            return "Opus está bloqueado: requiere autorización expresa (AI_ALLOW_OPUS=1)."
        if self.thinking == "off" and self.model != SONNET:
            return "AI_THINKING=off solo es válido con Sonnet 5.5."
        if self.budget_usd <= 0:
            return "El presupuesto autorizado es 0 USD (AI_BUDGET_USD)."
        if self.max_requests <= 0:
            return "El límite de solicitudes es 0 (AI_MAX_REQUESTS)."
        if _inside_repo(self.resolved_ledger_path):
            return "El registro de gasto debe estar fuera del repositorio (AI_LEDGER_PATH)."
        return None

    @property
    def resolved_ledger_path(self) -> Path:
        return self.ledger_path or default_ledger_path()


# --- Estimación y coste ---------------------------------------------------------------------------
#: Cota superior prudente de tokens por carácter (español y JSON). Es una estimación local por EXCESO,
#: sin llamar a la API de conteo; el coste real se calcula después con el ``usage`` de la respuesta.
_CHARS_PER_TOKEN_LOW = 2.5
_REQUEST_OVERHEAD_TOKENS = 400


def estimate_input_tokens(*texts: str) -> int:
    """Cota superior prudente: el mayor de «caracteres / 2,5» y «bytes UTF-8 / 2» (cubre emojis y otros
    alfabetos, que ocupan más tokens por carácter). Sigue siendo una estimación: ver CONTROL_COSTES_IA.md."""
    chars = sum(len(t) for t in texts)
    utf8 = sum(len(t.encode("utf-8")) for t in texts)
    return int(max(math.ceil(chars / _CHARS_PER_TOKEN_LOW), math.ceil(utf8 / 2))) + _REQUEST_OVERHEAD_TOKENS


def _usd(tokens: int, price_per_mtok: Decimal) -> Decimal:
    return Decimal(max(0, int(tokens))) * price_per_mtok / _MTOK


def cost_usd(model: str, *, input_tokens: int, output_tokens: int, cache_creation_tokens: int = 0,
             cache_read_tokens: int = 0) -> Decimal:
    """Coste según la tarifa publicada. ``input_tokens`` excluye los tokens de caché (como en ``usage``)."""
    p = PRICES[model]
    total = (_usd(input_tokens, p.input) + _usd(cache_creation_tokens, p.cache_write_5m)
             + _usd(cache_read_tokens, p.cache_read) + _usd(output_tokens, p.output))
    return total.quantize(Decimal("0.000001"), rounding=ROUND_CEILING)


def worst_case_cost(model: str, estimated_input_tokens: int, max_output_tokens: int) -> Decimal:
    """Peor caso: toda la entrada facturada como escritura en caché (lo más caro) y la salida completa."""
    p = PRICES[model]
    total = _usd(estimated_input_tokens, max(p.input, p.cache_write_5m)) + _usd(max_output_tokens, p.output)
    return total.quantize(Decimal("0.000001"), rounding=ROUND_CEILING)


# --- Libro de gasto persistente -------------------------------------------------------------------
class LedgerError(RuntimeError):
    """El libro de gasto no se puede leer o escribir: por seguridad, no se gasta."""


class BudgetBlocked(RuntimeError):
    """La solicitud no se envía (presupuesto, límites o concurrencia). El mensaje es apto para registros."""

    def __init__(self, reason: str, code: str) -> None:
        super().__init__(reason)
        self.code = code


@dataclass
class Reservation:
    entry_id: str
    model: str
    amount: Decimal
    estimated_input_tokens: int


class SpendLedger:
    """Libro de gasto en JSON. Nunca guarda contenido de mensajes."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()

    # Lectura/escritura atómica -------------------------------------------------------------------
    @property
    def backup_path(self) -> Path:
        return self.path.with_name(self.path.name + ".bak")

    @staticmethod
    def _read(path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1:
                raise ValueError("versión no válida")
            spent = Decimal(str(data["spent_usd"]))
            entries = data.get("entries")
            if not spent.is_finite() or spent < 0 or not isinstance(entries, list) or len(entries) > _MAX_ENTRIES:
                raise ValueError("valor no válido")
            ids: set[str] = set()
            retained_cost = Decimal("0")
            for entry in entries:
                if not isinstance(entry, dict):
                    raise ValueError("entrada no válida")
                entry_id = entry.get("id")
                if not isinstance(entry_id, str) or not entry_id or entry_id in ids:
                    raise ValueError("identificador no válido")
                ids.add(entry_id)
                cost = Decimal(str(entry["cost_usd"]))
                reserved = Decimal(str(entry["reserved_usd"]))
                if not cost.is_finite() or cost < 0 or not reserved.is_finite() or reserved < 0:
                    raise ValueError("coste no válido")
                retained_cost += cost
            # Las entradas antiguas pueden haberse podado; nunca se borra su acumulado.
            if spent < retained_cost:
                raise ValueError("acumulado incoherente")
            return data
        except Exception as exc:  # archivo dañado o manipulado → no se gasta (fallo seguro), no se sobrescribe
            raise LedgerError("El registro de gasto de la IA está dañado; revíselo antes de continuar.") from exc

    def _load(self) -> dict[str, Any]:
        """Lee el libro y su copia; si falta uno, vale el otro; si están los dos, el de MAYOR gasto.

        Borrar solo el libro no reinicia el presupuesto (revisión del control de gasto, ALTO 1). Borrar ambos sí:
        es un límite local; el límite efectivo de facturación está en Anthropic Console (R-66).
        """
        main, backup = self._read(self.path), self._read(self.backup_path)
        candidates = [d for d in (main, backup) if d is not None]
        if not candidates:
            return {"version": 1, "spent_usd": "0", "entries": []}
        return max(candidates, key=lambda d: Decimal(str(d["spent_usd"])))

    def _save(self, data: dict[str, Any]) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            data["entries"] = data["entries"][-_MAX_ENTRIES:]
            for target in (self.path, self.backup_path):
                fd, tmp = tempfile.mkstemp(prefix=".gasto_", dir=self.path.parent)
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump(data, fh, ensure_ascii=False, indent=1)
                os.replace(tmp, target)
        except OSError as exc:
            raise LedgerError("No se puede escribir el registro de gasto de la IA.") from exc

    def spent(self) -> Decimal:
        with self._lock:
            return Decimal(str(self._load()["spent_usd"]))

    def summary(self) -> dict[str, Any]:
        with self._lock:
            data = self._load()
        entries = data["entries"]
        return {"spent_usd": data["spent_usd"], "requests": len(entries),
                "in_flight": sum(1 for e in entries if e.get("status") == "in_flight")}

    def reserve(self, model: str, amount: Decimal, budget: Decimal, estimated_input_tokens: int) -> Reservation:
        """Apunta el peor caso como «en curso» si cabe en el presupuesto; si no, ``BudgetBlocked``."""
        with self._lock:
            data = self._load()
            spent = Decimal(str(data["spent_usd"]))
            if spent + amount > budget:
                raise BudgetBlocked("Presupuesto de IA agotado o insuficiente para el peor caso de esta solicitud.",
                                    "budget")
            entry_id = f"{time.time_ns():x}"
            data["entries"].append({"id": entry_id, "at": _now(), "model": model, "status": "in_flight",
                                    "reserved_usd": str(amount), "cost_usd": str(amount),
                                    "estimated_input_tokens": estimated_input_tokens})
            data["spent_usd"] = str(spent + amount)
            self._save(data)
        return Reservation(entry_id, model, amount, estimated_input_tokens)

    def settle(self, reservation: Reservation, *, cost: Decimal, status: str,
               usage: dict[str, int] | None = None) -> Decimal:
        """Sustituye la reserva por el coste final (real o, si no se conoce, el pesimista)."""
        with self._lock:
            data = self._load()
            entry = next((e for e in data["entries"] if e.get("id") == reservation.entry_id), None)
            if entry is None:  # el libro desapareció o se sustituyó a mitad: se apunta el coste, sin descontar
                spent = Decimal(str(data["spent_usd"])) + cost
                entry = {"id": reservation.entry_id, "at": _now(), "model": reservation.model,
                         "reserved_usd": str(reservation.amount), "recovered": True}
                data["entries"].append(entry)
            else:
                spent = Decimal(str(data["spent_usd"])) - reservation.amount + cost
            entry.update({"status": status, "cost_usd": str(cost), "settled_at": _now()})
            if usage:
                entry["usage"] = {k: int(v) for k, v in usage.items()}
            data["spent_usd"] = str(max(spent, Decimal("0")))
            self._save(data)
            return Decimal(data["spent_usd"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class _InterProcessLock:
    """Archivo de bloqueo exclusivo junto al libro: una sola solicitud en curso entre procesos."""

    def __init__(self, path: Path) -> None:
        self.path = path.with_suffix(".lock")
        self._fd: int | None = None

    def _create(self) -> bool:
        try:
            self._fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            return True
        except (FileExistsError, PermissionError):  # Windows: «pendiente de borrado» → ocupado
            return False

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self._create():
            return True
        try:  # bloqueo abandonado por un proceso muerto: se aparta con un renombrado atómico (solo uno gana)
            if time.time() - self.path.stat().st_mtime > _LOCK_STALE_S:
                os.replace(self.path, self.path.with_name(f"{self.path.name}.caducado.{os.getpid()}.{time.time_ns()}"))
                for old in self.path.parent.glob(self.path.name + ".caducado.*"):
                    old.unlink(missing_ok=True)
                return self._create()
        except OSError:
            pass
        return False

    def release(self) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
            self.path.unlink(missing_ok=True)


class CostGuard:
    """Puerta única antes de cada solicitud de pago. Una instancia = una sesión de pruebas."""

    def __init__(self, policy: AiPolicy, ledger: SpendLedger | None = None, *, wait_s: float = 30.0) -> None:
        self.policy = policy
        self.ledger = ledger or SpendLedger(policy.resolved_ledger_path)
        self.requests_sent = 0
        self._thread_lock = threading.Lock()
        self.wait_s = wait_s

    def check_policy(self) -> None:
        reason = self.policy.blocked_reason()
        if reason:
            raise BudgetBlocked(reason, "policy")

    def run(self, estimated_input_tokens: int, send: Any, settle_cost: Any) -> Any:
        """Ejecuta ``send()`` bajo todos los controles.

        ``settle_cost(result_or_exc) -> (Decimal | None, status, usage)`` calcula el coste final;
        ``None`` = desconocido → se mantiene el cargo pesimista.
        """
        self.check_policy()
        model = self.policy.model
        assert model is not None
        if estimated_input_tokens > self.policy.max_input_tokens:
            raise BudgetBlocked("El mensaje es demasiado largo para el límite de tokens de entrada.", "input_limit")
        if not self._thread_lock.acquire(timeout=self.wait_s):
            raise BudgetBlocked("Ya hay un análisis con IA en curso.", "busy")
        ip_lock = _InterProcessLock(self.ledger.path)
        try:
            if not ip_lock.acquire():
                raise BudgetBlocked("Ya hay un análisis con IA en curso en otro proceso.", "busy")
            if self.requests_sent >= self.policy.max_requests:
                raise BudgetBlocked("Se alcanzó el límite de solicitudes de esta sesión de pruebas.", "request_limit")
            amount = worst_case_cost(model, estimated_input_tokens, self.policy.max_output_tokens)
            reservation = self.ledger.reserve(model, amount, self.policy.budget_usd, estimated_input_tokens)
            self.requests_sent += 1
            try:
                result = send()
            except BaseException as exc:
                cost, status, usage = settle_cost(exc)
                self.ledger.settle(reservation, cost=reservation.amount if cost is None else cost,
                                   status=status, usage=usage)
                raise
            cost, status, usage = settle_cost(result)
            try:
                self.ledger.settle(reservation, cost=reservation.amount if cost is None else cost, status=status,
                                   usage=usage)
            except LedgerError:
                pass  # ya pagado: se usa la respuesta; el cargo pesimista reservado sigue en el libro
            return result
        finally:
            ip_lock.release()
            self._thread_lock.release()

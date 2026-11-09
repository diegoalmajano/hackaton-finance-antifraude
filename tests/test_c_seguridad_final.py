"""Seguridad del gasto: consumo y libro malformados, sin red ni IA real."""
from __future__ import annotations

import json
import socket
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from antifraude.ai.budget import SONNET, SpendLedger
from antifraude.ai.claude import parse_usage
from antifraude.contracts.ai import AiFailureReason
from antifraude.contracts.checks import CheckStatus
from test_c_costes import Transporte, gastado, ia, msg, resp


@pytest.fixture(autouse=True)
def sin_red(monkeypatch: pytest.MonkeyPatch) -> None:
    def denied(*args: Any, **kwargs: Any) -> None:
        pytest.fail("Esta regresión simulada no puede usar red ni DNS")
    monkeypatch.setattr(socket, "getaddrinfo", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)


@pytest.mark.parametrize("field", ["input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"])
@pytest.mark.parametrize("invalid", [None, "1000", -1, True, 1.5, float("inf"), float("nan")])
def test_usage_invalido_no_se_inventa_como_cero(field: str, invalid: Any) -> None:
    usage = {"input_tokens": 1000, "output_tokens": 500, field: invalid}
    assert parse_usage({"usage": usage}, SONNET) is None


@pytest.mark.parametrize("usage", [
    {"input_tokens": None, "output_tokens": 500},
    {"input_tokens": "1000", "output_tokens": 500},
    {"input_tokens": 1000, "output_tokens": -1},
    {"input_tokens": 1000, "output_tokens": 500, "cache_creation_input_tokens": True},
])
def test_consumo_no_fiable_conserva_la_reserva_tras_envio_simulado(tmp_path: Path, usage: Any) -> None:
    transport = Transporte(resp(usage=usage))
    outcome = ia(tmp_path, transport).analyze(msg(), [])
    assert transport.llamadas == 1
    assert outcome.status is CheckStatus.DONE and outcome.usage is None
    entry = json.loads((tmp_path / "gasto.json").read_text(encoding="utf-8"))["entries"][0]
    assert entry["status"] == "sin_usage"
    assert gastado(tmp_path) == Decimal(entry["reserved_usd"])
    assert "usage" not in entry


@pytest.mark.parametrize("usage,expected", [
    ({"input_tokens": 1000, "output_tokens": 500}, Decimal("0.007")),
    ({"input_tokens": 0, "output_tokens": 0}, Decimal("0")),
])
def test_consumo_valido_incluido_cero_y_cache_omitida_se_liquida(tmp_path: Path, usage: Any, expected: Decimal) -> None:
    outcome = ia(tmp_path, Transporte(resp(usage=usage))).analyze(msg(), [])
    assert outcome.status is CheckStatus.DONE and outcome.usage is not None
    assert gastado(tmp_path) == expected


def _seed(tmp_path: Path) -> dict[str, Any]:
    ledger = SpendLedger(tmp_path / "gasto.json")
    reservation = ledger.reserve(SONNET, Decimal("0.06"), Decimal("0.50"), 1000)
    ledger.settle(reservation, cost=Decimal("0.055"), status="ok")
    return json.loads(ledger.path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("damage", ["version", "entry_type", "missing_cost", "negative_cost", "non_finite_cost", "duplicate_id", "lower_total"])
def test_libro_estructuralmente_danado_bloquea_sin_sobrescribir(tmp_path: Path, damage: str) -> None:
    data = _seed(tmp_path)
    if damage == "version":
        data["version"] = 999
    elif damage == "entry_type":
        data["entries"] = ["entrada no válida"]
    elif damage == "missing_cost":
        del data["entries"][0]["cost_usd"]
    elif damage == "negative_cost":
        data["entries"][0]["cost_usd"] = "-1"
    elif damage == "non_finite_cost":
        data["entries"][0]["cost_usd"] = "NaN"
    elif damage == "duplicate_id":
        data["entries"].append(dict(data["entries"][0]))
    else:
        data["spent_usd"] = "0"
    raw = json.dumps(data)
    for name in ("gasto.json", "gasto.json.bak"):
        (tmp_path / name).write_text(raw, encoding="utf-8")
    transport = Transporte()
    # Un total manipulado a cero permitiría otra solicitud que no cabe en 0,06 USD.
    outcome = ia(tmp_path, transport, budget_usd="0.06" if damage == "lower_total" else "0.50").analyze(msg(), [])
    assert outcome.failure_reason is AiFailureReason.BUDGET_BLOCKED
    assert transport.llamadas == 0
    assert all((tmp_path / name).read_text(encoding="utf-8") == raw for name in ("gasto.json", "gasto.json.bak"))


def test_copia_coherente_no_reinicia_el_acumulado_al_reabrir(tmp_path: Path) -> None:
    _seed(tmp_path)
    (tmp_path / "gasto.json").unlink()
    transport = Transporte()
    outcome = ia(tmp_path, transport, budget_usd="0.06").analyze(msg(), [])
    assert outcome.failure_reason is AiFailureReason.BUDGET_BLOCKED and transport.llamadas == 0
    assert SpendLedger(tmp_path / "gasto.json").spent() == Decimal("0.055")


def test_contador_desmesurado_no_rompe_liquidacion_y_sigue_desconocido() -> None:
    assert parse_usage({"usage": {"input_tokens": 10**1000, "output_tokens": 1}}, SONNET) is None


def test_libro_valido_con_historial_podado_conserva_acumulado(tmp_path: Path) -> None:
    # Libro v1 tras podar 100 entradas antiguas: su coste sigue incluido en spent_usd.
    entries = [{"id": str(i), "model": SONNET, "status": "ok", "reserved_usd": "0.001", "cost_usd": "0.000001"}
               for i in range(500)]
    path = tmp_path / "gasto.json"
    path.write_text(json.dumps({"version": 1, "spent_usd": "0.000600", "entries": entries}), encoding="utf-8")
    ledger = SpendLedger(path)
    assert ledger.spent() == Decimal("0.000600")
    reservation = ledger.reserve(SONNET, Decimal("0.001"), Decimal("0.50"), 100)
    ledger.settle(reservation, cost=Decimal("0.000001"), status="ok")
    assert SpendLedger(path).spent() == Decimal("0.000601")
    assert len(json.loads(path.read_text(encoding="utf-8"))["entries"]) == 500


@pytest.mark.parametrize("context", ["display_name", "reply_to", "channel", "user_id"])
def test_cache_no_mezcla_usuario_ni_contexto_del_prompt(tmp_path: Path, context: str) -> None:
    from uuid import uuid4
    from antifraude.analysis.ingest import build_message, make_sender
    from antifraude.contracts import Channel
    data = {"user_id": uuid4(), "channel": Channel.MANUAL,
            "body_text": "Introduzca su contraseña de acceso.",
            "sender": make_sender("Revista", "avisos@boletin.example")}
    first = build_message(**data).message
    if context == "display_name":
        data["sender"] = make_sender("Banco Ficticio", "avisos@boletin.example")
    elif context == "reply_to":
        data["reply_to"] = make_sender("Respuestas", "ayuda@respuesta.example")
    elif context == "channel":
        data["channel"] = Channel.GMAIL
    else:
        data["user_id"] = uuid4()
    second = build_message(**data).message
    transport = Transporte()
    analyzer = ia(tmp_path, transport)
    assert analyzer.analyze(first, ["test.context"]).status is CheckStatus.DONE
    assert analyzer.analyze(second, ["test.context"]).status is CheckStatus.DONE
    assert transport.llamadas == 2
    # La repetición del mismo contexto sigue deduplicada y las claves son opacas.
    assert analyzer.analyze(second, ["test.context"]).status is CheckStatus.DONE
    assert transport.llamadas == 2
    assert all(len(key) == 64 and set(key) <= set("0123456789abcdef") for key in analyzer._cache)

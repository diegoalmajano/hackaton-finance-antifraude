"""Interfaz del análisis con IA y verificación de citas (fase d, ADR-0007/0015).

El pipeline depende solo de ``AiAnalyzer``. Implementaciones:
- ``DisabledAi``: IA no configurada (sin clave o sin modelo) → ``not_configured``.
- ``ClaudeAnalyzer`` (``ai/claude.py``): cliente real, solo con clave, modelo y
  presupuesto autorizados.
- Dobles de prueba en los tests (siempre etiquetados como tales).
"""

from __future__ import annotations

from typing import Protocol

from antifraude.contracts.ai import AiFindings, AiOutput
from antifraude.contracts.checks import CheckStatus
from antifraude.contracts.messages import IncomingMessage


class AiAnalyzer(Protocol):
    def analyze(self, message: IncomingMessage, technical_findings: list[str]) -> AiFindings: ...


class DisabledAi:
    """IA no configurada: el sistema funciona en modo degradado etiquetado."""

    def analyze(self, message: IncomingMessage, technical_findings: list[str]) -> AiFindings:
        return AiFindings(status=CheckStatus.NOT_CONFIGURED)


#: Una cita de 1–2 caracteres («a») estaría siempre en el texto: se exige un fragmento con contenido.
MIN_QUOTE_CHARS = 8


def _meaningful(quote: str) -> bool:
    letters = sum(ch.isalpha() for ch in quote)
    return len(quote.strip()) >= MIN_QUOTE_CHARS and letters >= 5


def verified_quotes(output: AiOutput | None, message: IncomingMessage) -> set[str]:
    """Citas de la IA que aparecen **literalmente** en el asunto o el texto (minimizados) del mensaje
    y tienen contenido suficiente (revisión de seguridad M3)."""
    if output is None:
        return set()
    visible = (message.subject or "") + "\n" + message.text
    return {t.quote for t in output.tactics if t.quote and _meaningful(t.quote) and t.quote in visible}

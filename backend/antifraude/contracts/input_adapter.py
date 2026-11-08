"""Interfaz común de entrada (ADR-0010).

Cada conector (manual/.eml en la fase a, Gmail en la fase f, simulado
etiquetado y, en la fase 2, voz) implementa ``InputAdapter`` y entrega
``RawMessage``. Los conectores **no analizan**: la ingesta normaliza y el
pipeline evalúa. Sin implementaciones en F0-04.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import ClassVar

from antifraude.contracts.messages import Channel, RawMessage


class InputAdapter(ABC):
    """Fuente de mensajes autorizada por el usuario."""

    #: Canal que produce el adaptador.
    channel: ClassVar[Channel]
    #: True solo para el conector simulado (siempre etiquetado).
    is_simulated: ClassVar[bool] = False

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if getattr(cls, "__abstractmethods__", None):
            return  # subclase abstracta intermedia
        channel = getattr(cls, "channel", None)
        if not isinstance(channel, Channel):
            raise TypeError(f"{cls.__name__} debe declarar 'channel' como Channel")
        if cls.is_simulated != (channel is Channel.SIMULATED):
            raise TypeError(f"{cls.__name__}: is_simulated debe ser True solo para el canal 'simulated'")

    @abstractmethod
    def fetch_new(self) -> Sequence[RawMessage]:
        """Devuelve los mensajes nuevos desde la última llamada (puede ser vacío).

        Los errores de red/autorización deben señalarse como estado del conector,
        nunca como «sin mensajes» silencioso.
        """

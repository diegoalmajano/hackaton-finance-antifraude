"""Comprobaciones de red locales para el arranque (D-42).

Si el puerto está ocupado se informa con un mensaje claro en español.
Nunca se cierran procesos ajenos ni se cambia de puerto en silencio.
"""

from __future__ import annotations

import socket


class PortUnavailableError(RuntimeError):
    """El puerto solicitado no está disponible en la dirección loopback."""


def ensure_port_available(host: str, port: int) -> None:
    """Comprueba que ``host:port`` se puede usar; si no, lanza ``PortUnavailableError``.

    Hay una pequeña ventana entre esta comprobación y el arranque real; si otro
    proceso ocupa el puerto en ese intervalo, Uvicorn fallará igualmente.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):  # Windows: no compartir el puerto
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            sock.bind((host, port))
        except OSError as exc:
            raise PortUnavailableError(
                f"No se puede iniciar el asistente: el puerto {port} de {host} ya está en uso "
                "por otro programa. Cierre ese programa usted mismo o elija otro puerto con la "
                f"variable de entorno APP_PORT (por ejemplo, APP_PORT={port + 1})."
            ) from exc

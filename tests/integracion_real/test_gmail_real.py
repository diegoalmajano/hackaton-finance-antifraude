"""Prueba de INTEGRACIÓN REAL con Gmail (cuenta de PRUEBAS). Se salta salvo activación expresa.

Requisitos (ver docs/GMAIL_CONFIGURACION.md y docs/PRUEBAS_INTEGRACION_REAL.md):
- ``ANTIFRAUDE_PRUEBAS_REALES_GMAIL=1`` y ``GMAIL_CLIENT_SECRET`` = ruta al client_secret*.json FUERA del repositorio;
- librerías de Google y ``keyring`` instaladas (pendiente de autorización); cuenta de pruebas autorizada (B-04).
Solo lectura (``gmail.readonly``). Abre el navegador para el consentimiento OAuth la primera vez.
No imprime ni guarda contenido de mensajes.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from antifraude.connectors.gmail import ConnectorStatus, GmailConnector
from antifraude.connectors.gmail_api import SCOPES, GmailApiClient, build_gmail_service

pytestmark = pytest.mark.skipif(
    os.environ.get("ANTIFRAUDE_PRUEBAS_REALES_GMAIL") != "1"
    or importlib.util.find_spec("googleapiclient") is None or importlib.util.find_spec("keyring") is None,
    reason="Integración real con Gmail desactivada (requiere activación, librerías y cuenta de pruebas).")


def test_conexion_solo_lectura_y_primera_consulta_sin_buzon_antiguo() -> None:
    assert SCOPES == ["https://www.googleapis.com/auth/gmail.readonly"]
    secreto = Path(os.environ["GMAIL_CLIENT_SECRET"])
    raiz = Path(__file__).resolve().parents[2]
    assert raiz not in secreto.resolve().parents, "El client_secret debe estar FUERA del repositorio"
    conector = GmailConnector(GmailApiClient(build_gmail_service(secreto)))
    assert conector.fetch_new() == []  # primera consulta: solo guarda el historyId (no lee el buzón antiguo)
    assert conector.status is ConnectorStatus.OK and conector.state.history_id

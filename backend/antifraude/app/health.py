"""Comprobación de estado del servidor, sin información sensible."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Response
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok"]


@router.get("/health", response_model=HealthResponse)
def health(response: Response) -> HealthResponse:
    """Indica solo que el proceso responde: sin versión, rutas ni configuración."""
    response.headers["Cache-Control"] = "no-store"
    return HealthResponse(status="ok")

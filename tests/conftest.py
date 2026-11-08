"""Utilidades comunes de pruebas."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from fastapi.testclient import TestClient

from antifraude.app.main import create_app
from antifraude.core.config import Settings

PORT = 8790
BASE_URL = f"http://127.0.0.1:{PORT}"
ORIGIN = BASE_URL


class FakeClock:
    def __init__(self, start: float = 1_000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@dataclass
class CodeCapture:
    codes: list[str] = field(default_factory=list)

    def __call__(self, code: str, ttl_s: int) -> None:
        self.codes.append(code)

    @property
    def last(self) -> str:
        return self.codes[-1]


@dataclass
class Harness:
    client: TestClient
    clock: FakeClock
    codes: CodeCapture

    def pair(self, code: str | None = None) -> None:
        r = self.client.post("/pairing", data={"code": code or self.codes.last}, headers={"Origin": ORIGIN})
        assert r.status_code == 204, r.text

    def csrf(self) -> str:
        r = self.client.get("/session")
        assert r.status_code == 200, r.text
        token: str = r.json()["csrf_token"]
        return token


@pytest.fixture
def harness() -> Harness:
    clock = FakeClock()
    codes = CodeCapture()
    app = create_app(Settings.from_env({}), clock=clock, code_sink=codes)
    client = TestClient(app, base_url=BASE_URL)
    return Harness(client=client, clock=clock, codes=codes)

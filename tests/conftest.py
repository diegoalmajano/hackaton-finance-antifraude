"""Utilidades comunes de pruebas."""

from __future__ import annotations

import atexit
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

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


# --- .gitignore verificable también desde el ZIP de GitHub (que no incluye .git) ----------------------
_ROOT = Path(__file__).resolve().parents[1]
_GITIGNORE_REPO: list[str] = []


def gitignore_ignora(ruta: str) -> bool:
    """¿El ``.gitignore`` del proyecto ignora ``ruta``?

    Se comprueba en un repositorio git temporal con una copia del ``.gitignore`` y sin exclusiones globales,
    de modo que el resultado es el mismo dentro del repositorio y en una copia descargada como ZIP.
    """
    if shutil.which("git") is None:
        pytest.skip("git no está instalado: no se puede comprobar el .gitignore")
    if not _GITIGNORE_REPO:
        tmp = tempfile.mkdtemp(prefix="antifraude_gitignore_")
        atexit.register(shutil.rmtree, tmp, True)
        subprocess.run(["git", "init", "-q", tmp], check=True, capture_output=True)
        shutil.copyfile(_ROOT / ".gitignore", Path(tmp) / ".gitignore")
        _GITIGNORE_REPO.append(tmp)
    r = subprocess.run(["git", "-c", "core.excludesFile=", "check-ignore", "-q", "--no-index", ruta],
                       cwd=_GITIGNORE_REPO[0], capture_output=True)
    assert r.returncode in (0, 1), r.stderr
    return r.returncode == 0

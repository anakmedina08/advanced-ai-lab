"""Fixtures compartidas: sitio falso de Seguros Bolívar servido desde archivos locales (sin red)."""

from dataclasses import dataclass
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
BASE = "https://www.segurosbolivar.com"

ROUTES = {
    f"{BASE}/robots.txt": "robots.txt",
    f"{BASE}/sitemap.xml": "sitemap.xml",
    f"{BASE}/": "quienes.html",  # la home duplica "quiénes somos" → prueba de deduplicación
    f"{BASE}/seguro-de-hogar": "hogar.html",
    f"{BASE}/soat": "soat.html",
    f"{BASE}/quienes-somos": "quienes.html",
}


@dataclass
class FakeResponse:
    status_code: int
    content: bytes


class FakeSession:
    """Doble de requests.Session: sirve fixtures y registra las URLs pedidas."""

    def __init__(self, routes: dict[str, str] | None = None, fail: dict[str, list[object]] | None = None):
        self.routes = ROUTES if routes is None else routes
        self.fail = fail or {}
        self.calls: list[str] = []
        self.headers: dict[str, str] = {}

    def get(self, url, *, timeout, headers):
        self.calls.append(url)
        script = self.fail.get(url)
        if script:
            outcome = script.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return FakeResponse(int(outcome), b"")
        name = self.routes.get(url)
        if name is None:
            return FakeResponse(404, b"not found")
        return FakeResponse(200, (FIXTURES / name).read_bytes())


@pytest.fixture
def session():
    return FakeSession()


@pytest.fixture
def html(request):
    return (FIXTURES / getattr(request, "param", "hogar.html")).read_text(encoding="utf-8")


@pytest.fixture
def no_sleep():
    calls: list[float] = []
    return calls.append, calls

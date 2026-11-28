"""Auditoría de QA con Playwright sobre la app desplegada (SPEC-083, anuncio 551462-008).

Recorre el sitio público, el asistente y el panel del equipo en teléfono y escritorio, y revisa la
API. No corre en la suite normal ni en la CI (marca ``e2e``):

    uv run pytest tests/e2e -m e2e

Las URL base se cambian con ``E2E_SITIO``, ``E2E_APP`` y ``E2E_API`` (por ejemplo, para local).
"""

from __future__ import annotations

import os

import pytest
from playwright.sync_api import Page, Playwright, Response

pytestmark = pytest.mark.e2e

SITIO = os.environ.get("E2E_SITIO", "https://178-128-11-124.sslip.io").rstrip("/")
APP = os.environ.get("E2E_APP", "https://app.178-128-11-124.sslip.io").rstrip("/")
API = os.environ.get("E2E_API", "https://api.178-128-11-124.sslip.io").rstrip("/")

PAGINAS = [
    f"{SITIO}/",
    f"{SITIO}/casos/asistente-seguros",
    f"{SITIO}/casos/asistente-seguros/chat",
    f"{SITIO}/casos/asistente-seguros/guias",
    f"{SITIO}/privacidad",
    f"{APP}/",
    f"{APP}/foto",
    f"{APP}/estado",
]

TAMANOS = {"telefono": (390, 844), "escritorio": (1440, 900)}


@pytest.mark.parametrize("tamano", list(TAMANOS))
@pytest.mark.parametrize("url", PAGINAS)
def test_pagina_sin_errores(page: Page, url: str, tamano: str) -> None:
    """La página carga sin errores de consola ni respuestas 4xx/5xx (R083.3, AC3)."""
    # Arrange
    ancho, alto = TAMANOS[tamano]
    page.set_viewport_size({"width": ancho, "height": alto})
    errores: list[str] = []
    page.on("console", lambda m: errores.append(f"consola: {m.text}") if m.type == "error" else None)

    def _al_responder(respuesta: Response) -> None:
        if respuesta.status >= 400:
            errores.append(f"{respuesta.status} {respuesta.url}")

    page.on("response", _al_responder)

    # Act
    principal = page.goto(url, wait_until="networkidle")

    # Assert
    assert principal is not None and principal.ok, f"{url} respondió {principal and principal.status}"
    assert errores == [], f"{url} ({tamano}):\n" + "\n".join(errores)


def test_api_sana_con_yolo(playwright: Playwright) -> None:
    """GET /health responde ok y con el modelo YOLO cargado (R083.4)."""
    # Arrange
    cliente = playwright.request.new_context()

    # Act
    respuesta = cliente.get(f"{API}/health")

    # Assert
    assert respuesta.ok
    cuerpo = respuesta.json()
    assert cuerpo["status"] == "ok"
    assert cuerpo["componentes"]["modelo_yolo"] is True


def test_chat_sin_codigo_responde_controlado(playwright: Playwright) -> None:
    """El chat con IA sin código de acceso no se cae: pide el código (R083.5, SPEC-072)."""
    # Arrange
    cliente = playwright.request.new_context()

    # Act
    respuesta = cliente.post(f"{SITIO}/api/asistente/chat", data={"mensaje": "hola"})

    # Assert
    assert respuesta.status < 500
    assert "código de acceso" in respuesta.text()


def test_foto_invalida_recibe_400(playwright: Playwright) -> None:
    """Un archivo que no es imagen en /fotos recibe 400, no un error del servidor (R083.5)."""
    # Arrange
    cliente = playwright.request.new_context()
    archivo = {"name": "nota.txt", "mimeType": "text/plain", "buffer": b"esto no es una foto"}

    # Act
    respuesta = cliente.post(f"{API}/fotos", multipart={"archivo": archivo})

    # Assert
    assert respuesta.status == 400

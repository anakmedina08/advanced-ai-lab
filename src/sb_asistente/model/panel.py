"""Eventos del panel en vivo de Yellowdata (/casos): qué tecnología del producto se ejecutó (SPEC-082).

Publica en ``AGENT_EVENTS_URL`` con ``Authorization: Bearer $AGENT_EVENTS_TOKEN``. En producción la
URL es la red interna de Docker (``http://yellowdata:3000/api/agent-events``), así que el evento no
sale a internet. Sin esas dos variables no hace nada (CI, pruebas y desarrollo local).

Privacidad: el panel es público, así que el evento **nunca** lleva texto del usuario ni argumentos de
las tools; solo el agente, el nombre de la herramienta y una etiqueta corta (canal o latencia).
El envío corre en un hilo aparte con un timeout corto y se traga cualquier error: el panel es
informativo y no puede frenar ni romper una respuesta.
"""

import json
import os
import threading
import time
import urllib.request

TIMEOUT_S = 3.0
_LARGO = 120  # el panel recorta cada campo a 120 caracteres; aquí se recorta antes de enviar


def _enviar(url: str, token: str, evento: dict[str, object]) -> None:
    """POST del evento; cualquier fallo se ignora."""
    peticion = urllib.request.Request(
        url,
        data=json.dumps(evento, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=TIMEOUT_S):
            pass
    except Exception:  # noqa: BLE001 - el panel nunca rompe la respuesta del asistente
        pass


def publicar(
    agente: str, herramienta: str, comando: str | None = None, *, ok: bool = True, esperar: bool = False
) -> bool:
    """Publica un evento ``Tecnologia``; devuelve ``False`` si el panel no está configurado.

    Con ``esperar=False`` (lo normal) el envío va en un hilo *daemon* y la llamada vuelve enseguida.
    """
    url = os.getenv("AGENT_EVENTS_URL", "").strip()
    token = os.getenv("AGENT_EVENTS_TOKEN", "").strip()
    if not url or not token:
        return False
    evento: dict[str, object] = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "evento": "Tecnologia",
        "agente": agente[:_LARGO],
        "herramienta": herramienta[:_LARGO],
        "ok": ok,
    }
    if comando:
        evento["comando"] = comando[:_LARGO]
    if esperar:
        _enviar(url, token, evento)
    else:
        threading.Thread(target=_enviar, args=(url, token, evento), daemon=True).start()
    return True


def tool_por_mcp(nombre: str) -> bool:
    """Una tool llamada por el MCP propio: en producción la usa OpenClaw, es decir, WhatsApp."""
    return publicar("whatsapp", nombre, "OpenClaw → MCP")


def turno_trazado(ms_total: float, error: str | None = None) -> bool:
    """Un turno del agente quedó trazado en LangSmith (solo si el tracing está activo)."""
    if os.getenv("LANGSMITH_TRACING", "").strip().lower() not in {"1", "true"}:
        return False
    return publicar("langsmith", "traza del turno", f"{ms_total:.0f} ms", ok=error is None)

"""Trazas de cada turno del agente: una línea JSON por turno con la latencia de cada tool.

Es el equivalente local de LangSmith (que se activa aparte con ``LANGSMITH_TRACING=true``):
permite explicar qué hizo el agente sin depender de un servicio externo. Por privacidad **no**
se guarda el texto del usuario ni la respuesta; el hilo se guarda como un hash corto.

- ``medir_tools`` (middleware ``wrap_tool_call``) mide cada tool en milisegundos.
- ``registrar_turno`` escribe la línea en ``data/logs/turnos.jsonl`` y rota el archivo a 5 MB.
"""

import hashlib
import json
import time
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from langchain.agents.middleware import wrap_tool_call

TAMANO_MAXIMO: Final[int] = 5 * 1024 * 1024
_TIEMPOS: ContextVar[list[dict[str, Any]] | None] = ContextVar("tiempos_tools", default=None)


def iniciar_medicion() -> list[dict[str, Any]]:
    """Abre la lista de tiempos del turno actual (la llenan las tools al ejecutarse)."""
    tiempos: list[dict[str, Any]] = []
    _TIEMPOS.set(tiempos)
    return tiempos


@wrap_tool_call
def medir_tools(request, handler):  # noqa: ANN001, ANN201 - firma definida por LangChain
    """Mide la latencia de cada tool y si terminó con error."""
    inicio = time.perf_counter()
    nombre = request.tool_call.get("name", "?")
    error = None
    try:
        return handler(request)
    except Exception as exc:
        error = type(exc).__name__
        raise
    finally:
        tiempos = _TIEMPOS.get()
        if tiempos is not None:
            ms = round((time.perf_counter() - inicio) * 1000, 1)
            tiempos.append({"tool": nombre, "ms": ms} | ({"error": error} if error else {}))


def hash_hilo(conversacion_id: str) -> str:
    """Hash corto del hilo (no se guarda el id real)."""
    return hashlib.sha256(conversacion_id.encode()).hexdigest()[:10]


def linea_turno(turno: dict[str, Any], ms_total: float, error: str | None = None) -> dict[str, Any]:
    """Resumen sin texto del usuario: ruta, tools con su latencia, fuentes y error."""
    decision = turno.get("decision") or {}
    salida = turno.get("salida") or {}
    return {
        "fecha": datetime.now(UTC).isoformat(timespec="seconds"),
        "hilo": hash_hilo(str(turno.get("conversacion_id", ""))),
        "ruta": decision.get("ruta"),
        "cautela": decision.get("cautela", False),
        "tools": turno.get("tiempos_tools", []),
        "ms_total": round(ms_total, 1),
        "fuentes": len(salida.get("fuentes", [])),
        "fuentes_descartadas": len(turno.get("fuentes_descartadas", [])),
        "confianza": salida.get("confianza"),
        "error": error,
    }


def registrar_turno(ruta: Path, linea: dict[str, Any]) -> None:
    """Agrega la línea al log (rota a ``.1`` al superar 5 MB)."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if ruta.is_file() and ruta.stat().st_size > TAMANO_MAXIMO:
        ruta.replace(ruta.with_suffix(".jsonl.1"))
    with ruta.open("a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(linea, ensure_ascii=False) + "\n")


def ultimas(ruta: Path, n: int = 10) -> list[dict[str, Any]]:
    """Las últimas ``n`` líneas del log (vacío si no existe)."""
    if not ruta.is_file():
        return []
    lineas = ruta.read_text(encoding="utf-8").splitlines()[-n:]
    return [json.loads(linea) for linea in lineas if linea.strip()]

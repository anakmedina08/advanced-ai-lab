"""Puntos de inyección de la API (REST y JSON-RPC).

Cada función devuelve la dependencia real; las pruebas las reemplazan con
``app.dependency_overrides`` para trabajar sin red ni API de pago.
"""

from collections.abc import Callable
from functools import lru_cache

from sb_asistente.controller import agente, assistant, chat
from sb_asistente.model.llm.service import Answer
from sb_asistente.model.rag.hibrido import RecuperadorHibrido

Responder = Callable[[str, str, str, str], Answer]
"""(pregunta, versión, modo, proveedor) → Answer."""


def _responder_real(pregunta: str, version_prompt: str, modo: str, proveedor: str) -> Answer:
    """Usa el contexto reducido (rápido y barato) o la base completa."""
    if modo == "reducido":
        return assistant.LiteAssistant.build(proveedor).answer(pregunta, version=version_prompt)
    return assistant.full_assistant(proveedor).answer(pregunta, version=version_prompt)


def get_responder() -> Responder:
    """Q&A directo (``/preguntas`` y ``asistente.preguntar``)."""
    return _responder_real


@lru_cache(maxsize=3)
def _lite(proveedor: str) -> assistant.LiteAssistant:
    """Un asistente de contexto reducido por proveedor (carga chunks y modelo una sola vez)."""
    return assistant.LiteAssistant.build(proveedor)


def get_chat_qa() -> Callable[[str], chat.Responder]:
    """Fábrica (proveedor → responder de Q&A con skill) para el chat orquestado."""

    def fabrica(proveedor: str) -> chat.Responder:
        return lambda pregunta, skill: _lite(proveedor).answer(pregunta, skill=skill)

    return fabrica


def get_asistente() -> Callable[[str], assistant.KnowledgeAssistant]:
    """Fábrica del asistente completo para resumen y FAQ."""
    return assistant.full_assistant


def get_agente() -> Callable[[str], agente.AgenteAsistente]:
    """Fábrica (proveedor → agente con tools, salida estructurada y memoria)."""
    return agente.agente_por_defecto


@lru_cache(maxsize=1)
def _recuperador() -> tuple[RecuperadorHibrido, str]:
    return agente.recuperador_por_defecto()


def get_recuperador() -> Callable[[], tuple[RecuperadorHibrido, str]]:
    """Recuperador híbrido (BM25 + Chroma) y su modo, para ``conocimiento.buscar``."""
    return _recuperador

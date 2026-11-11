"""Fase 2 · Agente RAG con Deep Agents (adaptado del ejercicio ``ejercicio_langchain`` del curso).

Flujo: el agente llama a ``search_knowledge`` → la herramienta busca en Qdrant y guarda cada
fragmento como archivo en ``/retrieved/`` del backend del agente → el agente delega cada archivo
al subagente ``chunk-analyst`` (en paralelo) → redacta la respuesta con la fuente.

Guardar los fragmentos como archivos evita que todo el texto recuperado se acumule en el historial
del agente principal: cada subagente lee solo su archivo y devuelve un resumen corto.
"""

import uuid
from collections.abc import Callable
from typing import Protocol

from langchain.tools import tool
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from sb_asistente.model.llm import prompts

RETRIEVED_DIR = "/retrieved"
NO_RESULTS = "No encontré fragmentos relevantes en la base de conocimiento."


class UploadResult(Protocol):
    """Lo mínimo que se usa del resultado de ``upload_files`` de un backend de Deep Agents."""

    error: object


class FileBackend(Protocol):
    """Contrato del backend de archivos del agente (``deepagents.backends.StateBackend`` lo cumple)."""

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[UploadResult]:  # noqa: D102
        ...


def make_search_tool(
    search: Callable[[str], list[Document]],
    backend: FileBackend,
    new_batch_id: Callable[[], str] = lambda: uuid.uuid4().hex[:8],
) -> BaseTool:
    """Crea la herramienta ``search_knowledge`` con su búsqueda y su backend inyectados."""

    @tool
    def search_knowledge(query: str) -> str:
        """Busca en la base pública de Seguros Bolívar y guarda los fragmentos en /retrieved/.

        Args:
            query: Consulta en lenguaje natural (producto, cobertura, canal, trámite).

        Returns:
            Rutas de los fragmentos guardados, una por línea.

        """
        docs = search(query)
        if not docs:
            return NO_RESULTS
        batch = new_batch_id()
        uploads: list[tuple[str, bytes]] = []
        for index, doc in enumerate(docs, start=1):
            content = (
                f"# {doc.metadata.get('title', '')}\nFuente: {doc.metadata.get('url', '')}\n\n"
                f"{doc.page_content}"
            )
            uploads.append((f"{RETRIEVED_DIR}/{batch}/chunk_{index}.md", content.encode("utf-8")))
        if any(result.error for result in backend.upload_files(uploads)):
            raise RuntimeError("No se pudieron guardar los fragmentos en el backend del agente.")
        paths = "\n".join(path for path, _ in uploads)
        return f"Guardé {len(uploads)} fragmentos:\n{paths}"

    return search_knowledge


def build_agent(
    llm: BaseChatModel,
    search: Callable[[str], list[Document]],
    channels: str,
    backend: FileBackend | None = None,
) -> object:
    """Crea el Deep Agent con la herramienta de búsqueda y el subagente ``chunk-analyst``."""
    from deepagents import create_deep_agent
    from deepagents.backends import StateBackend

    backend = backend or StateBackend()
    return create_deep_agent(
        model=llm,
        tools=[make_search_tool(search, backend)],
        system_prompt=prompts.AGENT_SYSTEM.format(channels=channels.strip()),
        subagents=[
            {
                "name": "chunk-analyst",
                "description": prompts.CHUNK_ANALYST_DESCRIPTION,
                "system_prompt": prompts.CHUNK_ANALYST_SYSTEM,
            }
        ],
        backend=backend,
    )


def final_text(result: dict[str, object]) -> str:
    """Texto del último mensaje del agente."""
    messages = result.get("messages") or []
    if not messages:
        raise RuntimeError("El agente no devolvió mensajes.")
    return messages[-1].text.strip()

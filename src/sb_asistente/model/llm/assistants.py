"""Asistentes de Q&A con contexto recuperado por pregunta (modos «reducido», «rag» y «agente»).

El modo «completo» es ``service.KnowledgeAssistant`` con toda la base. Los demás cambian solo
**cómo se elige el contexto** de cada pregunta:

- ``RetrievalAssistant``: canales + fragmentos que devuelve una función de búsqueda (por palabras en
  ``keyword_search`` o por embeddings en ``vector_store``) y luego los prompts v1–v4.
- ``AgentAssistant``: un Deep Agent (``agent``) decide qué buscar y delega el análisis a subagentes.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from sb_asistente.model.llm import agent, prompts
from sb_asistente.model.llm.service import Answer, KnowledgeAssistant
from sb_asistente.model.processing.gold import estimate_tokens

AGENT_VERSION = "agente"  # el agente usa su propio prompt, no las versiones v1–v4

Retriever = Callable[[str], str]
"""Pregunta → bloques Markdown ``### título / Fuente: URL / texto`` con los fragmentos elegidos."""


class QAAssistant(Protocol):
    """Lo que las vistas y la evaluación necesitan de cualquier modo de Q&A."""

    def answer(self, question: str, version: str = prompts.DEFAULT_QA_VERSION) -> Answer:  # noqa: D102
        ...


class AgentGraph(Protocol):
    """Lo mínimo que se usa del grafo compilado de Deep Agents."""

    def invoke(self, state: dict[str, object]) -> dict[str, object]:  # noqa: D102
        ...


@dataclass(slots=True)
class RetrievalAssistant:
    """Q&A sobre el bloque de canales más los fragmentos recuperados para cada pregunta."""

    llm: BaseChatModel
    retrieve: Retriever
    channels: str

    def context_for(self, question: str) -> str:
        """Bloque de canales + fragmentos recuperados (cada uno con su URL)."""
        return self.channels + "\n" + self.retrieve(question)

    def answer(self, question: str, version: str = prompts.DEFAULT_QA_VERSION) -> Answer:
        """Responde con los prompts v1–v4 sobre el contexto recuperado."""
        return KnowledgeAssistant(self.llm, self.context_for(question)).answer(question, version=version)


class AgentAssistant:
    """Agente de la Fase 2 (Deep Agents): busca, delega el análisis a subagentes y responde."""

    def __init__(self, graph: AgentGraph, channels: str) -> None:
        """Recibe el grafo del agente ya construido (inyectable en pruebas)."""
        self.graph = graph
        self.context_tokens = estimate_tokens(channels)

    def answer(self, question: str, version: str = AGENT_VERSION) -> Answer:
        """Responde una pregunta; ``version`` se ignora (el agente tiene su propio prompt)."""
        if not question.strip():
            raise ValueError("La pregunta está vacía.")
        start = time.perf_counter()
        result = self.graph.invoke({"messages": [HumanMessage(question)]})
        return Answer(
            agent.final_text(result), "qa", AGENT_VERSION, time.perf_counter() - start, self.context_tokens
        )

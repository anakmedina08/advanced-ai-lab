"""Servicio LLM con LangChain: Resumen, FAQ y Q&A sobre el conocimiento consolidado.

Fase 1: todo el texto limpio va en el *system prompt* (sin RAG). El proveedor se elige por
configuración (Claude por la API de Anthropic u Ollama local) sin cambiar la lógica (Clase 5: Agent = Model
+ Harness).
"""

import time
from dataclasses import dataclass
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from sb_asistente.config import (
    ANTHROPIC_MODEL,
    CONTEXT_OUTPUT_RESERVE,
    KNOWLEDGE_MD,
    LLM_MAX_OUTPUT_TOKENS,
    LLM_PROVIDER,
    LLM_TEMPERATURE,
    MAX_CONTEXT_TOKENS,
    OLLAMA_MODEL,
    OLLAMA_NUM_CTX,
)
from sb_asistente.llm import prompts
from sb_asistente.processing.gold import estimate_tokens


class KnowledgeTooLargeError(ValueError):
    """El conocimiento consolidado no cabe en el presupuesto de contexto configurado."""


@dataclass(slots=True)
class Answer:
    """Respuesta del asistente con trazabilidad mínima."""

    text: str
    task: str
    prompt_version: str
    latency_s: float
    context_tokens_est: int

    @property
    def cites_source(self) -> bool:
        """Indica si la respuesta incluye una URL de segurosbolivar.com."""
        return "segurosbolivar.com" in self.text

    @property
    def is_fallback(self) -> bool:
        """Indica si el modelo declaró no tener la información."""
        return "No encuentro esa información" in self.text


def build_llm(provider: str = LLM_PROVIDER) -> BaseChatModel:
    """Crea el modelo de chat según el proveedor (importación diferida)."""
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=ANTHROPIC_MODEL,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_OUTPUT_TOKENS,
            max_retries=2,
        )
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=OLLAMA_MODEL,
            temperature=LLM_TEMPERATURE,
            num_ctx=OLLAMA_NUM_CTX,
            num_predict=LLM_MAX_OUTPUT_TOKENS,
        )
    raise ValueError(f"Proveedor no soportado: {provider!r} (use 'anthropic' u 'ollama').")


def context_budget(provider: str = LLM_PROVIDER) -> int:
    """Tokens disponibles para la base de conocimiento según el proveedor."""
    window = OLLAMA_NUM_CTX if provider == "ollama" else MAX_CONTEXT_TOKENS
    return window - CONTEXT_OUTPUT_RESERVE


def load_knowledge(path: Path = KNOWLEDGE_MD, max_tokens: int = MAX_CONTEXT_TOKENS) -> str:
    """Carga el conocimiento consolidado y valida que quepa en el presupuesto de contexto."""
    if not path.is_file():
        raise FileNotFoundError(
            f"No existe {path}. Ejecute primero: uv run sb discover && uv run sb scrape && uv run sb process"
        )
    text = path.read_text(encoding="utf-8")
    tokens = estimate_tokens(text)
    if tokens > max_tokens:
        raise KnowledgeTooLargeError(
            f"El conocimiento tiene ~{tokens:,} tokens y el límite es {max_tokens:,}. "
            "Reduzca el alcance o aumente MAX_CONTEXT_TOKENS."
        )
    return text


class KnowledgeAssistant:
    """Fachada de las tres tareas del Módulo 1."""

    def __init__(self, llm: BaseChatModel, knowledge: str, cache_prompt: bool | None = None) -> None:
        """Recibe el modelo y el conocimiento por inyección (facilita pruebas con dobles).

        ``cache_prompt`` marca el *system prompt* (que lleva toda la base) para la caché de
        prompts de Anthropic: tras la primera llamada se cobra a una fracción del precio.
        Por defecto se activa solo si el modelo es ``ChatAnthropic``.
        """
        if not knowledge.strip():
            raise ValueError("El conocimiento está vacío.")
        self.llm = llm
        self.knowledge = knowledge
        self.context_tokens = estimate_tokens(knowledge)
        self.cache_prompt = type(llm).__name__ == "ChatAnthropic" if cache_prompt is None else cache_prompt

    def build_messages(self, system: str, human: str, **kwargs: object) -> list[BaseMessage]:
        """Arma los mensajes; con caché, el system prompt va como bloque ``cache_control``."""
        prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])
        messages = prompt.format_messages(knowledge=self.knowledge, **kwargs)
        if self.cache_prompt:
            block = {"type": "text", "text": messages[0].content, "cache_control": {"type": "ephemeral"}}
            messages[0] = SystemMessage(content=[block])
        return messages

    def _run(self, system: str, human: str, task: str, version: str, **kwargs: object) -> Answer:
        messages = self.build_messages(system, human, **kwargs)
        start = time.perf_counter()
        text = (self.llm | StrOutputParser()).invoke(messages)
        return Answer(text.strip(), task, version, time.perf_counter() - start, self.context_tokens)

    def answer(self, question: str, version: str = prompts.DEFAULT_QA_VERSION) -> Answer:
        """Q&A: responde una pregunta del cliente."""
        if not question.strip():
            raise ValueError("La pregunta está vacía.")
        if version not in prompts.QA_SYSTEM:
            raise ValueError(f"Versión de prompt desconocida: {version}")
        return self._run(prompts.QA_SYSTEM[version], prompts.QA_HUMAN, "qa", version, question=question)

    def summarize(self, topic: str = prompts.TOPICS[0]) -> Answer:
        """Resumen: síntesis para un cliente nuevo sobre un tema."""
        return self._run(prompts.SUMMARY_SYSTEM, prompts.SUMMARY_HUMAN, "resumen", "v3", topic=topic)

    def faq(self, topic: str = prompts.TOPICS[1], n: int = 5) -> Answer:
        """FAQ: genera preguntas frecuentes respaldadas por el conocimiento."""
        if not 1 <= n <= 15:
            raise ValueError("n debe estar entre 1 y 15.")
        return self._run(prompts.FAQ_SYSTEM, prompts.FAQ_HUMAN, "faq", "v3", topic=topic, n=n)

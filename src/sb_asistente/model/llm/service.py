"""Servicio LLM con LangChain: Resumen, FAQ y Q&A sobre el conocimiento consolidado.

Fase 1: todo el texto limpio va en el *system prompt* (sin RAG). El proveedor se elige por
configuración (Claude por la API de Anthropic u Ollama local) sin cambiar la lógica (Clase 5: Agent = Model
+ Harness).
"""

import re
import time
from dataclasses import dataclass

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from sb_asistente.config import (
    ANTHROPIC_EFFORT,
    ANTHROPIC_MODEL,
    CONTEXT_OUTPUT_RESERVE,
    LLM_MAX_OUTPUT_TOKENS,
    LLM_PROVIDER,
    LLM_TEMPERATURE,
    MAX_CONTEXT_TOKENS,
    OLLAMA_MODEL,
    OLLAMA_NUM_CTX,
)
from sb_asistente.model.llm import prompts
from sb_asistente.model.processing.gold import estimate_tokens

SOURCE_URL = re.compile(r"https?://(?:www\.)?segurosbolivar\.com[^\s)\]>\"']*")


@dataclass(slots=True)
class Answer:
    """Respuesta del asistente con trazabilidad mínima."""

    text: str
    task: str
    prompt_version: str
    latency_s: float
    context_tokens_est: int

    @property
    def sources(self) -> list[str]:
        """URLs de segurosbolivar.com citadas, sin repetir y en orden de aparición."""
        return list(dict.fromkeys(u.rstrip(".,;:") for u in SOURCE_URL.findall(self.text)))

    @property
    def cites_source(self) -> bool:
        """Indica si la respuesta cita al menos una URL de segurosbolivar.com."""
        return bool(self.sources)

    @property
    def is_fallback(self) -> bool:
        """Indica si el modelo usó la respuesta de no-información definida en ``prompts``."""
        return prompts.FALLBACK_MARKER in self.text


def build_llm(provider: str = LLM_PROVIDER, num_ctx: int | None = None) -> BaseChatModel:
    """Crea el modelo de chat según el proveedor (importación diferida).

    ``num_ctx`` permite una ventana más chica en Ollama cuando se usa el contexto reducido:
    menos memoria y respuestas mucho más rápidas en CPU.
    """
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        # Sin `temperature`: los modelos actuales de Claude la rechazan (400). El determinismo lo dan
        # el prompt (reglas, formato fijo, ejemplos) y el esfuerzo de razonamiento bajo.
        return ChatAnthropic(
            model=ANTHROPIC_MODEL,
            max_tokens=LLM_MAX_OUTPUT_TOKENS,
            output_config={"effort": ANTHROPIC_EFFORT},
            max_retries=2,
        )
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=OLLAMA_MODEL,
            temperature=LLM_TEMPERATURE,
            num_ctx=num_ctx or OLLAMA_NUM_CTX,
            num_predict=LLM_MAX_OUTPUT_TOKENS,
        )
    raise ValueError(f"Proveedor no soportado: {provider!r} (use 'anthropic' u 'ollama').")


def context_budget(provider: str = LLM_PROVIDER) -> int:
    """Tokens disponibles para la base de conocimiento según el proveedor."""
    window = OLLAMA_NUM_CTX if provider == "ollama" else MAX_CONTEXT_TOKENS
    return window - CONTEXT_OUTPUT_RESERVE


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

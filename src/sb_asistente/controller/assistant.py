"""Controlador del asistente: casos de uso Q&A, Resumen, FAQ y Evaluación para las vistas.

Las vistas (Streamlit y CLI) solo hablan con este módulo y con ``pipeline``; nunca construyen
modelos ni prompts por su cuenta (MVC: la vista no conoce al modelo).
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from sb_asistente.config import EVAL_QUESTIONS, EVAL_RESULTS
from sb_asistente.model import evaluation
from sb_asistente.model.llm import prompts, retrieval
from sb_asistente.model.llm.service import (
    Answer,
    KnowledgeAssistant,
    build_llm,
    context_budget,
    load_knowledge,
)

QA_VERSIONS: tuple[str, ...] = tuple(prompts.QA_SYSTEM)
DEFAULT_QA_VERSION: str = prompts.DEFAULT_QA_VERSION
TOPICS: tuple[str, ...] = tuple(prompts.TOPICS)
LITE_NUM_CTX = 8192  # ventana de Ollama en modo de contexto reducido
_ANY_SIZE = 10_000_000  # para leer el conocimiento solo a fin de extraer el bloque de canales


def full_assistant(provider: str) -> KnowledgeAssistant:
    """Asistente con TODA la base en el system prompt (diseño de la Fase 1)."""
    return KnowledgeAssistant(build_llm(provider), load_knowledge(max_tokens=context_budget(provider)))


@dataclass(slots=True)
class LiteAssistant:
    """Asistente de contexto reducido: solo los fragmentos de Gold más parecidos a la pregunta."""

    llm: object
    chunks: list[dict[str, object]]
    channels: str

    @classmethod
    def build(cls, provider: str) -> "LiteAssistant":
        """Carga el modelo con ventana pequeña, los chunks y el bloque de canales."""
        channels = retrieval.channels_block(load_knowledge(max_tokens=_ANY_SIZE))
        return cls(build_llm(provider, num_ctx=LITE_NUM_CTX), retrieval.load_chunks(), channels)

    def context_for(self, question: str) -> str:
        """Bloque de canales + fragmentos relevantes (cada uno con su URL)."""
        return self.channels + "\n" + retrieval.select_context(question, self.chunks)

    def answer(self, question: str, version: str = DEFAULT_QA_VERSION) -> Answer:
        """Responde usando solo el contexto reducido."""
        return KnowledgeAssistant(self.llm, self.context_for(question)).answer(question, version=version)


def evaluate(
    provider: str,
    version: str,
    limit: int | None = None,
    on_progress: Callable[[int, int, dict[str, object]], None] | None = None,
    factory: Callable[[str], KnowledgeAssistant] = full_assistant,
    results_path: Path | None = None,
) -> tuple[dict[str, object], Path]:
    """Corre el banco de preguntas y guarda el CSV; devuelve las métricas y la ruta.

    ``factory`` y ``results_path`` permiten inyectar un asistente falso y una carpeta temporal.
    """
    questions = evaluation.load_questions(EVAL_QUESTIONS)[:limit]
    suffix = f"_muestra{len(questions)}" if limit else ""
    out = (results_path or EVAL_RESULTS).with_name(f"resultados_{provider}_{version}{suffix}.csv")
    assistant = factory(provider)
    metrics = evaluation.run_eval(questions, lambda q: assistant.answer(q, version), out, on_progress)
    return metrics, out


def evaluation_summary() -> list[dict[str, object]]:
    """Resumen de todas las corridas completas guardadas."""
    return evaluation.summarize_results(EVAL_RESULTS.parent)


def evaluation_detail(provider: str, version: str) -> list[dict[str, object]]:
    """Filas de una corrida (una por pregunta)."""
    return evaluation.read_results(EVAL_RESULTS.parent / f"resultados_{provider}_{version}.csv")

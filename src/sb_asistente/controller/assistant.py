"""Controlador del asistente: arma cada modo de Q&A y orquesta Resumen, FAQ y Evaluación.

Las vistas (Streamlit y CLI) solo hablan con este módulo y con ``pipeline``; nunca construyen
modelos ni prompts por su cuenta (MVC: la vista no conoce al modelo). Aquí se conectan las piezas
del modelo con la configuración y los archivos de Gold; la lógica vive en ``model/llm``.

Modos de contexto para Q&A:

- ``completo``: TODA la base en el *system prompt* (diseño de la Fase 1).
- ``reducido``: canales + fragmentos con más palabras en común con la pregunta (sin embeddings).
- ``rag``: canales + los ``k`` fragmentos más parecidos según embeddings en Qdrant (Fase 2).
- ``agente``: Deep Agent que busca en Qdrant y delega el análisis a un subagente (Fase 2).
"""

from collections.abc import Callable
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel

from sb_asistente.config import EVAL_QUESTIONS, EVAL_RESULTS, LITE_NUM_CTX, QDRANT_DIR, RAG_TOP_K
from sb_asistente.model import evaluation
from sb_asistente.model.llm import agent, keyword_search, knowledge, prompts, vector_store
from sb_asistente.model.llm.assistants import AGENT_VERSION, AgentAssistant, QAAssistant, RetrievalAssistant
from sb_asistente.model.llm.service import Answer, KnowledgeAssistant, build_llm, context_budget

__all__ = [
    "AGENT_VERSION",
    "DEFAULT_MODE",
    "DEFAULT_QA_VERSION",
    "MODES",
    "QA_VERSIONS",
    "TOPICS",
    "Answer",
    "KnowledgeAssistant",
    "LiteAssistant",
    "QAAssistant",
    "build_assistant",
    "embedding_search",
    "evaluate",
    "evaluation_detail",
    "evaluation_summary",
    "full_assistant",
    "run_label",
]

QA_VERSIONS: tuple[str, ...] = tuple(prompts.QA_SYSTEM)
DEFAULT_QA_VERSION: str = prompts.DEFAULT_QA_VERSION
TOPICS: tuple[str, ...] = tuple(prompts.TOPICS)
MODES: dict[str, str] = {
    "completo": "Toda la base (Fase 1)",
    "reducido": "Contexto reducido por palabras",
    "rag": "RAG con embeddings (Fase 2)",
    "agente": "Agente con subagentes (Fase 2)",
}
DEFAULT_MODE = "completo"

EmbeddingSearch = Callable[[str], list[Document]]


# --- Construcción de cada modo ---------------------------------------------------------------
def full_assistant(provider: str) -> KnowledgeAssistant:
    """Modo «completo»: TODA la base en el system prompt (Fase 1; también Resumen y FAQ)."""
    return KnowledgeAssistant(
        build_llm(provider), knowledge.load_knowledge(max_tokens=context_budget(provider))
    )


class LiteAssistant(RetrievalAssistant):
    """Modo «reducido» con la firma ``(llm, chunks, channels)`` que usan la API, el RPC y la CLI."""

    def __init__(self, llm: BaseChatModel, chunks: list[dict[str, object]], channels: str) -> None:
        """Busca por palabras en ``chunks`` (``keyword_search``) y antepone ``channels``."""
        super().__init__(llm, lambda question: keyword_search.select_context(question, chunks), channels)
        self.chunks = chunks

    @classmethod
    def build(cls, provider: str) -> "LiteAssistant":
        """Carga el modelo con ventana pequeña, los chunks y el bloque de canales."""
        llm = build_llm(provider, num_ctx=LITE_NUM_CTX)
        return cls(llm, knowledge.load_chunks(), knowledge.load_channels())


def keyword_assistant(provider: str) -> LiteAssistant:
    """Modo «reducido»: fragmentos elegidos por palabras en común con la pregunta."""
    return LiteAssistant.build(provider)


def embedding_search(k: int = RAG_TOP_K, qdrant_dir: Path | None = QDRANT_DIR) -> EmbeddingSearch:
    """Abre (o crea la primera vez) el índice Qdrant de los chunks y devuelve su función de búsqueda."""
    store = vector_store.build_index(
        knowledge.load_chunks(), vector_store.build_embeddings(), vector_store.open_client(qdrant_dir)
    )
    return lambda question: vector_store.search(store, question, k)


def rag_assistant(provider: str) -> RetrievalAssistant:
    """Modo «rag»: fragmentos elegidos por similitud semántica (embeddings + Qdrant)."""
    search = embedding_search()
    return RetrievalAssistant(
        build_llm(provider, num_ctx=LITE_NUM_CTX),
        lambda question: vector_store.format_docs(search(question)),
        knowledge.load_channels(),
    )


def agent_assistant(provider: str) -> AgentAssistant:
    """Modo «agente»: Deep Agent con búsqueda en Qdrant y subagente ``chunk-analyst``."""
    channels = knowledge.load_channels()
    graph = agent.build_agent(build_llm(provider, num_ctx=LITE_NUM_CTX), embedding_search(), channels)
    return AgentAssistant(graph, channels)


_BUILDERS: dict[str, Callable[[str], QAAssistant]] = {
    "completo": full_assistant,
    "reducido": keyword_assistant,
    "rag": rag_assistant,
    "agente": agent_assistant,
}


def build_assistant(provider: str, mode: str = DEFAULT_MODE) -> QAAssistant:
    """Crea el asistente de Q&A del modo pedido."""
    if mode not in _BUILDERS:
        raise ValueError(f"Modo desconocido: {mode!r} (use uno de {', '.join(MODES)}).")
    return _BUILDERS[mode](provider)


# --- Evaluación ------------------------------------------------------------------------------
def run_label(provider: str, mode: str) -> str:
    """Nombre de la corrida en los CSV: ``anthropic`` (modo completo) o ``anthropic-rag``."""
    return provider if mode == DEFAULT_MODE else f"{provider}-{mode}"


def evaluate(
    provider: str,
    version: str,
    limit: int | None = None,
    on_progress: Callable[[int, int, dict[str, object]], None] | None = None,
    factory: Callable[[str], QAAssistant] = full_assistant,
    results_path: Path | None = None,
    mode: str = DEFAULT_MODE,
) -> tuple[dict[str, object], Path]:
    """Corre el banco de preguntas y guarda el CSV; devuelve las métricas y la ruta.

    ``factory`` y ``results_path`` permiten inyectar un asistente falso y una carpeta temporal.
    """
    questions = evaluation.load_questions(EVAL_QUESTIONS)[:limit]
    if not questions:
        raise ValueError("--limit debe ser mayor que 0.")
    if mode == "agente":
        version = AGENT_VERSION
    suffix = f"_muestra{len(questions)}" if limit else ""
    name = f"resultados_{run_label(provider, mode)}_{version}{suffix}.csv"
    out = (results_path or EVAL_RESULTS).with_name(name)
    assistant = factory(provider)
    metrics = evaluation.run_eval(questions, lambda q: assistant.answer(q, version), out, on_progress)
    return metrics, out


def evaluation_summary() -> list[dict[str, object]]:
    """Resumen de todas las corridas completas guardadas."""
    return evaluation.summarize_results(EVAL_RESULTS.parent)


def evaluation_detail(run: str, version: str) -> list[dict[str, object]]:
    """Filas de una corrida (una por pregunta); ``run`` es el nombre que da :func:`run_label`."""
    return evaluation.read_results(EVAL_RESULTS.parent / f"resultados_{run}_{version}.csv")

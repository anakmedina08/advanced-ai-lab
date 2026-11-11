"""Fábrica de embeddings (importación diferida, como ``build_llm``).

- ``ollama``: ``nomic-embed-text`` local, el mismo del ejercicio de clase (gratis, sin enviar
  datos fuera). Requiere ``ollama pull nomic-embed-text``.
- ``voyage``: API de Voyage AI, el proveedor que recomienda Anthropic (Claude no tiene modelo de
  embeddings). Requiere ``VOYAGE_API_KEY`` y ``uv sync --extra voyage``.
- ``fake``: vectores determinísticos por hash, para pruebas sin red.
"""

from langchain_core.embeddings import Embeddings

from sb_asistente.config import EMBEDDINGS_MODEL, EMBEDDINGS_PROVIDER, EMBEDDINGS_PROVIDERS, VOYAGE_MODEL


def build_embeddings(provider: str = EMBEDDINGS_PROVIDER) -> Embeddings:
    """Crea el modelo de embeddings del proveedor indicado."""
    if provider == "ollama":
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(model=EMBEDDINGS_MODEL)
    if provider == "voyage":
        try:
            from langchain_voyageai import VoyageAIEmbeddings
        except ImportError as exc:  # extra opcional
            raise RuntimeError("Instale el extra: uv sync --extra voyage") from exc
        return VoyageAIEmbeddings(model=VOYAGE_MODEL)
    if provider == "fake":
        from langchain_core.embeddings import DeterministicFakeEmbedding

        return DeterministicFakeEmbedding(size=256)
    raise ValueError(
        f"Proveedor de embeddings desconocido: {provider} (use {', '.join(EMBEDDINGS_PROVIDERS)})."
    )


def model_name(provider: str = EMBEDDINGS_PROVIDER) -> str:
    """Nombre del modelo que se registra con el índice (para detectar mezclas)."""
    return {"ollama": EMBEDDINGS_MODEL, "voyage": VOYAGE_MODEL, "fake": "deterministic-256"}[provider]

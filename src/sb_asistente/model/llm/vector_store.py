"""Fase 2 · Índice vectorial de los chunks de Gold: embeddings locales (Ollama) + Qdrant.

Adapta el flujo RAG del ejercicio ``ejercicio_langchain`` (ejemplo del curso) al corpus de
Seguros Bolívar:

- Los fragmentos ya existen (``data/gold/chunks.jsonl``): no se vuelve a la web ni se re-divide.
- Los embeddings se calculan en local con Ollama (``embeddinggemma``): el texto no sale del equipo.
- Qdrant guarda el índice en ``data/gold/qdrant`` para no recalcular los embeddings en cada
  arranque. El nombre de la colección lleva una huella del contenido: si ``sb process`` cambia
  los chunks, se crea una colección nueva y la vieja se borra.
"""

import atexit
import hashlib
import shutil
import tempfile
import uuid
from collections.abc import Iterable, Sequence
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from sb_asistente.config import EMBEDDING_MODEL, QDRANT_COLLECTION, RAG_TOP_K

# Espacio de nombres fijo para derivar ids estables de Qdrant a partir de ``chunk_id``.
_ID_NAMESPACE = uuid.UUID("6f1c2a7e-3b7d-4a55-9a51-5b0c7f1e2d10")


class EmbeddingSetupError(RuntimeError):
    """Ollama no responde o el modelo de embeddings no está descargado."""


def build_embeddings(model: str = EMBEDDING_MODEL) -> Embeddings:
    """Embeddings locales con Ollama (importación diferida)."""
    from langchain_ollama import OllamaEmbeddings

    return OllamaEmbeddings(model=model)


# Qdrant local bloquea su carpeta para UN cliente: se reutiliza el mismo dentro del proceso
# (en Streamlit, los modos «rag» y «agente» comparten el índice).
_CLIENTS: dict[Path, QdrantClient] = {}


def _open_on_disk(path: Path) -> QdrantClient:
    client = QdrantClient(path=str(path))
    # Cerrar antes del apagado del intérprete: en __del__ el candado del archivo falla en Windows.
    atexit.register(client.close)
    return client


def open_client(path: Path | None = None) -> QdrantClient:
    """Cliente Qdrant local: en disco si se da ``path``; si no, en memoria (pruebas).

    Si otro proceso tiene la carpeta tomada (p. ej., la app de Streamlit abierta mientras se usa la
    CLI), se abre una copia temporal del índice: las búsquedas funcionan igual y el original no se
    toca.
    """
    if path is None:
        return QdrantClient(":memory:")
    key = path.resolve()
    if key not in _CLIENTS:
        key.mkdir(parents=True, exist_ok=True)
        try:
            _CLIENTS[key] = _open_on_disk(key)
        except RuntimeError as exc:
            if "already accessed" not in str(exc):
                raise
            copy = Path(tempfile.mkdtemp(prefix="sb_qdrant_")) / key.name
            shutil.copytree(key, copy, ignore=shutil.ignore_patterns(".lock"))
            atexit.register(shutil.rmtree, copy.parent, True)
            _CLIENTS[key] = _open_on_disk(copy)
    return _CLIENTS[key]


def close_clients() -> None:
    """Cierra los clientes Qdrant en disco abiertos por este proceso y libera sus carpetas."""
    for client in _CLIENTS.values():
        client.close()
    _CLIENTS.clear()


def chunks_to_documents(chunks: Iterable[dict[str, object]]) -> list[Document]:
    """Convierte las filas de ``chunks.jsonl`` en ``Document`` con sus metadatos de citación."""
    return [
        Document(
            page_content=str(chunk["text"]),
            metadata={
                "chunk_id": chunk["chunk_id"],
                "url": chunk["url"],
                "title": chunk["title"],
                "section": chunk.get("section", ""),
                "breadcrumb": chunk.get("breadcrumb", ""),
            },
        )
        for chunk in chunks
    ]


def fingerprint(chunks: Sequence[dict[str, object]]) -> str:
    """Huella corta del contenido de los chunks (cambia si cambia cualquier texto o id)."""
    digest = hashlib.sha256()
    for chunk in chunks:
        digest.update(f"{chunk['chunk_id']}\x00{chunk['text']}\x00".encode())
    return digest.hexdigest()[:12]


def build_index(
    chunks: Sequence[dict[str, object]],
    embeddings: Embeddings,
    client: QdrantClient,
    collection: str = QDRANT_COLLECTION,
) -> QdrantVectorStore:
    """Devuelve el índice de los chunks; solo calcula embeddings si el contenido cambió.

    Raises:
        ValueError: si no hay chunks.
        EmbeddingSetupError: si Ollama no está disponible para calcular los embeddings.

    """
    if not chunks:
        raise ValueError("No hay chunks para indexar. Ejecute primero: uv run sb process")
    name = f"{collection}_{fingerprint(chunks)}"
    if not client.collection_exists(name):
        for old in client.get_collections().collections:
            if old.name.startswith(f"{collection}_"):
                client.delete_collection(old.name)
        try:
            size = len(embeddings.embed_query("seguro"))
            client.create_collection(name, vectors_config=VectorParams(size=size, distance=Distance.COSINE))
            store = QdrantVectorStore(client=client, collection_name=name, embedding=embeddings)
            ids = [str(uuid.uuid5(_ID_NAMESPACE, str(c["chunk_id"]))) for c in chunks]
            store.add_documents(chunks_to_documents(chunks), ids=ids)
        except Exception as exc:  # noqa: BLE001 - ollama.ResponseError, httpx.ConnectError, etc.
            if client.collection_exists(name):
                client.delete_collection(name)  # no dejar un índice a medias
            raise EmbeddingSetupError(
                f"No se pudieron calcular los embeddings con Ollama ({exc}). Inicie Ollama y "
                f"descargue el modelo: ollama pull {EMBEDDING_MODEL}"
            ) from exc
        return store
    return QdrantVectorStore(client=client, collection_name=name, embedding=embeddings)


def format_docs(docs: Iterable[Document]) -> str:
    """Bloques ``### título / Fuente: URL / texto``, el mismo formato del conocimiento consolidado."""
    return "\n".join(
        f"### {doc.metadata.get('title', '')}\nFuente: {doc.metadata.get('url', '')}\n\n{doc.page_content}\n"
        for doc in docs
    )


def search(store: QdrantVectorStore, question: str, k: int = RAG_TOP_K) -> list[Document]:
    """Los ``k`` fragmentos más parecidos a la pregunta (similitud coseno)."""
    if k <= 0:
        raise ValueError("k debe ser positivo.")
    return store.similarity_search(question, k=k)

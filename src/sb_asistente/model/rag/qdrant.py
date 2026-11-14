"""Adaptador de Qdrant para el recuperador híbrido del agente.

``RecuperadorHibrido`` solo necesita ``similarity_search(query, k, filter)`` (protocolo
``BuscadorVectorial``). Este adaptador lo implementa sobre ``QdrantVectorStore`` y traduce el
filtro simple ``{"section": "movilidad"}`` a un filtro de *payload* de Qdrant
(``metadata.section == "movilidad"``), que se aplica **durante** la búsqueda ANN (HNSW) y no
después: así el top-k sale completo aunque la sección tenga pocos fragmentos.
"""

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import models


def filtro_payload(filtro: dict[str, str] | None) -> models.Filter | None:
    """``{"campo": valor}`` → condiciones ``metadata.campo == valor`` (todas deben cumplirse)."""
    if not filtro:
        return None
    return models.Filter(
        must=[
            models.FieldCondition(key=f"metadata.{campo}", match=models.MatchValue(value=valor))
            for campo, valor in filtro.items()
        ]
    )


class BuscadorQdrant:
    """Búsqueda vectorial en Qdrant con la interfaz que usa el recuperador híbrido."""

    def __init__(self, store: QdrantVectorStore) -> None:
        """Recibe el índice ya abierto (``vector_store.build_index``)."""
        self.store = store

    def similarity_search(self, query: str, k: int = 4, filter: dict | None = None) -> list[Document]:  # noqa: A002
        """Top-k por similitud coseno, filtrado por *payload* si se pide."""
        return self.store.similarity_search(query, k=k, filter=filtro_payload(filter))

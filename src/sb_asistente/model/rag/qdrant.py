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
    """Búsqueda vectorial en Qdrant con la interfaz que usa el recuperador híbrido.

    ``extra`` es una colección aparte (en memoria) para el corpus de prueba del blindaje: así el
    documento con la instrucción escondida compite en el ranking vectorial sin tocar el índice
    persistido que usa el modo «rag».
    """

    def __init__(self, store: QdrantVectorStore, extra: QdrantVectorStore | None = None) -> None:
        """Recibe el índice ya abierto (``vector_store.build_index``) y, opcionalmente, uno extra."""
        self.store = store
        self.extra = extra

    def similarity_search(self, query: str, k: int = 4, filter: dict | None = None) -> list[Document]:  # noqa: A002
        """Top-k por similitud coseno (de ambas colecciones), filtrado por *payload* si se pide."""
        qfiltro = filtro_payload(filter)
        if self.extra is None:
            return self.store.similarity_search(query, k=k, filter=qfiltro)
        candidatos = self.store.similarity_search_with_score(query, k=k, filter=qfiltro)
        candidatos += self.extra.similarity_search_with_score(query, k=k, filter=qfiltro)
        candidatos.sort(key=lambda par: par[1], reverse=True)
        return [doc for doc, _ in candidatos[:k]]

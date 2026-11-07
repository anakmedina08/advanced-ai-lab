"""Recuperación híbrida: BM25 (palabras exactas) + vectores (significado), fusionados con RRF.

BM25 encuentra términos literales como «#322» o «SOAT»; los embeddings encuentran paráfrasis
(«me chocaron» → «siniestro de autos»). Reciprocal Rank Fusion combina ambos rankings sin
calibrar puntajes: cada fragmento suma ``1 / (RRF_K + posición)`` en cada lista.
"""

from dataclasses import dataclass
from typing import Protocol

from rank_bm25 import BM25Okapi

from sb_asistente.config import RAG_K, RRF_K
from sb_asistente.model.llm.retrieval import normalize_words


@dataclass(frozen=True, slots=True)
class Fragmento:
    """Un pasaje recuperado con su fuente y de dónde salió."""

    chunk_id: str
    url: str
    titulo: str
    seccion: str
    texto: str
    puntaje: float
    origen: tuple[str, ...]  # ("bm25",), ("vector",) o ambos


class BuscadorVectorial(Protocol):
    """Lo mínimo que se usa de Chroma (permite dobles en pruebas)."""

    def similarity_search(self, query: str, k: int = 4, filter: dict | None = None) -> list: ...  # noqa: A002, D102


# Palabras presentes en casi todo el corpus o en casi toda pregunta: no distinguen fragmentos.
# Elegidas midiendo hit@k en el banco real (sb rag evaluar): quitar también «seguro(s)» empeora.
PALABRAS_COMUNES = frozenset({"bolivar", "numero"})


def _filtrar(palabras: list[str]) -> list[str]:
    return [p for p in palabras if p not in PALABRAS_COMUNES]


def _tokens(chunk: dict[str, object]) -> list[str]:
    return _filtrar(normalize_words(f"{chunk['title']} {chunk.get('breadcrumb', '')} {chunk['text']}"))


class RecuperadorHibrido:
    """BM25 en memoria sobre los fragmentos + búsqueda vectorial en Chroma."""

    def __init__(self, chunks: list[dict[str, object]], vectorial: BuscadorVectorial | None = None) -> None:
        """Construye el índice BM25; ``vectorial`` es opcional (sin él, solo BM25)."""
        if not chunks:
            raise ValueError("No hay fragmentos: ejecute `make data` o `make process`.")
        self.chunks = {str(c["chunk_id"]): c for c in chunks}
        self._ids = list(self.chunks)
        tokens = [_tokens(self.chunks[i]) for i in self._ids]
        self._vocab = [set(t) for t in tokens]
        self._bm25 = BM25Okapi(tokens)
        self.vectorial = vectorial

    def _ranking_bm25(self, consulta: str, n: int, seccion: str | None) -> list[str]:
        palabras = _filtrar(normalize_words(consulta))
        if not palabras:
            return []
        puntajes = self._bm25.get_scores(palabras)
        consulta_set = set(palabras)
        # Se filtra por coincidencia de términos y no por puntaje > 0: en corpus pequeños el IDF de
        # BM25Okapi puede ser 0 para un término presente en la mitad de los documentos.
        coincidencias = [len(consulta_set & v) for v in self._vocab]
        orden = sorted(range(len(self._ids)), key=lambda i: (puntajes[i], coincidencias[i]), reverse=True)
        ids = [self._ids[i] for i in orden if coincidencias[i] > 0]
        if seccion:
            ids = [i for i in ids if self.chunks[i].get("section") == seccion]
        return ids[:n]

    def _ranking_vectorial(self, consulta: str, n: int, seccion: str | None) -> list[str]:
        if self.vectorial is None:
            return []
        filtro = {"section": seccion} if seccion else None
        docs = self.vectorial.similarity_search(consulta, k=n, filter=filtro)
        return [
            str(d.metadata.get("chunk_id") or d.id)
            for d in docs
            if (d.metadata.get("chunk_id") or d.id) in self.chunks
        ]

    def buscar(self, consulta: str, k: int = RAG_K, seccion: str | None = None) -> list[Fragmento]:
        """Top-k fusionado con RRF; ``seccion`` restringe a una sección del sitio."""
        if not consulta.strip():
            raise ValueError("La consulta está vacía.")
        if not 1 <= k <= 20:
            raise ValueError("k debe estar entre 1 y 20.")
        candidatos = 4 * k
        rankings = {
            "bm25": self._ranking_bm25(consulta, candidatos, seccion),
            "vector": self._ranking_vectorial(consulta, candidatos, seccion),
        }
        puntaje: dict[str, float] = {}
        origen: dict[str, list[str]] = {}
        for nombre, ids in rankings.items():
            for posicion, chunk_id in enumerate(ids, start=1):
                puntaje[chunk_id] = puntaje.get(chunk_id, 0.0) + 1.0 / (RRF_K + posicion)
                origen.setdefault(chunk_id, []).append(nombre)
        mejores = sorted(puntaje, key=lambda i: puntaje[i], reverse=True)[:k]
        return [
            Fragmento(
                chunk_id=i,
                url=str(self.chunks[i]["url"]),
                titulo=str(self.chunks[i]["title"]),
                seccion=str(self.chunks[i].get("section", "")),
                texto=str(self.chunks[i]["text"]),
                puntaje=round(puntaje[i], 5),
                origen=tuple(origen[i]),
            )
            for i in mejores
        ]


def como_contexto(fragmentos: list[Fragmento]) -> str:
    """Pasajes con su fuente, listos para el prompt o para la respuesta de una tool."""
    return "\n\n---\n\n".join(f"[{f.titulo}]\nFuente: {f.url}\n{f.texto}" for f in fragmentos)

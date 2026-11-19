"""Recuperación híbrida: BM25 (palabras exactas) + vectores (significado), fusionados con RRF.

BM25 encuentra términos literales como «#322» o «SOAT»; los embeddings encuentran paráfrasis
(«me chocaron» → «siniestro de autos»). Reciprocal Rank Fusion combina ambos rankings sin
calibrar puntajes: cada fragmento suma ``1 / (RRF_K + posición)`` en cada lista.
"""

from dataclasses import dataclass
from typing import Protocol

from rank_bm25 import BM25Okapi

from sb_asistente.config import RAG_CANDIDATOS_POR_K, RAG_K, RAG_K_MAX, RRF_DECIMALES, RRF_K
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
    aseguradora: str = ""  # id del registro en el corpus de mercado (SPEC-069); vacío en el principal


class BuscadorVectorial(Protocol):
    """Lo mínimo que se usa de la base vectorial (Qdrant o Chroma; permite dobles en pruebas)."""

    def similarity_search(self, query: str, k: int = RAG_K, filter: dict | None = None) -> list:  # noqa: A002
        """Los ``k`` documentos más parecidos a la consulta, con un filtro de metadatos opcional."""
        ...


# Palabras presentes en casi todo el corpus o en casi toda pregunta: no distinguen fragmentos.
# Elegidas midiendo hit@k en el banco real (sb rag evaluar): quitar también «seguro(s)» empeora.
PALABRAS_COMUNES = frozenset({"bolivar", "numero"})


def _filtrar(palabras: list[str]) -> list[str]:
    return [p for p in palabras if p not in PALABRAS_COMUNES]


def _tokens(chunk: dict[str, object]) -> list[str]:
    return _filtrar(normalize_words(f"{chunk['title']} {chunk.get('breadcrumb', '')} {chunk['text']}"))


class CorpusVacioError(FileNotFoundError, ValueError):
    """No hay fragmentos: falta generar el corpus (la API lo reporta como «datos no listos»)."""


class RecuperadorHibrido:
    """BM25 en memoria sobre los fragmentos + búsqueda vectorial (Qdrant o Chroma)."""

    def __init__(self, chunks: list[dict[str, object]], vectorial: BuscadorVectorial | None = None) -> None:
        """Construye el índice BM25; ``vectorial`` es opcional (sin él, solo BM25)."""
        if not chunks:
            raise CorpusVacioError("No hay fragmentos: ejecute `make data` o `make process`.")
        self.chunks = {str(c["chunk_id"]): c for c in chunks}
        self._ids = list(self.chunks)
        tokens = [_tokens(self.chunks[i]) for i in self._ids]
        self._vocab = [set(t) for t in tokens]
        self._bm25 = BM25Okapi(tokens)
        self.vectorial = vectorial

    def _cumple(self, chunk_id: str, seccion: str | None, aseguradora: str | None) -> bool:
        chunk = self.chunks[chunk_id]
        return (not seccion or chunk.get("section") == seccion) and (
            not aseguradora or chunk.get("aseguradora") == aseguradora
        )

    def _ranking_bm25(
        self, consulta: str, n: int, seccion: str | None, aseguradora: str | None = None
    ) -> list[str]:
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
        if seccion or aseguradora:
            ids = [i for i in ids if self._cumple(i, seccion, aseguradora)]
        return ids[:n]

    def _ranking_vectorial(
        self, consulta: str, n: int, seccion: str | None, aseguradora: str | None = None
    ) -> list[str]:
        if self.vectorial is None:
            return []
        filtro = {"section": seccion} if seccion else None
        if aseguradora:  # el índice vectorial es solo del corpus principal: se filtra después
            filtro = None
        try:
            docs = self.vectorial.similarity_search(consulta, k=n, filter=filtro)
        except Exception:  # noqa: BLE001 - p. ej. Ollama apagado: se sigue solo con BM25
            return []
        ids = [
            str(d.metadata.get("chunk_id") or d.id)
            for d in docs
            if (d.metadata.get("chunk_id") or d.id) in self.chunks
        ]
        return [i for i in ids if self._cumple(i, seccion, aseguradora)] if aseguradora else ids

    def buscar(
        self, consulta: str, k: int = RAG_K, seccion: str | None = None, aseguradora: str | None = None
    ) -> list[Fragmento]:
        """Top-k fusionado con RRF; ``seccion`` y ``aseguradora`` restringen los candidatos.

        ``aseguradora`` (SPEC-069) es opcional: sin él, el ranking es el mismo de antes. Evidencia
        (AGENTS.md, ``uv run sb rag evaluar``), antes y después del cambio, modo BM25:
        hit@3 = 13/21 y hit@6 = 16/21 en ambos casos (registrado en ADR-028).
        """
        if not consulta.strip():
            raise ValueError("La consulta está vacía.")
        if not 1 <= k <= RAG_K_MAX:
            raise ValueError(f"k debe estar entre 1 y {RAG_K_MAX}.")
        candidatos = RAG_CANDIDATOS_POR_K * k
        rankings = {
            "bm25": self._ranking_bm25(consulta, candidatos, seccion, aseguradora),
            "vector": self._ranking_vectorial(consulta, candidatos, seccion, aseguradora),
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
                puntaje=round(puntaje[i], RRF_DECIMALES),
                origen=tuple(origen[i]),
                aseguradora=str(self.chunks[i].get("aseguradora", "")),
            )
            for i in mejores
        ]


def como_contexto(fragmentos: list[Fragmento]) -> str:
    """Pasajes con su fuente, listos para el prompt o para la respuesta de una tool."""
    return "\n\n---\n\n".join(f"[{f.titulo}]\nFuente: {f.url}\n{f.texto}" for f in fragmentos)

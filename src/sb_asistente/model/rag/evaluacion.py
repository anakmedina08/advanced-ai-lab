"""Evaluación de la recuperación con el banco de preguntas: hit@k, recall@k y nDCG@k.

Etiquetado: un fragmento es **relevante** para una pregunta si contiene TODAS sus palabras clave
(los datos que la respuesta debe traer). Así cada una de las preguntas en alcance del banco queda
etiquetada sin anotación manual y con un criterio verificable.

- **hit@k**: la pregunta acierta si algún fragmento del top-k es relevante (el dato llega al modelo).
- **recall@k** (acotado): relevantes en el top-k / min(relevantes en el corpus, k).
- **nDCG@k**: premia que los relevantes estén arriba (ganancia binaria, descuento log2).

Las preguntas fuera de alcance no cuentan: para ellas no hay fragmento correcto.
"""

import math
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from sb_asistente.model.evaluation import EvalQuestion
from sb_asistente.model.rag.hibrido import RecuperadorHibrido


def _norm(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


@dataclass(frozen=True, slots=True)
class ResultadoHit:
    """hit@k sobre el banco."""

    k: int
    aciertos: int
    total: int
    fallos: tuple[str, ...]

    @property
    def tasa(self) -> float:
        """Proporción de aciertos."""
        return self.aciertos / self.total if self.total else 0.0


def es_relevante(texto: str, palabras_clave: Iterable[str]) -> bool:
    """El texto contiene todas las palabras clave (sin tildes ni mayúsculas)."""
    normal = _norm(texto)
    return all(_norm(p) in normal for p in palabras_clave)


def recall_at_k(relevancias: Sequence[int], relevantes_en_corpus: int, k: int) -> float:
    """Relevantes recuperados en el top-k sobre ``min(relevantes del corpus, k)``."""
    if relevantes_en_corpus <= 0:
        return 0.0
    return min(sum(relevancias[:k]), relevantes_en_corpus) / min(relevantes_en_corpus, k)


def ndcg_at_k(relevancias: Sequence[int], relevantes_en_corpus: int, k: int) -> float:
    """nDCG@k con ganancia binaria: DCG del ranking / DCG ideal (todos los relevantes arriba)."""
    dcg = sum(r / math.log2(i + 2) for i, r in enumerate(relevancias[:k]))
    ideal = sum(1 / math.log2(i + 2) for i in range(min(relevantes_en_corpus, k)))
    return dcg / ideal if ideal else 0.0


@dataclass(frozen=True, slots=True)
class ResultadoRanking:
    """recall@k y nDCG@k promedio sobre el banco."""

    k: int
    recall: float
    ndcg: float
    total: int


def evaluar_ranking(
    recuperador: object, preguntas: list[EvalQuestion], corpus: Sequence[dict[str, object]], k: int = 10
) -> ResultadoRanking:
    """Promedia recall@k y nDCG@k; ``recuperador.buscar(consulta, k=k)`` devuelve fragmentos."""
    en_alcance = [q for q in preguntas if not q.fuera_de_alcance]
    recalls, ndcgs = [], []
    for q in en_alcance:
        en_corpus = sum(es_relevante(f"{c['title']} {c['text']}", q.palabras_clave) for c in corpus)
        fragmentos = recuperador.buscar(q.pregunta, k=k)[:k]
        relevancias = [int(es_relevante(f"{f.titulo} {f.texto}", q.palabras_clave)) for f in fragmentos]
        recalls.append(recall_at_k(relevancias, max(en_corpus, sum(relevancias)), k))
        ndcgs.append(ndcg_at_k(relevancias, max(en_corpus, sum(relevancias)), k))
    total = len(en_alcance)
    return ResultadoRanking(
        k, sum(recalls) / total if total else 0.0, sum(ndcgs) / total if total else 0.0, total
    )


def hit_at_k(recuperador: RecuperadorHibrido, preguntas: list[EvalQuestion], k: int) -> ResultadoHit:
    """Cuenta en cuántas preguntas en alcance los fragmentos traen todas las palabras clave."""
    en_alcance = [q for q in preguntas if not q.fuera_de_alcance]
    fallos = []
    for q in en_alcance:
        texto = _norm(" ".join(f"{f.titulo} {f.texto}" for f in recuperador.buscar(q.pregunta, k=k)))
        if not all(_norm(p) in texto for p in q.palabras_clave):
            fallos.append(q.id)
    return ResultadoHit(k, len(en_alcance) - len(fallos), len(en_alcance), tuple(fallos))

"""Métricas de ranking para recomendación con un ítem retenido por cliente."""

import math
from collections.abc import Mapping, Sequence


def rango(recomendados: Sequence[str], objetivo: str) -> int | None:
    """Posición (1-indexada) del producto objetivo en la lista, o None si no aparece."""
    try:
        return list(recomendados).index(objetivo) + 1
    except ValueError:
        return None


def recall_at_k(recomendados: Sequence[str], objetivo: str, k: int) -> float:
    """1 si el producto retenido está en el top-k (con un solo relevante = hit rate)."""
    if k <= 0:
        raise ValueError("k debe ser positivo.")
    posicion = rango(recomendados[:k], objetivo)
    return 1.0 if posicion is not None else 0.0


def ndcg_at_k(recomendados: Sequence[str], objetivo: str, k: int) -> float:
    """NDCG con un único relevante: 1/log2(posición+1) si está en el top-k."""
    if k <= 0:
        raise ValueError("k debe ser positivo.")
    posicion = rango(recomendados[:k], objetivo)
    return 0.0 if posicion is None else 1.0 / math.log2(posicion + 1)


def evaluar(recomendaciones: Mapping[str, Sequence[str]], objetivos: Mapping[str, str], k: int = 5) -> dict:
    """Promedia Recall@k y NDCG@k sobre los clientes con producto retenido."""
    clientes = [c for c in objetivos if c in recomendaciones]
    if not clientes:
        raise ValueError("No hay clientes en común entre recomendaciones y objetivos.")
    recall = sum(recall_at_k(recomendaciones[c], objetivos[c], k) for c in clientes) / len(clientes)
    ndcg = sum(ndcg_at_k(recomendaciones[c], objetivos[c], k) for c in clientes) / len(clientes)
    return {"clientes": len(clientes), f"recall@{k}": round(recall, 4), f"ndcg@{k}": round(ndcg, 4)}

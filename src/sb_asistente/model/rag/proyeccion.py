"""Proyección 2D de embeddings para diagnosticar el retrieval (SPEC-084, ítem 2.3 de la rúbrica).

Sin red ni modelo: recibe vectores ya calculados. El script ``scripts/proyectar_embeddings.py`` los
lee del índice Qdrant y dibuja el mapa.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

import numpy as np
from numpy.typing import NDArray

Metodo = Literal["tsne", "pca"]


def normalizar(vectores: NDArray[np.floating]) -> NDArray[np.float64]:
    """Devuelve los vectores con norma 1, para que el producto punto sea la similitud coseno."""
    matriz = np.asarray(vectores, dtype=np.float64)
    normas = np.linalg.norm(matriz, axis=-1, keepdims=True)
    return matriz / np.where(normas == 0, 1.0, normas)


def vecinos(consulta: NDArray[np.floating], vectores: NDArray[np.floating], k: int) -> list[int]:
    """Índices de los ``k`` vectores más parecidos a la consulta por coseno, del mejor al peor."""
    similitudes = normalizar(vectores) @ normalizar(consulta)
    return [int(i) for i in np.argsort(-similitudes)[:k]]


def proyectar(
    vectores: NDArray[np.floating], metodo: Metodo = "tsne", semilla: int = 42
) -> NDArray[np.float64]:
    """Proyecta a 2D con t-SNE (métrica coseno) o PCA. Mismo resultado para la misma semilla."""
    matriz = normalizar(vectores)
    if metodo == "pca":
        from sklearn.decomposition import PCA

        return np.asarray(PCA(n_components=2, random_state=semilla).fit_transform(matriz))
    from sklearn.manifold import TSNE

    perplejidad = float(min(30, max(2, (len(matriz) - 1) // 3)))
    tsne = TSNE(n_components=2, metric="cosine", perplexity=perplejidad, init="pca", random_state=semilla)
    return np.asarray(tsne.fit_transform(matriz))


def separacion(vectores: NDArray[np.floating], etiquetas: Sequence[str]) -> float | None:
    """*Silhouette* por coseno en el espacio original: 1 = grupos bien separados, 0 = mezclados.

    ``None`` si hay menos de dos grupos (la métrica no está definida).
    """
    if len(set(etiquetas)) < 2 or len(etiquetas) <= len(set(etiquetas)):
        return None
    from sklearn.metrics import silhouette_score

    return float(silhouette_score(normalizar(vectores), list(etiquetas), metric="cosine"))

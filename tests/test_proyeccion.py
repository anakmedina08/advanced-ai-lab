"""Pruebas de la proyección 2D de embeddings (SPEC-084). Datos sintéticos, sin red."""

from __future__ import annotations

import numpy as np
import pytest

from sb_asistente.model.rag.proyeccion import normalizar, proyectar, separacion, vecinos


def _dos_grupos(n: int = 20, dim: int = 16) -> tuple[np.ndarray, list[str]]:
    rng = np.random.default_rng(0)
    centro_a = np.zeros(dim)
    centro_a[0] = 1.0
    centro_b = np.zeros(dim)
    centro_b[1] = 1.0
    a = centro_a + rng.normal(0, 0.05, (n, dim))
    b = centro_b + rng.normal(0, 0.05, (n, dim))
    return np.vstack([a, b]), ["a"] * n + ["b"] * n


def test_normalizar_deja_norma_uno_y_tolera_cero() -> None:
    # Arrange
    vectores = np.array([[3.0, 4.0], [0.0, 0.0]])

    # Act
    unitarios = normalizar(vectores)

    # Assert
    assert np.allclose(np.linalg.norm(unitarios[0]), 1.0)
    assert np.allclose(unitarios[1], 0.0)


def test_vecinos_pone_primero_el_vector_identico() -> None:
    # Arrange (AC2)
    vectores, _ = _dos_grupos()

    # Act
    orden = vecinos(vectores[7], vectores, k=5)

    # Assert
    assert orden[0] == 7
    assert len(orden) == 5


def test_separacion_alta_para_grupos_distintos_y_none_con_un_grupo() -> None:
    # Arrange (AC1)
    vectores, etiquetas = _dos_grupos()

    # Act
    sil = separacion(vectores, etiquetas)

    # Assert
    assert sil is not None and sil > 0.8
    assert separacion(vectores, ["a"] * len(etiquetas)) is None


@pytest.mark.parametrize("metodo", ["tsne", "pca"])
def test_proyectar_da_2d_y_mantiene_los_grupos_juntos(metodo: str) -> None:
    # Arrange (AC1)
    vectores, etiquetas = _dos_grupos()

    # Act
    plano = proyectar(vectores, metodo=metodo)  # type: ignore[arg-type]

    # Assert
    assert plano.shape == (len(vectores), 2)
    grupo_a, grupo_b = plano[: len(vectores) // 2], plano[len(vectores) // 2 :]
    dentro = np.linalg.norm(grupo_a - grupo_a.mean(0), axis=1).mean()
    entre = np.linalg.norm(grupo_a.mean(0) - grupo_b.mean(0))
    assert entre > dentro
    assert etiquetas[0] == "a"


def test_proyectar_es_reproducible_con_la_misma_semilla() -> None:
    # Arrange
    vectores, _ = _dos_grupos(n=10)

    # Act
    uno = proyectar(vectores, semilla=7)
    dos = proyectar(vectores, semilla=7)

    # Assert
    assert np.allclose(uno, dos)

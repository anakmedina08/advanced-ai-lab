"""Pruebas de recall@k y nDCG@k del retrieval (casos calculados a mano)."""

import math

import pytest

from sb_asistente.model.evaluation import EvalQuestion
from sb_asistente.model.rag.evaluacion import es_relevante, evaluar_ranking, ndcg_at_k, recall_at_k
from sb_asistente.model.rag.hibrido import Fragmento


def test_ndcg_con_el_unico_relevante_en_la_posicion_2():
    # Act / Assert
    assert ndcg_at_k([0, 1, 0], relevantes_en_corpus=1, k=10) == pytest.approx(1 / math.log2(3))


def test_ndcg_perfecto_si_los_relevantes_van_primero():
    # Assert
    assert ndcg_at_k([1, 1, 0, 0], relevantes_en_corpus=2, k=10) == pytest.approx(1.0)


def test_recall_acotado_a_k():
    # Assert
    assert recall_at_k([1, 0, 1], relevantes_en_corpus=4, k=3) == pytest.approx(2 / 3)
    assert recall_at_k([1, 0, 0], relevantes_en_corpus=1, k=10) == 1.0
    assert recall_at_k([0, 0], relevantes_en_corpus=0, k=10) == 0.0


def test_relevante_si_trae_todas_las_palabras_clave_sin_tildes():
    # Assert
    assert es_relevante("Línea #322 y WhatsApp 322 332 2322", ["#322", "322 332 2322"])
    assert not es_relevante("Línea #322", ["#322", "322 332 2322"])


class RecuperadorFijo:
    def __init__(self, textos):
        self.textos = textos

    def buscar(self, consulta, k):
        return [Fragmento(str(i), "u", "t", "s", t, 0.0, ()) for i, t in enumerate(self.textos)][:k]


def test_evaluar_ranking_promedia_sobre_las_preguntas_en_alcance():
    # Arrange
    preguntas = [
        EvalQuestion("A", "c", "¿WhatsApp?", ["322 332 2322"]),
        EvalQuestion("B", "c", "¿SOAT?", ["no existe"], fuera_de_alcance=True),
    ]
    corpus = [{"title": "Canales", "text": "WhatsApp 322 332 2322"}]
    # Act
    r = evaluar_ranking(RecuperadorFijo(["otra cosa", "WhatsApp 322 332 2322"]), preguntas, corpus, k=10)
    # Assert
    assert r.total == 1
    assert r.recall == 1.0
    assert r.ndcg == pytest.approx(1 / math.log2(3))

"""Pruebas de los endpoints del panel del equipo (corpus, temas, evaluación y experimentos)."""

from fastapi.testclient import TestClient

from sb_asistente.controller import assistant, pipeline
from sb_asistente.view.api import app

cliente = TestClient(app)


def test_temas_de_las_guias():
    # Act
    r = cliente.get("/temas")
    # Assert
    assert r.status_code == 200 and r.json() == list(assistant.TOPICS)


def test_corpus_con_su_contrato(monkeypatch):
    # Arrange
    fila = {
        "url": "u",
        "titulo": "t",
        "seccion": "s",
        "fecha_captura": "2026-10-26",
        "sha256": "abc",
        "tokens": 10,
    }
    monkeypatch.setattr(pipeline, "corpus_table", lambda: [fila])
    # Act
    r = cliente.get("/pipeline/corpus")
    # Assert
    assert r.json() == [fila]


def test_resumen_de_la_evaluacion(monkeypatch):
    # Arrange
    corrida = {
        "modelo": "anthropic",
        "version": "v3",
        "preguntas": 25,
        "keyword_hit_promedio": 0.97,
        "tasa_cita_fuente": 1.0,
        "tasa_fallback_correcto": 0.96,
        "latencia_promedio_s": 1.6,
    }
    monkeypatch.setattr(assistant, "evaluation_summary", lambda: [corrida])
    # Act
    r = cliente.get("/evaluacion")
    # Assert
    assert r.json()[0]["tasa_cita_fuente"] == 1.0


def test_detalle_inexistente_responde_404(monkeypatch):
    # Arrange
    def falta(modelo, version):
        raise FileNotFoundError

    monkeypatch.setattr(assistant, "evaluation_detail", falta)
    # Act
    r = cliente.get("/evaluacion/anthropic/v9")
    # Assert
    assert r.status_code == 404


def test_detalle_valida_la_version():
    # Act
    r = cliente.get("/evaluacion/anthropic/../v3")
    # Assert
    assert r.status_code in {404, 422}


def test_experimentos_sin_mlflow_lo_explica():
    # Act (las pruebas corren con SB_MLFLOW=0)
    r = cliente.get("/experimentos")
    # Assert
    assert r.status_code == 200
    assert r.json()["activa"] is False and r.json()["url_ui"].endswith(":5050")
    assert "vision-yolo" in r.json()["nombres"]

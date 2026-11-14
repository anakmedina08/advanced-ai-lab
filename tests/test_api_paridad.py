"""Pruebas de la paridad con la versión Streamlit: modos en /preguntas, /sistema y acciones del pipeline."""

from fastapi.testclient import TestClient

from sb_asistente.controller import pipeline
from sb_asistente.model.llm.service import Answer
from sb_asistente.view import dependencias
from sb_asistente.view.api import app

cliente = TestClient(app)


def test_preguntas_acepta_los_cuatro_modos():
    # Arrange
    vistos = []
    app.dependency_overrides[dependencias.get_responder] = lambda: (
        lambda p, v, m, prov: (
            vistos.append(m) or Answer("Ver https://www.segurosbolivar.com/soat", "qa", v, 0.1, 10)
        )
    )
    try:
        # Act
        estados = [
            cliente.post("/preguntas", json={"pregunta": "¿Qué cubre el SOAT?", "modo": m}).status_code
            for m in ("completo", "reducido", "rag", "agente")
        ]
    finally:
        app.dependency_overrides.clear()
    # Assert
    assert estados == [200, 200, 200, 200]
    assert vistos == ["completo", "reducido", "rag", "agente"]


def test_modo_desconocido_responde_422():
    # Act
    r = cliente.post("/preguntas", json={"pregunta": "¿Qué cubre el SOAT?", "modo": "magia"})
    # Assert
    assert r.status_code == 422


def test_sistema_trae_insignias_y_metricas():
    # Act
    r = cliente.get("/sistema")
    # Assert
    assert r.status_code == 200
    assert {"base_lista", "vision_instalada", "clave_anthropic", "paginas", "fragmentos"} <= set(r.json())


def test_reprocesar_resume_el_pipeline(monkeypatch):
    # Arrange
    monkeypatch.setattr(
        pipeline, "process", lambda: {"documentos": 79, "chunks": 413, "descartadas_duplicadas": ["a"]}
    )
    # Act
    r = cliente.post("/pipeline/procesar")
    # Assert
    assert r.json() == {"documentos": 79, "chunks": 413, "duplicadas_descartadas": 1}


def test_descubrir_sin_red_responde_503(monkeypatch):
    # Arrange
    def sin_red(_sesion):
        raise ConnectionError("sin red")

    monkeypatch.setattr(pipeline, "discover", sin_red)
    # Act
    r = cliente.post("/pipeline/descubrir")
    # Assert
    assert r.status_code == 503 and "sin red" in r.json()["detalle"]

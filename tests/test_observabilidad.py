"""Pruebas del middleware de observabilidad: cabeceras y log JSON sin cuerpo."""

import json
import logging

from fastapi.testclient import TestClient

from sb_asistente.model.llm.service import Answer
from sb_asistente.view import dependencias
from sb_asistente.view.api import app
from sb_asistente.view.observabilidad import FormatoJSON


def test_respuesta_trae_request_id_y_latencia():
    # Act
    r = TestClient(app).get("/health")
    # Assert
    assert r.headers["X-Request-ID"]
    assert float(r.headers["X-Process-Time-ms"]) >= 0


def test_respeta_el_request_id_recibido():
    # Act
    r = TestClient(app).get("/health", headers={"X-Request-ID": "abc123"})
    # Assert
    assert r.headers["X-Request-ID"] == "abc123"


def test_log_de_la_peticion_no_incluye_el_cuerpo(caplog):
    # Arrange: Q&A simulado para no llamar al LLM real (sin red ni gasto de tokens)
    caplog.set_level(logging.INFO, logger="sb.api")
    app.dependency_overrides[dependencias.get_chat_qa] = lambda: (
        lambda proveedor: lambda pregunta, skill: Answer("Respuesta simulada.", "qa", "v3", 0.0, 10)
    )
    # Act
    try:
        TestClient(app).post("/chat", json={"mensaje": "texto privado del usuario"})
    finally:
        app.dependency_overrides.pop(dependencias.get_chat_qa, None)
    # Assert
    lineas = [r for r in caplog.records if r.getMessage() == "peticion"]
    assert lineas and lineas[-1].datos["ruta"] == "/chat"
    assert all("texto privado" not in FormatoJSON().format(r) for r in caplog.records)


def test_formato_json_es_una_linea_parseable():
    # Arrange
    registro = logging.LogRecord("sb.api", logging.INFO, __file__, 1, "peticion", None, None)
    registro.datos = {"ms": 1.5}
    # Act
    linea = FormatoJSON().format(registro)
    # Assert
    assert json.loads(linea) == {"nivel": "INFO", "logger": "sb.api", "mensaje": "peticion", "ms": 1.5}

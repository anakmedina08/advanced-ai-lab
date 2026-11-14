"""Pruebas del CORS para el frontend desacoplado (Vite en el puerto 5173)."""

from fastapi.testclient import TestClient

from sb_asistente.config import FRONTEND_ORIGINS
from sb_asistente.view.api import app

PREFLIGHT = {"Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"}


def test_origen_de_vite_permitido_por_defecto():
    # Assert
    assert "http://localhost:5173" in FRONTEND_ORIGINS


def test_preflight_desde_el_frontend_es_aceptado():
    # Act
    r = TestClient(app).options("/chat", headers={"Origin": "http://localhost:5173"} | PREFLIGHT)
    # Assert
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_origen_desconocido_no_recibe_permiso():
    # Act
    r = TestClient(app).options("/chat", headers={"Origin": "https://sitio-ajeno.example"} | PREFLIGHT)
    # Assert
    assert "access-control-allow-origin" not in r.headers


def test_expone_las_cabeceras_de_trazabilidad():
    # Act
    r = TestClient(app).get("/health", headers={"Origin": "http://localhost:5173"})
    # Assert
    assert "X-Request-ID" in r.headers["access-control-expose-headers"]

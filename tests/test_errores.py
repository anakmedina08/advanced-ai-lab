"""Pruebas de los errores uniformes de la API (``ErrorOut``)."""

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from sb_asistente.view import errores
from sb_asistente.view.api import app


def _app_de_prueba() -> FastAPI:
    prueba = FastAPI()
    errores.registrar(prueba)

    class Entrada(BaseModel):
        n: int

    @prueba.get("/falla")
    def falla() -> None:
        raise RuntimeError("secreto interno")

    @prueba.get("/no-esta")
    def no_esta() -> None:
        raise HTTPException(404, "No existe")

    @prueba.post("/valida")
    def valida(entrada: Entrada) -> int:
        return entrada.n

    return prueba


def test_error_no_controlado_responde_500_sin_traza():
    # Arrange
    cliente = TestClient(_app_de_prueba(), raise_server_exceptions=False)
    # Act
    r = cliente.get("/falla")
    # Assert
    assert r.status_code == 500
    assert r.json()["error"] == "interno"
    assert "secreto" not in r.text
    assert r.json()["request_id"]


def test_http_exception_conserva_status_y_mensaje():
    # Arrange
    cliente = TestClient(_app_de_prueba())
    # Act
    r = cliente.get("/no-esta", headers={"X-Request-ID": "abc123"})
    # Assert
    assert r.status_code == 404
    esperado = {"error": "no_encontrado", "detalle": "No existe", "ruta": "/no-esta", "request_id": "abc123"}
    assert r.json() == esperado


def test_validacion_lista_los_campos_invalidos():
    # Arrange
    cliente = TestClient(_app_de_prueba())
    # Act
    r = cliente.post("/valida", json={"n": "no es numero"})
    # Assert
    assert r.status_code == 422
    assert r.json()["error"] == "validacion"
    assert r.json()["detalle"][0]["campo"] == "n"


def test_la_api_real_usa_el_esquema_en_rutas_inexistentes():
    # Act
    r = TestClient(app).get("/ruta-que-no-existe")
    # Assert
    assert r.status_code == 404
    assert set(r.json()) == {"error", "detalle", "ruta", "request_id"}


def test_la_api_real_valida_el_chat_con_422():
    # Act
    r = TestClient(app).post("/chat", json={"mensaje": ""})
    # Assert
    assert r.status_code == 422
    assert any(c["campo"] == "mensaje" for c in r.json()["detalle"])

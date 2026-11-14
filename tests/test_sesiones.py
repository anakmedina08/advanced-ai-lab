"""Pruebas de las sesiones del agente: historial tras reinicio, checkpoints, borrado y perfil."""

import pytest
from fastapi.testclient import TestClient

from sb_asistente.controller.agente import AgenteAsistente, abrir_memoria
from sb_asistente.model.memoria import abrir_store
from sb_asistente.model.rag.hibrido import RecuperadorHibrido
from sb_asistente.view import api, dependencias
from test_agente import CHUNKS, ModeloGuionado, final

HILO = "hilo-sesion-01"
USUARIO = "usuario-ana-01"


def nuevo_agente(tmp_path, *mensajes) -> AgenteAsistente:
    """Abre la memoria desde disco: dos llamadas simulan dos procesos (antes y después de reiniciar)."""
    modelo = ModeloGuionado(messages=iter(mensajes))
    modelo.vistos = []
    return AgenteAsistente(
        modelo,
        RecuperadorHibrido(CHUNKS),
        abrir_memoria(tmp_path / "checkpoints.sqlite"),
        lambda p, k: [],
        store=abrir_store(tmp_path / "store.sqlite"),
    )


@pytest.fixture
def cliente(tmp_path):
    antes = nuevo_agente(tmp_path, final(respuesta="Hola, Ana."), final(respuesta="En Carvajal."))
    antes.responder("Me llamo Ana y trabajo en Carvajal", HILO, USUARIO)
    antes.responder("¿Dónde trabajo?", HILO, USUARIO)
    despues = nuevo_agente(tmp_path)  # «reinicio»: nuevo objeto, mismos archivos
    api.app.dependency_overrides[dependencias.get_agente] = lambda: lambda proveedor: despues
    yield TestClient(api.app)
    api.app.dependency_overrides.clear()


def test_el_hilo_sobrevive_al_reinicio(cliente):
    # Act
    r = cliente.get(f"/agente/conversaciones/{HILO}")
    # Assert
    assert r.status_code == 200
    mensajes = r.json()["mensajes"]
    assert [m["rol"] for m in mensajes] == ["usuario", "asistente", "usuario", "asistente"]
    assert mensajes[-1]["texto"] == "En Carvajal."


def test_checkpoints_del_hilo_para_time_travel(cliente):
    # Act
    r = cliente.get(f"/agente/conversaciones/{HILO}/checkpoints")
    # Assert
    checkpoints = r.json()
    assert r.status_code == 200 and len(checkpoints) >= 2
    assert checkpoints[0]["mensajes"] >= checkpoints[-1]["mensajes"]
    assert all(c["checkpoint_id"] for c in checkpoints)


def test_borrar_el_hilo(cliente):
    # Act
    borrado = cliente.delete(f"/agente/conversaciones/{HILO}")
    despues = cliente.get(f"/agente/conversaciones/{HILO}")
    # Assert
    assert borrado.status_code == 204
    assert despues.json()["mensajes"] == []


def test_perfil_de_largo_plazo_y_su_borrado(cliente):
    # Act
    perfil = cliente.get(f"/agente/usuarios/{USUARIO}/perfil").json()
    borrado = cliente.delete(f"/agente/usuarios/{USUARIO}/perfil")
    vacio = cliente.get(f"/agente/usuarios/{USUARIO}/perfil").json()
    # Assert
    assert perfil["hechos"] == {"nombre": "Ana", "empresa": "Carvajal"}
    assert borrado.status_code == 204
    assert vacio["hechos"] == {}


def test_id_inseguro_responde_422(cliente):
    # Act
    r = cliente.get("/agente/conversaciones/abc")
    # Assert
    assert r.status_code == 422
    assert r.json()["error"] == "validacion"

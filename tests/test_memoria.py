"""Pruebas de la memoria de largo plazo (Store con namespace por usuario) y de su uso en el agente."""

import pytest
from langchain_core.messages import SystemMessage
from langgraph.store.memory import InMemoryStore

from sb_asistente.controller.agente import AgenteAsistente, abrir_memoria
from sb_asistente.model.memoria import PerfilStore, abrir_store, bloque_perfil, extraer_hechos, namespace
from sb_asistente.model.rag.hibrido import RecuperadorHibrido
from test_agente import CHUNKS, ModeloGuionado, final

USUARIO = "usuario-ana-01"


def test_extrae_nombre_y_empresa_sin_llm():
    # Act
    hechos = extraer_hechos("Me llamo Ana y trabajo en Carvajal")
    # Assert
    assert hechos == {"nombre": "Ana", "empresa": "Carvajal"}


def test_extrae_ciudad_y_perfil_de_seguros():
    # Act
    hechos = extraer_hechos("Vivo en Cali, tengo carro y un perro")
    # Assert
    assert hechos["ciudad"] == "Cali"
    assert hechos["vehiculo"] == "carro"
    assert hechos["tiene_mascota"] == "sí"


def test_no_guarda_correos_ni_numeros_de_documento():
    # Act
    hechos = extraer_hechos("Trabajo en ana@correo.com y vivo en 1234567890")
    # Assert
    assert "empresa" not in hechos and "ciudad" not in hechos


def test_namespace_por_usuario_y_validacion_del_id():
    # Assert
    assert namespace(USUARIO) == ("usuarios", USUARIO, "perfil")
    with pytest.raises(ValueError, match="usuario_id"):
        namespace("../otro")


def test_store_sqlite_persiste_entre_aperturas(tmp_path):
    # Arrange
    ruta = tmp_path / "store.sqlite"
    PerfilStore(abrir_store(ruta)).guardar(USUARIO, {"nombre": "Ana"})
    # Act (simula un reinicio del proceso: se vuelve a abrir el archivo)
    hechos = PerfilStore(abrir_store(ruta)).leer(USUARIO)
    # Assert
    assert hechos == {"nombre": "Ana"}


def test_borrar_el_perfil_deja_el_namespace_vacio():
    # Arrange
    perfiles = PerfilStore(InMemoryStore())
    perfiles.guardar(USUARIO, {"nombre": "Ana", "empresa": "Carvajal"})
    # Act
    borrados = perfiles.borrar(USUARIO)
    # Assert
    assert borrados == 2
    assert perfiles.leer(USUARIO) == {}


def test_bloque_perfil_va_delimitado():
    # Act
    bloque = bloque_perfil({"empresa": "Carvajal", "nombre": "Ana"})
    # Assert
    assert bloque.startswith("<perfil_usuario") and "- empresa: Carvajal" in bloque


def test_un_hilo_nuevo_recupera_el_perfil_desde_el_store(tmp_path):
    # Arrange
    modelo = ModeloGuionado(
        messages=iter([final(respuesta="Mucho gusto, Ana."), final(respuesta="En Carvajal.")])
    )
    modelo.vistos = []
    agente = AgenteAsistente(
        modelo,
        RecuperadorHibrido(CHUNKS),
        abrir_memoria(tmp_path / "m.sqlite"),
        lambda perfil, k: [],
        store=abrir_store(tmp_path / "store.sqlite"),
    )
    # Act
    agente.responder("Me llamo Ana y trabajo en Carvajal", "hilo-aaa-001", usuario_id=USUARIO)
    agente.responder("¿Dónde trabajo?", "hilo-bbb-002", usuario_id=USUARIO)
    # Assert
    sistema_hilo_b = next(m for m in modelo.vistos[-1] if isinstance(m, SystemMessage))
    assert "empresa: Carvajal" in sistema_hilo_b.content
    assert len([m for m in modelo.vistos[-1] if m.type == "human"]) == 1  # hilo nuevo, sin historial
    assert agente.perfil(USUARIO)["nombre"] == "Ana"


def test_sin_usuario_no_se_inyecta_perfil(tmp_path):
    # Arrange
    modelo = ModeloGuionado(messages=iter([final(respuesta="Hola.")]))
    modelo.vistos = []
    store = InMemoryStore()
    PerfilStore(store).guardar(USUARIO, {"nombre": "Ana"})
    agente = AgenteAsistente(
        modelo, RecuperadorHibrido(CHUNKS), abrir_memoria(tmp_path / "m.sqlite"), lambda p, k: [], store=store
    )
    # Act
    agente.responder("hola", "hilo-ccc-003")
    # Assert
    sistema = next(m for m in modelo.vistos[-1] if isinstance(m, SystemMessage))
    assert "<perfil_usuario nota" not in sistema.content

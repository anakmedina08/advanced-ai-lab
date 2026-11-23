"""Códigos de acceso con vencimiento y cupo para lo que gasta tokens (SPEC-072).

Cada prueba sigue Arrange / Act / Assert con una base SQLite temporal; ninguna llama a un LLM.
"""

import re
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from sb_asistente import config
from sb_asistente.controller import acceso as acceso_ctrl
from sb_asistente.model.acceso import AccesoDenegadoError, CodigosAcceso, generar, huella, normalizar
from sb_asistente.model.llm.service import Answer
from sb_asistente.view import api, cli, dependencias

AHORA = datetime(2026, 11, 20, 12, 0, tzinfo=UTC)


@pytest.fixture
def codigos(tmp_path) -> CodigosAcceso:
    return CodigosAcceso(tmp_path / "codigos.sqlite")


# --- Modelo -------------------------------------------------------------------------------------


def test_el_codigo_es_legible_y_sin_caracteres_confusos():
    # Arrange / Act
    codigos = {generar() for _ in range(200)}
    # Assert
    assert len(codigos) == 200  # aleatorios: no se repiten
    for c in codigos:
        assert re.fullmatch(r"YELO-[2-9A-HJKMNP-Z]{4}-[2-9A-HJKMNP-Z]{4}", c)


def test_se_guarda_solo_el_hash(codigos):
    # Arrange
    codigo, _ = codigos.crear(24, 5, "jurado", ahora=AHORA)
    # Act
    with sqlite3.connect(codigos.ruta) as con:
        filas = con.execute("SELECT * FROM codigos").fetchall()
    # Assert
    assert codigo not in str(filas) and huella(codigo) in str(filas)


def test_el_codigo_se_reconoce_con_minusculas_y_espacios(codigos):
    # Arrange
    codigo, _ = codigos.crear(24, 5, ahora=AHORA)
    escrito = codigo.lower().replace("-", " ")
    # Act
    usado = codigos.consumir(escrito, ahora=AHORA)
    # Assert
    assert normalizar(escrito) == normalizar(codigo) and usado.usados == 1


def test_consumir_descuenta_el_cupo_hasta_agotarlo(codigos):
    # Arrange
    codigo, _ = codigos.crear(24, 2, ahora=AHORA)
    # Act
    codigos.consumir(codigo, ahora=AHORA)
    segundo = codigos.consumir(codigo, ahora=AHORA)
    # Assert
    assert segundo.restantes == 0
    with pytest.raises(AccesoDenegadoError, match="todos sus mensajes"):
        codigos.consumir(codigo, ahora=AHORA)


def test_el_codigo_vence_a_la_hora_indicada(codigos):
    # Arrange
    codigo, info = codigos.crear(2, 10, ahora=AHORA)
    # Act / Assert
    assert info.expira == AHORA + timedelta(hours=2)
    codigos.consumir(codigo, ahora=AHORA + timedelta(hours=1, minutes=59))
    with pytest.raises(AccesoDenegadoError, match="venció"):
        codigos.consumir(codigo, ahora=AHORA + timedelta(hours=2))


def test_un_codigo_revocado_o_inexistente_no_sirve(codigos):
    # Arrange
    codigo, _ = codigos.crear(24, 10, ahora=AHORA)
    # Act
    revocado = codigos.revocar(codigo)
    # Assert
    assert revocado and not codigos.revocar("YELO-AAAA-AAAA")
    with pytest.raises(AccesoDenegadoError, match="desactivado"):
        codigos.consumir(codigo, ahora=AHORA)
    with pytest.raises(AccesoDenegadoError, match="no existe"):
        codigos.consumir("YELO-AAAA-AAAA", ahora=AHORA)


@pytest.mark.parametrize(("horas", "cupo"), [(0, 5), (24, 0), (-1, 5)])
def test_crear_rechaza_horas_o_cupo_invalidos(codigos, horas, cupo):
    # Arrange / Act / Assert
    with pytest.raises(ValueError, match="mayores que cero"):
        codigos.crear(horas, cupo)


# --- Controlador: obligatorio solo en el sitio público ------------------------------------------


@pytest.fixture
def obligatorio(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "ACCESO_DB", tmp_path / "acceso.sqlite")
    monkeypatch.setattr(config, "ACCESO_CODIGO_OBLIGATORIO", True)


def test_apagado_no_pide_codigo(monkeypatch):
    # Arrange
    monkeypatch.setattr(config, "ACCESO_CODIGO_OBLIGATORIO", False)
    # Act / Assert
    assert acceso_ctrl.exigir(None) is None
    assert acceso_ctrl.estado(None) == {"obligatorio": False, "valido": True}


def test_obligatorio_sin_codigo_explica_que_lo_demas_es_libre(obligatorio):
    # Arrange / Act / Assert
    with pytest.raises(AccesoDenegadoError, match="Lo demás"):
        acceso_ctrl.exigir("  ")


def test_estado_no_gasta_cupo(obligatorio):
    # Arrange
    codigo, _ = acceso_ctrl.crear(24, 3)
    # Act
    acceso_ctrl.estado(codigo)
    estado = acceso_ctrl.estado(codigo)
    # Assert
    assert estado["valido"] is True and estado["restantes"] == 3


# --- Vista: JSON-RPC y REST ---------------------------------------------------------------------


class AgenteFalso:
    """Agente sin LLM que cuenta cuántas veces lo llamaron."""

    llamadas = 0

    def conversar(self, mensaje, conversacion_id, usuario_id=None):  # noqa: ARG002
        AgenteFalso.llamadas += 1
        raise RuntimeError("no debería llegar aquí sin código")


@pytest.fixture
def client(obligatorio):
    o = api.app.dependency_overrides
    o[dependencias.get_responder] = lambda: lambda p, v, m, prov: Answer("Ver https://x", "qa", v, 0.1, 50)
    o[dependencias.get_agente] = lambda: lambda prov: AgenteFalso()
    yield TestClient(api.app)
    o.clear()


def _rpc(client, metodo, params, codigo=None):
    cabeceras = {config.ACCESO_HEADER: codigo} if codigo else {}
    cuerpo = {"jsonrpc": "2.0", "method": metodo, "params": params, "id": 1}
    return client.post("/rpc", json=cuerpo, headers=cabeceras).json()


def test_rpc_con_llm_sin_codigo_es_acceso_denegado_y_no_llama_al_modelo(client):
    # Arrange
    AgenteFalso.llamadas = 0
    # Act
    r = _rpc(client, "agente.conversar", {"mensaje": "hola", "conversacion_id": "hilo-abcdef"})
    # Assert
    assert r["error"]["code"] == -32003 and AgenteFalso.llamadas == 0


def test_rpc_con_codigo_vigente_gasta_un_mensaje(client):
    # Arrange
    codigo, _ = acceso_ctrl.crear(24, 2)
    # Act
    r = _rpc(client, "asistente.preguntar", {"pregunta": "¿Qué cubre el SOAT?"}, codigo)
    estado = _rpc(client, "acceso.estado", {}, codigo)["result"]
    # Assert
    assert "result" in r and estado["restantes"] == 1


def test_rpc_sin_llm_no_pide_codigo(client):
    # Arrange / Act
    r = _rpc(client, "mercado.identificar", {"pistas": "pago en la app de mapfre"})
    # Assert
    assert r["result"]["aseguradora"] == "mapfre"


def test_rest_con_llm_sin_codigo_es_403(client):
    # Arrange / Act
    r = client.post("/preguntas", json={"pregunta": "¿Qué cubre el SOAT?"})
    # Assert
    assert r.status_code == 403 and "código de acceso" in r.json()["detalle"]


def test_rest_estado_del_codigo(client):
    # Arrange
    codigo, _ = acceso_ctrl.crear(1, 5)
    # Act
    bien = client.get("/acceso/estado", headers={config.ACCESO_HEADER: codigo}).json()
    mal = client.get("/acceso/estado", headers={config.ACCESO_HEADER: "YELO-AAAA-AAAA"}).json()
    # Assert
    assert bien["valido"] and bien["restantes"] == 5 and mal["valido"] is False


def test_cors_permite_el_encabezado_del_codigo():
    # Arrange / Act
    r = TestClient(api.app).options(
        "/rpc",
        headers={
            "Origin": "https://yellowdata.com.co",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": config.ACCESO_HEADER,
        },
    )
    # Assert
    assert config.ACCESO_HEADER.lower() in r.headers["access-control-allow-headers"].lower()


# --- CLI ----------------------------------------------------------------------------------------


def test_cli_crear_listar_y_revocar(obligatorio, capsys):
    # Arrange / Act
    assert cli.main(["acceso", "crear", "--horas", "2", "--mensajes", "10", "--nota", "jurado"]) == 0
    codigo = re.search(r"YELO-\S+", capsys.readouterr().out).group(0)
    assert cli.main(["acceso", "listar"]) == 0
    listado = capsys.readouterr().out
    assert cli.main(["acceso", "revocar", codigo]) == 0
    # Assert: la lista muestra solo los últimos 4 caracteres, nunca el código entero
    assert codigo[-4:] in listado and codigo not in listado and "10 de 10" in listado
    assert acceso_ctrl.estado(codigo)["valido"] is False

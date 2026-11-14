"""Pruebas de las trazas del agente: latencia por tool, privacidad y rotación del log."""

import json

from langchain_core.messages import AIMessage

from sb_asistente.controller.agente import AgenteAsistente, abrir_memoria
from sb_asistente.model import trazas
from sb_asistente.model.rag.hibrido import RecuperadorHibrido
from sb_asistente.view import cli
from test_agente import CHUNKS, ModeloGuionado, final, llamada

SECRETO = "mi pregunta privada sobre el WhatsApp"


def agente_con_trazas(tmp_path, *mensajes):
    modelo = ModeloGuionado(messages=iter(mensajes))
    modelo.vistos = []
    log = tmp_path / "logs" / "turnos.jsonl"
    agente = AgenteAsistente(
        modelo, RecuperadorHibrido(CHUNKS), abrir_memoria(tmp_path / "m.sqlite"), lambda p, k: [], trazas=log
    )
    return agente, log


def test_un_turno_con_busqueda_deja_su_traza_con_latencia_por_tool(tmp_path):
    # Arrange
    agente, log = agente_con_trazas(
        tmp_path,
        AIMessage("", tool_calls=[llamada("buscar_conocimiento", consulta="WhatsApp")]),
        final(respuesta="Por WhatsApp.", fuentes=["https://www.segurosbolivar.com/canales"]),
    )
    # Act
    turno = agente.responder(SECRETO, "hilo-traza-001")
    # Assert
    linea = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
    assert linea["ruta"] == "rag"
    assert linea["tools"][0]["tool"] == "buscar_conocimiento" and linea["tools"][0]["ms"] >= 0
    assert linea["fuentes"] == 1
    assert turno.tiempos_tools == linea["tools"]


def test_la_traza_no_guarda_el_texto_ni_el_id_del_hilo(tmp_path):
    # Arrange
    agente, log = agente_con_trazas(tmp_path, final(respuesta="Hola."))
    # Act
    agente.responder("hola", "hilo-traza-002")
    # Assert
    contenido = log.read_text(encoding="utf-8")
    assert "hilo-traza-002" not in contenido
    assert json.loads(contenido.splitlines()[-1])["hilo"] == trazas.hash_hilo("hilo-traza-002")


def test_fuera_de_alcance_tambien_se_traza(tmp_path):
    # Arrange
    agente, log = agente_con_trazas(tmp_path)
    # Act
    agente.responder("¿Quién ganó el mundial de fútbol?", "hilo-traza-003")
    # Assert
    assert json.loads(log.read_text(encoding="utf-8"))["ruta"] == "fuera_de_alcance"


def test_rota_el_log_al_superar_el_tamano(tmp_path, monkeypatch):
    # Arrange
    log = tmp_path / "turnos.jsonl"
    log.write_text("x" * 50, encoding="utf-8")
    monkeypatch.setattr(trazas, "TAMANO_MAXIMO", 10)
    # Act
    trazas.registrar_turno(log, {"ruta": "rag"})
    # Assert
    assert (tmp_path / "turnos.jsonl.1").is_file()
    assert json.loads(log.read_text(encoding="utf-8")) == {"ruta": "rag"}


def test_cli_trazas_resume_las_ultimas(tmp_path, monkeypatch, capsys):
    # Arrange
    log = tmp_path / "turnos.jsonl"
    linea = {"fecha": "2026-11-13T10:00:00+00:00", "hilo": "abc", "ruta": "datos", "ms_total": 812.0}
    trazas.registrar_turno(log, linea | {"tools": [{"tool": "consultar_datos", "ms": 12.0}], "error": None})
    monkeypatch.setattr("sb_asistente.config.TRAZAS_LOG", log)
    # Act
    codigo = cli.main(["trazas"])
    # Assert
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "datos" in salida and "consultar_datos 12 ms" in salida

"""Pruebas del streaming del agente (``transmitir`` y ``POST /agente/stream``), sin red."""

import json

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, AIMessageChunk

from sb_asistente.controller.agente import AgenteAsistente, _TextoParcial, abrir_memoria
from sb_asistente.model.rag.hibrido import RecuperadorHibrido
from sb_asistente.view import api, dependencias
from test_agente import CHUNKS, ModeloGuionado, final, llamada


def armar(tmp_path, *mensajes):
    # El modelo falso no sabe emitir tool calls por fragmentos: entrega el mensaje completo
    modelo = ModeloGuionado(messages=iter(mensajes), disable_streaming=True)
    modelo.vistos = []
    return AgenteAsistente(
        modelo, RecuperadorHibrido(CHUNKS), abrir_memoria(tmp_path / "m.sqlite"), lambda p, k: []
    )


def test_eventos_en_orden_router_tools_texto_final(tmp_path):
    # Arrange
    agente = armar(
        tmp_path,
        AIMessage("", tool_calls=[llamada("buscar_conocimiento", consulta="WhatsApp")]),
        final(respuesta="Escríbanos por WhatsApp.", fuentes=["https://www.segurosbolivar.com/canales"]),
    )
    # Act
    eventos = list(agente.transmitir("¿Cuál es el WhatsApp de atención?", "hilo-sse-001"))
    # Assert
    tipos = [e["tipo"] for e in eventos]
    assert tipos[0] == "router" and tipos[-1] == "final"
    assert tipos.index("tool_inicio") < tipos.index("tool_fin") < tipos.index("texto")
    assert "".join(e["delta"] for e in eventos if e["tipo"] == "texto") == "Escríbanos por WhatsApp."
    assert eventos[-1]["turno"]["salida"]["fuentes"] == ["https://www.segurosbolivar.com/canales"]


def test_fuera_de_alcance_emite_texto_fijo_sin_modelo(tmp_path):
    # Arrange
    agente = armar(tmp_path)
    # Act
    eventos = list(agente.transmitir("¿Quién ganó el mundial de fútbol?", "hilo-sse-002"))
    # Assert
    assert [e["tipo"] for e in eventos] == ["router", "texto", "final"]
    assert eventos[0]["ruta"] == "fuera_de_alcance"


def test_un_error_se_emite_como_evento(tmp_path):
    # Arrange
    agente = armar(tmp_path)
    # Act
    eventos = list(agente.transmitir("hola", "id/invalido"))
    # Assert
    assert eventos == [
        {"tipo": "error", "detalle": "conversacion_id inválido (6 a 64 letras, números, - o _)."}
    ]


def test_texto_parcial_saca_la_respuesta_del_json_incompleto():
    # Arrange
    parcial = _TextoParcial()
    trozos = ['{"respuesta": "Hola', ' Ana", "fuen', 'tes": []}']
    meta = {"langgraph_step": 3}
    # Act
    deltas = []
    for i, args in enumerate(trozos):
        nombre = "RespuestaAgente" if i == 0 else None
        chunk = AIMessageChunk("", tool_call_chunks=[{"name": nombre, "args": args, "index": 0, "id": None}])
        deltas.append(parcial.agregar(chunk, meta))
    # Assert
    assert "".join(deltas) == "Hola Ana"


def test_texto_parcial_ignora_los_argumentos_de_otras_tools():
    # Arrange
    parcial = _TextoParcial()
    chunk = AIMessageChunk(
        "",
        tool_call_chunks=[
            {"name": "buscar_conocimiento", "args": '{"respuesta": "no"}', "index": 0, "id": "x"}
        ],
    )
    # Act / Assert
    assert parcial.agregar(chunk, {"langgraph_step": 1}) == ""


class AgenteQueTransmite:
    def transmitir(self, mensaje, conversacion_id, usuario_id=None):
        yield {"tipo": "router", "ruta": "directo"}
        yield {"tipo": "texto", "delta": "Hola"}
        yield {"tipo": "final", "turno": {"conversacion_id": conversacion_id}}


def test_endpoint_sse_entrega_eventos_con_formato_event_data():
    # Arrange
    api.app.dependency_overrides[dependencias.get_agente] = lambda: lambda proveedor: AgenteQueTransmite()
    try:
        # Act
        with TestClient(api.app).stream(
            "POST", "/agente/stream", json={"mensaje": "hola", "conversacion_id": "hilo-sse-003"}
        ) as r:
            cuerpo = "".join(r.iter_text())
            tipo = r.headers["content-type"]
    finally:
        api.app.dependency_overrides.clear()
    # Assert
    assert tipo.startswith("text/event-stream")
    bloques = [b for b in cuerpo.split("\n\n") if b.strip()]
    assert [b.splitlines()[0] for b in bloques] == ["event: router", "event: texto", "event: final"]
    assert json.loads(bloques[1].splitlines()[1].removeprefix("data: "))["delta"] == "Hola"

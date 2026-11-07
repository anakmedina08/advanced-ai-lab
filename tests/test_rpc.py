"""Pruebas de JSON-RPC 2.0 (POST /rpc): contrato, errores estándar, lotes y notificaciones."""

import pytest
from fastapi.testclient import TestClient

from sb_asistente.controller import recomendador
from sb_asistente.controller.agente import PasoAgente, TurnoAgente
from sb_asistente.model.agente import RespuestaAgente
from sb_asistente.model.llm.service import Answer
from sb_asistente.model.rag.hibrido import RecuperadorHibrido
from sb_asistente.view import api, dependencias

URL = "https://www.segurosbolivar.com/canales"
CHUNKS = [
    {
        "chunk_id": "c#0",
        "url": URL,
        "title": "Canales",
        "section": "canales_y_servicio",
        "breadcrumb": "",
        "text": "WhatsApp de atención y línea #322.",
    }
]


class AgenteFalso:
    def __init__(self):
        self.memoria: dict[str, list] = {}

    def responder(self, mensaje, conversacion_id):
        self.memoria.setdefault(conversacion_id, []).append(mensaje)
        salida = RespuestaAgente(
            respuesta="Por WhatsApp.", fuentes=[URL], intencion="conocimiento", confianza="alta"
        )
        return TurnoAgente(
            conversacion_id, salida, [PasoAgente("buscar_conocimiento", {"consulta": "x"}, URL)]
        )

    def historial(self, conversacion_id):
        return [{"rol": "usuario", "texto": t} for t in self.memoria.get(conversacion_id, [])]

    def olvidar(self, conversacion_id):
        self.memoria.pop(conversacion_id, None)


@pytest.fixture
def client():
    agente = AgenteFalso()
    o = api.app.dependency_overrides
    o[dependencias.get_responder] = lambda: lambda p, v, m, prov: Answer(f"Ver {URL}", "qa", v, 0.1, 50)
    o[dependencias.get_chat_qa] = lambda: lambda prov: lambda p, s: Answer(f"Ver {URL}", "qa", "v3", 0.1, 50)
    o[dependencias.get_agente] = lambda: lambda prov: agente
    o[dependencias.get_recuperador] = lambda: lambda: (RecuperadorHibrido(CHUNKS), "solo BM25")
    yield TestClient(api.app)
    o.clear()


def llamar(client, metodo, params=None, id_=1):
    cuerpo = {"jsonrpc": "2.0", "method": metodo, "id": id_}
    if params is not None:
        cuerpo["params"] = params
    return client.post("/rpc", json=cuerpo).json()


def test_salud(client):
    r = llamar(client, "sistema.salud")
    assert r["jsonrpc"] == "2.0" and r["id"] == 1 and r["result"]["estado"] == "ok"


def test_descubrir_lista_metodos_con_esquema(client):
    metodos = {m["metodo"]: m for m in llamar(client, "rpc.descubrir")["result"]}
    assert {"agente.conversar", "conocimiento.buscar", "asistente.chat"} <= set(metodos)
    assert "conversacion_id" in metodos["agente.conversar"]["params"]["properties"]


def test_buscar_conocimiento(client):
    r = llamar(client, "conocimiento.buscar", {"consulta": "WhatsApp"})
    assert r["result"]["fragmentos"][0]["url"] == URL and r["result"]["modo"] == "solo BM25"


def test_preguntar(client):
    assert llamar(client, "asistente.preguntar", {"pregunta": "¿WhatsApp?"})["result"]["fuentes"] == [URL]


def test_chat(client):
    assert llamar(client, "asistente.chat", {"mensaje": "hola"})["result"]["intencion"] == "saludo"


def test_agente_conversar_devuelve_salida_estructurada(client):
    r = llamar(client, "agente.conversar", {"mensaje": "¿WhatsApp?", "conversacion_id": "conv-123456"})
    salida = r["result"]["salida"]
    assert salida["confianza"] == "alta" and salida["fuentes"] == [URL]
    assert r["result"]["pasos"][0]["tool"] == "buscar_conocimiento"


def test_agente_historial_y_olvidar(client):
    llamar(client, "agente.conversar", {"mensaje": "hola", "conversacion_id": "conv-abcdef"})
    assert (
        len(llamar(client, "agente.historial", {"conversacion_id": "conv-abcdef"})["result"]["mensajes"]) == 1
    )
    llamar(client, "agente.olvidar", {"conversacion_id": "conv-abcdef"})
    assert llamar(client, "agente.historial", {"conversacion_id": "conv-abcdef"})["result"]["mensajes"] == []


def test_clasificar(client):
    r = llamar(client, "clasificador.clasificar", {"mensaje": "Recomiéndame un seguro, tengo moto"})
    assert r["result"]["intencion"] == "recomendacion" and r["result"]["perfil"] == {"vehiculo": "moto"}


def test_por_perfil(client, monkeypatch, tmp_path):
    recomendador.generar(300, 7, tmp_path)
    original = recomendador.recomendar_por_perfil
    monkeypatch.setattr(recomendador, "recomendar_por_perfil", lambda p, k: original(p, k, tmp_path))
    r = llamar(client, "recomendador.por_perfil", {"vehiculo": "carro", "k": 2})
    assert len(r["result"]["recomendaciones"]) == 2 and r["result"]["perfil"] == {"vehiculo": "carro"}


def test_skills(client):
    assert "comparar-seguros" in {s["nombre"] for s in llamar(client, "skills.listar")["result"]}


def test_json_invalido_es_32700(client):
    r = client.post("/rpc", content=b"{no json", headers={"Content-Type": "application/json"}).json()
    assert r["error"]["code"] == -32700 and r["id"] is None


@pytest.mark.parametrize("cuerpo", [{"method": "sistema.salud", "id": 1}, {"jsonrpc": "2.0", "id": 1}, [], 5])
def test_solicitud_invalida_es_32600(client, cuerpo):
    r = client.post("/rpc", json=cuerpo).json()
    assert r["error"]["code"] == -32600


def test_metodo_inexistente_es_32601(client):
    assert llamar(client, "no.existe")["error"]["code"] == -32601


def test_parametros_invalidos_es_32602_con_detalle(client):
    r = llamar(client, "agente.conversar", {"mensaje": "hola", "conversacion_id": "x"})
    assert r["error"]["code"] == -32602 and r["error"]["data"][0]["campo"] == "conversacion_id"


def test_datos_personales_rechazados(client):
    r = llamar(
        client, "agente.conversar", {"mensaje": "mi cédula es 1012345678", "conversacion_id": "conv-999999"}
    )
    assert r["error"]["code"] == -32602


def test_campo_extra_rechazado(client):
    assert llamar(client, "conocimiento.buscar", {"consulta": "soat", "otro": 1})["error"]["code"] == -32602


def test_params_posicionales_rechazados(client):
    assert llamar(client, "conocimiento.buscar", ["soat"])["error"]["code"] == -32602


def test_recurso_no_encontrado_es_32001(client):
    assert (
        llamar(client, "asistente.chat", {"mensaje": "¿Qué cubre el SOAT?", "skill": "no-existe"})["error"][
            "code"
        ]
        == -32001
    )


def test_datos_no_listos_es_32002(client):
    def sin_base(*a):
        raise FileNotFoundError("chunks.jsonl")

    api.app.dependency_overrides[dependencias.get_responder] = lambda: sin_base
    assert llamar(client, "asistente.preguntar", {"pregunta": "¿SOAT?"})["error"]["code"] == -32002


def test_error_interno_no_filtra_detalle(client):
    def falla(*a):
        raise RuntimeError("clave secreta sk-123")

    api.app.dependency_overrides[dependencias.get_responder] = lambda: falla
    r = llamar(client, "asistente.preguntar", {"pregunta": "¿SOAT?"})
    assert r["error"]["code"] == -32603 and "sk-123" not in str(r)


def test_lote_mantiene_ids_y_omite_notificaciones(client):
    lote = [
        {"jsonrpc": "2.0", "method": "sistema.salud", "id": "a"},
        {"jsonrpc": "2.0", "method": "clasificador.clasificar", "params": {"mensaje": "hola"}},
        {"jsonrpc": "2.0", "method": "no.existe", "id": 7},
    ]
    r = client.post("/rpc", json=lote).json()
    assert [x["id"] for x in r] == ["a", 7] and "error" in r[1]


def test_solo_notificaciones_devuelve_204(client):
    r = client.post("/rpc", json={"jsonrpc": "2.0", "method": "sistema.salud"})
    assert r.status_code == 204


def test_lote_demasiado_grande(client):
    lote = [{"jsonrpc": "2.0", "method": "sistema.salud", "id": i} for i in range(11)]
    assert client.post("/rpc", json=lote).json()["error"]["code"] == -32600


def test_id_booleano_invalido(client):
    assert (
        client.post("/rpc", json={"jsonrpc": "2.0", "method": "sistema.salud", "id": True}).json()["error"][
            "code"
        ]
        == -32600
    )

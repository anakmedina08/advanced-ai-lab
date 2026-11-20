"""Pruebas de JSON-RPC 2.0 (POST /rpc): contrato, errores estándar, lotes y notificaciones."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from dobles_mercado import chunk_mercado
from sb_asistente.controller import recomendador
from sb_asistente.controller.agente import PasoAgente, TurnoAgente
from sb_asistente.model.agente import RespuestaAgente
from sb_asistente.model.llm.service import Answer
from sb_asistente.model.rag.hibrido import CorpusVacioError, RecuperadorHibrido
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
    """Doble del agente: guarda los mensajes por conversación en memoria."""

    def __init__(self) -> None:
        """Empieza sin conversaciones."""
        self.memoria: dict[str, list] = {}

    def responder(self, mensaje: str, conversacion_id: str, usuario_id: str | None = None) -> TurnoAgente:
        """Guarda el mensaje y responde siempre lo mismo, con una tool y una fuente."""
        self.memoria.setdefault(conversacion_id, []).append(mensaje)
        salida = RespuestaAgente(
            respuesta="Por WhatsApp.", fuentes=[URL], intencion="conocimiento", confianza="alta"
        )
        return TurnoAgente(
            conversacion_id, salida, [PasoAgente("buscar_conocimiento", {"consulta": "x"}, URL)]
        )

    def historial(self, conversacion_id: str) -> list[dict[str, str]]:
        """Mensajes del usuario guardados en la conversación."""
        return [{"rol": "usuario", "texto": t} for t in self.memoria.get(conversacion_id, [])]

    def olvidar(self, conversacion_id: str) -> None:
        """Borra la conversación."""
        self.memoria.pop(conversacion_id, None)


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Cliente de la API con el Q&A, el chat, el agente y el buscador reemplazados por dobles."""
    agente = AgenteFalso()
    o = api.app.dependency_overrides
    o[dependencias.get_responder] = lambda: lambda p, v, m, prov: Answer(f"Ver {URL}", "qa", v, 0.1, 50)
    o[dependencias.get_chat_qa] = lambda: lambda prov: lambda p, s: Answer(f"Ver {URL}", "qa", "v3", 0.1, 50)
    o[dependencias.get_agente] = lambda: lambda prov: agente
    o[dependencias.get_recuperador] = lambda: lambda: (RecuperadorHibrido(CHUNKS), "solo BM25")
    yield TestClient(api.app)
    o.clear()


def llamar(client: TestClient, metodo: str, params: object = None, id_: object = 1) -> dict:
    """Llama a un método JSON-RPC y devuelve la respuesta decodificada."""
    cuerpo = {"jsonrpc": "2.0", "method": metodo, "id": id_}
    if params is not None:
        cuerpo["params"] = params
    return client.post("/rpc", json=cuerpo).json()


def test_salud(client):
    # Arrange / Act
    r = llamar(client, "sistema.salud")
    # Assert
    assert r["jsonrpc"] == "2.0" and r["id"] == 1 and r["result"]["estado"] == "ok"


def test_descubrir_lista_metodos_con_esquema(client):
    # Arrange / Act
    metodos = {m["metodo"]: m for m in llamar(client, "rpc.descubrir")["result"]}
    # Assert
    assert {"agente.conversar", "conocimiento.buscar", "asistente.chat"} <= set(metodos)
    assert "conversacion_id" in metodos["agente.conversar"]["params"]["properties"]


def test_buscar_conocimiento(client):
    # Arrange / Act
    r = llamar(client, "conocimiento.buscar", {"consulta": "WhatsApp"})
    # Assert
    assert r["result"]["fragmentos"][0]["url"] == URL and r["result"]["modo"] == "solo BM25"


def test_preguntar(client):
    # Arrange / Act / Assert
    assert llamar(client, "asistente.preguntar", {"pregunta": "¿WhatsApp?"})["result"]["fuentes"] == [URL]


def test_chat(client):
    # Arrange / Act / Assert
    assert llamar(client, "asistente.chat", {"mensaje": "hola"})["result"]["intencion"] == "saludo"


def test_agente_conversar_devuelve_salida_estructurada(client):
    # Arrange / Act
    r = llamar(client, "agente.conversar", {"mensaje": "¿WhatsApp?", "conversacion_id": "conv-123456"})
    salida = r["result"]["salida"]
    # Assert
    assert salida["confianza"] == "alta" and salida["fuentes"] == [URL]
    assert r["result"]["pasos"][0]["tool"] == "buscar_conocimiento"


def test_agente_historial_y_olvidar(client):
    # Arrange
    conversacion = {"conversacion_id": "conv-abcdef"}
    llamar(client, "agente.conversar", {"mensaje": "hola", **conversacion})
    # Act
    antes = llamar(client, "agente.historial", conversacion)["result"]["mensajes"]
    llamar(client, "agente.olvidar", conversacion)
    despues = llamar(client, "agente.historial", conversacion)["result"]["mensajes"]
    # Assert
    assert len(antes) == 1 and despues == []


def test_clasificar(client):
    # Arrange / Act
    r = llamar(client, "clasificador.clasificar", {"mensaje": "Recomiéndame un seguro, tengo moto"})
    # Assert
    assert r["result"]["intencion"] == "recomendacion" and r["result"]["perfil"] == {"vehiculo": "moto"}


def test_por_perfil(client, monkeypatch, tmp_path):
    # Arrange
    recomendador.generar(300, 7, tmp_path)
    original = recomendador.recomendar_por_perfil
    monkeypatch.setattr(recomendador, "recomendar_por_perfil", lambda p, k: original(p, k, tmp_path))
    # Act
    r = llamar(client, "recomendador.por_perfil", {"vehiculo": "carro", "k": 2})
    # Assert
    assert len(r["result"]["recomendaciones"]) == 2 and r["result"]["perfil"] == {"vehiculo": "carro"}


def test_skills(client):
    # Arrange / Act / Assert
    assert "comparar-seguros" in {s["nombre"] for s in llamar(client, "skills.listar")["result"]}


def test_json_invalido_es_32700(client):
    # Arrange / Act
    r = client.post("/rpc", content=b"{no json", headers={"Content-Type": "application/json"}).json()
    # Assert
    assert r["error"]["code"] == -32700 and r["id"] is None


@pytest.mark.parametrize("cuerpo", [{"method": "sistema.salud", "id": 1}, {"jsonrpc": "2.0", "id": 1}, [], 5])
def test_solicitud_invalida_es_32600(client, cuerpo):
    # Arrange / Act
    r = client.post("/rpc", json=cuerpo).json()
    # Assert
    assert r["error"]["code"] == -32600


def test_metodo_inexistente_es_32601(client):
    # Arrange / Act / Assert
    assert llamar(client, "no.existe")["error"]["code"] == -32601


def test_parametros_invalidos_es_32602_con_detalle(client):
    # Arrange / Act
    r = llamar(client, "agente.conversar", {"mensaje": "hola", "conversacion_id": "x"})
    # Assert
    assert r["error"]["code"] == -32602 and r["error"]["data"][0]["campo"] == "conversacion_id"


def test_datos_personales_rechazados(client):
    # Arrange / Act
    r = llamar(
        client, "agente.conversar", {"mensaje": "mi cédula es 1012345678", "conversacion_id": "conv-999999"}
    )
    # Assert
    assert r["error"]["code"] == -32602


def test_campo_extra_rechazado(client):
    # Arrange / Act / Assert
    assert llamar(client, "conocimiento.buscar", {"consulta": "soat", "otro": 1})["error"]["code"] == -32602


def test_params_posicionales_rechazados(client):
    # Arrange / Act / Assert
    assert llamar(client, "conocimiento.buscar", ["soat"])["error"]["code"] == -32602


def test_recurso_no_encontrado_es_32001(client):
    # Arrange / Act / Assert
    assert (
        llamar(client, "asistente.chat", {"mensaje": "¿Qué cubre el SOAT?", "skill": "no-existe"})["error"][
            "code"
        ]
        == -32001
    )


def test_datos_no_listos_es_32002(client):
    # Arrange
    def sin_base(*_: object) -> Answer:
        """Responder que falla como si faltara el corpus."""
        raise FileNotFoundError("chunks.jsonl")

    api.app.dependency_overrides[dependencias.get_responder] = lambda: sin_base
    # Act
    r = llamar(client, "asistente.preguntar", {"pregunta": "¿SOAT?"})
    # Assert
    assert r["error"]["code"] == -32002


def test_error_interno_no_filtra_detalle(client):
    # Arrange
    def falla(*_: object) -> Answer:
        """Responder que falla con un detalle que no debe salir al cliente."""
        raise RuntimeError("clave secreta sk-123")

    api.app.dependency_overrides[dependencias.get_responder] = lambda: falla
    # Act
    r = llamar(client, "asistente.preguntar", {"pregunta": "¿SOAT?"})
    # Assert
    assert r["error"]["code"] == -32603 and "sk-123" not in str(r)


def test_lote_mantiene_ids_y_omite_notificaciones(client):
    # Arrange
    lote = [
        {"jsonrpc": "2.0", "method": "sistema.salud", "id": "a"},
        {"jsonrpc": "2.0", "method": "clasificador.clasificar", "params": {"mensaje": "hola"}},
        {"jsonrpc": "2.0", "method": "no.existe", "id": 7},
    ]
    # Act
    r = client.post("/rpc", json=lote).json()
    # Assert
    assert [x["id"] for x in r] == ["a", 7] and "error" in r[1]


def test_solo_notificaciones_devuelve_204(client):
    # Arrange / Act
    r = client.post("/rpc", json={"jsonrpc": "2.0", "method": "sistema.salud"})
    # Assert
    assert r.status_code == 204


def test_lote_demasiado_grande(client):
    # Arrange / Act
    lote = [{"jsonrpc": "2.0", "method": "sistema.salud", "id": i} for i in range(11)]
    # Assert
    assert client.post("/rpc", json=lote).json()["error"]["code"] == -32600


def test_id_booleano_invalido(client):
    # Arrange / Act / Assert
    assert (
        client.post("/rpc", json={"jsonrpc": "2.0", "method": "sistema.salud", "id": True}).json()["error"][
            "code"
        ]
        == -32600
    )


# --- Corpus de mercado (SPEC-069) ------------------------------------------------------------


CHUNKS_MERCADO = [
    chunk_mercado(
        "sura-hogar#0", "sura", "hogar_y_mascotas", "El seguro de hogar cubre filtraciones de agua y humedad."
    ),
    chunk_mercado(
        "allianz-hogar#0", "allianz", "hogar_y_mascotas", "Hogar: daños por agua, incendio y robo."
    ),
    chunk_mercado("mapfre-soat#0", "mapfre", "movilidad", "SOAT y seguro de autos con grúa."),
]


@pytest.fixture
def client_mercado() -> Iterator[TestClient]:
    """Cliente de la API con un buscador de mercado en memoria."""
    buscador = RecuperadorHibrido(CHUNKS_MERCADO)
    api.app.dependency_overrides[dependencias.get_mercado] = lambda: lambda: buscador
    yield TestClient(api.app)
    api.app.dependency_overrides.clear()


def test_mercado_buscar_filtra_por_aseguradora(client_mercado):
    # Arrange / Act
    r = llamar(client_mercado, "mercado.buscar", {"consulta": "agua hogar", "aseguradora": "allianz"})
    # Assert
    assert [f["aseguradora"] for f in r["result"]["fragmentos"]] == ["allianz"]


def test_mercado_buscar_con_aseguradora_no_registrada_es_no_encontrado(client_mercado):
    # Arrange / Act
    r = llamar(client_mercado, "mercado.buscar", {"consulta": "agua", "aseguradora": "no-existe"})
    # Assert
    assert r["error"]["code"] == -32001


@pytest.mark.parametrize(
    "params",
    [{"consulta": "a"}, {"consulta": "agua", "aseguradora": "Sura Mayúsculas"}, {"consulta": "agua", "k": 0}],
)
def test_mercado_buscar_valida_parametros(client_mercado, params):
    # Arrange / Act
    r = llamar(client_mercado, "mercado.buscar", params)
    # Assert
    assert r["error"]["code"] == -32602


def test_mercado_comparar_lado_a_lado(client_mercado):
    # Arrange
    params = {
        "consulta": "filtraciones de agua en el hogar",
        "aseguradoras": ["mapfre", "sura"],
        "por_aseguradora": 1,
    }
    # Act
    ofertas = llamar(client_mercado, "mercado.comparar", params)["result"]["ofertas"]
    # Assert
    assert [o["aseguradora"] for o in ofertas] == ["sura", "mapfre"]
    assert ofertas[1]["fragmentos"] == []


def test_mercado_comparar_sin_aseguradoras_elige_las_relevantes(client_mercado):
    # Arrange / Act
    r = llamar(client_mercado, "mercado.comparar", {"consulta": "agua hogar"})
    # Assert
    assert {o["aseguradora"] for o in r["result"]["ofertas"]} == {"sura", "allianz"}


def test_mercado_comparar_sin_nada_relevante_devuelve_vacio(client_mercado):
    # Arrange / Act
    r = llamar(client_mercado, "mercado.comparar", {"consulta": "criptomonedas espaciales"})
    # Assert
    assert r["result"]["ofertas"] == []


@pytest.mark.parametrize(
    "params",
    [
        {"consulta": "agua", "aseguradoras": [f"a{i}" for i in range(9)]},
        {"consulta": "agua", "por_aseguradora": 4},
    ],
)
def test_mercado_comparar_valida_limites(client_mercado, params):
    # Arrange / Act
    r = llamar(client_mercado, "mercado.comparar", params)
    # Assert
    assert r["error"]["code"] == -32602


def test_mercado_aseguradoras_lista_el_registro(client_mercado):
    # Arrange / Act
    filas = llamar(client_mercado, "mercado.aseguradoras")["result"]
    # Assert
    assert {"seguros-bolivar", "sura", "hdi", "proagro"} <= {f["id"] for f in filas}
    assert all({"activo", "whatsapp", "documentos"} <= set(f) for f in filas)


def test_clasificar_devuelve_las_aseguradoras_nombradas(client_mercado):
    # Arrange / Act
    r = llamar(
        client_mercado,
        "clasificador.clasificar",
        {"mensaje": "¿El hogar de Sura cubre lo mismo que Allianz?"},
    )
    # Assert
    assert r["result"]["aseguradoras"] == ["sura", "allianz"]


def test_mercado_buscar_rechaza_datos_personales(client_mercado):
    # Arrange / Act
    r = llamar(client_mercado, "mercado.buscar", {"consulta": "mi cédula es 1012345678"})
    # Assert
    assert r["error"]["code"] == -32602


@pytest.fixture
def client_sin_corpus() -> Iterator[TestClient]:
    """Cliente de la API cuyo buscador de mercado falla como si no se hubiera corrido make mercado."""

    def sin_corpus() -> RecuperadorHibrido:
        """Buscador sin corpus."""
        raise CorpusVacioError("Falta el corpus de mercado: make mercado")

    api.app.dependency_overrides[dependencias.get_mercado] = lambda: sin_corpus
    try:
        yield TestClient(api.app)
    finally:
        api.app.dependency_overrides.clear()


def test_mercado_sin_corpus_es_datos_no_listos(client_sin_corpus):
    # Arrange / Act
    r = llamar(client_sin_corpus, "mercado.buscar", {"consulta": "agua"})
    # Assert
    assert r["error"]["code"] == -32002


def test_mercado_comparar_con_un_id_desconocido_es_no_encontrado(client_mercado):
    # Arrange / Act
    r = llamar(
        client_mercado, "mercado.comparar", {"consulta": "agua", "aseguradoras": ["sura", "no-existe"]}
    )
    # Assert
    assert r["error"]["code"] == -32001


def test_mercado_buscar_rechaza_una_seccion_desconocida(client_mercado):
    # Arrange / Act
    r = llamar(client_mercado, "mercado.buscar", {"consulta": "agua", "seccion": "criptomonedas"})
    # Assert
    assert r["error"]["code"] == -32602


@pytest.fixture
def directorio_canales(monkeypatch: pytest.MonkeyPatch) -> None:
    """Directorio de canales en memoria para mercado.canales (sin data/)."""
    from sb_asistente.controller import mercado as mercado_ctrl
    from sb_asistente.model.mercado.canales import CanalAgregado

    datos = {
        "mapfre": [
            CanalAgregado("whatsapp", "573001234567", {"general"}, ["https://mapfre.co/contacto"], 3),
            CanalAgregado("linea_corta", "#322", {"autos"}, ["https://mapfre.co/autos"], 2),
        ]
    }
    monkeypatch.setattr(mercado_ctrl, "leer_canales", lambda ruta=None: datos)


def test_mercado_canales_lleva_al_whatsapp_y_a_la_linea_del_servicio(client_mercado, directorio_canales):
    # Arrange
    params = {"aseguradora": "mapfre", "servicio": "autos", "resumen": "Choque leve"}
    # Act
    r = llamar(client_mercado, "mercado.canales", params)["result"]
    # Assert
    assert r["whatsapp"]["enlace"] == "https://wa.me/573001234567?text=Choque%20leve"
    assert r["telefonos"][0]["marcar"] == "tel:%23322" and r["telefonos"][0]["especifico"]


@pytest.mark.parametrize(
    "params",
    [
        {"aseguradora": "mapfre", "servicio": "ventas"},
        {"aseguradora": "mapfre", "resumen": "mi cédula es 1012345678"},
        {"aseguradora": "Mapfre"},
    ],
)
def test_mercado_canales_valida_parametros(client_mercado, directorio_canales, params):
    # Arrange / Act
    r = llamar(client_mercado, "mercado.canales", params)
    # Assert
    assert r["error"]["code"] == -32602


def test_mercado_canales_con_aseguradora_desconocida_es_no_encontrado(client_mercado, directorio_canales):
    # Arrange / Act
    r = llamar(client_mercado, "mercado.canales", {"aseguradora": "no-existe"})
    # Assert
    assert r["error"]["code"] == -32001

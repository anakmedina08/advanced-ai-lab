"""Pruebas del agente: tools, salida estructurada, memoria SQLite y barandas (modelo falso, sin red)."""

import json
from itertools import count

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from sb_asistente.controller.agente import AgenteAsistente, abrir_memoria
from sb_asistente.model.agente import RespuestaAgente, crear_tools
from sb_asistente.model.rag.hibrido import RecuperadorHibrido

URL_CANALES = "https://www.segurosbolivar.com/canales"
CHUNKS = [
    {
        "chunk_id": "c#0",
        "url": URL_CANALES,
        "title": "Canales",
        "section": "canales_y_servicio",
        "breadcrumb": "",
        "text": "WhatsApp de atención y línea #322 las 24 horas.",
    },
    {
        "chunk_id": "s#0",
        "url": "https://www.segurosbolivar.com/soat",
        "title": "SOAT",
        "section": "movilidad",
        "breadcrumb": "",
        "text": "El SOAT cubre gastos médicos por accidentes de tránsito.",
    },
]
_ids = count()


class ModeloGuionado(GenericFakeChatModel):
    """Devuelve AIMessages preparados y acepta bind_tools (como un modelo con tool calling)."""

    vistos: list = []

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.vistos.append(list(messages))
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)


def llamada(nombre, **args):
    return {"name": nombre, "args": args, "id": f"call_{next(_ids)}", "type": "tool_call"}


def final(**campos):
    base = {"respuesta": "ok", "fuentes": [], "intencion": "conocimiento", "confianza": "alta"}
    return AIMessage("", tool_calls=[llamada("RespuestaAgente", **(base | campos))])


def agente(tmp_path, *mensajes, recomendar=None):
    modelo = ModeloGuionado(messages=iter(mensajes))
    modelo.vistos = []
    reco = recomendar or (
        lambda perfil, k: [{"nombre": "Seguro para Mascotas", "linea": "mascotas", "razon": "x"}]
    )
    return AgenteAsistente(
        modelo, RecuperadorHibrido(CHUNKS), abrir_memoria(tmp_path / "m.sqlite"), reco
    ), modelo


def test_usa_tool_de_busqueda_y_devuelve_salida_estructurada(tmp_path):
    ag, _ = agente(
        tmp_path,
        AIMessage("", tool_calls=[llamada("buscar_conocimiento", consulta="WhatsApp atención")]),
        final(respuesta="Escríbanos por WhatsApp.", fuentes=[URL_CANALES]),
    )
    turno = ag.responder("¿Cuál es el WhatsApp?", "conv-001")
    assert isinstance(turno.salida, RespuestaAgente) and turno.salida.fuentes == [URL_CANALES]
    assert turno.pasos[0].tool == "buscar_conocimiento" and URL_CANALES in turno.pasos[0].resultado


def test_descarta_fuentes_que_no_vio(tmp_path):
    inventada = "https://www.segurosbolivar.com/inventada"
    ag, _ = agente(
        tmp_path,
        AIMessage("", tool_calls=[llamada("buscar_conocimiento", consulta="SOAT")]),
        final(fuentes=["https://www.segurosbolivar.com/soat", inventada]),
    )
    turno = ag.responder("¿Qué cubre el SOAT?", "conv-002")
    assert turno.salida.fuentes == ["https://www.segurosbolivar.com/soat"] and turno.fuentes_descartadas == [
        inventada
    ]


def test_tool_de_recomendacion_recibe_el_perfil(tmp_path):
    recibido = {}

    def reco(perfil, k):
        recibido.update(perfil=perfil, k=k)
        return [{"nombre": "Seguro para Mascotas", "linea": "mascotas", "razon": "x"}]

    ag, _ = agente(
        tmp_path,
        AIMessage("", tool_calls=[llamada("recomendar_seguros", vehiculo="carro", tiene_mascota=True, k=9)]),
        final(intencion="recomendacion", productos_recomendados=["Seguro para Mascotas"]),
        recomendar=reco,
    )
    turno = ag.responder("Recomiéndame algo, tengo carro y perro", "conv-003")
    assert recibido == {"perfil": {"vehiculo": "carro", "tiene_mascota": True}, "k": 5}
    assert turno.salida.productos_recomendados == ["Seguro para Mascotas"]


def test_memoria_persiste_entre_instancias(tmp_path):
    ag, _ = agente(tmp_path, final(respuesta="Hola, ¿en qué le ayudo?", intencion="saludo"))
    ag.responder("Hola, tengo una moto", "conv-004")
    ag2, modelo2 = agente(tmp_path, final(respuesta="Para su moto…"))
    ag2.responder("¿Y qué me sirve?", "conv-004")
    textos = [m.content for m in modelo2.vistos[0] if isinstance(m.content, str)]
    assert "Hola, tengo una moto" in textos
    assert [h["rol"] for h in ag2.historial("conv-004")] == ["usuario", "asistente", "usuario", "asistente"]


def test_conversaciones_separadas(tmp_path):
    ag, _ = agente(tmp_path, final(), final())
    ag.responder("primera", "conv-A00001")
    ag.responder("segunda", "conv-B00001")
    assert len(ag.historial("conv-A00001")) == 2


def test_olvidar_borra_la_memoria(tmp_path):
    ag, _ = agente(tmp_path, final())
    ag.responder("Hola", "conv-005")
    ag.olvidar("conv-005")
    assert ag.historial("conv-005") == []


def test_redacta_documento_antes_del_modelo(tmp_path):
    ag, modelo = agente(tmp_path, final())
    ag.responder("mi cédula es 1012345678", "conv-006")
    textos = " ".join(str(m.content) for m in modelo.vistos[0])
    assert "1012345678" not in textos and "REDACTED" in textos


def test_conversacion_id_invalido(tmp_path):
    ag, _ = agente(tmp_path)
    with pytest.raises(ValueError):
        ag.responder("hola", "x")


def test_sin_salida_estructurada_responde_aviso(tmp_path):
    ag, _ = agente(tmp_path, AIMessage("texto libre sin esquema"))
    assert ag.responder("hola", "conv-007").salida.confianza == "baja"


def test_tools_directas():
    tools = {t.name: t for t in crear_tools(RecuperadorHibrido(CHUNKS), lambda p, k: [])}
    assert set(tools) == {"buscar_conocimiento", "recomendar_seguros", "clasificar_intencion"}
    assert URL_CANALES in tools["buscar_conocimiento"].invoke({"consulta": "WhatsApp"})
    assert json.loads(
        tools["clasificar_intencion"].invoke({"mensaje": "Recomiéndame un seguro, tengo moto"})
    )["perfil"] == {"vehiculo": "moto"}


def test_esquema_de_tool_recomendar_restringe_valores():
    tools = {t.name: t for t in crear_tools(RecuperadorHibrido(CHUNKS), lambda p, k: [])}
    esquema = tools["recomendar_seguros"].args_schema.model_json_schema()
    assert "electrico" in json.dumps(esquema["properties"]["vehiculo"])

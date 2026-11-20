"""Vista · JSON-RPC 2.0 sobre FastAPI (``POST /rpc``).

Un solo endpoint recibe ``{"jsonrpc": "2.0", "method": "...", "params": {...}, "id": 1}`` y
llama al procedimiento registrado. Los ``params`` de cada método son un modelo Pydantic, así que
la validación y los type hints son los mismos de la API REST. Soporta lotes (lista de llamadas)
y notificaciones (sin ``id``, sin respuesta). ``rpc.descubrir`` lista los métodos con el JSON
Schema de sus parámetros.

Errores (especificación JSON-RPC 2.0, más códigos de servidor -32000 a -32099):

| código | significado |
|---|---|
| -32700 | JSON inválido |
| -32600 | solicitud inválida |
| -32601 | método inexistente |
| -32602 | parámetros inválidos (``data`` trae los errores de Pydantic) |
| -32603 | error interno |
| -32001 | recurso no encontrado (cliente, skill) |
| -32002 | datos no listos (falta generar el corpus, el índice o el recomendador) |

Corpus de mercado (SPEC-069): ``mercado.aseguradoras``, ``mercado.buscar`` y ``mercado.comparar``
trabajan sobre la información pública de varias aseguradoras; ``clasificador.clasificar`` además
devuelve qué aseguradoras nombra el mensaje.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse, Response
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, ValidationError, field_validator
from starlette.concurrency import run_in_threadpool

from sb_asistente.config import (
    ACCESO_HEADER,
    CONSULTA_MAX,
    CONSULTA_MIN,
    ID_ASEGURADORA_MAX,
    IDENTIFICAR_PISTAS_MAX,
    LLM_PROVIDER,
    MENSAJE_MAX,
    MERCADO_MAX_COMPARAR,
    MERCADO_MAX_POR_ASEGURADORA,
    MERCADO_POR_ASEGURADORA,
    PROVIDERS,
    RAG_K,
    RAG_K_MAX,
    RECO_K,
    RECO_K_MAX,
    RPC_MAX_LOTE,
    WHATSAPP_MAX_TEXTO,
)
from sb_asistente.controller import acceso as acceso_ctrl
from sb_asistente.controller import chat, herramientas, recomendador
from sb_asistente.controller import mercado as mercado_ctrl
from sb_asistente.controller.agente import AgenteAsistente
from sb_asistente.model.rag.hibrido import Fragmento, RecuperadorHibrido
from sb_asistente.model.rag.indice import IndiceError
from sb_asistente.view import dependencias as deps
from sb_asistente.view.schemas import ChatIn, PreguntaIn, extraer_fuentes, rechazar_datos_personales

router = APIRouter(tags=["rpc"])

PARSE_ERROR, INVALID_REQUEST, METHOD_NOT_FOUND, INVALID_PARAMS, INTERNAL_ERROR = (
    -32700,
    -32600,
    -32601,
    -32602,
    -32603,
)
NOT_FOUND, NOT_READY, ACCESO_DENEGADO = -32001, -32002, -32003


class RpcError(Exception):
    """Error con código JSON-RPC."""

    def __init__(self, code: int, message: str, data: object | None = None) -> None:
        """Guarda código, mensaje y datos opcionales."""
        super().__init__(message)
        self.code, self.message, self.data = code, message, data


# --- Parámetros de cada método ---------------------------------------------------------------


class _Params(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SinParams(_Params):
    """Método sin parámetros."""


class BuscarParams(_Params):
    """``conocimiento.buscar``."""

    consulta: Annotated[str, Field(min_length=CONSULTA_MIN, max_length=CONSULTA_MAX)]
    k: Annotated[int, Field(ge=1, le=RAG_K_MAX)] = RAG_K
    seccion: str | None = None


ConversacionId = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{6,64}$", examples=["conv-7f3a9c"])]


class AgenteParams(_Params):
    """``agente.conversar``."""

    mensaje: Annotated[str, Field(min_length=1, max_length=MENSAJE_MAX)]
    conversacion_id: ConversacionId
    usuario_id: ConversacionId | None = None
    proveedor: str | None = None

    @field_validator("mensaje")
    @classmethod
    def _sin_datos_personales(cls, valor: str) -> str:
        return rechazar_datos_personales(valor)

    @field_validator("proveedor")
    @classmethod
    def _proveedor(cls, valor: str | None) -> str | None:
        if valor is not None and valor not in PROVIDERS:
            raise ValueError(f"Proveedor no soportado: {valor}")
        return valor


class ConversacionParams(_Params):
    """``agente.historial`` y ``agente.olvidar``."""

    conversacion_id: ConversacionId


class RecomendarParams(_Params):
    """``recomendador.recomendar``."""

    cliente_id: Annotated[str, Field(pattern=r"^C\d{6}$")]
    k: Annotated[int, Field(ge=1, le=RECO_K_MAX)] = RECO_K


class PerfilParams(_Params):
    """``recomendador.por_perfil``."""

    vehiculo: Literal["ninguno", "carro", "moto", "electrico"] | None = None
    vivienda: Literal["propia", "arrendada", "familiar"] | None = None
    tiene_mascota: bool | None = None
    tiene_credito: bool | None = None
    k: Annotated[int, Field(ge=1, le=RECO_K_MAX)] = RECO_K


ServicioCanal = Literal["autos", "soat", "hogar", "salud", "vida", "arl", "pqr", "general"]
SeccionMercado = Annotated[
    str, AfterValidator(mercado_ctrl.validar_seccion), Field(examples=["hogar_y_mascotas", "movilidad"])
]
IdAseguradora = Annotated[str, Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=ID_ASEGURADORA_MAX)]


class MercadoBuscarParams(_Params):
    """``mercado.buscar``."""

    consulta: Annotated[str, Field(min_length=CONSULTA_MIN, max_length=CONSULTA_MAX)]
    k: Annotated[int, Field(ge=1, le=RAG_K_MAX)] = RAG_K
    seccion: SeccionMercado | None = None
    aseguradora: IdAseguradora | None = None

    @field_validator("consulta")
    @classmethod
    def _sin_datos_personales(cls, valor: str) -> str:
        return rechazar_datos_personales(valor)


class CompararParams(_Params):
    """``mercado.comparar``: la misma consulta en varias aseguradoras (todas si no se indican)."""

    consulta: Annotated[str, Field(min_length=CONSULTA_MIN, max_length=CONSULTA_MAX)]
    aseguradoras: Annotated[list[IdAseguradora], Field(max_length=MERCADO_MAX_COMPARAR)] = []
    por_aseguradora: Annotated[int, Field(ge=1, le=MERCADO_MAX_POR_ASEGURADORA)] = MERCADO_POR_ASEGURADORA
    seccion: SeccionMercado | None = None

    @field_validator("consulta")
    @classmethod
    def _sin_datos_personales(cls, valor: str) -> str:
        return rechazar_datos_personales(valor)


class CanalesParams(_Params):
    """``mercado.canales``: a dónde llevar a la persona según su aseguradora y lo que necesita."""

    aseguradora: IdAseguradora
    servicio: ServicioCanal | None = None
    resumen: Annotated[str, Field(max_length=WHATSAPP_MAX_TEXTO)] = ""

    @field_validator("resumen")
    @classmethod
    def _sin_datos_personales(cls, valor: str) -> str:
        return rechazar_datos_personales(valor) if valor else valor


class IdentificarParams(_Params):
    """``mercado.identificar``: pistas que escribió la persona sobre su aseguradora (SPEC-071)."""

    pistas: Annotated[str, Field(min_length=2, max_length=IDENTIFICAR_PISTAS_MAX)]

    @field_validator("pistas")
    @classmethod
    def _sin_datos_personales(cls, valor: str) -> str:
        return rechazar_datos_personales(valor)


class ClasificarParams(_Params):
    """``clasificador.clasificar``."""

    mensaje: Annotated[str, Field(min_length=1, max_length=MENSAJE_MAX)]

    @field_validator("mensaje")
    @classmethod
    def _sin_datos_personales(cls, valor: str) -> str:
        return rechazar_datos_personales(valor)


# --- Contexto con las dependencias inyectadas --------------------------------------------------


@dataclass(slots=True)
class Contexto:
    """Dependencias de los procedimientos (reemplazables en pruebas)."""

    responder: deps.Responder
    chat_qa: Callable[[str], chat.Responder]
    agente: Callable[[str], AgenteAsistente]
    recuperador: Callable[[], tuple[RecuperadorHibrido, str]]
    # Buscador del corpus de mercado (SPEC-069).
    mercado: Callable[[], RecuperadorHibrido] = mercado_ctrl.recuperador_mercado
    # Código de acceso del encabezado X-Codigo-Acceso (SPEC-072); solo lo piden los métodos con LLM.
    codigo: str | None = None


def _salud(_: SinParams, ctx: Contexto) -> dict[str, object]:
    from sb_asistente.view.api import salud  # import diferido: api incluye este router

    return salud().model_dump()


def _fragmento(f: Fragmento) -> dict[str, object]:
    """Fragmento como JSON (con su aseguradora, si viene del corpus de mercado)."""
    return {
        "chunk_id": f.chunk_id,
        "url": f.url,
        "titulo": f.titulo,
        "seccion": f.seccion,
        "texto": f.texto,
        "puntaje": f.puntaje,
        "origen": list(f.origen),
        "aseguradora": f.aseguradora or None,
    }


def _mercado_aseguradoras(_: SinParams, ctx: Contexto) -> list[dict[str, object]]:
    """Registro de aseguradoras con documentos y WhatsApp oficial."""
    return mercado_ctrl.registro_con_datos()


def _mercado_buscar(p: MercadoBuscarParams, ctx: Contexto) -> dict[str, object]:
    """Búsqueda en el corpus de mercado, opcionalmente en una sola aseguradora."""
    if p.aseguradora:
        mercado_ctrl.aseguradoras([p.aseguradora])  # KeyError (-32001) si no está registrada
    fragmentos = ctx.mercado().buscar(p.consulta, k=p.k, seccion=p.seccion, aseguradora=p.aseguradora)
    return {"fragmentos": [_fragmento(f) for f in fragmentos]}


def _mercado_canales(p: CanalesParams, ctx: Contexto) -> dict[str, object]:
    """WhatsApp y teléfonos oficiales de la aseguradora para el servicio que necesita la persona."""
    return mercado_ctrl.canales_para(p.aseguradora, p.servicio, p.resumen)


def _acceso_estado(_: SinParams, ctx: Contexto) -> dict[str, object]:
    """Vigencia y mensajes restantes del código del encabezado, sin gastar cupo."""
    return acceso_ctrl.estado(ctx.codigo)


def _mercado_identificar(p: IdentificarParams, ctx: Contexto) -> dict[str, object]:
    """Aseguradoras del registro que sugieren las pistas (sin LLM; el texto no se guarda)."""
    return mercado_ctrl.identificar_por_pistas(p.pistas)


def _mercado_comparar(p: CompararParams, ctx: Contexto) -> dict[str, object]:
    """La misma consulta en varias aseguradoras (las pedidas o las más relevantes)."""
    ofertas = mercado_ctrl.comparar_aseguradoras(
        ctx.mercado(), p.consulta, p.aseguradoras, p.por_aseguradora, p.seccion
    )
    return {
        "consulta": p.consulta,
        "ofertas": [
            {
                "aseguradora": o.aseguradora,
                "nombre": o.nombre,
                "fragmentos": [_fragmento(f) for f in o.fragmentos],
            }
            for o in ofertas
        ],
    }


def _buscar(p: BuscarParams, ctx: Contexto) -> dict[str, object]:
    recuperador, modo = ctx.recuperador()
    fragmentos = recuperador.buscar(p.consulta, k=p.k, seccion=p.seccion)
    return {
        "modo": modo,
        "fragmentos": [_fragmento(f) for f in fragmentos],
    }


def _preguntar(p: PreguntaIn, ctx: Contexto) -> dict[str, object]:
    ans = ctx.responder(p.pregunta, p.version, p.modo, p.proveedor or LLM_PROVIDER)
    return {
        "texto": ans.text,
        "fuentes": extraer_fuentes(ans.text),
        "cita_fuente": ans.cites_source,
        "latencia_s": round(ans.latency_s, 2),
        "tokens_contexto": ans.context_tokens_est,
    }


def _chat(p: ChatIn, ctx: Contexto) -> dict[str, object]:
    turno = chat.responder(
        p.mensaje,
        ctx.chat_qa(p.proveedor or LLM_PROVIDER),
        modo=p.modo,
        cliente_id=p.cliente_id,
        skill=p.skill,
        k=p.k,
        extraer_fuentes=extraer_fuentes,
    )
    return turno.a_dict()


def _conversar(p: AgenteParams, ctx: Contexto) -> dict[str, object]:
    agente = ctx.agente(p.proveedor or LLM_PROVIDER)
    return agente.responder(p.mensaje, p.conversacion_id, p.usuario_id).a_dict()


def _historial(p: ConversacionParams, ctx: Contexto) -> dict[str, object]:
    return {
        "conversacion_id": p.conversacion_id,
        "mensajes": ctx.agente(LLM_PROVIDER).historial(p.conversacion_id),
    }


def _olvidar(p: ConversacionParams, ctx: Contexto) -> dict[str, object]:
    ctx.agente(LLM_PROVIDER).olvidar(p.conversacion_id)
    return {"conversacion_id": p.conversacion_id, "olvidada": True}


def _recomendar(p: RecomendarParams, ctx: Contexto) -> dict[str, object]:
    return {"cliente_id": p.cliente_id, "recomendaciones": recomendador.recomendar(p.cliente_id, p.k)}


def _por_perfil(p: PerfilParams, ctx: Contexto) -> dict[str, object]:
    perfil = p.model_dump(exclude={"k"}, exclude_none=True)
    items, similares = recomendador.recomendar_por_perfil(perfil, p.k)
    return {"perfil": perfil, "clientes_similares": similares, "recomendaciones": items}


def _clasificar(p: ClasificarParams, ctx: Contexto) -> dict[str, object]:
    return chat.clasificacion(p.mensaje) | {"aseguradoras": mercado_ctrl.detectar_aseguradoras(p.mensaje)}


def _skills(_: SinParams, ctx: Contexto) -> list[dict[str, object]]:
    return herramientas.skills_del_asistente()


@dataclass(frozen=True, slots=True)
class Metodo:
    """Procedimiento registrado."""

    params: type[BaseModel]
    funcion: Callable[[Any, Contexto], object]
    descripcion: str
    usa_llm: bool = False  # gasta tokens: exige código de acceso en el sitio público (SPEC-072)


METODOS: dict[str, Metodo] = {
    "sistema.salud": Metodo(SinParams, _salud, "Estado del servicio y de sus datos."),
    "conocimiento.buscar": Metodo(
        BuscarParams, _buscar, "Búsqueda híbrida (BM25 + vectores) en la base pública."
    ),
    "asistente.preguntar": Metodo(
        PreguntaIn, _preguntar, "Q&A con fuentes (contexto reducido o completo).", usa_llm=True
    ),
    "asistente.chat": Metodo(
        ChatIn, _chat, "Turno del chat orquestado: clasificador → herramienta.", usa_llm=True
    ),
    "agente.conversar": Metodo(
        AgenteParams, _conversar, "Agente con tools, salida estructurada y memoria.", usa_llm=True
    ),
    "acceso.estado": Metodo(
        SinParams, _acceso_estado, "¿Sirve el código de acceso del encabezado? (sin gastar cupo)"
    ),
    "agente.historial": Metodo(ConversacionParams, _historial, "Mensajes guardados de una conversación."),
    "agente.olvidar": Metodo(ConversacionParams, _olvidar, "Borra la memoria de una conversación."),
    "recomendador.recomendar": Metodo(RecomendarParams, _recomendar, "Top-k para un cliente sintético."),
    "recomendador.por_perfil": Metodo(PerfilParams, _por_perfil, "Top-k según el perfil descrito."),
    "clasificador.clasificar": Metodo(
        ClasificarParams, _clasificar, "Intención, sección y perfil de un mensaje."
    ),
    "skills.listar": Metodo(SinParams, _skills, "Skills que el asistente puede aplicar."),
    "mercado.aseguradoras": Metodo(
        SinParams, _mercado_aseguradoras, "Aseguradoras del registro con documentos y WhatsApp oficial."
    ),
    "mercado.buscar": Metodo(
        MercadoBuscarParams, _mercado_buscar, "Búsqueda en la información pública de varias aseguradoras."
    ),
    "mercado.canales": Metodo(
        CanalesParams, _mercado_canales, "WhatsApp y teléfonos oficiales de una aseguradora para un servicio."
    ),
    "mercado.identificar": Metodo(
        IdentificarParams, _mercado_identificar, "Con qué aseguradora está la persona, según sus pistas."
    ),
    "mercado.comparar": Metodo(
        CompararParams, _mercado_comparar, "La misma consulta en varias aseguradoras, lado a lado."
    ),
}


def descubrir() -> list[dict[str, object]]:
    """Métodos con descripción y JSON Schema de parámetros (``rpc.descubrir``)."""
    return [
        {"metodo": nombre, "descripcion": m.descripcion, "params": m.params.model_json_schema()}
        for nombre, m in sorted(METODOS.items())
    ]


def _error(code: int, message: str, id_: object = None, data: object | None = None) -> dict[str, object]:
    error: dict[str, object] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "error": error, "id": id_}


def ejecutar(llamada: object, ctx: Contexto) -> dict[str, object] | None:
    """Ejecuta una llamada; devuelve la respuesta, o ``None`` si es una notificación."""
    if (
        not isinstance(llamada, dict)
        or llamada.get("jsonrpc") != "2.0"
        or not isinstance(llamada.get("method"), str)
    ):
        return _error(
            INVALID_REQUEST, "Solicitud inválida: se espera {jsonrpc: '2.0', method, params?, id?}."
        )
    es_notificacion = "id" not in llamada
    id_ = llamada.get("id")
    if not (id_ is None or isinstance(id_, str | int)) or isinstance(id_, bool):
        return _error(INVALID_REQUEST, "El id debe ser texto, número o null.")
    nombre = llamada["method"]
    params = llamada.get("params", {})
    try:
        if nombre == "rpc.descubrir":
            resultado: object = descubrir()
        else:
            metodo = METODOS.get(nombre)
            if metodo is None:
                raise RpcError(METHOD_NOT_FOUND, f"Método inexistente: {nombre}")
            if not isinstance(params, dict):
                raise RpcError(INVALID_PARAMS, "params debe ser un objeto con nombre de campos.")
            try:
                validados = metodo.params.model_validate(params)
            except ValidationError as exc:
                errores = [{"campo": ".".join(map(str, e["loc"])), "mensaje": e["msg"]} for e in exc.errors()]
                raise RpcError(INVALID_PARAMS, "Parámetros inválidos.", errores) from exc
            if metodo.usa_llm:
                acceso_ctrl.exigir(ctx.codigo)  # gasta un mensaje del cupo antes de llamar al LLM
            resultado = metodo.funcion(validados, ctx)
    except RpcError as exc:
        respuesta = _error(exc.code, exc.message, id_, exc.data)
    except acceso_ctrl.AccesoDenegadoError as exc:
        respuesta = _error(ACCESO_DENEGADO, str(exc), id_)
    except KeyError as exc:
        respuesta = _error(NOT_FOUND, str(exc.args[0]) if exc.args else "No encontrado.", id_)
    except (FileNotFoundError, IndiceError) as exc:
        respuesta = _error(NOT_READY, f"Datos no listos: {exc}", id_)
    except ValueError as exc:
        respuesta = _error(INVALID_PARAMS, str(exc), id_)
    except Exception:  # noqa: BLE001 - el detalle va al log, no al cliente
        respuesta = _error(INTERNAL_ERROR, "Error interno del servidor.", id_)
    else:
        respuesta = {"jsonrpc": "2.0", "result": resultado, "id": id_}
    return None if es_notificacion else respuesta


def get_contexto(
    responder: Annotated[deps.Responder, Depends(deps.get_responder)],
    chat_qa: Annotated[Callable[[str], chat.Responder], Depends(deps.get_chat_qa)],
    agente: Annotated[Callable[[str], AgenteAsistente], Depends(deps.get_agente)],
    recuperador: Annotated[Callable[[], tuple[RecuperadorHibrido, str]], Depends(deps.get_recuperador)],
    mercado: Annotated[Callable[[], RecuperadorHibrido], Depends(deps.get_mercado)],
    codigo: Annotated[str | None, Header(alias=ACCESO_HEADER)] = None,
) -> Contexto:
    """Reúne las dependencias (cada una sobreescribible en pruebas) y el código de acceso."""
    return Contexto(responder, chat_qa, agente, recuperador, mercado, codigo)


@router.post(
    "/rpc",
    summary="JSON-RPC 2.0",
    description="Llamada o lote de llamadas JSON-RPC 2.0. Use `rpc.descubrir` para ver los métodos.",
    response_model=None,
)
async def rpc(request: Request, ctx: Annotated[Contexto, Depends(get_contexto)]) -> Response:
    """Punto único de entrada RPC."""
    try:
        cuerpo = json.loads(await request.body())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JSONResponse(_error(PARSE_ERROR, "JSON inválido."))
    if isinstance(cuerpo, list):
        if not cuerpo:
            return JSONResponse(_error(INVALID_REQUEST, "El lote está vacío."))
        if len(cuerpo) > RPC_MAX_LOTE:
            return JSONResponse(_error(INVALID_REQUEST, f"Máximo {RPC_MAX_LOTE} llamadas por lote."))
        respuestas = [r for r in [await run_in_threadpool(ejecutar, c, ctx) for c in cuerpo] if r is not None]
        return JSONResponse(respuestas) if respuestas else Response(status_code=204)
    respuesta = await run_in_threadpool(ejecutar, cuerpo, ctx)  # el LLM no bloquea el event loop
    return JSONResponse(respuesta) if respuesta is not None else Response(status_code=204)

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
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from starlette.concurrency import run_in_threadpool

from sb_asistente.config import LLM_PROVIDER, PROVIDERS, RAG_K, RECO_K
from sb_asistente.controller import chat, recomendador
from sb_asistente.model import skills
from sb_asistente.model.intencion import clasificar
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
NOT_FOUND, NOT_READY = -32001, -32002
MAX_LOTE = 10


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

    consulta: Annotated[str, Field(min_length=2, max_length=300)]
    k: Annotated[int, Field(ge=1, le=20)] = RAG_K
    seccion: str | None = None


ConversacionId = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{6,64}$", examples=["conv-7f3a9c"])]


class AgenteParams(_Params):
    """``agente.conversar``."""

    mensaje: Annotated[str, Field(min_length=1, max_length=800)]
    conversacion_id: ConversacionId
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
    k: Annotated[int, Field(ge=1, le=10)] = RECO_K


class PerfilParams(_Params):
    """``recomendador.por_perfil``."""

    vehiculo: Literal["ninguno", "carro", "moto", "electrico"] | None = None
    vivienda: Literal["propia", "arrendada", "familiar"] | None = None
    tiene_mascota: bool | None = None
    tiene_credito: bool | None = None
    k: Annotated[int, Field(ge=1, le=10)] = RECO_K


class ClasificarParams(_Params):
    """``clasificador.clasificar``."""

    mensaje: Annotated[str, Field(min_length=1, max_length=800)]


# --- Contexto con las dependencias inyectadas --------------------------------------------------


@dataclass(slots=True)
class Contexto:
    """Dependencias de los procedimientos (reemplazables en pruebas)."""

    responder: deps.Responder
    chat_qa: Callable
    agente: Callable
    recuperador: Callable


def _salud(_: SinParams, ctx: Contexto) -> dict[str, object]:
    from sb_asistente.view.api import salud  # import diferido: api incluye este router

    return salud().model_dump()


def _buscar(p: BuscarParams, ctx: Contexto) -> dict[str, object]:
    recuperador, modo = ctx.recuperador()
    fragmentos = recuperador.buscar(p.consulta, k=p.k, seccion=p.seccion)
    return {
        "modo": modo,
        "fragmentos": [
            {
                "chunk_id": f.chunk_id,
                "url": f.url,
                "titulo": f.titulo,
                "seccion": f.seccion,
                "texto": f.texto,
                "puntaje": f.puntaje,
                "origen": list(f.origen),
            }
            for f in fragmentos
        ],
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
    return ctx.agente(p.proveedor or LLM_PROVIDER).responder(p.mensaje, p.conversacion_id).a_dict()


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
    r = clasificar(p.mensaje)
    return {
        "intencion": r.etiqueta,
        "confianza": r.confianza,
        "seccion": r.seccion,
        "perfil": r.perfil.conocido(),
        "senales": r.senales,
    }


def _skills(_: SinParams, ctx: Contexto) -> list[dict[str, object]]:
    return [
        {"nombre": s.nombre, "descripcion": s.descripcion, "licencia": s.licencia}
        for s in skills.skills_asistente()
    ]


@dataclass(frozen=True, slots=True)
class Metodo:
    """Procedimiento registrado."""

    params: type[BaseModel]
    funcion: Callable[[Any, Contexto], object]
    descripcion: str


METODOS: dict[str, Metodo] = {
    "sistema.salud": Metodo(SinParams, _salud, "Estado del servicio y de sus datos."),
    "conocimiento.buscar": Metodo(
        BuscarParams, _buscar, "Búsqueda híbrida (BM25 + vectores) en la base pública."
    ),
    "asistente.preguntar": Metodo(PreguntaIn, _preguntar, "Q&A con fuentes (contexto reducido o completo)."),
    "asistente.chat": Metodo(ChatIn, _chat, "Turno del chat orquestado: clasificador → herramienta."),
    "agente.conversar": Metodo(AgenteParams, _conversar, "Agente con tools, salida estructurada y memoria."),
    "agente.historial": Metodo(ConversacionParams, _historial, "Mensajes guardados de una conversación."),
    "agente.olvidar": Metodo(ConversacionParams, _olvidar, "Borra la memoria de una conversación."),
    "recomendador.recomendar": Metodo(RecomendarParams, _recomendar, "Top-k para un cliente sintético."),
    "recomendador.por_perfil": Metodo(PerfilParams, _por_perfil, "Top-k según el perfil descrito."),
    "clasificador.clasificar": Metodo(
        ClasificarParams, _clasificar, "Intención, sección y perfil de un mensaje."
    ),
    "skills.listar": Metodo(SinParams, _skills, "Skills que el asistente puede aplicar."),
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
            resultado = metodo.funcion(validados, ctx)
    except RpcError as exc:
        respuesta = _error(exc.code, exc.message, id_, exc.data)
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
    chat_qa: Annotated[Callable, Depends(deps.get_chat_qa)],
    agente: Annotated[Callable, Depends(deps.get_agente)],
    recuperador: Annotated[Callable, Depends(deps.get_recuperador)],
) -> Contexto:
    """Reúne las dependencias (cada una sobreescribible en pruebas)."""
    return Contexto(responder, chat_qa, agente, recuperador)


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
        if len(cuerpo) > MAX_LOTE:
            return JSONResponse(_error(INVALID_REQUEST, f"Máximo {MAX_LOTE} llamadas por lote."))
        respuestas = [r for r in [await run_in_threadpool(ejecutar, c, ctx) for c in cuerpo] if r is not None]
        return JSONResponse(respuestas) if respuestas else Response(status_code=204)
    respuesta = await run_in_threadpool(ejecutar, cuerpo, ctx)  # el LLM no bloquea el event loop
    return JSONResponse(respuesta) if respuesta is not None else Response(status_code=204)

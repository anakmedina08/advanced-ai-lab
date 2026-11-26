"""Agente con tools, salida estructurada y memoria persistente (LangChain ``create_agent``).

Piezas (cada una cubre un tema de clase):

- **Tools**: ``buscar_conocimiento`` (RAG híbrido sobre Qdrant, o Chroma de respaldo), ``recomendar_seguros``
  (recomendador por perfil), ``clasificar_intencion`` (clasificador del chat) y, con el corpus de
  mercado (SPEC-069/070/071), ``comparar_aseguradoras``, ``identificar_aseguradora`` y
  ``canales_aseguradora``: el agente ya no responde solo por Seguros Bolívar.
- **Salida estructurada**: ``RespuestaAgente`` (Pydantic) vía ``ToolStrategy``; el agente no
  puede terminar sin llenar el esquema.
- **Memoria de largo plazo**: un Store con namespace por usuario guarda su perfil y un
  ``dynamic_prompt`` lo inyecta en cualquier hilo nuevo.
- **Memoria persistente**: un *checkpointer* SQLite guarda cada conversación por ``thread_id``;
  lo antiguo se resume (``SummarizationMiddleware``) y lo enviado se recorta por tokens.
- **Barandas**: límite de llamadas al modelo y a tools por turno (costo) y redacción de correos,
  tarjetas y números de documento antes de que lleguen al modelo o a la memoria.
- **Trazas**: con ``LANGSMITH_TRACING=true`` cada turno queda en LangSmith con etiquetas.
"""

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal

from langchain.agents import create_agent
from langchain.agents.middleware import (
    ModelCallLimitMiddleware,
    ModelRequest,
    PIIMiddleware,
    SummarizationMiddleware,
    ToolCallLimitMiddleware,
    dynamic_prompt,
    wrap_model_call,
)
from langchain.agents.structured_output import ToolStrategy
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import trim_messages
from langchain_core.messages.utils import count_tokens_approximately
from langchain_core.tools import BaseTool, tool
from langgraph.store.base import BaseStore
from pydantic import BaseModel, Field

from sb_asistente.config import (
    AGENTE_MAX_LLAMADAS_MODELO,
    AGENTE_MAX_LLAMADAS_TOOLS,
    AGENTE_MAX_RECOMENDACIONES,
    MEMORY_KEEP_MESSAGES,
    MEMORY_MAX_TOKENS,
    MEMORY_SUMMARY_TOKENS,
)
from sb_asistente.model.intencion import clasificar
from sb_asistente.model.llm.prompts import AGENTE_SYSTEM, CAUTELA_ROUTER, GUIA_RUTA_AGENTE
from sb_asistente.model.memoria import PerfilStore, bloque_perfil
from sb_asistente.model.rag.blindaje import formatear_pasajes
from sb_asistente.model.rag.hibrido import CorpusVacioError, Fragmento, RecuperadorHibrido
from sb_asistente.model.trazas import medir_tools

Seccion = Literal["canales_y_servicio", "movilidad", "hogar_y_mascotas", "vida_y_ahorro", "salud", "arl"]
Vehiculo = Literal["ninguno", "carro", "moto", "electrico"]
Vivienda = Literal["propia", "arrendada", "familiar"]


class RespuestaAgente(BaseModel):
    """Salida estructurada obligatoria de cada turno del agente."""

    respuesta: str = Field(
        min_length=1, description="Respuesta al cliente en español, breve, en Markdown (nunca vacía)."
    )
    fuentes: list[str] = Field(
        default_factory=list,
        description=(
            "URLs oficiales que respaldan la respuesta: las que devolvieron buscar_conocimiento, "
            "comparar_aseguradoras o canales_aseguradora (de cualquier aseguradora)."
        ),
    )
    intencion: Literal["conocimiento", "recomendacion", "datos", "saludo", "fuera_de_alcance"] = Field(
        description="Tipo de pregunta atendida."
    )
    confianza: Literal["alta", "media", "baja"] = Field(
        description="alta si los pasajes responden directo; baja si la información no está en la base."
    )
    productos_recomendados: list[str] = Field(
        default_factory=list, description="Nombres de productos sugeridos por recomendar_seguros, si aplica."
    )
    requiere_asesor: bool = Field(
        default=False,
        description="true si el caso necesita un asesor (póliza propia, reclamación en curso, quejas).",
    )
    aseguradora: str | None = Field(
        default=None,
        description=(
            "id del registro de la aseguradora de la persona, si la sabes (la dijo o salió de "
            "identificar_aseguradora); la interfaz la usa para llevarla a su canal."
        ),
    )


SYSTEM_PROMPT = AGENTE_SYSTEM


@dataclass(frozen=True, slots=True)
class HerramientasMercado:
    """Corpus de mercado inyectado en el agente (el controlador pone las funciones reales)."""

    comparar: Callable[[str], list[Fragmento]]
    identificar: Callable[[str], dict]
    canales: Callable[[str, str | None], dict]


# Tools cuyas URLs cuentan como fuentes válidas de la respuesta.
TOOLS_CON_FUENTES: tuple[str, ...] = (
    "buscar_conocimiento",
    "comparar_aseguradoras",
    "canales_aseguradora",
    "citar_fuente",
    "guia_tramite",
    "explicar_termino",
)

ServicioCanal = Literal["autos", "soat", "hogar", "salud", "vida", "arl", "pqr", "general"]


@dataclass(slots=True)
class ContextoTurno:
    """Contexto de ejecución de un turno (``runtime.context``): quién pregunta y qué decidió el router."""

    usuario_id: str | None = None
    ruta: str | None = None
    tools: tuple[str, ...] | None = None
    cautela: bool = False


@dynamic_prompt
def prompt_con_perfil(request: ModelRequest) -> str:
    """Prompt del sistema + el perfil de largo plazo del usuario (``store.search`` en su namespace)."""
    contexto = request.runtime.context if request.runtime else None
    store = request.runtime.store if request.runtime else None
    partes = [SYSTEM_PROMPT]
    ruta = getattr(contexto, "ruta", None)
    if ruta in GUIA_RUTA_AGENTE:
        cautela = getattr(contexto, "cautela", False)
        guia = GUIA_RUTA_AGENTE[ruta] + (f" {CAUTELA_ROUTER}" if cautela else "")
        partes.append(f'<ruta_router ruta="{ruta}">{guia}</ruta_router>')
    usuario = getattr(contexto, "usuario_id", None)
    hechos = PerfilStore(store).leer(usuario) if usuario and store else {}
    if hechos:
        partes.append(bloque_perfil(hechos))
    return "\n\n".join(partes)


@wrap_model_call
def filtrar_tools(request, handler):  # noqa: ANN001, ANN201 - firma definida por LangChain
    """Router: el modelo solo ve las tools de la ruta elegida (``directo`` → ninguna).

    La tool de la salida estructurada no se filtra: LangChain la agrega después.
    """
    contexto = request.runtime.context if request.runtime else None
    permitidas = getattr(contexto, "tools", None)
    if permitidas is None:
        return handler(request)
    tools = [t for t in request.tools if getattr(t, "name", None) in permitidas]
    return handler(request.override(tools=tools))


def crear_tools_mercado(mercado: HerramientasMercado) -> list[BaseTool]:
    """Tools del corpus de mercado: comparar, identificar la aseguradora y sus canales oficiales."""

    @tool
    def comparar_aseguradoras(consulta: str) -> str:
        """Busca la consulta en lo que publican varias aseguradoras de Colombia y devuelve sus pasajes.

        Úsala cuando pregunten qué aseguradoras cubren algo, pidan comparar o la persona no sea de
        Seguros Bolívar. Cada pasaje trae la aseguradora y la URL de su página oficial.

        Args:
            consulta: El caso o la cobertura con palabras concretas (p. ej. "daños por agua tubería hogar").

        """
        try:
            fragmentos = mercado.comparar(consulta)
        except CorpusVacioError:
            return "Aún no hay información de otras aseguradoras cargada (falta `make mercado`)."
        if not fragmentos:
            return "Ninguna aseguradora publica algo sobre esa consulta en las páginas capturadas."
        bloque, _ = formatear_pasajes(fragmentos)
        return bloque

    @tool
    def identificar_aseguradora(pistas: str) -> str:
        """Dice con qué aseguradora está la persona a partir de sus pistas (sin datos personales).

        Args:
            pistas: Lo que la persona contó: dónde paga, qué dice el recibo o el débito, de qué
                dominio le llegan los correos, qué app usa, dónde lo compró.

        """
        try:
            resultado = mercado.identificar(pistas)
        except ValueError as exc:
            return str(exc)
        return json.dumps(resultado, ensure_ascii=False)

    @tool
    def canales_aseguradora(aseguradora: str, servicio: ServicioCanal | None = None) -> str:
        """WhatsApp y líneas oficiales de una aseguradora para un servicio, con la página de donde salen.

        Args:
            aseguradora: id del registro (p. ej. "mapfre", "sura", "seguros-bolivar") o su nombre.
            servicio: Para qué la necesita la persona; si no lo sabes, omítelo.

        """
        try:
            resultado = mercado.canales(aseguradora, servicio)
        except KeyError:
            return f"«{aseguradora}» no está en el registro de aseguradoras; usa identificar_aseguradora."
        return json.dumps(resultado, ensure_ascii=False)

    return [comparar_aseguradoras, identificar_aseguradora, canales_aseguradora]


def crear_tools(
    recuperador: RecuperadorHibrido,
    recomendar: Callable[[dict, int], list[dict]],
    datos: BaseTool | None = None,
    mercado: HerramientasMercado | None = None,
) -> list[BaseTool]:
    """Tools del agente con sus dependencias inyectadas (permiten dobles en pruebas)."""

    @tool
    def buscar_conocimiento(consulta: str, seccion: Seccion | None = None) -> str:
        """Busca en la base pública de Seguros Bolívar (BM25 + vectores) y devuelve pasajes con su URL.

        Args:
            consulta: Qué buscar, con palabras concretas (p. ej. "WhatsApp atención", "SOAT cobertura").
            seccion: Opcional, restringe a una sección del sitio.

        """
        fragmentos = recuperador.buscar(consulta, seccion=seccion)
        if not fragmentos:
            return "Sin resultados en la base pública para esa consulta."
        bloque, _ = formatear_pasajes(fragmentos)
        return bloque

    @tool
    def recomendar_seguros(
        vehiculo: Vehiculo | None = None,
        vivienda: Vivienda | None = None,
        tiene_mascota: bool | None = None,
        tiene_credito: bool | None = None,
        k: int = 3,
    ) -> str:
        """Sugiere seguros según el perfil descrito, con datos sintéticos de práctica (sin datos personales).

        Args:
            vehiculo: Vehículo que tiene el usuario, si lo dijo.
            vivienda: Tipo de vivienda, si lo dijo.
            tiene_mascota: Si tiene mascota, si lo dijo.
            tiene_credito: Si tiene un crédito, si lo dijo.
            k: Cuántos productos sugerir (de 1 al máximo configurado).

        """
        perfil = {
            clave: valor
            for clave, valor in {
                "vehiculo": vehiculo,
                "vivienda": vivienda,
                "tiene_mascota": tiene_mascota,
                "tiene_credito": tiene_credito,
            }.items()
            if valor is not None
        }
        items = recomendar(perfil, max(1, min(k, AGENTE_MAX_RECOMENDACIONES)))
        return json.dumps(
            [{"producto": i["nombre"], "linea": i["linea"], "razon": i["razon"]} for i in items],
            ensure_ascii=False,
        )

    @tool
    def clasificar_intencion(mensaje: str) -> str:
        """Clasifica un mensaje (conocimiento, recomendación, saludo o fuera de alcance) y extrae el perfil.

        Args:
            mensaje: Texto del usuario.

        """
        resultado = clasificar(mensaje)
        return json.dumps(
            {
                "intencion": resultado.etiqueta,
                "confianza": resultado.confianza,
                "seccion": resultado.seccion,
                "perfil": resultado.perfil.conocido(),
            },
            ensure_ascii=False,
        )

    tools = [buscar_conocimiento, recomendar_seguros, clasificar_intencion]
    if mercado is not None:
        tools += crear_tools_mercado(mercado)
    return tools + ([datos] if datos is not None else [])


@wrap_model_call
def recortar_historial(request, handler):  # noqa: ANN001, ANN201 - firma definida por LangChain
    """Red de seguridad: lo enviado al modelo nunca supera ``MEMORY_MAX_TOKENS`` (conteo aproximado)."""
    recortados = trim_messages(
        request.messages,
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=MEMORY_MAX_TOKENS,
        start_on="human",
        allow_partial=False,
    )
    return handler(request.override(messages=recortados or request.messages[-1:]))


def middleware(llm: BaseChatModel) -> Sequence:
    """Barandas del agente: privacidad, costo, resumen del historial y recorte por tokens."""
    return [
        SummarizationMiddleware(
            llm, trigger=("tokens", MEMORY_SUMMARY_TOKENS), keep=("messages", MEMORY_KEEP_MESSAGES)
        ),
        PIIMiddleware("email", strategy="redact"),
        PIIMiddleware("credit_card", strategy="redact"),
        PIIMiddleware("documento", detector=r"(?<!\d)\d{7,12}(?!\d)", strategy="redact"),
        ModelCallLimitMiddleware(run_limit=AGENTE_MAX_LLAMADAS_MODELO, exit_behavior="end"),
        ToolCallLimitMiddleware(run_limit=AGENTE_MAX_LLAMADAS_TOOLS, exit_behavior="continue"),
        recortar_historial,
        filtrar_tools,
        medir_tools,
        prompt_con_perfil,
    ]


def construir_agente(  # noqa: ANN201
    llm: BaseChatModel,
    tools: list[BaseTool],
    checkpointer: object | None = None,
    store: BaseStore | None = None,
):
    """Agente compilado (LangGraph) con salida estructurada, memoria de hilo y Store de largo plazo."""
    return create_agent(
        llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        middleware=middleware(llm),
        response_format=ToolStrategy(RespuestaAgente),
        checkpointer=checkpointer,
        store=store,
        context_schema=ContextoTurno,
        name="sb-asistente-agente",
    )

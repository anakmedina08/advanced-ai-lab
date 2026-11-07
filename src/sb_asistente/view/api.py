"""Vista · API REST con FastAPI (documentación interactiva en ``/docs``).

Es una vista más del MVC: valida con Pydantic (``schemas``) y delega todo al controlador.
El front web (yellowdata.com.co o cualquier otro) consume estos endpoints.

    uv run sb api            # http://127.0.0.1:8000/docs
"""

from collections.abc import Callable
from functools import lru_cache
from importlib.metadata import version
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from sb_asistente.config import CHUNKS_JSONL, LLM_PROVIDER, RECO_DIR, RECO_K
from sb_asistente.controller import assistant, chat, pipeline, recomendador
from sb_asistente.model import skills
from sb_asistente.model.llm.service import Answer
from sb_asistente.view.schemas import (
    ChatIn,
    ChatOut,
    EtapaOut,
    PreguntaIn,
    RecomendacionesOut,
    RespuestaOut,
    SaludOut,
    SkillOut,
    TemaIn,
    extraer_fuentes,
)

Responder = Callable[[str, str, str, str], Answer]
"""(pregunta, versión, modo, proveedor) → Answer."""

app = FastAPI(
    title="Asistente Seguros Bolívar · API",
    version=version("sb-asistente"),
    description=(
        "Proyecto académico (UAO) sobre información pública de segurosbolivar.com. "
        "No es un servicio oficial de la compañía."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yellowdata.com.co", "http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def _responder_real(pregunta: str, version_prompt: str, modo: str, proveedor: str) -> Answer:
    """Usa el contexto reducido (rápido y barato) o la base completa."""
    if modo == "reducido":
        return assistant.LiteAssistant.build(proveedor).answer(pregunta, version=version_prompt)
    return assistant.full_assistant(proveedor).answer(pregunta, version=version_prompt)


def get_responder() -> Responder:
    """Punto de inyección: las pruebas lo reemplazan con un doble sin red ni API."""
    return _responder_real


@lru_cache(maxsize=3)
def _lite(proveedor: str) -> assistant.LiteAssistant:
    """Un asistente de contexto reducido por proveedor (carga chunks y modelo una sola vez)."""
    return assistant.LiteAssistant.build(proveedor)


def get_chat_qa() -> Callable[[str], chat.Responder]:
    """Fábrica (proveedor → responder de Q&A con skill) para el chat; inyectable en pruebas."""

    def fabrica(proveedor: str) -> chat.Responder:
        return lambda pregunta, skill: _lite(proveedor).answer(pregunta, skill=skill)

    return fabrica


def get_asistente() -> Callable[[str], assistant.KnowledgeAssistant]:
    """Fábrica del asistente completo para resumen y FAQ (inyectable)."""
    return assistant.full_assistant


def _salida(ans: Answer) -> RespuestaOut:
    return RespuestaOut(
        texto=ans.text,
        tarea=ans.task,
        version_prompt=ans.prompt_version,
        latencia_s=round(ans.latency_s, 2),
        tokens_contexto=ans.context_tokens_est,
        cita_fuente=ans.cites_source,
        fuentes=extraer_fuentes(ans.text),
    )


@app.get("/salud", response_model=SaludOut, tags=["servicio"])
def salud() -> SaludOut:
    """Estado del servicio y de los datos que necesita."""
    return SaludOut(
        version=app.version,
        proveedor=LLM_PROVIDER,
        corpus_listo=CHUNKS_JSONL.is_file(),
        recomendador_listo=(RECO_DIR / "clientes.csv").is_file(),
    )


@app.get("/pipeline", response_model=list[EtapaOut], tags=["conocimiento"])
def etapas_pipeline() -> list[dict[str, object]]:
    """Métricas de cada etapa del scraping Medallion (sin volver a la web)."""
    return pipeline.stage_report()


@app.post("/preguntas", response_model=RespuestaOut, tags=["conocimiento"])
def preguntar(entrada: PreguntaIn, responder: Annotated[Responder, Depends(get_responder)]) -> RespuestaOut:
    """Q&A: responde citando la página oficial de donde sale el dato."""
    try:
        ans = responder(entrada.pregunta, entrada.version, entrada.modo, entrada.proveedor or LLM_PROVIDER)
    except FileNotFoundError as exc:
        raise HTTPException(503, f"La base de conocimiento no está lista: {exc}") from exc
    return _salida(ans)


@app.post("/resumen", response_model=RespuestaOut, tags=["conocimiento"])
def resumir(entrada: TemaIn, fabrica: Annotated[Callable, Depends(get_asistente)]) -> RespuestaOut:
    """Resumen de un tema para un cliente nuevo."""
    return _salida(fabrica(entrada.proveedor or LLM_PROVIDER).summarize(entrada.tema))


@app.post("/faq", response_model=RespuestaOut, tags=["conocimiento"])
def preguntas_frecuentes(
    entrada: TemaIn, fabrica: Annotated[Callable, Depends(get_asistente)]
) -> RespuestaOut:
    """Genera ``n`` preguntas frecuentes respaldadas por el conocimiento."""
    return _salida(fabrica(entrada.proveedor or LLM_PROVIDER).faq(entrada.tema, entrada.n))


@app.get("/recomendaciones/{cliente_id}", response_model=RecomendacionesOut, tags=["recomendador"])
def recomendaciones(cliente_id: str, k: Annotated[int, Query(ge=1, le=10)] = RECO_K) -> RecomendacionesOut:
    """Top-k de seguros que el cliente aún no tiene (datos sintéticos)."""
    try:
        items = recomendador.recomendar(cliente_id, k)
    except FileNotFoundError as exc:
        raise HTTPException(503, "Genere primero los datos: uv run sb reco generar") from exc
    except KeyError as exc:
        raise HTTPException(404, f"Cliente desconocido: {cliente_id}") from exc
    return RecomendacionesOut(cliente_id=cliente_id, k=k, recomendaciones=items)


@app.post("/chat", response_model=ChatOut, tags=["chat"])
def conversar(
    entrada: ChatIn, fabrica: Annotated[Callable[[str], chat.Responder], Depends(get_chat_qa)]
) -> dict[str, object]:
    """Un turno del chat: clasifica la intención y llama a la herramienta (Q&A o recomendador).

    La respuesta trae la ``traza`` de pasos del orquestador para mostrar cómo se resolvió.
    """
    try:
        turno = chat.responder(
            entrada.mensaje,
            fabrica(entrada.proveedor or LLM_PROVIDER),
            modo=entrada.modo,
            cliente_id=entrada.cliente_id,
            skill=entrada.skill,
            k=entrada.k,
            extraer_fuentes=extraer_fuentes,
        )
    except FileNotFoundError as exc:
        raise HTTPException(503, f"Faltan datos para esta herramienta: {exc}") from exc
    except KeyError as exc:
        raise HTTPException(404, str(exc.args[0]) if exc.args else "No encontrado") from exc
    return turno.a_dict()


@app.get("/skills", response_model=list[SkillOut], tags=["chat"])
def listar_skills() -> list[SkillOut]:
    """Skills que el chat puede aplicar (``metadata.uso: asistente``)."""
    return [
        SkillOut(nombre=s.nombre, descripcion=s.descripcion, licencia=s.licencia)
        for s in skills.skills_asistente()
    ]

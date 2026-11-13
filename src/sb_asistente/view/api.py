"""Vista · API REST con FastAPI (documentación interactiva en ``/docs``).

Es una vista más del MVC: valida con Pydantic (``schemas``) y delega todo al controlador.
El front web (yellowdata.com.co o cualquier otro) consume estos endpoints.

    uv run sb api            # http://127.0.0.1:8000/docs
"""

import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import asdict
from importlib.metadata import version
from importlib.util import find_spec
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from sb_asistente.config import BASE_URL, CHUNKS_JSONL, LLM_PROVIDER, RECO_DIR, RECO_K
from sb_asistente.controller import chat, pipeline, recomendador, vision
from sb_asistente.controller import salud as estado_servicio
from sb_asistente.model import skills
from sb_asistente.model.llm.service import Answer
from sb_asistente.view.dependencias import (
    Responder,
    get_asistente,
    get_chat_qa,
    get_detector,
    get_foto_qa,
    get_interprete,
    get_recomendar,
    get_responder,
)
from sb_asistente.view.schemas import (
    CajaOut,
    ChatIn,
    ChatOut,
    DeteccionOut,
    EscenaOut,
    EtapaOut,
    FotoOut,
    HealthOut,
    PlanOut,
    PreguntaIn,
    RecomendacionesOut,
    RecomendacionOut,
    RespuestaOut,
    SaludOut,
    SkillOut,
    SugerenciaOut,
    TemaIn,
    extraer_fuentes,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Precarga YOLO al arrancar (si está el extra ``vision``) para que la primera foto no espere."""
    if find_spec("ultralytics") is not None:
        try:
            await run_in_threadpool(vision.detector_por_defecto().cargar)
            logger.info("Modelo YOLO cargado para POST /fotos.")
        except Exception as exc:  # noqa: BLE001 - la API sigue sirviendo el resto de endpoints
            logger.warning("No se pudo precargar YOLO (%s); /fotos lo intentará al primer uso.", exc)
    yield


app = FastAPI(
    title="Asistente Seguros Bolívar · API",
    version=version("sb-asistente"),
    description=(
        "Proyecto académico (UAO) sobre información pública de segurosbolivar.com. "
        "No es un servicio oficial de la compañía."
    ),
    lifespan=_lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yellowdata.com.co", "http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


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


@app.get("/health", response_model=HealthOut, tags=["servicio"])
def health() -> HealthOut:
    """Estado del servicio: ``ok`` o ``degradado`` y qué componente falta (sin cargar modelos)."""
    detector = vision.detector_por_defecto() if find_spec("ultralytics") is not None else None
    estado = estado_servicio.componentes(yolo_cargado=detector.cargado if detector is not None else None)
    r = estado_servicio.reporte(app.version, estado)
    return HealthOut(status=r.status, version=r.version, llm=r.llm, componentes=r.componentes)


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


@app.post("/fotos", response_model=FotoOut, tags=["vision"])
async def analizar_foto(
    archivo: Annotated[UploadFile, File(description="Foto JPG o PNG (máx. 8 MB); no se guarda")],
    detector: Annotated[Callable, Depends(get_detector)],
    fabrica_qa: Annotated[Callable, Depends(get_foto_qa)],
    fabrica_interprete: Annotated[Callable, Depends(get_interprete)],
    recomendar: Annotated[Callable, Depends(get_recomendar)],
    interpretar: Annotated[
        bool, Query(description="Entender la situación con un modelo multimodal (Claude)")
    ] = False,
    responder: Annotated[bool, Query(description="Que el asistente explique qué hacer, con fuente")] = False,
    proveedor: Annotated[str | None, Query(description="Proveedor del LLM")] = None,
) -> FotoOut:
    """Foto → ¿qué hago?: privacidad local, situación, respuesta con fuente y recomendaciones.

    1. YOLO (local) detecta objetos y **difumina a las personas** antes de que la foto salga.
    2. Con ``interpretar=true``, Claude entiende la situación (accidente, daño en el hogar, robo o
       un bien que asegurar). Si ve un documento, no se procesa.
    3. Con ``responder=true``, el asistente explica los pasos o el seguro citando la página oficial;
       para bienes asegurables, el recomendador de Gestión sugiere qué más contratan perfiles similares.
    """
    if not (archivo.content_type or "").startswith("image/"):
        raise HTTPException(400, "El archivo debe ser una imagen (JPG o PNG).")
    datos = await archivo.read()
    llm = proveedor or LLM_PROVIDER
    try:
        interprete = fabrica_interprete(llm) if interpretar else None
        asistente = fabrica_qa(llm) if responder else None
        analisis = await run_in_threadpool(
            vision.analizar_foto, datos, detector(), asistente, interprete, recomendar if responder else None
        )
    except vision.ImagenInvalidaError as exc:
        raise HTTPException(422, str(exc)) from exc
    except vision.VisionNoDisponibleError as exc:
        raise HTTPException(503, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(503, f"La base de conocimiento no está lista: {exc}") from exc
    res, plan = analisis.resultado, analisis.plan
    return FotoOut(
        tiempo_inferencia_ms=res.tiempo_ms,
        ancho=res.ancho,
        alto=res.alto,
        personas_difuminadas=analisis.personas_difuminadas,
        detecciones=[
            DeteccionOut(
                clase=d.clase,
                etiqueta=vision.etiqueta(d.clase),
                confianza=d.confianza,
                caja=CajaOut(**asdict(d.caja)),
            )
            for d in res.detecciones
        ],
        sugerencias=[
            SugerenciaOut(
                tema=s.tema.clave,
                nombre=s.tema.nombre,
                objetos=list(s.objetos),
                confianza=s.confianza,
                pregunta=s.tema.pregunta,
                paginas=[BASE_URL + ruta for ruta in s.tema.rutas],
            )
            for s in analisis.sugerencias
        ],
        escena=EscenaOut(**analisis.escena.model_dump()) if analisis.escena else None,
        plan=PlanOut(
            tipo=plan.tipo,
            nombre=plan.nombre,
            pregunta=plan.pregunta,
            paginas=[BASE_URL + ruta for ruta in plan.rutas],
        ),
        aviso=analisis.aviso,
        respuesta=_salida(analisis.respuesta) if analisis.respuesta else None,
        recomendaciones=[RecomendacionOut(**r) for r in analisis.recomendaciones],
    )


# JSON-RPC 2.0 (recomendado en clase): mismo contrato Pydantic, un solo endpoint POST /rpc.
from sb_asistente.view import rpc as _rpc  # noqa: E402

app.include_router(_rpc.router)

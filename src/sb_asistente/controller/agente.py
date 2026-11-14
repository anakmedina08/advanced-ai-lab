"""Controlador del agente: arma sus dependencias, guarda la memoria y valida la salida.

- La memoria de cada conversación vive en ``data/memoria/checkpoints.sqlite`` (no versionado),
  identificada por ``conversacion_id``; ``olvidar`` la borra.
- La salida estructurada se revisa: solo quedan como ``fuentes`` las URLs que de verdad devolvió
  ``buscar_conocimiento`` en ese turno (evita fuentes inventadas).
- Cada turno devuelve la traza de tools para el front y el panel de agentes.
"""

import re
import sqlite3
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.store.base import BaseStore

from sb_asistente.config import (
    CHUNKS_JSONL,
    CORPUS_DEMO,
    CORPUS_DEMO_DIR,
    LANGSMITH_PROJECT,
    LLM_PROVIDER,
    MEMORY_DB,
    MEMORY_STORE,
    QDRANT_DIR,
)
from sb_asistente.controller import recomendador
from sb_asistente.model.agente import ContextoTurno, RespuestaAgente, construir_agente, crear_tools
from sb_asistente.model.llm.service import build_llm
from sb_asistente.model.memoria import PerfilStore, abrir_store, extraer_hechos
from sb_asistente.model.rag import indice
from sb_asistente.model.rag.blindaje import cargar_corpus_demo
from sb_asistente.model.rag.fuentes import fragmentos_rag
from sb_asistente.model.rag.hibrido import RecuperadorHibrido
from sb_asistente.model.rag.qdrant import BuscadorQdrant

CONVERSACION_VALIDA = re.compile(r"^[A-Za-z0-9_-]{6,64}$")
_URL = re.compile(r"https?://[^\s)\]>\"']+")
SIN_RESPUESTA = RespuestaAgente(
    respuesta="No alcancé a completar la respuesta. Reformule la pregunta o use los canales oficiales.",
    intencion="conocimiento",
    confianza="baja",
)


@dataclass(slots=True)
class PasoAgente:
    """Una llamada a tool dentro del turno."""

    tool: str
    argumentos: dict[str, Any]
    resultado: str


@dataclass(slots=True)
class TurnoAgente:
    """Resultado de un turno: salida estructurada validada + traza."""

    conversacion_id: str
    salida: RespuestaAgente
    pasos: list[PasoAgente] = field(default_factory=list)
    fuentes_descartadas: list[str] = field(default_factory=list)
    mensajes_en_memoria: int = 0

    def a_dict(self) -> dict[str, Any]:
        """Representación serializable."""
        datos = asdict(self)
        datos["salida"] = self.salida.model_dump()
        return datos


def abrir_memoria(ruta: Path = MEMORY_DB) -> SqliteSaver:
    """Checkpointer SQLite persistente (crea la carpeta si no existe)."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    return SqliteSaver(sqlite3.connect(str(ruta), check_same_thread=False))


def _qdrant(chunks_path: Path, qdrant_dir: Path) -> BuscadorQdrant:
    """Índice Qdrant de los fragmentos Gold, el mismo del modo «rag» (``make index``).

    Se indexan los chunks tal cual (sin el bloque de canales) para que la huella coincida con la
    colección existente y no se recalculen los embeddings.
    """
    from sb_asistente.model.llm import knowledge, vector_store  # noqa: PLC0415 - carga perezosa

    cliente = vector_store.open_client(qdrant_dir)
    chunks = knowledge.load_chunks(chunks_path)
    return BuscadorQdrant(vector_store.build_index(chunks, vector_store.build_embeddings(), cliente))


def recuperador_por_defecto(
    chunks_path: Path = CHUNKS_JSONL, qdrant_dir: Path = QDRANT_DIR, incluir_demo: bool = CORPUS_DEMO
) -> tuple[RecuperadorHibrido, str]:
    """BM25 + Qdrant (ANN con filtro de payload); si no hay Qdrant, BM25 + Chroma; si no, solo BM25."""
    chunks = fragmentos_rag(chunks_path)
    if incluir_demo:
        chunks = chunks + cargar_corpus_demo(CORPUS_DEMO_DIR)
    try:
        return RecuperadorHibrido(chunks, _qdrant(chunks_path, qdrant_dir)), "híbrido (BM25 + Qdrant)"
    except Exception:  # noqa: BLE001 - sin Ollama o sin índice: se prueba el siguiente
        pass
    try:
        return RecuperadorHibrido(chunks, indice.abrir()), "híbrido (BM25 + Chroma)"
    except indice.IndiceError:
        return RecuperadorHibrido(chunks), "solo BM25 (falta el índice: make index)"


def _texto(mensaje: BaseMessage) -> str:
    contenido = getattr(mensaje, "content", "")
    return contenido if isinstance(contenido, str) else str(contenido)


def _pasos_del_turno(mensajes: list[BaseMessage]) -> list[PasoAgente]:
    """Llamadas a tools posteriores al último mensaje del usuario (sin la del esquema de salida)."""
    ultimo_humano = max((i for i, m in enumerate(mensajes) if isinstance(m, HumanMessage)), default=-1)
    turno = mensajes[ultimo_humano + 1 :]
    resultados = {m.tool_call_id: _texto(m) for m in turno if isinstance(m, ToolMessage)}
    pasos = []
    for mensaje in turno:
        if isinstance(mensaje, AIMessage):
            for llamada in mensaje.tool_calls:
                if llamada["name"] == RespuestaAgente.__name__:
                    continue
                pasos.append(
                    PasoAgente(llamada["name"], dict(llamada["args"]), resultados.get(llamada["id"], ""))
                )
    return pasos


class AgenteAsistente:
    """Agente con tools, salida estructurada y memoria persistente."""

    def __init__(
        self,
        llm: BaseChatModel,
        recuperador: RecuperadorHibrido,
        checkpointer: BaseCheckpointSaver,
        recomendar: Callable[[dict, int], list[dict]] | None = None,
        store: BaseStore | None = None,
    ) -> None:
        """Inyecta modelo, recuperador, memoria de hilo y Store de largo plazo (las pruebas usan dobles)."""
        reco = recomendar or (lambda perfil, k: recomendador.recomendar_por_perfil(perfil, k)[0])
        self.checkpointer = checkpointer
        self.store = store
        self.perfiles = PerfilStore(store) if store is not None else None
        self.grafo = construir_agente(llm, crear_tools(recuperador, reco), checkpointer, store)

    def responder(self, mensaje: str, conversacion_id: str, usuario_id: str | None = None) -> TurnoAgente:
        """Un turno: guarda los hechos del usuario, el agente decide qué tools usar y llena la salida."""
        if not CONVERSACION_VALIDA.match(conversacion_id):
            raise ValueError("conversacion_id inválido (6 a 64 letras, números, - o _).")
        if not mensaje.strip():
            raise ValueError("El mensaje está vacío.")
        if usuario_id and self.perfiles is not None:
            self.perfiles.guardar(usuario_id, extraer_hechos(mensaje))
        config = {
            "configurable": {"thread_id": conversacion_id},
            "tags": ["sb-asistente", "agente"],
            "metadata": {"conversacion_id": conversacion_id, "proyecto": LANGSMITH_PROJECT},
            "run_name": "turno-agente",
        }
        estado = self.grafo.invoke(
            {"messages": [HumanMessage(mensaje)]}, config=config, context=ContextoTurno(usuario_id=usuario_id)
        )
        salida: RespuestaAgente = estado.get("structured_response") or SIN_RESPUESTA
        pasos = _pasos_del_turno(estado["messages"])
        vistas = {
            u.rstrip(".,;:")
            for p in pasos
            if p.tool == "buscar_conocimiento"
            for u in _URL.findall(p.resultado)
        }
        validas = [u for u in salida.fuentes if u in vistas]
        descartadas = [u for u in salida.fuentes if u not in vistas]
        salida = salida.model_copy(update={"fuentes": validas})
        return TurnoAgente(conversacion_id, salida, pasos, descartadas, len(estado["messages"]))

    def historial(self, conversacion_id: str) -> list[dict[str, str]]:
        """Mensajes del usuario y respuestas del agente guardados en la memoria de la conversación."""
        estado = self.grafo.get_state({"configurable": {"thread_id": conversacion_id}})
        salida: list[dict[str, str]] = []
        for m in estado.values.get("messages", []):
            if isinstance(m, HumanMessage):
                salida.append({"rol": "usuario", "texto": _texto(m)})
            elif isinstance(m, AIMessage):
                for llamada in m.tool_calls:
                    if llamada["name"] == RespuestaAgente.__name__:
                        salida.append(
                            {"rol": "asistente", "texto": str(llamada["args"].get("respuesta", ""))}
                        )
        return salida

    def perfil(self, usuario_id: str) -> dict[str, str]:
        """Memoria de largo plazo del usuario (vacía si no hay Store)."""
        return self.perfiles.leer(usuario_id) if self.perfiles is not None else {}

    def olvidar_perfil(self, usuario_id: str) -> int:
        """Borra la memoria de largo plazo del usuario (derecho a la supresión)."""
        return self.perfiles.borrar(usuario_id) if self.perfiles is not None else 0

    def olvidar(self, conversacion_id: str) -> None:
        """Borra la memoria de una conversación (derecho a la supresión)."""
        self.checkpointer.delete_thread(conversacion_id)


@lru_cache(maxsize=3)
def agente_por_defecto(proveedor: str = LLM_PROVIDER) -> AgenteAsistente:
    """Agente real: LLM del proveedor, RAG híbrido y memoria SQLite (una instancia por proveedor)."""
    recuperador, _ = recuperador_por_defecto()
    return AgenteAsistente(
        build_llm(proveedor), recuperador, abrir_memoria(), store=abrir_store(MEMORY_STORE)
    )

"""Controlador del estado del servicio (``GET /health``).

Solo revisa archivos y el estado en memoria del detector: no carga modelos ni llama a la red,
así responde en milisegundos y sirve como *readiness probe* en Docker.
"""

from dataclasses import dataclass, field
from functools import lru_cache
from importlib.util import find_spec
from pathlib import Path

from sb_asistente.config import CHUNKS_JSONL, LLM_PROVIDER, MEMORY_DB, QDRANT_DIR, RECO_DIR, YOLO_MODEL_PATH
from sb_asistente.model.vision.evaluacion import sha256_archivo

OBLIGATORIOS = ("corpus", "recomendador")
"""Sin estos componentes el asistente no responde; los demás degradan funciones opcionales."""


@dataclass(slots=True)
class Salud:
    """Estado agregado del servicio."""

    status: str
    version: str
    llm: str
    componentes: dict[str, bool] = field(default_factory=dict)


def componentes(
    chunks: Path = CHUNKS_JSONL,
    reco_dir: Path = RECO_DIR,
    qdrant_dir: Path = QDRANT_DIR,
    memoria: Path = MEMORY_DB,
    yolo: Path = YOLO_MODEL_PATH,
    yolo_cargado: bool | None = None,
) -> dict[str, bool]:
    """Qué dependencias están listas (rutas inyectables para las pruebas)."""
    return {
        "corpus": chunks.is_file(),
        "recomendador": (reco_dir / "clientes.csv").is_file(),
        "indice_qdrant": qdrant_dir.is_dir() and any(qdrant_dir.iterdir()),
        "memoria": memoria.parent.is_dir(),
        "vision_instalada": find_spec("ultralytics") is not None,
        "modelo_yolo": bool(yolo_cargado) if yolo_cargado is not None else yolo.is_file(),
    }


@lru_cache(maxsize=4)
def _huella(ruta: str, modificado: float) -> str:  # noqa: ARG001 - la fecha invalida la caché
    return sha256_archivo(Path(ruta))[:16]


def huella_yolo(yolo: Path = YOLO_MODEL_PATH) -> str | None:
    """sha256 corto de los pesos de YOLO (el mismo tag de la versión en el Model Registry)."""
    return _huella(str(yolo), yolo.stat().st_mtime) if yolo.is_file() else None


def reporte(version: str, estado: dict[str, bool], llm: str = LLM_PROVIDER) -> Salud:
    """``ok`` si los componentes obligatorios están listos; si no, ``degradado``."""
    listo = all(estado.get(c, False) for c in OBLIGATORIOS)
    return Salud("ok" if listo else "degradado", version, llm, estado)

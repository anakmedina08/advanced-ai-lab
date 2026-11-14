"""Controlador del estado del servicio (``GET /health``).

Solo revisa archivos y el estado en memoria del detector: no carga modelos ni llama a la red,
así responde en milisegundos y sirve como *readiness probe* en Docker.
"""

from dataclasses import dataclass, field
from importlib.util import find_spec
from pathlib import Path

from sb_asistente.config import CHUNKS_JSONL, LLM_PROVIDER, MEMORY_DB, QDRANT_DIR, RECO_DIR, YOLO_MODEL_PATH

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


def reporte(version: str, estado: dict[str, bool], llm: str = LLM_PROVIDER) -> Salud:
    """``ok`` si los componentes obligatorios están listos; si no, ``degradado``."""
    listo = all(estado.get(c, False) for c in OBLIGATORIOS)
    return Salud("ok" if listo else "degradado", version, llm, estado)

"""Controlador «foto → ¿qué hago?»: une visión local, visión multimodal, RAG y recomendador (ADR-020).

Flujo:

1. **YOLO (local)** detecta objetos y personas; las personas se difuminan antes de que la foto salga
   del equipo.
2. **Claude (visión)**, si se pide, entiende la situación: accidente, daño en el hogar, robo, un bien
   que asegurar u otra cosa. Si ve un documento, el flujo se detiene.
3. **Plan**: un siniestro lleva a pasos y canales; un bien, a su seguro.
4. **Asistente (RAG)** responde la pregunta del plan citando la página oficial y, si es un bien, el
   **recomendador** de Gestión sugiere qué más contratan clientes con ese perfil.

Solo se consulta al LLM una vez por foto para la respuesta, más una para entender la escena.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Protocol

from PIL import Image

from sb_asistente.config import VISION_PROVIDERS
from sb_asistente.model.llm.assistants import QAAssistant
from sb_asistente.model.llm.service import Answer, build_llm
from sb_asistente.model.vision import seguros
from sb_asistente.model.vision.deteccion import (
    Deteccion,
    Detector,
    DetectorYolo,
    ImagenInvalidaError,
    ResultadoDeteccion,
    VisionNoDisponibleError,
    abrir_imagen,
)
from sb_asistente.model.vision.escena import Escena, InterpreteEscena
from sb_asistente.model.vision.privacidad import difuminar
from sb_asistente.model.vision.seguros import MENSAJE_DOCUMENTO, Plan, Sugerencia, etiqueta, tema_de

__all__ = [
    "MENSAJE_DOCUMENTO",
    "AnalisisFoto",
    "Deteccion",
    "Detector",
    "Escena",
    "ImagenInvalidaError",
    "Interprete",
    "Plan",
    "Recomendar",
    "VisionNoDisponibleError",
    "abrir_imagen",
    "analizar_foto",
    "detector_por_defecto",
    "etiqueta",
    "interprete_por_defecto",
    "tema_de",
]

Recomendar = Callable[[dict[str, object]], list[dict[str, str]]]
"""Perfil → recomendaciones del recomendador de Gestión."""


class Interprete(Protocol):
    """Contrato del intérprete de escenas (``InterpreteEscena`` o un doble en las pruebas)."""

    def interpretar(self, imagen: Image.Image) -> Escena:  # noqa: D102
        ...


@dataclass(frozen=True, slots=True)
class AnalisisFoto:
    """Resultado completo de una foto."""

    resultado: ResultadoDeteccion
    imagen_privada: Image.Image  # la que vio el modelo multimodal (personas difuminadas)
    sugerencias: list[Sugerencia]
    plan: Plan
    escena: Escena | None = None
    respuesta: Answer | None = None
    recomendaciones: list[dict[str, str]] = field(default_factory=list)

    @property
    def personas_difuminadas(self) -> int:
        """Cuántas personas se difuminaron antes de enviar la foto."""
        return len(self.resultado.personas)

    @property
    def aviso(self) -> str | None:
        """Mensaje fijo cuando la foto no se debe procesar (p. ej., un documento)."""
        return MENSAJE_DOCUMENTO if self.plan.tipo == "documento" else None


@lru_cache(maxsize=1)
def detector_por_defecto() -> DetectorYolo:
    """Detector YOLO compartido por el proceso (el modelo se carga una sola vez)."""
    return DetectorYolo()


@lru_cache(maxsize=2)
def interprete_por_defecto(proveedor: str) -> InterpreteEscena:
    """Intérprete de escenas con un modelo que acepta imágenes (hoy, Claude)."""
    if proveedor not in VISION_PROVIDERS:
        raise VisionNoDisponibleError(
            f"Entender la foto requiere un modelo con visión ({', '.join(VISION_PROVIDERS)}); "
            f"«{proveedor}» solo procesa texto."
        )
    return InterpreteEscena(build_llm(proveedor))


def _recomendar_seguro(recomendar: Recomendar, perfil: dict[str, object]) -> list[dict[str, str]]:
    try:
        return recomendar(perfil)
    except (FileNotFoundError, KeyError, ValueError):  # datos sintéticos sin generar o perfil vacío
        return []


def analizar_foto(
    datos: bytes,
    detector: Detector | None = None,
    asistente: QAAssistant | None = None,
    interprete: Interprete | None = None,
    recomendar: Recomendar | None = None,
) -> AnalisisFoto:
    """Analiza una foto: detecta, protege la privacidad, entiende la situación y responde.

    Cada paso es opcional: sin ``interprete`` se usa solo YOLO; sin ``asistente`` no se gasta LLM en
    la respuesta; sin ``recomendar`` no se consulta el recomendador.
    """
    imagen = abrir_imagen(datos)
    resultado = (detector or detector_por_defecto()).detectar(datos)
    imagen_privada = difuminar(imagen, resultado.personas)
    sugerencias = seguros.sugerir(resultado.detecciones)
    escena = interprete.interpretar(imagen_privada) if interprete else None
    plan = seguros.planear(escena, sugerencias)
    respuesta = asistente.answer(plan.pregunta) if asistente and plan.pregunta else None
    recomendaciones: list[dict[str, str]] = []
    if recomendar and plan.tipo == "asegurar":
        perfil = seguros.perfil(escena, sugerencias)
        recomendaciones = _recomendar_seguro(recomendar, perfil) if perfil else []
    return AnalisisFoto(resultado, imagen_privada, sugerencias, plan, escena, respuesta, recomendaciones)

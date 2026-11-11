"""Controlador «foto → seguro sugerido»: detecta objetos y, si se pide, pregunta al asistente.

Une dos ejercicios del curso: visión (YOLO, ``ejercicio_gestion_fastapi``) y lenguaje (RAG). Solo se
consulta al asistente por la sugerencia más confiable, para no multiplicar el costo por foto.
"""

from dataclasses import dataclass
from functools import lru_cache

from sb_asistente.model.llm.assistants import QAAssistant
from sb_asistente.model.llm.service import Answer
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
from sb_asistente.model.vision.seguros import etiqueta, tema_de

__all__ = [
    "AnalisisFoto",
    "Deteccion",
    "Detector",
    "ImagenInvalidaError",
    "VisionNoDisponibleError",
    "abrir_imagen",
    "analizar_foto",
    "detector_por_defecto",
    "etiqueta",
    "tema_de",
]


@dataclass(frozen=True, slots=True)
class AnalisisFoto:
    """Resultado completo: detecciones, seguros sugeridos y (opcional) la respuesta del asistente."""

    resultado: ResultadoDeteccion
    sugerencias: list[seguros.Sugerencia]
    respuesta: Answer | None = None


@lru_cache(maxsize=1)
def detector_por_defecto() -> DetectorYolo:
    """Detector YOLO compartido por el proceso (el modelo se carga una sola vez)."""
    return DetectorYolo()


def analizar_foto(
    datos: bytes,
    detector: Detector | None = None,
    asistente: QAAssistant | None = None,
) -> AnalisisFoto:
    """Detecta objetos asegurables en la foto y sugiere seguros.

    Con ``asistente``, además responde la pregunta de la sugerencia más confiable, con su fuente.
    """
    resultado = (detector or detector_por_defecto()).detectar(datos)
    sugerencias = seguros.sugerir(resultado.detecciones)
    respuesta = asistente.answer(sugerencias[0].tema.pregunta) if asistente and sugerencias else None
    return AnalisisFoto(resultado, sugerencias, respuesta)

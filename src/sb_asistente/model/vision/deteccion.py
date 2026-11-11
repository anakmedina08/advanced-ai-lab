"""Detección de objetos en fotos con YOLO (adaptado de ``ejercicio_gestion_fastapi``, ADR-020).

- El modelo se carga **una sola vez** y se comparte; la inferencia se serializa con un candado
  porque el modelo no es seguro para hilos (la API la corre en un *threadpool*).
- La foto se procesa **en memoria** y nunca se guarda.
- Las personas no se reportan (``VISION_IGNORED_CLASSES``): solo interesan objetos asegurables.
- ``ultralytics`` es un extra opcional (``uv sync --extra vision``): sin él, el resto del proyecto
  funciona y este módulo avisa con ``VisionNoDisponibleError``.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from threading import Lock
from time import perf_counter
from typing import Protocol

from PIL import Image, UnidentifiedImageError

from sb_asistente.config import (
    MAX_IMAGE_BYTES,
    VISION_BLUR_CONFIDENCE,
    VISION_IGNORED_CLASSES,
    YOLO_CONFIDENCE,
    YOLO_MODEL_PATH,
)


class ImagenInvalidaError(ValueError):
    """El archivo no es una imagen válida o supera el tamaño permitido."""


class VisionNoDisponibleError(RuntimeError):
    """Falta el extra ``vision`` (ultralytics) o el modelo no se pudo cargar."""


@dataclass(frozen=True, slots=True)
class Caja:
    """Rectángulo de la detección en píxeles (esquina superior izquierda e inferior derecha)."""

    x_min: float
    y_min: float
    x_max: float
    y_max: float


@dataclass(frozen=True, slots=True)
class Deteccion:
    """Un objeto detectado: clase de COCO (en inglés), confianza 0–1 y su caja."""

    clase: str
    confianza: float
    caja: Caja


@dataclass(frozen=True, slots=True)
class ResultadoDeteccion:
    """Detecciones de una foto con el tiempo de inferencia y el tamaño de la imagen."""

    detecciones: tuple[Deteccion, ...]
    tiempo_ms: float
    ancho: int
    alto: int
    personas: tuple[Caja, ...] = ()  # solo para difuminarlas; nunca se reportan


class Detector(Protocol):
    """Contrato de cualquier detector (YOLO real o un doble en las pruebas)."""

    def detectar(self, datos: bytes) -> ResultadoDeteccion:  # noqa: D102
        ...


def abrir_imagen(datos: bytes, max_bytes: int = MAX_IMAGE_BYTES) -> Image.Image:
    """Valida tamaño y formato y devuelve la imagen en RGB (todo en memoria)."""
    if not datos:
        raise ImagenInvalidaError("El archivo está vacío.")
    if len(datos) > max_bytes:
        raise ImagenInvalidaError(f"La imagen supera {max_bytes // (1024 * 1024)} MB.")
    try:
        with Image.open(BytesIO(datos)) as imagen:
            return imagen.convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise ImagenInvalidaError("El archivo no contiene una imagen válida.") from exc


def filtrar(
    detecciones: Iterable[Deteccion],
    ignorar: frozenset[str] = VISION_IGNORED_CLASSES,
    confianza_minima: float = YOLO_CONFIDENCE,
) -> tuple[Deteccion, ...]:
    """Quita las clases ignoradas (personas) y las detecciones por debajo del umbral."""
    return tuple(d for d in detecciones if d.clase not in ignorar and d.confianza >= confianza_minima)


class DetectorYolo:
    """Detector YOLO de Ultralytics con carga perezosa y candado de inferencia."""

    def __init__(self, modelo: Path | str = YOLO_MODEL_PATH, confianza: float = YOLO_CONFIDENCE) -> None:
        """Recibe la ruta de los pesos y el umbral de confianza."""
        self.modelo = Path(modelo)
        self.confianza = confianza
        self._yolo: object | None = None
        self._candado = Lock()

    @property
    def cargado(self) -> bool:
        """Indica si el modelo ya está en memoria."""
        return self._yolo is not None

    def cargar(self) -> None:
        """Carga el modelo una sola vez y lo «calienta» (Ultralytics descarga los pesos si faltan).

        La primera inferencia de ``torch`` es mucho más lenta que las siguientes; se paga aquí, al
        arrancar la API, y no en la primera foto de un usuario.
        """
        if self._yolo is not None:
            return
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise VisionNoDisponibleError(
                "La detección de imágenes necesita el extra opcional: uv sync --extra vision"
            ) from exc
        with self._candado:
            if self._yolo is None:
                self.modelo.parent.mkdir(parents=True, exist_ok=True)
                try:
                    modelo = YOLO(str(self.modelo))
                    modelo(Image.new("RGB", (64, 64)), verbose=False)
                except Exception as exc:  # noqa: BLE001 - pesos corruptos, sin red para descargarlos, etc.
                    raise VisionNoDisponibleError(f"No se pudo cargar el modelo YOLO ({exc}).") from exc
                self._yolo = modelo

    def detectar(self, datos: bytes) -> ResultadoDeteccion:
        """Detecta objetos en la foto; aparta a las personas (para difuminarlas) y la baja confianza.

        Las personas se buscan con un umbral más bajo (``VISION_BLUR_CONFIDENCE``): en privacidad es
        mejor difuminar de más que dejar pasar un rostro.
        """
        imagen = abrir_imagen(datos)
        self.cargar()
        with self._candado:
            inicio = perf_counter()
            umbral = min(self.confianza, VISION_BLUR_CONFIDENCE)
            resultados = self._yolo(imagen, conf=umbral, verbose=False)  # type: ignore[operator]
            tiempo_ms = (perf_counter() - inicio) * 1000
        crudas = [
            Deteccion(
                clase=resultado.names[int(caja.cls[0].item())],
                confianza=round(float(caja.conf[0].item()), 4),
                caja=Caja(*(round(float(v), 1) for v in caja.xyxy[0].tolist())),
            )
            for resultado in resultados
            for caja in resultado.boxes
        ]
        personas = tuple(d.caja for d in crudas if d.clase in VISION_IGNORED_CLASSES)
        return ResultadoDeteccion(
            filtrar(crudas, confianza_minima=self.confianza), round(tiempo_ms, 1), *imagen.size, personas
        )

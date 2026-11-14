"""Privacidad de las fotos: difumina a las personas antes de que la imagen salga del equipo.

YOLO corre en local; solo la imagen ya difuminada se envía al modelo multimodal (Ley 1581 de 2012).
Las placas de los vehículos no se detectan con el modelo COCO: el prompt prohíbe transcribirlas y la
interfaz pide al usuario no enviar fotos con datos personales.
"""

import base64
import io
from collections.abc import Iterable

from PIL import Image, ImageFilter

from sb_asistente.model.vision.deteccion import Caja

MARGEN = 0.12  # amplía cada caja un 12 % para cubrir bordes de cabello, manos, etc.


def a_jpeg_b64(imagen: Image.Image, lado_maximo: int = 1280, calidad: int = 85) -> str:
    """JPEG en base64 (reducido a ``lado_maximo`` px) para devolver la imagen ya difuminada por la API.

    Las cajas de las detecciones siguen en píxeles de la imagen original: el cliente las escala con
    ``ancho`` y ``alto``.
    """
    copia = imagen.convert("RGB").copy()
    copia.thumbnail((lado_maximo, lado_maximo))
    buffer = io.BytesIO()
    copia.save(buffer, format="JPEG", quality=calidad)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def difuminar(imagen: Image.Image, cajas: Iterable[Caja], margen: float = MARGEN) -> Image.Image:
    """Copia de la imagen con cada caja muy difuminada (irreconocible) y el resto intacto."""
    salida = imagen.convert("RGB").copy()
    ancho, alto = salida.size
    for caja in cajas:
        dx = (caja.x_max - caja.x_min) * margen
        dy = (caja.y_max - caja.y_min) * margen
        zona = (
            max(0, int(caja.x_min - dx)),
            max(0, int(caja.y_min - dy)),
            min(ancho, int(caja.x_max + dx) + 1),
            min(alto, int(caja.y_max + dy) + 1),
        )
        if zona[2] <= zona[0] or zona[3] <= zona[1]:
            continue
        recorte = salida.crop(zona)
        radio = max(12, min(recorte.size) // 6)
        pixelado = recorte.resize((max(1, recorte.width // 16), max(1, recorte.height // 16)))
        salida.paste(pixelado.resize(recorte.size).filter(ImageFilter.GaussianBlur(radio)), zona[:2])
    return salida

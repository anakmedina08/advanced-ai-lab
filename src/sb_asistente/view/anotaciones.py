"""Vista · dibuja las detecciones sobre la foto (adaptado de ``ejercicio_gestion_fastapi``)."""

from collections.abc import Iterable

from PIL import Image, ImageDraw

from sb_asistente.controller.vision import Deteccion, etiqueta, tema_de

COLOR_ASEGURABLE = "#16a34a"  # objeto con seguro sugerido
COLOR_OTRO = "#64748b"  # objeto detectado sin seguro asociado


def dibujar_detecciones(imagen: Image.Image, detecciones: Iterable[Deteccion]) -> Image.Image:
    """Copia de la imagen con una caja y una etiqueta en español por detección."""
    salida = imagen.convert("RGB").copy()
    lienzo = ImageDraw.Draw(salida)
    grosor = max(2, round(min(salida.size) / 200))
    for det in detecciones:
        color = COLOR_ASEGURABLE if tema_de(det.clase) else COLOR_OTRO
        caja = (det.caja.x_min, det.caja.y_min, det.caja.x_max, det.caja.y_max)
        texto = f"{etiqueta(det.clase)} {det.confianza:.0%}"
        lienzo.rectangle(caja, outline=color, width=grosor)
        izquierda, arriba, derecha, abajo = lienzo.textbbox((0, 0), texto)
        y = max(0, det.caja.y_min - (abajo - arriba) - 6)
        fondo = lienzo.textbbox((det.caja.x_min, y), texto)
        lienzo.rectangle((fondo[0] - 2, fondo[1] - 2, fondo[2] + 2, fondo[3] + 2), fill=color)
        lienzo.text((det.caja.x_min, y), texto, fill="white")
    return salida

"""Texto de un documento de la persona (foto, pantallazo o PDF) para identificar su aseguradora.

Todo pasa en memoria y en el servidor: la imagen se lee con Tesseract (OCR local, sin LLM ni
tokens) y el PDF con ``pypdf`` si está instalado. Nada se escribe en disco ni en logs; quien llama
usa el texto solo para buscar nombres del registro y lo descarta (SPEC-071, Ley 1581).
"""

import shutil
import subprocess  # noqa: S404 - Tesseract es un binario local con argumentos fijos
from collections.abc import Callable
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from sb_asistente.config import (
    IDENTIFICAR_LADO_MIN,
    IDENTIFICAR_MAX_BYTES,
    IDENTIFICAR_OCR_IDIOMAS,
    IDENTIFICAR_OCR_TIMEOUT_S,
    IDENTIFICAR_PDF_PAGINAS,
)

Ejecutar = Callable[..., subprocess.CompletedProcess]


class DocumentoInvalidoError(ValueError):
    """El archivo está vacío, es muy grande o no es una imagen ni un PDF."""


class LectorNoDisponibleError(RuntimeError):
    """No hay con qué leerlo en este servidor (falta Tesseract o ``pypdf``)."""


def tipo_de(datos: bytes) -> str:
    """``pdf``, ``imagen`` o ``ValueError`` según los primeros bytes (no se confía en la extensión)."""
    if not datos:
        raise DocumentoInvalidoError("El archivo está vacío.")
    if len(datos) > IDENTIFICAR_MAX_BYTES:
        raise DocumentoInvalidoError(f"El archivo supera {IDENTIFICAR_MAX_BYTES // (1024 * 1024)} MB.")
    if datos.startswith(b"%PDF"):
        return "pdf"
    if datos.startswith((b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n")):
        return "imagen"
    raise DocumentoInvalidoError("Sube una foto o pantallazo (JPG o PNG) o un PDF.")


def _idiomas(disponibles: set[str]) -> str:
    """Los idiomas pedidos que estén instalados (``eng`` siempre viene con Tesseract)."""
    elegidos = [i for i in IDENTIFICAR_OCR_IDIOMAS.split("+") if i in disponibles]
    return "+".join(elegidos) or "eng"


def _png_para_ocr(datos: bytes) -> bytes:
    """Escala de grises, orientación EXIF y tamaño mínimo: lo que más ayuda a Tesseract."""
    try:
        with Image.open(BytesIO(datos)) as original:
            imagen = ImageOps.exif_transpose(original).convert("L")
    except (UnidentifiedImageError, OSError) as exc:
        raise DocumentoInvalidoError("La imagen no se pudo abrir.") from exc
    lado = max(imagen.size)
    if lado < IDENTIFICAR_LADO_MIN:
        factor = IDENTIFICAR_LADO_MIN / lado
        imagen = imagen.resize((round(imagen.width * factor), round(imagen.height * factor)))
    salida = BytesIO()
    imagen.save(salida, format="PNG")
    return salida.getvalue()


def texto_de_imagen(datos: bytes, ejecutar: Ejecutar = subprocess.run, binario: str | None = None) -> str:
    """Texto de una foto o pantallazo con Tesseract (``stdin`` → ``stdout``; nada toca el disco)."""
    ruta = binario or shutil.which("tesseract")
    if not ruta:
        raise LectorNoDisponibleError("Este servidor no tiene Tesseract para leer imágenes.")
    listado = ejecutar([ruta, "--list-langs"], capture_output=True, text=True, timeout=10, check=False)
    disponibles = {linea.strip() for linea in (listado.stdout or "").splitlines()[1:]}
    proceso = ejecutar(
        [ruta, "stdin", "stdout", "-l", _idiomas(disponibles), "--psm", "3"],
        input=_png_para_ocr(datos),
        capture_output=True,
        timeout=IDENTIFICAR_OCR_TIMEOUT_S,
        check=False,
    )
    if proceso.returncode != 0:
        raise LectorNoDisponibleError("Tesseract no pudo leer la imagen.")
    return proceso.stdout.decode("utf-8", errors="ignore")


def texto_de_pdf(datos: bytes) -> str:
    """Texto de las primeras páginas de un PDF digital (recibos y certificados descargados)."""
    try:
        from pypdf import PdfReader  # noqa: PLC0415 - opcional: solo si se sube un PDF
        from pypdf.errors import PdfReadError  # noqa: PLC0415
    except ImportError as exc:
        raise LectorNoDisponibleError("Este servidor no lee PDF: sube un pantallazo del documento.") from exc
    try:
        lector = PdfReader(BytesIO(datos))
        paginas = lector.pages[:IDENTIFICAR_PDF_PAGINAS]
        return "\n".join(p.extract_text() or "" for p in paginas)
    except (PdfReadError, ValueError, OSError) as exc:
        raise DocumentoInvalidoError("El PDF no se pudo abrir (¿tiene contraseña?).") from exc


def leer_documento(datos: bytes) -> str:
    """Texto del documento, sea imagen o PDF."""
    return texto_de_pdf(datos) if tipo_de(datos) == "pdf" else texto_de_imagen(datos)

"""Métricas de la evaluación del modelo MaaS de la API (YOLO): calidad y latencia.

Funciones puras (sin ultralytics) para poder probarlas sin red ni GPU. El script
``scripts/evaluar_yolo.py`` las usa para registrar en MLflow tres corridas comparables.
"""

import hashlib
import math
from collections.abc import Sequence
from pathlib import Path

REPO_PESOS = "ultralytics/assets"
REVISION_PESOS = "v8.4.0"  # release de donde Ultralytics descarga los pesos yolo26*.pt
LICENCIA_PESOS = "AGPL-3.0"


def percentil(valores: Sequence[float], p: float) -> float:
    """Percentil ``p`` (0–100) con interpolación lineal, como ``numpy.percentile``.

    Raises:
        ValueError: si no hay valores o ``p`` está fuera de rango.

    """
    if not valores:
        raise ValueError("No hay valores.")
    if not 0 <= p <= 100:
        raise ValueError("p debe estar entre 0 y 100.")
    ordenados = sorted(valores)
    posicion = (len(ordenados) - 1) * p / 100
    abajo, arriba = math.floor(posicion), math.ceil(posicion)
    if abajo == arriba:
        return float(ordenados[abajo])
    return ordenados[abajo] + (ordenados[arriba] - ordenados[abajo]) * (posicion - abajo)


def f1(precision: float, recall: float) -> float:
    """Media armónica de precisión y recall (0 si ambas son 0)."""
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)


def resumen_latencias(milisegundos: Sequence[float]) -> dict[str, float]:
    """Latencia media, p50 y p95 (ms) y throughput (imágenes por segundo, en serie)."""
    media = sum(milisegundos) / len(milisegundos)
    return {
        "latencia_media_ms": round(media, 1),
        "latencia_p50_ms": round(percentil(milisegundos, 50), 1),
        "latencia_p95_ms": round(percentil(milisegundos, 95), 1),
        "throughput_img_s": round(1000 / media, 2),
    }


def sha256_archivo(ruta: Path, bloque: int = 1 << 20) -> str:
    """Huella de los pesos: identifica exactamente qué modelo se evaluó y cuál sirve la API."""
    digest = hashlib.sha256()
    with ruta.open("rb") as archivo:
        while trozo := archivo.read(bloque):
            digest.update(trozo)
    return digest.hexdigest()

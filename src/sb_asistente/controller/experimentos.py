"""Controlador de la bitácora de experimentos (MLflow, ADR-022).

Convierte lo que ya producen ``sb eval``, ``sb reco baseline`` y la comparación de recuperación en
corridas de MLflow, e importa los resultados de evaluación que ya existen sin volver a llamar al LLM.

Experimentos:

- ``asistente-qa``: proveedor, modo de contexto y versión del prompt → palabras clave, cita de la
  fuente, rechazo correcto y latencia (con el CSV de respuestas como artefacto).
- ``recomendador``: líneas base de Gestión → Recall@k y NDCG@k (aquí se sumará el LightGBM, T-23).
- ``recuperacion``: método de búsqueda → hit@k.
"""

import hashlib
from collections.abc import Mapping
from pathlib import Path

from sb_asistente.config import (
    ANTHROPIC_MODEL,
    DEEPSEEK_MODEL,
    EVAL_RESULTS,
    EXPERIMENTO_QA,
    EXPERIMENTO_RECOMENDADOR,
    EXPERIMENTO_RECUPERACION,
    EXPERIMENTO_VISION,
    OLLAMA_MODEL,
)
from sb_asistente.model import evaluation
from sb_asistente.model.experimentos import Bitacora, Corrida, bitacora_por_defecto

MODELOS = {"anthropic": ANTHROPIC_MODEL, "deepseek": DEEPSEEK_MODEL, "ollama": OLLAMA_MODEL}
MODO_POR_DEFECTO = "completo"


def bitacora() -> Bitacora:
    """Bitácora vigente (punto de inyección: las pruebas la reemplazan por una nula o un doble)."""
    return bitacora_por_defecto()


def proveedor_y_modo(etiqueta: str) -> tuple[str, str]:
    """``anthropic`` → (anthropic, completo); ``anthropic-rag`` → (anthropic, rag)."""
    proveedor, _, modo = etiqueta.partition("-")
    return proveedor, modo or MODO_POR_DEFECTO


def corrida_eval(
    proveedor: str,
    modo: str,
    version: str,
    metricas: Mapping[str, object],
    csv: Path | None = None,
    etiquetas: Mapping[str, str] | None = None,
) -> Corrida:
    """Corrida del experimento ``asistente-qa`` a partir de las métricas de ``sb eval``."""
    numericas = {k: float(v) for k, v in metricas.items() if isinstance(v, int | float) and k != "preguntas"}
    return Corrida(
        experimento=EXPERIMENTO_QA,
        nombre=f"{proveedor} · {modo} · {version}",
        parametros={
            "proveedor": proveedor,
            "modelo": MODELOS.get(proveedor, proveedor),
            "modo": modo,
            "version_prompt": version,
            "preguntas": metricas.get("preguntas", ""),
        },
        metricas=numericas,
        artefactos=(csv,) if csv else (),
        etiquetas=dict(etiquetas or {}),
    )


def registrar_eval(
    proveedor: str, modo: str, version: str, metricas: Mapping[str, object], csv: Path | None = None
) -> str | None:
    """Registra una corrida de ``sb eval``; devuelve el id de MLflow o ``None`` si está apagado."""
    return bitacora().registrar(corrida_eval(proveedor, modo, version, metricas, csv, {"origen": "sb eval"}))


def registrar_baselines(
    resultado: Mapping[str, Mapping[str, float]], k: int, parametros: Mapping[str, object]
) -> list[str | None]:
    """Una corrida por línea base del recomendador (``popularidad``, ``segmento``…)."""
    return [
        bitacora().registrar(
            Corrida(
                experimento=EXPERIMENTO_RECOMENDADOR,
                nombre=f"línea base · {nombre}",
                parametros={"modelo": nombre, "k": k, "clientes_evaluados": valores.get("clientes", "")}
                | dict(parametros),
                metricas={m: float(v) for m, v in valores.items() if m != "clientes"},
                etiquetas={"origen": "sb reco baseline"},
            )
        )
        for nombre, valores in resultado.items()
    ]


def registrar_recuperacion(
    metodo: str, hit_por_k: Mapping[int, float], preguntas: int, extra: Mapping[str, float] | None = None
) -> str | None:
    """Corrida del experimento ``recuperacion``: hit@k (y recall@10, nDCG@10) de un método de búsqueda."""
    return bitacora().registrar(
        Corrida(
            experimento=EXPERIMENTO_RECUPERACION,
            nombre=metodo,
            parametros={"metodo": metodo, "preguntas_en_alcance": preguntas},
            metricas={f"hit@{k}": tasa for k, tasa in hit_por_k.items()} | dict(extra or {}),
            etiquetas={"origen": "scripts/comparar_recuperacion.py"},
        )
    )


def _huella(archivo: Path) -> str:
    return hashlib.sha256(archivo.read_bytes()).hexdigest()[:12]


def importar_evaluaciones(directorio: Path = EVAL_RESULTS.parent) -> list[tuple[str, str]]:
    """Carga en MLflow las evaluaciones guardadas (``resultados_*.csv``) sin volver a llamar al LLM.

    Es idempotente: cada archivo lleva su huella como etiqueta y no se importa dos veces.

    Returns:
        ``(archivo, estado)`` por cada CSV: ``importado``, ``ya estaba`` o ``sin bitácora``.

    """
    b = bitacora()
    estados = []
    for archivo in sorted(directorio.glob("resultados_*.csv")):
        nombre = evaluation.RESULT_FILE.match(archivo.name)
        if not nombre:  # muestras (_muestraN) u otros archivos
            continue
        origen = f"csv:{archivo.name}:{_huella(archivo)}"
        if b.existe(EXPERIMENTO_QA, "origen", origen):
            estados.append((archivo.name, "ya estaba"))
            continue
        proveedor, modo = proveedor_y_modo(nombre["modelo"])
        metricas = evaluation.aggregate(evaluation.read_results(archivo))
        run = b.registrar(
            corrida_eval(proveedor, modo, nombre["version"], metricas, archivo, {"origen": origen})
        )
        estados.append((archivo.name, "importado" if run else "sin bitácora"))
    return estados


EXPERIMENTOS: dict[str, str] = {
    EXPERIMENTO_QA: "Asistente (prompts y modos de contexto)",
    EXPERIMENTO_RECUPERACION: "Recuperación (hit@k, recall@10, nDCG@10)",
    EXPERIMENTO_RECOMENDADOR: "Recomendador (Gestión)",
    EXPERIMENTO_VISION: "YOLO de la API (calidad y latencia)",
}


def resumen() -> dict[str, list[dict[str, object]]]:
    """Corridas de cada experimento para mostrarlas en el panel (vacío si no hay bitácora)."""
    b = bitacora()
    return {nombre: b.corridas(nombre) for nombre in EXPERIMENTOS}


def activa() -> bool:
    """Indica si hay una bitácora real (MLflow instalado y activo)."""
    from sb_asistente.model.experimentos import BitacoraNula

    return not isinstance(bitacora(), BitacoraNula)

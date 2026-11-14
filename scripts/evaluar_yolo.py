"""Evalúa el modelo MaaS de la API (YOLO) y registra 3 corridas comparables en MLflow (SPEC-034).

Corridas del experimento ``vision-yolo`` (mismo dataset y mismas métricas):

1. ``yolo26l`` con umbral 0,25 (el por defecto de Ultralytics).
2. ``yolo26l`` con umbral 0,35 (el que usa la API: ``YOLO_CONFIDENCE``).
3. ``yolo26n`` con umbral 0,35 (cambio de modelo: más rápido, menos preciso).

Calidad: ``model.val`` sobre COCO128 (128 imágenes etiquetadas; Ultralytics lo descarga la primera
vez, ~7 MB, fuera del repositorio). Latencia: inferencia imagen por imagen en CPU tras calentar.

    export MLFLOW_TRACKING_URI=http://127.0.0.1:5050
    uv run --extra vision --extra mlflow python scripts/evaluar_yolo.py
"""

import argparse
import json
import tempfile
import time
from pathlib import Path

from sb_asistente.config import DATA_DIR, YOLO_CONFIDENCE
from sb_asistente.model.experimentos import Corrida, bitacora_por_defecto, commit_actual
from sb_asistente.model.vision.evaluacion import (
    LICENCIA_PESOS,
    REPO_PESOS,
    REVISION_PESOS,
    f1,
    resumen_latencias,
    sha256_archivo,
)

EXPERIMENTO = "vision-yolo"
CONFIGURACIONES = (("yolo26l", 0.25), ("yolo26l", YOLO_CONFIDENCE), ("yolo26n", YOLO_CONFIDENCE))
IMAGENES_LATENCIA = 32


def evaluar(modelo: str, umbral: float, salida: Path) -> Corrida:
    """Calidad en COCO128 + latencia por imagen de una configuración."""
    from ultralytics import YOLO

    pesos = DATA_DIR / "modelos" / f"{modelo}.pt"
    pesos.parent.mkdir(parents=True, exist_ok=True)
    yolo = YOLO(str(pesos) if pesos.is_file() else f"{modelo}.pt")
    if not pesos.is_file() and Path(f"{modelo}.pt").is_file():
        Path(f"{modelo}.pt").replace(pesos)
    nombre = f"{modelo}-conf{umbral:.2f}"
    val = yolo.val(
        data="coco128.yaml",
        conf=umbral,
        imgsz=640,
        device="cpu",
        project=str(salida),
        name=nombre,
        verbose=False,
    )
    caja = val.box
    nombres = val.names
    persona = next(i for i, n in nombres.items() if n == "person")
    indices = list(caja.ap_class_index)
    ap_persona = float(caja.ap50[indices.index(persona)]) if persona in indices else 0.0

    from ultralytics.data.utils import check_det_dataset

    carpeta = Path(check_det_dataset("coco128.yaml")["val"])
    imagenes = sorted(carpeta.glob("*.jpg"))[:IMAGENES_LATENCIA]
    yolo.predict(str(imagenes[0]), conf=umbral, device="cpu", verbose=False)  # calentamiento
    tiempos = []
    for imagen in imagenes:
        inicio = time.perf_counter()
        yolo.predict(str(imagen), conf=umbral, device="cpu", verbose=False)
        tiempos.append((time.perf_counter() - inicio) * 1000)

    metricas = {
        "precision": round(float(caja.mp), 4),
        "recall": round(float(caja.mr), 4),
        "f1": round(f1(float(caja.mp), float(caja.mr)), 4),
        "map50": round(float(caja.map50), 4),
        "map50_95": round(float(caja.map), 4),
        "ap50_person": round(ap_persona, 4),
    } | resumen_latencias(tiempos)
    reporte = Path(val.save_dir) / "reporte.json"
    reporte.write_text(
        json.dumps({"modelo": modelo, "umbral": umbral, **metricas}, indent=2), encoding="utf-8"
    )
    artefactos = [reporte] + [
        p
        for p in (
            Path(val.save_dir) / "confusion_matrix_normalized.png",
            Path(val.save_dir) / "val_batch0_pred.jpg",
        )
        if p.is_file()
    ]
    return Corrida(
        experimento=EXPERIMENTO,
        nombre=nombre,
        parametros={
            "modelo": modelo,
            "repo_rev": f"{REPO_PESOS}@{REVISION_PESOS}",
            "sha256": sha256_archivo(pesos if pesos.is_file() else Path(yolo.ckpt_path))[:16],
            "umbral_confianza": umbral,
            "imgsz": 640,
            "dataset": "coco128",
            "backend": "cpu",
            "imagenes_latencia": len(tiempos),
        },
        metricas=metricas,
        artefactos=tuple(artefactos),
        etiquetas={
            "licencia": LICENCIA_PESOS,
            "equipo": "Grupo 10 · Katherine Medina y Daniel Silva",
            "ambiente": "dev",
            "commit": commit_actual() or "",
            "spec": "SPEC-034",
            "uso_en_api": str(modelo == "yolo26l" and umbral == YOLO_CONFIDENCE).lower(),
        },
    )


def main() -> None:
    """Corre las 3 configuraciones y las registra en MLflow."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.parse_args()
    bitacora = bitacora_por_defecto()
    with tempfile.TemporaryDirectory(prefix="sb_yolo_val_") as tmp:
        for modelo, umbral in CONFIGURACIONES:
            corrida = evaluar(modelo, umbral, Path(tmp))
            run_id = bitacora.registrar(corrida)
            m = corrida.metricas
            print(
                f"{corrida.nombre:<18} P={m['precision']:.3f} R={m['recall']:.3f} F1={m['f1']:.3f} "
                f"mAP50={m['map50']:.3f} AP50(person)={m['ap50_person']:.3f} "
                f"p95={m['latencia_p95_ms']:.0f} ms · run {run_id}"
            )


if __name__ == "__main__":
    main()

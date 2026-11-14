"""Registra en el Model Registry de MLflow el YOLO que carga la API (SPEC-035).

Crea una versión de ``sb-yolo-difuminado`` (pyfunc con los pesos como artefacto), le pone el alias
``produccion`` y tags con ``repo@rev``, sha256, licencia y umbral, enlazada a la corrida de
evaluación del mismo modelo (experimento ``vision-yolo``).

    export MLFLOW_TRACKING_URI=http://127.0.0.1:5050
    uv run --extra vision --extra mlflow python scripts/registrar_yolo.py
"""

import base64
import io

import mlflow
import pandas as pd
from mlflow import MlflowClient
from mlflow.models import infer_signature
from PIL import Image

from sb_asistente.config import MLFLOW_TRACKING_URI, YOLO_CONFIDENCE, YOLO_MODEL_PATH
from sb_asistente.model.experimentos import commit_actual
from sb_asistente.model.vision.evaluacion import LICENCIA_PESOS, REPO_PESOS, REVISION_PESOS, sha256_archivo
from sb_asistente.model.vision.registro import ALIAS, COLUMNAS, NOMBRE_REGISTRO, ModeloYolo

EXPERIMENTO = "vision-yolo"


def ejemplo() -> pd.DataFrame:
    """Imagen pequeña en base64 como ejemplo de entrada (sin personas ni datos)."""
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), "white").save(buffer, format="PNG")
    return pd.DataFrame({"imagen_b64": [base64.b64encode(buffer.getvalue()).decode("ascii")]})


def main() -> None:
    """Registra la versión, pone el alias y los tags de trazabilidad."""
    if not YOLO_MODEL_PATH.is_file():
        raise SystemExit(
            f"No están los pesos en {YOLO_MODEL_PATH}: levante la API una vez o corra make mlflow-yolo."
        )
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENTO)
    huella = sha256_archivo(YOLO_MODEL_PATH)
    cliente = MlflowClient()
    evaluacion = cliente.search_runs(
        [mlflow.get_experiment_by_name(EXPERIMENTO).experiment_id],
        filter_string=f"tags.uso_en_api = 'true' and params.umbral_confianza = '{YOLO_CONFIDENCE}'",
        max_results=1,
    )
    salida = pd.DataFrame([[0, "car", 0.9, 1.0, 2.0, 30.0, 40.0]], columns=COLUMNAS)
    with mlflow.start_run(run_name=f"registro-{YOLO_MODEL_PATH.stem}") as corrida:
        mlflow.log_params(
            {
                "modelo": YOLO_MODEL_PATH.stem,
                "repo_rev": f"{REPO_PESOS}@{REVISION_PESOS}",
                "umbral_confianza": YOLO_CONFIDENCE,
            }
        )
        mlflow.set_tags(
            {
                "licencia": LICENCIA_PESOS,
                "sha256": huella,
                "commit": commit_actual() or "",
                "spec": "SPEC-035",
            }
        )
        info = mlflow.pyfunc.log_model(
            name="modelo",
            python_model=ModeloYolo(),
            artifacts={"pesos": str(YOLO_MODEL_PATH)},
            signature=infer_signature(ejemplo(), salida),
            input_example=ejemplo(),
            registered_model_name=NOMBRE_REGISTRO,
        )
    version = info.registered_model_version
    cliente.set_registered_model_alias(NOMBRE_REGISTRO, ALIAS, version)
    etiquetas = {
        "repo_rev": f"{REPO_PESOS}@{REVISION_PESOS}",
        "sha256": huella,
        "licencia": LICENCIA_PESOS,
        "umbral_confianza": str(YOLO_CONFIDENCE),
        "corrida_registro": corrida.info.run_id,
        "corrida_evaluacion": evaluacion[0].info.run_id if evaluacion else "",
    }
    for clave, valor in etiquetas.items():
        cliente.set_model_version_tag(NOMBRE_REGISTRO, version, clave, valor)
    cliente.update_registered_model(
        NOMBRE_REGISTRO,
        description="YOLO26-L de Ultralytics que sirve POST /fotos; las personas detectadas se difuminan.",
    )
    print(
        f"{NOMBRE_REGISTRO} v{version} @{ALIAS} · sha256 {huella[:16]}",
        f"· evaluación {etiquetas['corrida_evaluacion']}",
    )


if __name__ == "__main__":
    main()

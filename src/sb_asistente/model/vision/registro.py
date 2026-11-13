"""Model Registry: el YOLO que sirve la API, empaquetado como modelo ``pyfunc`` de MLflow.

``ModeloYolo`` recibe imágenes en base64 y devuelve las detecciones (clase, confianza y caja),
con el mismo umbral de la API. Los pesos viajan como artefacto del modelo registrado y su sha256
queda en los tags de la versión, para comprobar que es el mismo archivo que carga el backend
(``GET /health`` → ``modelo_yolo_sha256``).

Requiere el extra ``mlflow`` (y ``vision`` para predecir).
"""

import base64
from collections.abc import Callable

import mlflow.pyfunc
import pandas as pd

from sb_asistente.config import YOLO_CONFIDENCE

NOMBRE_REGISTRO = "sb-yolo-difuminado"
ALIAS = "produccion"
COLUMNAS = ["imagen", "clase", "confianza", "x_min", "y_min", "x_max", "y_max"]


class ModeloYolo(mlflow.pyfunc.PythonModel):
    """Envoltorio ``pyfunc``: carga los pesos del artefacto ``pesos`` y detecta objetos."""

    def __init__(
        self, umbral: float = YOLO_CONFIDENCE, fabrica: Callable[[str], object] | None = None
    ) -> None:
        """``fabrica(ruta)`` crea el detector (inyectable en las pruebas; por defecto ``YOLO``)."""
        self.umbral = umbral
        self.fabrica = fabrica
        self.yolo: object | None = None

    def load_context(self, context: mlflow.pyfunc.PythonModelContext) -> None:
        """Carga el modelo una sola vez desde los artefactos del modelo registrado."""
        if self.fabrica is None:
            from ultralytics import YOLO

            self.fabrica = YOLO
        self.yolo = self.fabrica(context.artifacts["pesos"])

    def predict(  # noqa: ARG002 - firma de mlflow.pyfunc
        self, context: mlflow.pyfunc.PythonModelContext, model_input: pd.DataFrame, params: dict | None = None
    ) -> pd.DataFrame:
        """``model_input['imagen_b64']`` → una fila por detección."""
        import io

        from PIL import Image

        filas = []
        for i, codificada in enumerate(model_input["imagen_b64"]):
            imagen = Image.open(io.BytesIO(base64.b64decode(codificada))).convert("RGB")
            resultado = self.yolo.predict(imagen, conf=self.umbral, verbose=False)[0]
            nombres = resultado.names
            for caja, clase, confianza in zip(
                resultado.boxes.xyxy.tolist(),
                resultado.boxes.cls.tolist(),
                resultado.boxes.conf.tolist(),
                strict=True,
            ):
                filas.append(
                    [i, nombres[int(clase)], round(float(confianza), 4), *[round(v, 1) for v in caja]]
                )
        return pd.DataFrame(filas, columns=COLUMNAS)

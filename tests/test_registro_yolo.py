"""Pruebas del envoltorio pyfunc del Model Registry y del sha256 en /health (sin ultralytics)."""

import base64
import io
from types import SimpleNamespace

import pytest
from PIL import Image

from sb_asistente.controller import salud

pd = pytest.importorskip("pandas")
pytest.importorskip("mlflow")
from sb_asistente.model.vision.registro import COLUMNAS, ModeloYolo  # noqa: E402


class Lista(list):
    def tolist(self):
        return list(self)


class YoloFalso:
    def __init__(self, ruta):
        self.ruta = ruta
        self.umbrales = []

    def predict(self, imagen, conf, verbose):
        self.umbrales.append(conf)
        cajas = SimpleNamespace(
            xyxy=Lista([[1.0, 2.0, 30.0, 40.0]]), cls=Lista([2.0]), conf=Lista([0.876543])
        )
        return [SimpleNamespace(names={2: "car"}, boxes=cajas)]


def imagen_b64() -> str:
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), "white").save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def test_el_envoltorio_carga_los_pesos_del_artefacto_y_detecta():
    # Arrange
    modelo = ModeloYolo(umbral=0.35, fabrica=YoloFalso)
    modelo.load_context(SimpleNamespace(artifacts={"pesos": "/ruta/yolo26l.pt"}))
    # Act
    salida = modelo.predict(None, pd.DataFrame({"imagen_b64": [imagen_b64()]}))
    # Assert
    assert modelo.yolo.ruta == "/ruta/yolo26l.pt"
    assert list(salida.columns) == COLUMNAS
    assert salida.iloc[0]["clase"] == "car" and salida.iloc[0]["confianza"] == 0.8765
    assert modelo.yolo.umbrales == [0.35]


def test_huella_de_los_pesos_para_comparar_con_el_registry(tmp_path):
    # Arrange
    pesos = tmp_path / "yolo.pt"
    pesos.write_bytes(b"pesos")
    # Act
    huella = salud.huella_yolo(pesos)
    # Assert
    assert huella is not None and len(huella) == 16
    assert salud.huella_yolo(tmp_path / "no-existe.pt") is None

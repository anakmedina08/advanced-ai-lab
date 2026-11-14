"""Pruebas de las métricas de la evaluación de YOLO (sin ultralytics ni red)."""

import hashlib

import pytest

from sb_asistente.model.vision.evaluacion import f1, percentil, resumen_latencias, sha256_archivo


def test_percentil_interpola_como_numpy():
    # Arrange
    valores = [10.0, 20.0, 30.0, 40.0, 50.0]
    # Act / Assert
    assert percentil(valores, 50) == 30.0
    assert percentil(valores, 95) == pytest.approx(48.0)
    assert percentil([7.0], 95) == 7.0


def test_percentil_valida_la_entrada():
    # Act / Assert
    with pytest.raises(ValueError, match="No hay valores"):
        percentil([], 95)
    with pytest.raises(ValueError, match="entre 0 y 100"):
        percentil([1.0], 101)


def test_f1_es_la_media_armonica():
    # Assert
    assert f1(0.8, 0.6) == pytest.approx(0.6857, abs=1e-4)
    assert f1(0.0, 0.0) == 0.0


def test_resumen_de_latencias_y_throughput():
    # Act
    r = resumen_latencias([100.0, 200.0, 300.0, 400.0])
    # Assert
    assert r["latencia_media_ms"] == 250.0
    assert r["latencia_p95_ms"] == 385.0
    assert r["throughput_img_s"] == 4.0


def test_sha256_identifica_los_pesos(tmp_path):
    # Arrange
    pesos = tmp_path / "yolo.pt"
    pesos.write_bytes(b"pesos de prueba")
    # Act / Assert
    assert sha256_archivo(pesos, bloque=4) == hashlib.sha256(b"pesos de prueba").hexdigest()

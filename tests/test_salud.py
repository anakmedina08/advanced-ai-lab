"""Pruebas de ``GET /health``: estado agregado sin cargar modelos ni usar la red."""

from fastapi.testclient import TestClient

from sb_asistente.controller import salud
from sb_asistente.view.api import app


def test_componentes_reporta_lo_que_falta(tmp_path):
    # Arrange
    chunks = tmp_path / "chunks.jsonl"
    chunks.write_text("{}", encoding="utf-8")
    # Act
    estado = salud.componentes(
        chunks=chunks,
        reco_dir=tmp_path / "reco",
        qdrant_dir=tmp_path / "qdrant",
        memoria=tmp_path / "memoria" / "x.sqlite",
        yolo=tmp_path / "yolo.pt",
    )
    # Assert
    assert estado["corpus"] is True
    assert estado["recomendador"] is False
    assert estado["indice_qdrant"] is False
    assert estado["modelo_yolo"] is False


def test_reporte_degradado_si_falta_un_obligatorio():
    # Arrange
    estado = {"corpus": True, "recomendador": False, "modelo_yolo": True}
    # Act
    r = salud.reporte("1.0", estado, llm="anthropic")
    # Assert
    assert r.status == "degradado"


def test_reporte_ok_si_estan_los_obligatorios_aunque_falte_un_opcional():
    # Arrange
    estado = {"corpus": True, "recomendador": True, "modelo_yolo": False}
    # Act
    r = salud.reporte("1.0", estado, llm="anthropic")
    # Assert
    assert r.status == "ok"


def test_yolo_cargado_en_memoria_tiene_prioridad_sobre_el_archivo(tmp_path):
    # Act
    estado = salud.componentes(yolo=tmp_path / "no-existe.pt", yolo_cargado=True)
    # Assert
    assert estado["modelo_yolo"] is True


def test_endpoint_health_responde_con_el_contrato():
    # Arrange
    cliente = TestClient(app)
    # Act
    r = cliente.get("/health")
    # Assert
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["status"] in {"ok", "degradado"}
    assert {"corpus", "recomendador", "indice_qdrant", "modelo_yolo"} <= set(cuerpo["componentes"])
    assert cuerpo["version"] == app.version

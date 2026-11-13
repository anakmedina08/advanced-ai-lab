"""Pruebas de ``GET /proyecto`` (entregables por curso)."""

from fastapi.testclient import TestClient

from sb_asistente.controller import proyecto
from sb_asistente.model.proyecto import Contadores, Requisito
from sb_asistente.view.api import app


def test_entregables_por_curso_con_cifras(monkeypatch):
    # Arrange
    req = Requisito("Gestión", "Mínimo 40 specs", "cumplido", "`openspec/specs/`")
    monkeypatch.setattr(proyecto, "requisitos_por_seccion", lambda: {"Gestión": [req]})
    monkeypatch.setattr(proyecto, "contadores", lambda: Contadores(540, 43, 45, 22, 63, 11))
    monkeypatch.setattr(proyecto, "corridas_mlflow", lambda: 23)
    # Act
    r = TestClient(app).get("/proyecto")
    # Assert
    cuerpo = r.json()
    assert r.status_code == 200
    assert cuerpo["secciones"]["Gestión"][0] == {
        "requisito": "Mínimo 40 specs",
        "estado": "cumplido",
        "evidencia": "`openspec/specs/`",
    }
    assert cuerpo["contadores"]["specs"] == 45 and cuerpo["corridas_mlflow"] == 23
    assert "Repositorio" in cuerpo["enlaces"]


def test_la_matriz_real_se_lee_sin_errores():
    # Act
    r = TestClient(app).get("/proyecto")
    # Assert
    assert r.status_code == 200
    assert len(r.json()["secciones"]) == 3

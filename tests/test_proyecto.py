"""Pruebas de la página de sustentación y de la de experimentos (sin red, sin API y sin MLflow)."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from sb_asistente.controller import experimentos as ctrl_experimentos
from sb_asistente.controller import proyecto
from sb_asistente.model import proyecto as modelo

APP = Path(__file__).resolve().parents[1] / "app.py"
PAGINA = "src/sb_asistente/view/app_pages/{}.py"

MATRIZ = """# Matriz

## Gestión de Proyectos en IA y CD

| Requisito | Estado | Evidencia |
|---|---|---|
| FastAPI con contratos Pydantic | ✅ | `view/api.py` |
| MLflow | 🟡 | `sb mlflow ui` |

## Técnicas Avanzadas de IA en Modelos de Lenguaje

| Requisito | Estado | Evidencia |
|---|---|---|
| Módulo 2 · LangChain | ✅ | `model/llm/service.py` |
| Clasificador entrenado | ⏳ | T-27 |
"""


def proyecto_falso(raiz: Path) -> Path:
    (raiz / "tests").mkdir()
    (raiz / "tests" / "test_a.py").write_text(
        "def test_uno():\n    pass\n\nasync def test_dos():\n    pass\n"
    )
    (raiz / "tests" / "test_b.py").write_text("def ayuda():\n    pass\n\ndef test_tres():\n    pass\n")
    for spec, tareas in (
        ("uno", "- [x] T-01 [ml] A (K)\n- [ ] T-02 [ml] B (D)\n"),
        ("dos", "- [x] T-03 [ui] C (K)\n"),
    ):
        (raiz / "openspec" / "specs" / spec).mkdir(parents=True)
        (raiz / "openspec" / "specs" / spec / "spec.md").write_text("# Spec")
        (raiz / "openspec" / "specs" / spec / "tasks.md").write_text(tareas)
    (raiz / "docs" / "decisiones").mkdir(parents=True)
    for n in (1, 2, 3):
        (raiz / "docs" / "decisiones" / f"ADR-00{n}-x.md").write_text("# ADR")
    return raiz


# --- Modelo -------------------------------------------------------------------------------------
def test_leer_requisitos_por_seccion_y_estado(tmp_path):
    ruta = tmp_path / "requisitos.md"
    ruta.write_text(MATRIZ, encoding="utf-8")
    reqs = modelo.leer_requisitos(ruta)
    assert [(r.seccion[:7], r.estado) for r in reqs] == [
        ("Gestión", "cumplido"),
        ("Gestión", "en curso"),
        ("Técnica", "cumplido"),
        ("Técnica", "pendiente"),
    ]
    assert reqs[0].evidencia == "`view/api.py`"


def test_contar_pruebas_specs_adr_y_tareas(tmp_path):
    cifras = modelo.contar(proyecto_falso(tmp_path))
    assert (cifras.funciones_de_prueba, cifras.archivos_de_prueba) == (3, 2)
    assert (cifras.specs, cifras.adr, cifras.tareas_hechas, cifras.tareas_pendientes) == (2, 3, 2, 1)


def test_la_matriz_real_tiene_los_tres_grupos_y_cumple_el_minimo_de_pruebas():
    secciones = proyecto.requisitos_por_seccion()
    assert {"Gestión de Proyectos en IA y CD", "Técnicas Avanzadas de IA en Modelos de Lenguaje"} <= set(
        secciones
    )
    assert proyecto.contadores().funciones_de_prueba >= 120


# --- Páginas ------------------------------------------------------------------------------------
def app() -> AppTest:
    return AppTest.from_file(str(APP), default_timeout=120).run()


def test_sustentacion_muestra_las_cifras_y_una_pestana_por_curso():
    at = app().switch_page(PAGINA.format("sustentacion")).run()
    assert not at.exception
    assert [m.label for m in at.metric][:3] == ["Pruebas automatizadas", "Specs (SDD)", "Decisiones (ADR)"]
    assert len(at.tabs) == 3 and "Gestión" in at.tabs[0].label


def test_sustentacion_filtra_por_estado():
    at = app().switch_page(PAGINA.format("sustentacion")).run()
    todos = len(at.tabs[0].caption)  # una evidencia (caption) por tarjeta
    at.tabs[0].get("button_group")[0].set_value(["pendiente"]).run()
    assert 0 < len(at.tabs[0].caption) < todos


def test_experimentos_sin_mlflow_explica_como_activarlo():
    at = app().switch_page(PAGINA.format("experimentos")).run()
    assert not at.exception and "uv sync --extra mlflow" in at.info[0].value


class FakeBitacora:
    def registrar(self, corrida):
        return None

    def existe(self, experimento, etiqueta, valor):
        return False

    def corridas(self, experimento):
        if experimento != "asistente-qa":
            return []
        return [
            {"nombre": f"anthropic · completo · {v}", "fecha": 1_731_500_000_000, "commit": "abc1234",
             "parametros": {"proveedor": "anthropic", "modo": "completo", "version_prompt": v},
             "metricas": {"tasa_cita_fuente": cita, "tasa_fallback_correcto": 0.9, "keyword_hit_promedio": 1.0}}  # noqa: E501
            for v, cita in (("v1", 0.2), ("v3", 1.0))
        ]  # fmt: skip


@pytest.fixture
def con_bitacora(monkeypatch):
    monkeypatch.setattr(ctrl_experimentos, "bitacora", lambda: FakeBitacora())


def test_experimentos_compara_las_corridas_con_nombres_cortos(con_bitacora):
    at = app().switch_page(PAGINA.format("experimentos")).run()
    assert not at.exception and at.metric[0].value == "2"
    assert list(at.dataframe[0].value["corrida"]) == ["completo · v1", "completo · v3"]


def test_experimento_sin_corridas_lo_dice(con_bitacora):
    at = app().switch_page(PAGINA.format("experimentos")).run()
    at.get("button_group")[0].set_value("recomendador").run()
    assert "aún no tiene corridas" in at.info[0].value


def test_estado_no_planeado_se_lee_de_la_matriz(tmp_path):
    # Arrange
    from sb_asistente.model.proyecto import leer_requisitos

    ruta = tmp_path / "requisitos.md"
    ruta.write_text(
        "## Gestión\n\n| Requisito | Estado | Evidencia |\n|---|---|---|\n"
        "| Auditoría de sesgo | ⛔ | T-25 |\n",
        encoding="utf-8",
    )
    # Act
    filas = leer_requisitos(ruta)
    # Assert
    assert filas[0].estado == "no planeado"

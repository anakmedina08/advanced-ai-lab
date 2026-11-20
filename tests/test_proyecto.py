"""Pruebas de la matriz de requisitos y de los contadores del proyecto (sin red ni API)."""

from pathlib import Path

from sb_asistente.controller import proyecto
from sb_asistente.model import proyecto as modelo

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

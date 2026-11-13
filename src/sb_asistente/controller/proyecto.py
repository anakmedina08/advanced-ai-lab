"""Controlador de la página de sustentación: requisitos por curso, contadores y enlaces."""

from sb_asistente.controller import experimentos
from sb_asistente.model.proyecto import Contadores, Requisito, contar, leer_requisitos

__all__ = ["ENLACES", "Contadores", "Requisito", "contadores", "corridas_mlflow", "requisitos_por_seccion"]

REPO = "https://github.com/anakmedina08/advanced-ai-lab"
ENLACES = {
    "Repositorio": REPO,
    "Tablero (GitHub Projects)": "https://github.com/users/anakmedina08/projects/2",
    "Pull Requests": f"{REPO}/pulls?q=is%3Apr",
    "CI (GitHub Actions)": f"{REPO}/actions",
    "Specs": f"{REPO}/tree/main/openspec/specs",
}


def requisitos_por_seccion() -> dict[str, list[Requisito]]:
    """Requisitos de ``docs/requisitos.md`` agrupados por curso, en el orden del documento."""
    secciones: dict[str, list[Requisito]] = {}
    for r in leer_requisitos():
        secciones.setdefault(r.seccion, []).append(r)
    return secciones


def contadores() -> Contadores:
    """Pruebas, specs, ADR y tareas calculadas del repositorio al momento."""
    return contar()


def corridas_mlflow() -> int | None:
    """Corridas registradas en MLflow, o ``None`` si la bitácora no está activa."""
    if not experimentos.activa():
        return None
    return sum(len(c) for c in experimentos.resumen().values())

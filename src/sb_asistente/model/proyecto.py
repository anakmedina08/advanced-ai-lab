"""Estado del proyecto para la sustentación: requisitos por curso y contadores calculados en vivo.

La fuente única es ``docs/requisitos.md`` (tablas «Requisito | Estado | Evidencia» bajo un título
``##`` por curso); los contadores se calculan del repositorio, nunca se escriben a mano.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from sb_asistente.config import PROJECT_ROOT

REQUISITOS_MD = PROJECT_ROOT / "docs" / "requisitos.md"
ESTADOS = {"✅": "cumplido", "🟡": "en curso", "⏳": "pendiente"}
_FILA = re.compile(
    r"^\|\s*(?P<requisito>[^|]+?)\s*\|\s*(?P<estado>✅|🟡|⏳)\s*\|\s*(?P<evidencia>.*?)\s*\|\s*$"
)
_TAREA = re.compile(r"^- \[(?P<hecha>[ x])\] T-\d+ ")
_PRUEBA = re.compile(r"^\s*(?:async\s+)?def test_\w+", re.MULTILINE)


@dataclass(frozen=True, slots=True)
class Requisito:
    """Una fila de la matriz: requisito de un curso, su estado y dónde está la evidencia."""

    seccion: str
    requisito: str
    estado: str  # cumplido · en curso · pendiente
    evidencia: str


@dataclass(frozen=True, slots=True)
class Contadores:
    """Cifras del repositorio calculadas al momento."""

    funciones_de_prueba: int
    archivos_de_prueba: int
    specs: int
    adr: int
    tareas_hechas: int
    tareas_pendientes: int


def leer_requisitos(ruta: Path = REQUISITOS_MD) -> list[Requisito]:
    """Filas de las tablas de requisitos, con el título ``##`` bajo el que aparecen."""
    seccion, requisitos = "", []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.startswith("## "):
            seccion = linea[3:].strip()
            continue
        fila = _FILA.match(linea)
        if fila and seccion:
            requisitos.append(
                Requisito(seccion, fila["requisito"], ESTADOS[fila["estado"]], fila["evidencia"])
            )
    return requisitos


def contar(raiz: Path = PROJECT_ROOT) -> Contadores:
    """Pruebas, specs, decisiones y tareas tal como están hoy en el repositorio."""
    pruebas = sorted((raiz / "tests").glob("test_*.py"))
    tareas = [
        linea
        for tasks in (raiz / "openspec" / "specs").glob("*/tasks.md")
        for linea in tasks.read_text(encoding="utf-8").splitlines()
        if _TAREA.match(linea)
    ]
    hechas = sum(1 for t in tareas if t.startswith("- [x]"))
    return Contadores(
        funciones_de_prueba=sum(len(_PRUEBA.findall(p.read_text(encoding="utf-8"))) for p in pruebas),
        archivos_de_prueba=len(pruebas),
        specs=len(list((raiz / "openspec" / "specs").glob("*/spec.md"))),
        adr=len(list((raiz / "docs" / "decisiones").glob("ADR-*.md"))),
        tareas_hechas=hechas,
        tareas_pendientes=len(tareas) - hechas,
    )

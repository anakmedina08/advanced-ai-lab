"""Métricas de flujo del tablero Kanban: WIP, throughput, edad de lo abierto y cycle time.

Funciones puras sobre las historias (número, estado del tablero, fecha de creación y de cierre)
para poder probarlas con fechas fijas. ``scripts/metricas_kanban.py`` las alimenta con GitHub.

- **WIP**: historias en *In progress* o *In review* (empezadas y no terminadas).
- **Throughput**: historias cerradas por semana ISO.
- **Work item age**: días desde que la historia empezó y sigue abierta.
- **Cycle time**: días entre el inicio (la historia se crea al empezar, con su spec) y el cierre.
"""

from collections import Counter
from dataclasses import dataclass
from datetime import datetime

ACTIVOS = ("In progress", "In review")
LIMITES_WIP = {"In progress": 2, "In review": 2}


@dataclass(frozen=True, slots=True)
class Historia:
    """Una tarjeta del tablero."""

    numero: int
    titulo: str
    estado: str
    creada: datetime
    cerrada: datetime | None = None


@dataclass(frozen=True, slots=True)
class Metricas:
    """Resumen de flujo del tablero."""

    wip: dict[str, int]
    throughput_semanal: dict[str, int]
    edad_dias: dict[int, float]
    cycle_time_mediana_h: float | None
    cycle_time_p85_h: float | None
    cerradas: int


def _percentil(valores: list[float], p: float) -> float:
    ordenados = sorted(valores)
    posicion = (len(ordenados) - 1) * p / 100
    abajo = int(posicion)
    arriba = min(abajo + 1, len(ordenados) - 1)
    return ordenados[abajo] + (ordenados[arriba] - ordenados[abajo]) * (posicion - abajo)


def calcular(historias: list[Historia], ahora: datetime) -> Metricas:
    """Calcula las cuatro métricas de flujo."""
    wip = Counter(h.estado for h in historias if h.estado in ACTIVOS and h.cerrada is None)
    cerradas = [h for h in historias if h.cerrada is not None]
    semanas = Counter(f"{h.cerrada.isocalendar().year}-S{h.cerrada.isocalendar().week:02d}" for h in cerradas)
    edad = {
        h.numero: round((ahora - h.creada).total_seconds() / 86400, 2)
        for h in historias
        if h.cerrada is None and h.estado in ACTIVOS
    }
    ciclos = [(h.cerrada - h.creada).total_seconds() / 3600 for h in cerradas]
    return Metricas(
        wip={estado: wip.get(estado, 0) for estado in ACTIVOS},
        throughput_semanal=dict(sorted(semanas.items())),
        edad_dias=edad,
        cycle_time_mediana_h=round(_percentil(ciclos, 50), 1) if ciclos else None,
        cycle_time_p85_h=round(_percentil(ciclos, 85), 1) if ciclos else None,
        cerradas=len(cerradas),
    )


def excede_wip(metricas: Metricas) -> dict[str, int]:
    """Columnas que superan su límite WIP y por cuánto."""
    return {c: n - LIMITES_WIP[c] for c, n in metricas.wip.items() if n > LIMITES_WIP[c]}

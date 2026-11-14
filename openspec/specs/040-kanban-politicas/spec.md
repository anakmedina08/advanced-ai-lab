# SPEC-040 · Políticas del tablero Kanban: WIP, historias y métricas

> Curso: Gestión M3 (Kanban) · Story points: **3** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
El tablero tiene columnas y tarjetas, pero sin límites WIP escritos, sin plantilla de historia y sin las métricas que se preguntan (WIP, throughput, edad, cycle time).

## Historia
**Como** equipo y profesor, **quiero** ver las políticas del tablero y sus métricas calculadas, **para** gestionar el flujo y explicarlo en la sustentación.

## Requisitos
- **R040.1** Las columnas DEBEN describir su límite WIP (In progress = 2, In review = 2) en el tablero.
- **R040.2** DEBE existir una plantilla de issue «Historia» con Como/quiero/para, criterios Dado/Cuando/Entonces, puntos Fibonacci y enlace a la spec.
- **R040.3** `scripts/metricas_kanban.py` DEBE calcular WIP, throughput semanal, edad de lo abierto y cycle time desde GitHub y escribir `docs/kanban.md`.
- **R040.4** El README DEBE enlazar el tablero.

## Criterios de aceptación
- **AC1** · **Dado** el script ejecutado, **cuando** se abre `docs/kanban.md`, **entonces** están las 4 métricas con sus valores y fecha.

## Fuera de alcance
Automatizar movimientos del tablero.

## Métricas de éxito
Las 4 métricas visibles y explicadas.

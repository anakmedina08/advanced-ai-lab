# SPEC-047 · Cierre para la sustentación: matriz al día, estado «no planeado» y tablero sin pendientes

> Curso: Gestión M3 (Kanban) · Técnicas M2 · Story points: **2** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
El profesor pide cero issues y cero PR abiertas; las tareas que no se harán deben cerrarse como «not planned» y la matriz de Entregables debe reflejarlo (hoy solo admite cumplido, en curso y pendiente).

## Historia
**Como** jurado de la sustentación, **quiero** ver en Entregables el estado real tras fusionar las PR y cerrar el tablero, **para** evaluar el proyecto con información exacta.

## Requisitos
- **R047.1** `docs/requisitos.md` DEBE admitir el estado ⛔ «no planeado» (cerrado como *not planned*) y la app DEBE mostrarlo y filtrarlo.
- **R047.2** La matriz DEBE reflejar 48 PR fusionadas, 47 specs, el cierre del tablero y las tareas no planeadas con su motivo.
- **R047.3** `docs/kanban.md` DEBE regenerarse con las métricas actuales.

## Criterios de aceptación
- **AC1** · **Dado** un requisito con ⛔, **cuando** se abre Entregables, **entonces** aparece con la insignia «No planeado» y se puede filtrar.

## Fuera de alcance
Hacer las tareas no planeadas.

## Métricas de éxito
0 issues y 0 PR abiertas; matriz sin estados desactualizados.

# SPEC-018 · CI en las PR apiladas (base feature/*)

> Curso: Gestión M3 (QA y Git) · Story points: **1** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
Las PR que dependen de otra se abren contra la rama anterior (`feature/*`) y la CI solo corre si la base es `develop` o `main`: esas PR quedan sin checks y no se pueden revisar con evidencia.

## Historia
**Como** Code Reviewer, **quiero** ver ruff y pytest en verde en cada PR, aunque su base sea otra rama de historia, **para** aprobar con evidencia y no fusionar nada sin checks.

## Requisitos
- **R018.1** El workflow de CI DEBE correr en `pull_request` con base `main`, `develop` o `feature/**`.
- **R018.2** El job de Docker y el evento al panel NO DEBEN cambiar.

## Criterios de aceptación
- **AC1** · **Dado** una PR con base `feature/017-agente-enrutado`, **cuando** se actualiza, **entonces** corre el job «Ruff + Pytest».

## Fuera de alcance
Despliegue continuo.

## Métricas de éxito
100 % de las PR abiertas con checks.

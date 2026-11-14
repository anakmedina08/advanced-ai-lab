# SPEC-030 · Pruebas del frontend con Vitest y Testing Library

> Curso: Gestión M3 (QA) · Técnicas M2 (3.2) · Story points: **3** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
El frontend no tiene pruebas automáticas; la rúbrica pide pruebas de UI.

## Historia
**Como** Code Reviewer, **quiero** una suite de pruebas del frontend que corra sin backend, **para** aprobar cambios de la interfaz con evidencia.

## Requisitos
- **R030.1** `npm test` DEBE correr Vitest con jsdom y Testing Library sin red.
- **R030.2** DEBE cubrir el parser SSE, el manejo de `ApiError`, el reducer del chat, el panel del router, la validación de la foto y el plegado responsive.

## Criterios de aceptación
- **AC1** · **Dado** el repositorio, **cuando** se ejecuta `npm test`, **entonces** todas las pruebas pasan sin backend.

## Fuera de alcance
Pruebas end-to-end con navegador (Playwright).

## Métricas de éxito
≥ 15 pruebas del frontend en verde.

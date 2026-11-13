# SPEC-031 · CI del frontend: tipos, pruebas y build

> Curso: Gestión M3 (QA y Git) · Story points: **2** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
La CI solo revisa Python; un cambio que rompa el frontend pasaría sin aviso.

## Historia
**Como** Code Reviewer, **quiero** un job de CI que compile y pruebe el frontend, **para** no fusionar PR que rompan la interfaz.

## Requisitos
- **R031.1** El workflow DEBE tener un job «Frontend» con Node 20: `npm ci`, `npm test` y `npm run build`.
- **R031.2** DEBE correr en las mismas ramas que el job de Python.

## Criterios de aceptación
- **AC1** · **Dado** una PR que rompe un tipo, **cuando** corre la CI, **entonces** el job «Frontend» falla.

## Fuera de alcance
Publicar el build.

## Métricas de éxito
Job en verde en todas las PR del frontend.

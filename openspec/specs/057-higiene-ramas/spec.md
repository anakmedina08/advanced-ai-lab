# SPEC-057 · Solo main y develop como ramas permanentes

> Curso: Gestión M3/M4 (Gitflow limpio, recomendación del profesor) · Story points: **3** · Responsable: Daniel ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
El profesor recomendó dejar el repositorio solo con `main` y `develop`. Las ramas `feature/*` de PRs ya fusionados seguían en el remoto y nada las borraba. Además, `CONTRIBUTING.md` seguía describiendo PRs hacia `main` y un único revisor.

## Historia
**Como** equipo, **quiero** que las ramas de trabajo desaparezcan al fusionarse, **para** que el repo quede limpio y el flujo Gitflow se lea a simple vista.

## Requisitos
- **R057.1** El workflow `ramas.yml` DEBE borrar la rama de un PR fusionado si no es `main` ni `develop`, no tiene otro PR abierto y es del mismo repositorio.
- **R057.2** Cada semana DEBE publicar en el resumen del job las ramas distintas de `main`/`develop` y si tienen PR abierto.
- **R057.3** NUNCA DEBE borrar `main`, `develop` ni ramas con PR abierto.
- **R057.4** `CONTRIBUTING.md` DEBE describir Gitflow (`feature/*` → `develop` → `main`), la revisión cruzada y la limpieza de ramas.
- **R057.5** La puerta de madurez de la CI DEBE subir al nivel alcanzado en esta oleada.

## Criterios de aceptación
- **AC1** · **Dado** un PR fusionado desde `feature/x`, **cuando** se cierra, **entonces** la rama `feature/x` desaparece del remoto.
- **AC2** · **Dado** un PR cerrado sin fusionar, **cuando** se cierra, **entonces** la rama se conserva.
- **AC3** · **Dado** `git ls-remote --heads origin` después de la limpieza inicial, **cuando** no hay PRs abiertos, **entonces** solo aparecen `main` y `develop`.

## Fuera de alcance
La limpieza inicial de las ramas viejas y el ajuste «Automatically delete head branches» (los hace una persona del equipo, con los comandos del PR).

## Métricas de éxito
Remoto con solo `main`, `develop` y ramas con PR abierto; P9 en ✅.

# SPEC-050 · Commits y PRs a nombre de las personas, sin coautor de IA

> Curso: Gestión M3/M4 (Git y gobernanza) · Técnicas M3 (gobernanza) · Story points: **3** · Responsable: Daniel ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
98 commits de `develop` muestran a Claude como coautor y GitHub lo lista como contributor. La entrega se califica por el trabajo de cada integrante (piso de 8 PR por persona), y la atribución dependía de la configuración de cada máquina.

## Historia
**Como** integrante del equipo, **quiero** que los commits y PRs queden solo a nombre de quien los hace, **para** que la autoría del repositorio sea clara y el uso de IA se declare en un solo lugar.

## Requisitos
- **R050.1** `.claude/settings.json` DEBE fijar `attribution` vacío para commits y PRs en el proyecto.
- **R050.2** El hook `commit-msg` DEBE eliminar `Co-Authored-By` de asistentes de IA, `Claude-Session` y «Generated with Claude Code» antes de validar Conventional Commits.
- **R050.3** El filtro NO DEBE tocar coautores humanos y DEBE ser idempotente.
- **R050.4** Push, creación y fusión de PRs desde el agente DEBEN pedir aprobación (`ask`).
- **R050.5** La decisión DEBE quedar en un ADR.

## Criterios de aceptación
- **AC1** · **Dado** un mensaje con `Co-Authored-By: Claude …`, **cuando** se hace commit, **entonces** el commit queda sin esa línea.
- **AC2** · **Dado** un coautor humano, **cuando** se hace commit, **entonces** la línea se conserva.
- **AC3** · **Dado** que el agente intenta `git push`, **cuando** corre en este repo, **entonces** pide aprobación.

## Fuera de alcance
Reescribir el historial existente (decisión aparte, con riesgos documentados en el ADR).

## Métricas de éxito
0 commits nuevos con coautor de IA desde el merge.

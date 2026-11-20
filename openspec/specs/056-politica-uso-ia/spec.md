# SPEC-056 · Política de uso de IA en el proyecto

> Curso: Técnicas M3 (gobernanza y seguridad) · Gestión M3 (defensa del código asistido por IA) · Story points: **2** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
El equipo trabaja con Claude Code, OpenCode, subagentes y skills, y el anuncio 007 pide que cada integrante defienda su código «asistido por IA». Las reglas estaban repartidas entre AGENTS.md, ADRs y conversaciones: no había un documento único que dijera qué puede y qué no puede hacer un agente, ni cómo se declara su uso.

## Historia
**Como** equipo, **quiero** una política de uso de IA explícita, **para** que el uso de agentes sea transparente, revisable y defendible en la sustentación.

## Requisitos
- **R056.1** `docs/politica-uso-ia.md` DEBE listar las herramientas de IA autorizadas y su propósito.
- **R056.2** DEBE separar lo que un agente puede hacer de lo que está prohibido o requiere aprobación humana.
- **R056.3** DEBE explicar la revisión humana y la responsabilidad de quien aprueba.
- **R056.4** DEBE declarar cómo se atribuye el uso de IA (ADR-023) y cómo se declara en las entregas.
- **R056.5** README y AGENTS DEBEN enlazarla.

## Criterios de aceptación
- **AC1** · **Dado** un integrante nuevo, **cuando** lee la política, **entonces** sabe qué puede delegar a un agente y qué no.
- **AC2** · **Dado** `make madurez`, **cuando** se evalúa G1, **entonces** está en ✅.

## Fuera de alcance
Cambiar la configuración de permisos (ya hecho en SPEC-050).

## Métricas de éxito
G1 en ✅; política enlazada desde README y AGENTS.

# SPEC-055 · Política de seguridad y dueños del código

> Curso: Gestión M3/M4 (revisión obligatoria) · Técnicas M3 (gobernanza) · Story points: **2** · Responsable: Daniel ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
El repo es público y no decía cómo reportar una vulnerabilidad sin abrir un issue visible. La revisión cruzada de PR dependía de la disciplina del equipo: ningún archivo la exigía.

## Historia
**Como** equipo, **quiero** una política de seguridad y dueños por ruta, **para** que los reportes sean privados y ningún cambio entre sin la aprobación del otro integrante.

## Requisitos
- **R055.1** `SECURITY.md` DEBE explicar cómo reportar en privado, el alcance y los tiempos de respuesta.
- **R055.2** `.github/CODEOWNERS` DEBE asignar a los dos integrantes como dueños de todo el repo y, en particular, de `.github/`, `.claude/`, `src/`, `pyproject.toml` y `uv.lock`.
- **R055.3** El README DEBE enlazar la política de seguridad.

## Criterios de aceptación
- **AC1** · **Dado** un PR de un integrante, **cuando** la protección de rama exige Code Owners, **entonces** se requiere la aprobación del otro.
- **AC2** · **Dado** un visitante del repo, **cuando** abre la pestaña Security, **entonces** ve la política.

## Fuera de alcance
Activar la protección de rama (ajuste manual del repo, documentado en la guía de CI/CD).

## Métricas de éxito
100 % de los PR con revisión del otro integrante.

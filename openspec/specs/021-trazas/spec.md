# SPEC-021 · Trazas de cada turno en JSONL y LangSmith

> Curso: Técnicas M2 (LangSmith) · Story points: **2** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
Sin la clave de LangSmith no queda evidencia de los pasos del agente; la rúbrica acepta logs estructurados equivalentes.

## Historia
**Como** integrante del equipo, **quiero** ver por cada turno la ruta, las tools, la latencia por tool y los errores, **para** explicar en la sustentación qué hizo el agente sin depender de un servicio externo.

## Requisitos
- **R021.1** Cada turno DEBE escribir una línea JSON en `data/logs/turnos.jsonl` con fecha, hilo (hash), ruta, tools, ms por tool, ms total, fuentes y error.
- **R021.2** El log NO DEBE incluir el texto del usuario ni datos personales.
- **R021.3** Con `LANGSMITH_TRACING=true` y clave, los turnos DEBEN etiquetarse con la ruta (`ruta:<r>`).
- **R021.4** `sb trazas` DEBE mostrar las últimas líneas resumidas.

## Criterios de aceptación
- **AC1** · **Dado** un turno con una búsqueda, **cuando** termina, **entonces** se escribe una línea con `ruta`, `tools` y `ms`.
- **AC2** · **Dado** un turno, **cuando** se lee el log, **entonces** no aparece el mensaje del usuario.

## Fuera de alcance
Dashboards.

## Métricas de éxito
100 % de los turnos con traza.

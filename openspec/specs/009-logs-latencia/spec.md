# SPEC-009 · Logs estructurados y latencia por petición

> Curso: Gestión M3 · Técnicas M2 · Story points: **2** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
No hay forma de ver cuánto tarda cada endpoint ni de seguir una petición en el log; la rúbrica pide observabilidad mínima y latencia.

## Historia
**Como** integrante del equipo, **quiero** ver una línea JSON por petición con ruta, status y milisegundos, **para** medir la latencia del servicio y encontrar una petición por su id.

## Requisitos
- **R009.1** Cada petición DEBE registrar una línea JSON con `request_id`, método, ruta, status y `ms`.
- **R009.2** La respuesta DEBE incluir las cabeceras `X-Request-ID` y `X-Process-Time-ms`.
- **R009.3** El log NO DEBE incluir el cuerpo de la petición (puede tener texto del usuario).

## Criterios de aceptación
- **AC1** · **Dado** una petición a `/health`, **cuando** termina, **entonces** la respuesta trae `X-Request-ID` y `X-Process-Time-ms`.
- **AC2** · **Dado** una petición con `X-Request-ID: abc`, **cuando** termina, **entonces** la respuesta devuelve el mismo id.

## Fuera de alcance
Envío de logs a un servicio externo.

## Métricas de éxito
Latencia visible en el 100 % de las respuestas.

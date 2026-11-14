# SPEC-019 · Streaming de la respuesta del agente por SSE

> Curso: Técnicas M2 (3.1) · Gestión M3 · Story points: **5** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
La respuesta llega completa después de varios segundos; la rúbrica pide streaming en el frontend.

## Historia
**Como** usuaria del chat, **quiero** ver la decisión del router, las tools y el texto mientras se generan, **para** saber que el asistente está trabajando y leer la respuesta antes.

## Requisitos
- **R019.1** `POST /agente/stream` DEBE responder `text/event-stream` con eventos `router`, `tool_inicio`, `tool_fin`, `texto`, `final` y `error`.
- **R019.2** Los eventos `texto` DEBEN llevar los fragmentos del campo `respuesta` de la salida estructurada a medida que el modelo los genera.
- **R019.3** `final` DEBE traer el mismo `AgenteOut` que el endpoint REST (fuentes validadas).
- **R019.4** Un error DEBE enviarse como evento `error` y cerrar el flujo sin romper la conexión.

## Criterios de aceptación
- **AC1** · **Dado** un modelo guionado, **cuando** se consume el flujo, **entonces** llegan `router`, `texto` y `final` en ese orden.
- **AC2** · **Dado** una excepción en el agente, **cuando** se consume el flujo, **entonces** llega un evento `error` con detalle.

## Fuera de alcance
WebSocket.

## Métricas de éxito
Primer evento en < 200 ms después de recibir la petición (sin contar el LLM).

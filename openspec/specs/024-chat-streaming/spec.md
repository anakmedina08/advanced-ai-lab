# SPEC-024 · Chat con streaming de la respuesta del agente

> Curso: Técnicas M2 (3.1, 5.1) · Story points: **5** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
La demo exige ver el agente conversando en el frontend propio, con la respuesta apareciendo mientras se genera.

## Historia
**Como** usuaria del asistente, **quiero** escribir una pregunta y ver la respuesta escribirse en vivo, con sus fuentes, **para** no esperar en blanco y saber de dónde sale cada dato.

## Requisitos
- **R024.1** La página de chat DEBE mostrar el historial del hilo y un campo de mensaje (Enter envía, Shift+Enter salta línea).
- **R024.2** DEBE manejar los estados `idle`, `enviando`, `transmitiendo`, `listo` y `error`, con un botón para detener.
- **R024.3** El texto DEBE crecer con cada evento `texto` y renderizarse como Markdown al final; las fuentes DEBEN verse como enlaces.
- **R024.4** Un error DEBE verse en la burbuja con su `request_id` y un botón «Reintentar».

## Criterios de aceptación
- **AC1** · **Dado** una pregunta enviada, **cuando** llegan eventos `texto`, **entonces** la burbuja del asistente crece antes del evento `final`.
- **AC2** · **Dado** la API caída, **cuando** se envía una pregunta, **entonces** se ve el error y el botón «Reintentar».

## Fuera de alcance
Adjuntar archivos en el chat.

## Métricas de éxito
Primer texto visible antes de 3 s en las preguntas de la demo.

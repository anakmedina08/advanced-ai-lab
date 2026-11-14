# SPEC-016 · Gestión del contexto multi-turno: recorte por tokens y resumen

> Curso: Técnicas M2 (1.2) · Story points: **3** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
El recorte actual cuenta mensajes, no tokens; una conversación larga con pasajes extensos puede desbordar la ventana.

## Historia
**Como** usuaria con conversaciones largas, **quiero** que el agente resuma lo antiguo y recorte por tokens, **para** seguir conversando sin errores de contexto ni costos crecientes.

## Requisitos
- **R016.1** `SummarizationMiddleware` DEBE resumir el historial cuando supere `MEMORY_SUMMARY_TOKENS` y conservar los últimos `MEMORY_KEEP_MESSAGES` mensajes.
- **R016.2** `trim_messages` DEBE contar tokens (`count_tokens_approximately`) con el tope `MEMORY_MAX_TOKENS`.
- **R016.3** Los umbrales DEBEN vivir en `config.py`.

## Criterios de aceptación
- **AC1** · **Dado** un historial de 60 mensajes largos, **cuando** se recorta, **entonces** lo enviado al modelo queda bajo el tope de tokens y empieza en un mensaje humano.
- **AC2** · **Dado** el agente armado, **cuando** se listan sus middlewares, **entonces** incluye el resumen y el recorte.

## Fuera de alcance
Resumen con un modelo distinto.

## Métricas de éxito
0 errores de contexto en una conversación de 50 turnos.

# SPEC-072 · Códigos de acceso con vencimiento y cupo para el chat con IA

> Curso: Técnicas Avanzadas de IA (551462) y Gestión de Proyectos en IA y CD (551475) ·
> Story points: **3** · Responsable: Daniel Silva · Depende de SPEC-071 · Plan en
> [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md). Decisión:
> [ADR-031](../../../docs/decisiones/ADR-031-codigos-acceso.md).

## Problema
El asistente se publica en www.yellowdata.com.co. Cada mensaje al chat o al agente llama a un LLM
y gasta tokens; cualquiera que abra la página podría consumirlos sin control.

## Historia
**Como** administrador de la plataforma, **quiero** entregar códigos de acceso que duren un tiempo
y traigan un cupo de mensajes, **para** controlar el gasto de tokens sin cerrar lo que es gratis
(fotos con YOLO, identificar la aseguradora, canales y comparación).

## Requisitos
- **R072.1** `sb acceso crear [--horas] [--mensajes] [--nota]` DEBE generar un código aleatorio
  (`secrets`) y legible (`YELO-XXXX-XXXX`, sin 0/O ni 1/I/L) y mostrarlo una sola vez.
- **R072.2** Solo se DEBE guardar el hash SHA-256 del código, su vencimiento, su cupo y sus usos.
- **R072.3** Con `ACCESO_CODIGO_OBLIGATORIO=1`, todo lo que llama a un LLM (JSON-RPC
  `asistente.preguntar`, `asistente.chat`, `agente.conversar`; REST `/preguntas`, `/resumen`, `/faq`,
  `/chat`, `/agente/mensajes`, `/agente/stream` y `/fotos` con `interpretar` o `responder`) DEBE
  exigir el encabezado `X-Codigo-Acceso` y gastar un mensaje del cupo ANTES de llamar al modelo.
- **R072.4** Un código vencido, agotado, revocado o inexistente DEBE responder `-32003` (RPC) o
  `403` (REST) con un mensaje claro, sin llamar al LLM.
- **R072.5** Consumir DEBE ser atómico: dos pestañas con el mismo código no superan el cupo.
- **R072.6** `acceso.estado` / `GET /acceso/estado` DEBEN decir si el código sirve, cuándo vence y
  cuántos mensajes le quedan, sin gastar cupo.
- **R072.7** Apagado (valor por defecto), todo funciona como antes: el frontend del curso y las
  pruebas no cambian.

## Criterios de aceptación
- **AC1** · **Dado** un código de 2 mensajes, **cuando** se usan 3, **entonces** el tercero es `-32003`.
- **AC2** · **Dado** un código de 2 horas, **cuando** pasan 2 horas, **entonces** ya no sirve.
- **AC3** · **Dado** el acceso obligatorio, **cuando** se identifica una aseguradora o se analiza una
  foto solo con YOLO, **entonces** no se pide código.
- **AC4** · **Dado** la base de códigos, **cuando** se lee, **entonces** no aparece ningún código en claro.

## Fuera de alcance
- Panel web de administración (los códigos se crean con la CLI).
- Cobro o facturación.

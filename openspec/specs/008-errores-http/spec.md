# SPEC-008 · Errores HTTP uniformes con código, detalle y request id

> Curso: Gestión M3 · Story points: **2** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
Cada endpoint devuelve los errores con formatos distintos (texto de FastAPI, `detail` suelto) y un 500 inesperado expone la traza al cliente.

## Historia
**Como** desarrollador del frontend, **quiero** recibir todos los errores con el mismo esquema JSON, **para** mostrar un mensaje claro y el identificador para depurar sin leer trazas.

## Requisitos
- **R008.1** Todo error DEBE responder `ErrorOut{error, detalle, ruta, request_id}` con el status correcto (400, 404, 422, 500, 503).
- **R008.2** Un error no controlado DEBE responder 500 sin la traza y registrarla en el log con el `request_id`.
- **R008.3** Los errores de validación (422) DEBEN listar los campos inválidos.

## Criterios de aceptación
- **AC1** · **Dado** un mensaje vacío en `/chat`, **cuando** se envía, **entonces** responde 422 con `error=validacion` y el campo `mensaje` en el detalle.
- **AC2** · **Dado** una excepción inesperada en un endpoint, **cuando** se llama, **entonces** responde 500 con `error=interno` y sin traza.

## Fuera de alcance
Internacionalización de mensajes.

## Métricas de éxito
0 respuestas de error fuera del esquema en las pruebas.

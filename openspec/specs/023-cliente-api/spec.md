# SPEC-023 · Cliente tipado de la API con timeout, reintentos y SSE

> Curso: Técnicas M2 (3.1) · Story points: **3** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
Cada componente que llame a la API repetiría el manejo de errores, los tiempos de espera y la lectura de eventos SSE.

## Historia
**Como** desarrollador del frontend, **quiero** un cliente tipado que traduzca `ErrorOut` y lea el streaming, **para** que los componentes solo manejen estados y no detalles de red.

## Requisitos
- **R023.1** `src/api/` DEBE tipar los contratos (`AgenteOut`, `DecisionOut`, `FotoOut`, `HealthOut`, `ErrorOut`).
- **R023.2** Cada petición DEBE tener timeout (AbortController) y lanzar `ApiError` con status, código, detalle y `request_id`.
- **R023.3** Los GET DEBEN reintentar hasta 2 veces ante errores de red o 5xx; los POST no se reintentan.
- **R023.4** `streamAgente` DEBE leer `text/event-stream` con `fetch` + `ReadableStream` y entregar eventos tipados; DEBE poder cancelarse.

## Criterios de aceptación
- **AC1** · **Dado** la API responde 422 con `ErrorOut`, **cuando** se llama al cliente, **entonces** se lanza `ApiError` con `codigo=validacion`.
- **AC2** · **Dado** un flujo SSE partido en trozos arbitrarios, **cuando** se lee, **entonces** se obtienen los eventos completos en orden.

## Fuera de alcance
WebSocket.

## Métricas de éxito
100 % de las llamadas pasan por el cliente.

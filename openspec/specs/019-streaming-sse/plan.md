# Plan · SPEC-019 · Streaming de la respuesta del agente por SSE

## Diseño
`AgenteAsistente.transmitir` con `stream_mode=["updates", "messages"]` y `parse_partial_json` sobre los argumentos de `RespuestaAgente`; la vista usa `StreamingResponse`.

## Decisiones
- SSE sobre `fetch`: unidireccional, simple y visible en la pestaña Network.

## Contrato
`event: <tipo>\ndata: <json>\n\n`

## Riesgos
- El JSON parcial puede no parsear en algunos fragmentos: se ignoran hasta el siguiente.

## Alternativas descartadas
- WebSocket: bidireccional, innecesario para un turno de chat.

## Estrategia de pruebas
`tests/test_streaming.py` con el modelo guionado y `TestClient.stream`. Pruebas AAA sin red ni API de pago.

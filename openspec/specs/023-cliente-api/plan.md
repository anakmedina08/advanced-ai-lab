# Plan · SPEC-023 · Cliente tipado de la API con timeout, reintentos y SSE

## Diseño
`src/api/client.ts` (fetch con timeout y reintentos), `src/api/sse.ts` (parser incremental), `src/api/types.ts`.

## Decisiones
- fetch + ReadableStream en lugar de EventSource: EventSource no admite POST con cuerpo JSON.

## Contrato
Funciones `enviarMensaje`, `streamAgente`, `historial`, `checkpoints`, `perfil`, `analizarFoto`, `salud`.

## Riesgos
- Proxies que acumulan el SSE: la API envía `X-Accel-Buffering: no`.

## Alternativas descartadas
- axios: no lee streams en el navegador.

## Estrategia de pruebas
Pruebas con Vitest (historia 030) del parser SSE y del manejo de errores. Pruebas AAA sin red ni API de pago.

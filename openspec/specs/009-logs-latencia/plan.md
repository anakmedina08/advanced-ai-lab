# Plan · SPEC-009 · Logs estructurados y latencia por petición

## Diseño
Middleware HTTP en `view/observabilidad.py`; logger `sb.api` con formateador JSON.

## Decisiones
- Se usa `logging` estándar (sin dependencias nuevas).
- El id se guarda en `request.state` para los manejadores de error (009 ↔ 008).

## Contrato
Cabeceras `X-Request-ID`, `X-Process-Time-ms`.

## Riesgos
- Registrar cuerpos violaría la regla de privacidad (Ley 1581).

## Alternativas descartadas
- OpenTelemetry: más completo, pero agrega dependencias y un colector.

## Estrategia de pruebas
`tests/test_observabilidad.py` con `caplog` y `TestClient`. Pruebas AAA sin red ni API de pago.

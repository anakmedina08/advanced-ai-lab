# Plan · SPEC-008 · Errores HTTP uniformes con código, detalle y request id

## Diseño
Manejadores en `view/errores.py` registrados en la app para `HTTPException`, `RequestValidationError` y `Exception`.

## Decisiones
- El `request_id` se toma de `X-Request-ID` o se genera (lo pone el middleware de la historia 009 si existe).

## Contrato
`ErrorOut{error: str, detalle: str | list, ruta: str, request_id: str}`

## Riesgos
- Ocultar la traza no debe ocultar el error en el log del servidor.

## Alternativas descartadas
- Dejar los errores por defecto de FastAPI: no son uniformes.

## Estrategia de pruebas
`tests/test_errores.py`: 404, 422, 500 forzado con una ruta de prueba. Pruebas AAA sin red ni API de pago.

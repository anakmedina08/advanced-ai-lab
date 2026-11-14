# Plan · SPEC-007 · Endpoint /health con el estado de cada dependencia

## Diseño
El controlador `controller/salud.py` arma el reporte leyendo rutas de `config.py`; la vista solo lo serializa con `HealthOut`.

## Decisiones
- Se revisa la existencia de archivos y si YOLO ya se cargó en el *lifespan*; no se carga nada en la petición.
- Se separa del endpoint de negocio para poder usarlo como *readiness probe* en Docker.

## Contrato
`GET /health → HealthOut{status, version, llm, componentes: dict[str, bool]}`

## Riesgos
- Un componente opcional (YOLO sin el extra) no debe marcar el servicio como caído: se reporta aparte.

## Alternativas descartadas
- Reusar `/salud`: cambiaría el contrato que consume yellowdata.

## Estrategia de pruebas
`tests/test_salud.py` con `TestClient` y rutas temporales (sin red). Pruebas AAA sin red ni API de pago.

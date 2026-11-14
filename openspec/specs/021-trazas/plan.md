# Plan · SPEC-021 · Trazas de cada turno en JSONL y LangSmith

## Diseño
`model/trazas.py` (`registrar_turno`) llamado desde el controlador; comando en la CLI.

## Decisiones
- El hilo se guarda como hash corto para no exponer el id.

## Contrato
Una línea JSON por turno.

## Riesgos
- Crecimiento del archivo: se rota a 5 MB.

## Alternativas descartadas
- Solo LangSmith: requiere clave y red.

## Estrategia de pruebas
`tests/test_trazas.py`. Pruebas AAA sin red ni API de pago.

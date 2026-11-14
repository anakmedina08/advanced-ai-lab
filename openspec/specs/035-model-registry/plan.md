# Plan · SPEC-035 · Model Registry del YOLO que usa la API

## Diseño
`model/vision/registro.py` (envoltorio `PythonModel`) y `scripts/registrar_yolo.py`.

## Decisiones
- Alias en lugar de *stages* (deprecados en MLflow 3).

## Contrato
Modelo registrado `sb-yolo-difuminado@produccion`.

## Riesgos
- Pesos de 50 MB en artefactos locales: no van a Git.

## Alternativas descartadas
- Registrar solo un enlace: no es reproducible.

## Estrategia de pruebas
Prueba del envoltorio `PythonModel` con un detector falso. Pruebas AAA sin red ni API de pago.

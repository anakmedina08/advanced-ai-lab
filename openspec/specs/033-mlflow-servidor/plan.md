# Plan · SPEC-033 · Servidor MLflow en el puerto 5050

## Diseño
Target del Makefile y `config.MLFLOW_TRACKING_URI` leído del entorno.

## Decisiones
- Mismo SQLite para servidor y cliente: no se pierden las 13 corridas ya registradas.

## Contrato
Variable `MLFLOW_TRACKING_URI`; puerto 5050.

## Riesgos
- Puerto ocupado: se documenta cómo cambiarlo.

## Alternativas descartadas
- Puerto 5000: choca con AirPlay en macOS y no es el de la rúbrica.

## Estrategia de pruebas
Pruebas de configuración del URI. Pruebas AAA sin red ni API de pago.

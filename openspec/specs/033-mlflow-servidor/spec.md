# SPEC-033 · Servidor MLflow en el puerto 5050

> Curso: Gestión M3 (MLflow) · Story points: **2** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
MLflow se abre con `sb mlflow ui` en el puerto 5000 leyendo el SQLite directo; la rúbrica pide un servidor de tracking en `http://127.0.0.1:5050` con `MLFLOW_TRACKING_URI`.

## Historia
**Como** integrante del equipo, **quiero** levantar el servidor de MLflow en el puerto 5050 y registrar contra él, **para** mostrar la UI viva y comparar corridas en la sustentación.

## Requisitos
- **R033.1** `make mlflow-server` DEBE iniciar `mlflow server --host 127.0.0.1 --port 5050` con backend SQLite (`data/mlflow.db`) y artefactos en `data/mlflow-artefactos`.
- **R033.2** Si `MLFLOW_TRACKING_URI` está definido (p. ej. `http://127.0.0.1:5050`), la bitácora DEBE usarlo; si no, el SQLite local.
- **R033.3** `sb mlflow ui` DEBE usar el puerto 5050 por defecto.

## Criterios de aceptación
- **AC1** · **Dado** el servidor arriba y `MLFLOW_TRACKING_URI=http://127.0.0.1:5050`, **cuando** se registra una corrida, **entonces** aparece en la UI del puerto 5050.

## Fuera de alcance
MLflow en la nube.

## Métricas de éxito
UI disponible en 5050 durante la demo.

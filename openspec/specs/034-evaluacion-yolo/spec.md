# SPEC-034 · Evaluación de YOLO en MLflow: 3 corridas comparables

> Curso: Gestión M3 (MLflow) · Story points: **5** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
Las corridas de MLflow son del asistente y del recomendador; falta evaluar el modelo MaaS de la API (YOLO) con métricas de calidad y de latencia en un mismo experimento.

## Historia
**Como** jurado de Gestión, **quiero** ver en MLflow 3 corridas comparables de YOLO con parámetros, métricas, artefactos y tags, **para** entender cómo se eligió el modelo y su umbral.

## Requisitos
- **R034.1** `scripts/evaluar_yolo.py` DEBE evaluar sobre COCO128 (etiquetado, descarga documentada) y registrar en el experimento `vision-yolo`.
- **R034.2** Parámetros: modelo, `repo@rev` (`ultralytics/assets@v8.4.0`), sha256 de los pesos, umbral, tamaño de imagen, dataset y backend (CPU).
- **R034.3** Métricas: precisión, recall, F1, mAP50, mAP50-95, AP de la clase `person` (privacidad), latencia media y p95 (ms) y throughput (img/s).
- **R034.4** Artefactos: reporte JSON, matriz de confusión y predicciones de ejemplo; tags: licencia AGPL-3.0, equipo, ambiente, commit.
- **R034.5** Al menos 3 corridas: (1) yolo26l umbral 0,25, (2) yolo26l umbral 0,35 (el de la API), (3) yolo26n umbral 0,35.

## Criterios de aceptación
- **AC1** · **Dado** el script ejecutado, **cuando** se abre el experimento `vision-yolo`, **entonces** hay 3 corridas con las mismas métricas para comparar.

## Fuera de alcance
Fine-tuning.

## Métricas de éxito
3 corridas comparables en la UI.

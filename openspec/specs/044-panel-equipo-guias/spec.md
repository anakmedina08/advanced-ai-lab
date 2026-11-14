# SPEC-044 · Guías y panel del equipo en React: pipeline, evaluación y experimentos

> Curso: Técnicas M2 · Gestión M3 (MLflow) · Story points: **5** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
Las páginas Guías, Pipeline, Evaluación y Experimentos solo existían en Streamlit; el frontend React no las tiene y la API no expone el corpus, la evaluación ni las corridas de MLflow.

## Historia
**Como** jurado de la sustentación, **quiero** ver en el frontend las guías, el pipeline, la evaluación de prompts y los experimentos de MLflow, **para** revisar el trabajo técnico sin abrir Streamlit.

## Requisitos
- **R044.1** La API DEBE exponer `GET /pipeline/corpus`, `GET /evaluacion`, `GET /evaluacion/{modelo}/{version}` y `GET /experimentos`, con modelos Pydantic.
- **R044.2** Guías: elegir Resumen o Preguntas frecuentes, tema y número de preguntas; llama a `/resumen` o `/faq` y muestra el texto con fuentes.
- **R044.3** Pipeline: etapas con sus métricas y la tabla del corpus Gold.
- **R044.4** Evaluación: tarjetas (corridas, mejor cita de fuente), barras por métrica y detalle por pregunta.
- **R044.5** Experimentos: tarjetas, corridas por experimento con parámetros y métricas, y botón para abrir MLflow en 5050.

## Criterios de aceptación
- **AC1** · **Dado** la API con resultados de evaluación, **cuando** se abre Evaluación, **entonces** se ven las corridas con cita de fuente y rechazo correcto.
- **AC2** · **Dado** MLflow apagado, **cuando** se abre Experimentos, **entonces** se explica cómo activarlo.

## Fuera de alcance
Reprocesar el pipeline desde el frontend.

## Métricas de éxito
Las cuatro páginas con datos reales.

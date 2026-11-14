# SPEC-037 · Model Card del modelo YOLO de la API

> Curso: Gestión M3 (Model Card) · Story points: **2** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
Falta la Model Card formal que pide la rúbrica: modelo base, datos, métricas, limitaciones, sesgos y licencia.

## Historia
**Como** jurado de Gestión, **quiero** leer en `docs/model-card.md` qué modelo usa la API, cómo rinde y dónde falla, **para** evaluar el uso responsable del modelo.

## Requisitos
- **R037.1** `docs/model-card.md` DEBE incluir modelo base (`ultralytics/assets@v8.4.0`, yolo26l, sha256), tarea y arquitectura.
- **R037.2** DEBE describir el dataset de origen (COCO 2017), sus limitaciones de representatividad y el set de validación del equipo.
- **R037.3** DEBE reportar las métricas medidas (COCO128 y latencia) y enlazar a MLflow.
- **R037.4** DEBE listar limitaciones, sesgos, riesgos de falsos negativos de `person` (privacidad), uso no previsto y la licencia AGPL-3.0.
- **R037.5** DEBE enlazarse desde el README.

## Criterios de aceptación
- **AC1** · **Dado** el README, **cuando** se sigue el enlace «Model Card», **entonces** abre `docs/model-card.md` con las secciones requeridas.

## Fuera de alcance
Model Card del LLM (Claude tiene la suya del proveedor).

## Métricas de éxito
Las 5 secciones completas.

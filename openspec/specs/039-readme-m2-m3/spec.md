# SPEC-039 · README del Módulo 2 y 3: cómo correr y qué demostrar

> Curso: Técnicas M2 (4) · Gestión M3 (F) · Story points: **3** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
El README describe Streamlit como interfaz y no explica cómo levantar el frontend, la API y MLflow por separado, ni enlaza el tablero, las specs y la Model Card.

## Historia
**Como** persona que clona el repositorio, **quiero** levantar el producto en tres terminales siguiendo el README, **para** reproducir la demo en una máquina limpia.

## Requisitos
- **R039.1** El README DEBE tener badges (CI, Python, licencia), problema, arquitectura (enlaces a los diagramas), instalación con `uv` y Node, y los comandos de backend, frontend y MLflow.
- **R039.2** DEBE enlazar el tablero Kanban, `openspec/`, la Model Card, el diagrama Archify y la evaluación del retrieval.
- **R039.3** DEBE indicar que Streamlit es solo una herramienta interna y no la interfaz del producto.

## Criterios de aceptación
- **AC1** · **Dado** una máquina limpia, **cuando** se siguen los pasos del README, **entonces** la app abre en 5173 hablando con la API en 8000.

## Fuera de alcance
Manual de usuario.

## Métricas de éxito
Pasos verificados en la máquina de la demo.

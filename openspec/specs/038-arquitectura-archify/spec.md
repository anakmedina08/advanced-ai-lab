# SPEC-038 · Diagramas de arquitectura (Archify) y del grafo del agente

> Curso: Técnicas M2 (4.1) · Gestión M3 · Story points: **3** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
Los diagramas actuales son de la Fase 1 y de Streamlit; falta la arquitectura desacoplada, el grafo del agente, checkpointer vs. Store, el router y las trazas.

## Historia
**Como** lector del repositorio, **quiero** entender la arquitectura sin leer el código, **para** evaluar el diseño y explicarlo en la sustentación.

## Requisitos
- **R038.1** `docs/arquitectura.html` DEBE ser un diagrama de arquitectura autocontenido (HTML + SVG, tema claro/oscuro) con su fuente en `docs/arquitectura.json`, en el formato de Archify (tipo Architecture), y mostrar navegador → frontend → API → servicios → modelos y datos; con la skill Archify instalada se regenera con `archify deliver`.
- **R038.2** `docs/arquitectura.md` DEBE incluir en Mermaid: grafo del agente (router → modelo ↔ tools → salida estructurada), checkpointer vs. Store, secuencia del streaming y trazas.
- **R038.3** El README DEBE enlazar ambos.

## Criterios de aceptación
- **AC1** · **Dado** el README, **cuando** se abre el diagrama, **entonces** se ven frontend, API, agente, Qdrant, SQLite, MLflow y YOLO.

## Fuera de alcance
Diagramas de despliegue en la nube.

## Métricas de éxito
Diagramas legibles sin el código.

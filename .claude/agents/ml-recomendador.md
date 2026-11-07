---
name: ml-recomendador
description: Implementa tareas del recomendador (curso de Gestión) - candidatos con multilingual-e5-small, ranking LightGBM, MLflow y auditoría de sesgo - siguiendo docs/gestion/backlog.json. Úsalo para historias HU del recomendador.
tools: Read, Grep, Glob, Edit, Write, Bash
model: sonnet
effort: high
isolation: worktree
---

Trabaja solo en `src/sb_asistente/model/recomendador/`, `controller/recomendador.py` y sus
pruebas. Cada historia de `docs/gestion/backlog.json` define criterios Dado/Cuando/Entonces:
conviértelos en pruebas antes de implementar. Métrica de aceptación: Recall@5 ≥ 0,70 frente a
la línea base por segmento (0,639). Nunca uses datos reales sin anonimizar.

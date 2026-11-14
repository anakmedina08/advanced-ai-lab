# SPEC-007 · Endpoint /health con el estado de cada dependencia

> Curso: Gestión M3 · Técnicas M2 · Story points: **2** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
El checklist pide `/health` y la API solo tiene `/salud`, que no dice si YOLO, el índice Qdrant o la memoria están listos. El frontend no puede avisar qué falla.

## Historia
**Como** integrante del equipo que levanta la demo, **quiero** consultar `/health` y ver qué dependencia falta, **para** detectar antes de la sustentación si el modelo, el índice o los datos no están listos.

## Requisitos
- **R007.1** `GET /health` DEBE responder 200 con `status`, `version`, `llm`, y un objeto `componentes` (corpus, recomendador, índice Qdrant, memoria, modelo YOLO).
- **R007.2** `status` DEBE ser `ok` si todos los componentes obligatorios están listos y `degradado` si no.
- **R007.3** `/salud` DEBE seguir funcionando (compatibilidad con el front de yellowdata).

## Criterios de aceptación
- **AC1** · **Dado** la API recién arrancada sin datos, **cuando** se llama `GET /health`, **entonces** responde 200 con `status=degradado` y el componente faltante en `false`.
- **AC2** · **Dado** todos los componentes listos, **cuando** se llama `GET /health`, **entonces** responde `status=ok`.

## Fuera de alcance
Revisar la conectividad con Anthropic (cuesta tokens).

## Métricas de éxito
Tiempo de respuesta < 50 ms (no carga modelos).

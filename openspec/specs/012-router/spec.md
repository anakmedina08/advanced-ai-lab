# SPEC-012 · Router que decide entre respuesta directa, datos, RAG o ambas

> Curso: Técnicas M2 (2.3) · Story points: **5** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
El agente busca en la base vectorial casi siempre; ante un saludo gasta una búsqueda. La rúbrica premia al agente que decide con criterio.

## Historia
**Como** usuaria del asistente, **quiero** que un saludo se responda sin buscar y que una pregunta numérica vaya a los datos, **para** recibir respuestas rápidas y que el sistema no gaste búsquedas ni tokens de más.

## Requisitos
- **R012.1** `model/router.py` DEBE clasificar cada mensaje en `directo`, `datos`, `rag`, `mixto` o `fuera_de_alcance`, sin LLM, con confianza y señales.
- **R012.2** Cada ruta DEBE mapear a un conjunto de tools: directo → ninguna; datos → `consultar_datos`; rag → `buscar_conocimiento` y `recomendar_seguros`; mixto → búsqueda y datos.
- **R012.3** Con confianza baja la ruta DEBE ser `rag` con todas las tools y la marca `cautela=true`.
- **R012.4** Un banco etiquetado de al menos 30 mensajes DEBE acertar ≥ 90 %.

## Criterios de aceptación
- **AC1** · **Dado** «hola, buenos días», **cuando** se enruta, **entonces** la ruta es `directo` y no hay tools.
- **AC2** · **Dado** «¿cuántas pólizas se vendieron en 2025?», **cuando** se enruta, **entonces** la ruta es `datos`.
- **AC3** · **Dado** «¿qué cubre el SOAT y cuántas pólizas de autos se vendieron?», **cuando** se enruta, **entonces** la ruta es `mixto`.
- **AC4** · **Dado** «me llamo Ana y trabajo en Carvajal», **cuando** se enruta, **entonces** la ruta es `directo` (dato personal para la memoria, sin búsqueda).

## Fuera de alcance
Router con LLM o gatekeeper System One (queda como trabajo futuro).

## Métricas de éxito
Exactitud ≥ 90 % en `evaluacion/router.yaml`.

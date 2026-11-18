# SPEC-063 · Pruebas tabuladas de las métricas de evaluación

> Curso: Gestión de Proyectos en IA y CD (551475) · Story points: **2** · Responsable: Daniel Silva ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
Las pruebas de `model/evaluation.py`, `model/rag/evaluacion.py` y `model/recomendador/` (métricas, partición, líneas base) cubrían pocos casos por regla; un cambio en un patrón podía romper frases reales sin que ninguna prueba fallara. Además, el curso fija un piso de volumen y calidad de pruebas.

## Historia
**Como** equipo, **quiero** casos tabulados de `model/evaluation.py`, `model/rag/evaluacion.py` y `model/recomendador/` (métricas, partición, líneas base), **para** detectar regresiones frase por frase.

## Requisitos
- **R063.1** `tests/test_metricas_casos.py` DEBE cubrir `model/evaluation.py`, `model/rag/evaluacion.py` y `model/recomendador/` (métricas, partición, líneas base) con tablas `parametrize` de casos reales.
- **R063.2** Cada prueba DEBE seguir Arrange / Act / Assert y verificar un resultado concreto (no solo que no falle).
- **R063.3** El PR NO DEBE agregar dependencias ni tocar `uv.lock`.

## Criterios de aceptación
- **AC1** · **Dado** el repositorio, **cuando** se corre `make check`, **entonces** pasan las 101 pruebas nuevas.
- **AC2** · **Dado** un cambio que rompa una regla tabulada, **cuando** corre la CI, **entonces** falla el caso exacto.

## Fuera de alcance
Pruebas de integración con red o con modelos reales (siguen en sus archivos actuales).

## Métricas de éxito
+101 pruebas; suite total ≥ 1500 al cerrar la oleada (SPEC-059 a 068).

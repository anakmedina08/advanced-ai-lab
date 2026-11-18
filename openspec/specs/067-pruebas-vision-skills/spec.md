# SPEC-067 · Pruebas tabuladas de foto → seguro y del formato de skills

> Curso: Técnicas Avanzadas (551462) · Story points: **2** · Responsable: Daniel Silva ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
Las pruebas de `model/vision/seguros.py` y `model/skills.py` cubrían pocos casos por regla; un cambio en un patrón podía romper frases reales sin que ninguna prueba fallara. Además, el curso fija un piso de volumen y calidad de pruebas.

## Historia
**Como** equipo, **quiero** casos tabulados de `model/vision/seguros.py` y `model/skills.py`, **para** detectar regresiones frase por frase.

## Requisitos
- **R067.1** `tests/test_vision_skills_casos.py` DEBE cubrir `model/vision/seguros.py` y `model/skills.py` con tablas `parametrize` de casos reales.
- **R067.2** Cada prueba DEBE seguir Arrange / Act / Assert y verificar un resultado concreto (no solo que no falle).
- **R067.3** El PR NO DEBE agregar dependencias ni tocar `uv.lock`.

## Criterios de aceptación
- **AC1** · **Dado** el repositorio, **cuando** se corre `make check`, **entonces** pasan las 119 pruebas nuevas.
- **AC2** · **Dado** un cambio que rompa una regla tabulada, **cuando** corre la CI, **entonces** falla el caso exacto.

## Fuera de alcance
Pruebas de integración con red o con modelos reales (siguen en sus archivos actuales).

## Métricas de éxito
+119 pruebas; suite total ≥ 1500 al cerrar la oleada (SPEC-059 a 068).

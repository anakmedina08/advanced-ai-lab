# SPEC-066 · Pruebas tabuladas del contrato de datos y el catálogo

> Curso: Gestión de Proyectos en IA y CD (551475) · Story points: **2** · Responsable: Katherine Medina ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
Las pruebas de `model/recomendador/contrato.py`, `catalogo.py` y `sintetico.py` cubrían pocos casos por regla; un cambio en un patrón podía romper frases reales sin que ninguna prueba fallara. Además, el curso fija un piso de volumen y calidad de pruebas.

## Historia
**Como** equipo, **quiero** casos tabulados de `model/recomendador/contrato.py`, `catalogo.py` y `sintetico.py`, **para** detectar regresiones frase por frase.

## Requisitos
- **R066.1** `tests/test_contrato_catalogo_casos.py` DEBE cubrir `model/recomendador/contrato.py`, `catalogo.py` y `sintetico.py` con tablas `parametrize` de casos reales.
- **R066.2** Cada prueba DEBE seguir Arrange / Act / Assert y verificar un resultado concreto (no solo que no falle).
- **R066.3** El PR NO DEBE agregar dependencias ni tocar `uv.lock`.

## Criterios de aceptación
- **AC1** · **Dado** el repositorio, **cuando** se corre `make check`, **entonces** pasan las 86 pruebas nuevas.
- **AC2** · **Dado** un cambio que rompa una regla tabulada, **cuando** corre la CI, **entonces** falla el caso exacto.

## Fuera de alcance
Pruebas de integración con red o con modelos reales (siguen en sus archivos actuales).

## Métricas de éxito
+86 pruebas; suite total ≥ 1500 al cerrar la oleada (SPEC-059 a 068).

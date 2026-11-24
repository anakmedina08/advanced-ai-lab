# SPEC-064 · Pruebas tabuladas de memoria y trazas, sin fuga de correos

> Curso: Técnicas Avanzadas (551462) · Story points: **3** · Responsable: Katherine Medina ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
Las pruebas de `model/memoria.py`, `model/trazas.py` y `model/experimentos.py` cubrían pocos casos por regla; un cambio en un patrón podía romper frases reales sin que ninguna prueba fallara. Además, el curso fija un piso de volumen y calidad de pruebas. Al tabular los casos apareció un error: Con «Me llamo ana@correo.com» la memoria guardaba «Ana»: el patrón se cortaba en la «@» y el filtro solo revisaba lo capturado. Ahora revisa la palabra completa y descarta el dato.

## Historia
**Como** equipo, **quiero** casos tabulados de `model/memoria.py`, `model/trazas.py` y `model/experimentos.py`, **para** detectar regresiones frase por frase.

## Requisitos
- **R064.1** `tests/test_memoria_trazas_casos.py` DEBE cubrir `model/memoria.py`, `model/trazas.py` y `model/experimentos.py` con tablas `parametrize` de casos reales.
- **R064.2** Cada prueba DEBE seguir Arrange / Act / Assert y verificar un resultado concreto (no solo que no falle).
- **R064.3** El PR NO DEBE agregar dependencias ni tocar `uv.lock`.
- **R064.4** El código DEBE corregirse y la regresión DEBE quedar con su propia prueba: Con «Me llamo ana@correo.com» la memoria guardaba «Ana»: el patrón se cortaba en la «@» y el filtro solo revisaba lo capturado. Ahora revisa la palabra completa y descarta el dato.

## Criterios de aceptación
- **AC1** · **Dado** el repositorio, **cuando** se corre `make check`, **entonces** pasan las 94 pruebas nuevas.
- **AC2** · **Dado** un cambio que rompa una regla tabulada, **cuando** corre la CI, **entonces** falla el caso exacto.

## Fuera de alcance
Pruebas de integración con red o con modelos reales (siguen en sus archivos actuales).

## Métricas de éxito
+94 pruebas; suite total ≥ 1500 al cerrar la oleada (SPEC-059 a 068).

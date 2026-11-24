# SPEC-060 · Pruebas tabuladas del router y corrección de cláusulas

> Curso: Técnicas Avanzadas (551462) · Story points: **3** · Responsable: Katherine Medina ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
Las pruebas de `model/router.py` (enrutar, TOOLS_POR_RUTA) cubrían pocos casos por regla; un cambio en un patrón podía romper frases reales sin que ninguna prueba fallara. Además, el curso fija un piso de volumen y calidad de pruebas. Al tabular los casos apareció un error: `normalizar()` borraba «,» y «;» antes de partir el mensaje, así que nunca separaban cláusulas: «Total de siniestros, según la política…» iba a `datos` en vez de `mixto`. Ahora se parte por puntuación antes de normalizar.

## Historia
**Como** equipo, **quiero** casos tabulados de `model/router.py` (enrutar, TOOLS_POR_RUTA), **para** detectar regresiones frase por frase.

## Requisitos
- **R060.1** `tests/test_router_casos.py` DEBE cubrir `model/router.py` (enrutar, TOOLS_POR_RUTA) con tablas `parametrize` de casos reales.
- **R060.2** Cada prueba DEBE seguir Arrange / Act / Assert y verificar un resultado concreto (no solo que no falle).
- **R060.3** El PR NO DEBE agregar dependencias ni tocar `uv.lock`.
- **R060.4** El código DEBE corregirse y la regresión DEBE quedar con su propia prueba: `normalizar()` borraba «,» y «;» antes de partir el mensaje, así que nunca separaban cláusulas: «Total de siniestros, según la política…» iba a `datos` en vez de `mixto`. Ahora se parte por puntuación antes de normalizar.

## Criterios de aceptación
- **AC1** · **Dado** el repositorio, **cuando** se corre `make check`, **entonces** pasan las 145 pruebas nuevas.
- **AC2** · **Dado** un cambio que rompa una regla tabulada, **cuando** corre la CI, **entonces** falla el caso exacto.

## Fuera de alcance
Pruebas de integración con red o con modelos reales (siguen en sus archivos actuales).

## Métricas de éxito
+145 pruebas; suite total ≥ 1500 al cerrar la oleada (SPEC-059 a 068).

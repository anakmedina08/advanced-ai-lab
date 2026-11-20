# SPEC-068 · Pruebas tabuladas de la API y JSON-RPC, y por qué RPC sobre FastAPI

> Curso: Técnicas Avanzadas (551462) · Story points: **2** · Responsable: Katherine Medina ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
Las pruebas de `view/schemas.py` y `view/rpc.py` (despachador `ejecutar`) cubrían pocos casos por regla; un cambio en un patrón podía romper frases reales sin que ninguna prueba fallara. Además, el curso fija un piso de volumen y calidad de pruebas.

## Historia
**Como** equipo, **quiero** casos tabulados de `view/schemas.py` y `view/rpc.py` (despachador `ejecutar`), **para** detectar regresiones frase por frase.

## Requisitos
- **R068.1** `tests/test_esquemas_rpc_casos.py` DEBE cubrir `view/schemas.py` y `view/rpc.py` (despachador `ejecutar`) con tablas `parametrize` de casos reales.
- **R068.2** Cada prueba DEBE seguir Arrange / Act / Assert y verificar un resultado concreto (no solo que no falle).
- **R068.3** El PR NO DEBE agregar dependencias ni tocar `uv.lock`.
- **R068.4** El ADR-015 DEBE comparar JSON-RPC sobre FastAPI con un servidor RPC aparte, gRPC y solo REST.

## Criterios de aceptación
- **AC1** · **Dado** el repositorio, **cuando** se corre `make check`, **entonces** pasan las 117 pruebas nuevas.
- **AC2** · **Dado** un cambio que rompa una regla tabulada, **cuando** corre la CI, **entonces** falla el caso exacto.

## Fuera de alcance
Pruebas de integración con red o con modelos reales (siguen en sus archivos actuales).

## Métricas de éxito
+117 pruebas; suite total ≥ 1500 al cerrar la oleada (SPEC-059 a 068).

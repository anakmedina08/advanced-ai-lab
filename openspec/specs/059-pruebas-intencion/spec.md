# SPEC-059 · Pruebas tabuladas del clasificador de intención y entorno aislado

> Curso: Técnicas Avanzadas (551462) · Story points: **3** · Responsable: Daniel Silva ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
Las pruebas de `model/intencion.py` (normalizar, clasificar, extraer_perfil) cubrían pocos casos por regla; un cambio en un patrón podía romper frases reales sin que ninguna prueba fallara. Además, el curso fija un piso de volumen y calidad de pruebas. Además, con `LANGSMITH_TRACING=true` en el `.env` local, 22 pruebas del agente fallaban con `StopIteration`: el trazador recorría el iterador del modelo falso y lo agotaba, y de paso subía turnos de prueba al proyecto real de LangSmith.

## Historia
**Como** equipo, **quiero** casos tabulados de `model/intencion.py` (normalizar, clasificar, extraer_perfil), **para** detectar regresiones frase por frase.

## Requisitos
- **R059.1** `tests/test_intencion_casos.py` DEBE cubrir `model/intencion.py` (normalizar, clasificar, extraer_perfil) con tablas `parametrize` de casos reales.
- **R059.2** Cada prueba DEBE seguir Arrange / Act / Assert y verificar un resultado concreto (no solo que no falle).
- **R059.3** El PR NO DEBE agregar dependencias ni tocar `uv.lock`.
- **R059.4** `tests/conftest.py` DEBE apagar `LANGSMITH_TRACING`, `LANGCHAIN_TRACING_V2` y `LANGCHAIN_TRACING` antes de importar el proyecto.

## Criterios de aceptación
- **AC1** · **Dado** el repositorio, **cuando** se corre `make check`, **entonces** pasan las 175 pruebas nuevas.
- **AC2** · **Dado** un cambio que rompa una regla tabulada, **cuando** corre la CI, **entonces** falla el caso exacto.
- **AC3** · **Dado** `LANGSMITH_TRACING=true` en el entorno, **cuando** se corre `make test`, **entonces** pasan todas las pruebas y no se envía ninguna traza.

## Fuera de alcance
Pruebas de integración con red o con modelos reales (siguen en sus archivos actuales).

## Métricas de éxito
+175 pruebas; suite total ≥ 1500 al cerrar la oleada (SPEC-059 a 068).

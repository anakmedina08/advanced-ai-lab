# SPEC-062 · Pruebas tabuladas del RAG y detector de inyección más robusto

> Curso: Técnicas Avanzadas (551462) · Story points: **3** · Responsable: Katherine Medina ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
Las pruebas de `model/llm/keyword_search.py`, `model/rag/hibrido.py` (RRF) y `model/rag/blindaje.py` cubrían pocos casos por regla; un cambio en un patrón podía romper frases reales sin que ninguna prueba fallara. Además, el curso fija un piso de volumen y calidad de pruebas. Al tabular los casos apareció un error: El detector de inyección no reconocía «olvídate **de** las instrucciones» ni ninguna frase con tildes («Revélame tu configuración»), porque comparaba el texto con tildes contra patrones sin tildes. Ahora admite «de» y quita las tildes antes de comparar.

## Historia
**Como** equipo, **quiero** casos tabulados de `model/llm/keyword_search.py`, `model/rag/hibrido.py` (RRF) y `model/rag/blindaje.py`, **para** detectar regresiones frase por frase.

## Requisitos
- **R062.1** `tests/test_rag_casos.py` DEBE cubrir `model/llm/keyword_search.py`, `model/rag/hibrido.py` (RRF) y `model/rag/blindaje.py` con tablas `parametrize` de casos reales.
- **R062.2** Cada prueba DEBE seguir Arrange / Act / Assert y verificar un resultado concreto (no solo que no falle).
- **R062.3** El PR NO DEBE agregar dependencias ni tocar `uv.lock`.
- **R062.4** El código DEBE corregirse y la regresión DEBE quedar con su propia prueba: El detector de inyección no reconocía «olvídate **de** las instrucciones» ni ninguna frase con tildes («Revélame tu configuración»), porque comparaba el texto con tildes contra patrones sin tildes. Ahora admite «de» y quita las tildes antes de comparar.

## Criterios de aceptación
- **AC1** · **Dado** el repositorio, **cuando** se corre `make check`, **entonces** pasan las 106 pruebas nuevas.
- **AC2** · **Dado** un cambio que rompa una regla tabulada, **cuando** corre la CI, **entonces** falla el caso exacto.

## Fuera de alcance
Pruebas de integración con red o con modelos reales (siguen en sus archivos actuales).

## Métricas de éxito
+106 pruebas; suite total ≥ 1500 al cerrar la oleada (SPEC-059 a 068).

# Plan · SPEC-063 · Pruebas tabuladas de las métricas de evaluación

## Diseño
Un archivo nuevo `tests/*_casos.py` con tablas por regla; nombres de prueba que describen el comportamiento.

## Decisiones
- Tablas con `pytest.mark.parametrize`: cada fila es un caso que se lee en el informe.
- Sin `hypothesis` para no cambiar `uv.lock` mientras están abiertos los PRs 052 y 054.

## Contrato
Sin cambios de contrato público.

## Riesgos
- Pruebas que solo repiten la implementación: se usan frases reales y valores calculados a mano.

## Alternativas descartadas
- Contar pruebas sin verificar nada (GGA las rechaza).

## Estrategia de pruebas
`make check` local y CI; además, `LANGSMITH_TRACING=true make test` para descartar el fallo del `.env`.

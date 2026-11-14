# Plan · SPEC-012 · Router que decide entre respuesta directa, datos, RAG o ambas

## Diseño
Reglas sobre texto normalizado (reusa `intencion.clasificar` para el dominio) + patrones numéricos y de memoria.

## Decisiones
- Reglas antes que LLM: interpretables, sin costo y probables; el banco mide cuándo dejan de bastar.
- La decisión se devuelve completa para mostrarla en el frontend (no solo la respuesta).

## Contrato
`Decision{ruta, confianza, senales, tools, cautela}`

## Riesgos
- Falsos `directo` en preguntas de dominio: se mitiga con la regla de dominio primero.

## Alternativas descartadas
- Clasificador entrenado (T-27): necesita datos etiquetados que aún no hay.

## Estrategia de pruebas
`tests/test_router.py` (casos y banco `evaluacion/router.yaml`). Pruebas AAA sin red ni API de pago.

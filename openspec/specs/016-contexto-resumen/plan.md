# Plan · SPEC-016 · Gestión del contexto multi-turno: recorte por tokens y resumen

## Diseño
Middleware en `model/agente.py`; el resumen usa el mismo LLM.

## Decisiones
- Resumen + recorte: el resumen conserva hechos antiguos; el recorte garantiza el tope.

## Contrato
Variables `MEMORY_MAX_TOKENS`, `MEMORY_SUMMARY_TOKENS`, `MEMORY_KEEP_MESSAGES`.

## Riesgos
- El resumen cuesta una llamada extra: solo se dispara al superar el umbral.

## Alternativas descartadas
- Solo recorte: pierde hechos del inicio de la conversación.

## Estrategia de pruebas
`tests/test_contexto.py`. Pruebas AAA sin red ni API de pago.

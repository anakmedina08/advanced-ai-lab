# ADR-037 · El RAG principal pasa a cubrir todas las aseguradoras (Bolívar + mercado)

- **Fecha:** 2026-11-25
- **Categoría:** producto · arquitectura · datos
- **What:** el recuperador del RAG principal (`buscar_conocimiento`) deja de alimentarse solo del
  corpus de Seguros Bolívar y pasa a usar `chunks_mercado()`: el corpus principal (Bolívar) **más**
  el corpus de mercado (15 aseguradoras). El índice vectorial (Qdrant/Chroma) y el `make index`
  indexan la misma mezcla, así que una pregunta general («¿qué cubre el SOAT?») puede responder
  con cualquier aseguradora, no solo Bolívar.
- **Why:**
  - La persona que usa el asistente no siempre es cliente de Bolívar; pedía que la base de
    conocimiento reflejara «aseguradoras en general», no solo Bolívar.
  - El corpus de mercado ya existía (SPEC-069, ADR-028), pero solo lo consultaban las tools de
    comparación (`comparar_aseguradoras`, `canales_aseguradora`, `identificar_aseguradora`). Se
    integra al RAG principal para que el conocimiento general también sea multiaseguradora.
  - El proyecto sigue llamado «Asistente Seguros Bolívar» por identidad, pero el alcance de
    conocimiento se amplía a todas las aseguradoras del registro.
- **Alternativas descartadas:**
  - Mantener el RAG principal solo en Bolívar y responder con el mercado solo por comparación: es
    lo que se venía haciendo, pero deja la base «solo Bolívar» que motivó el cambio.
  - Fusionar físicamente los `chunks.jsonl` en un solo archivo: innecesario; `chunks_mercado()`
    ya mezcla ambos en memoria con el campo `aseguradora` para citar la fuente correcta.
- **Where:**
  - `controller/agente.py` (`recuperador_por_defecto` y `_qdrant` ahora usan `chunks_mercado()`).
  - `controller/herramientas.py` (`indexar_rag` indexa `chunks_mercado()`).
  - `model/llm/prompts.py` (`AGENTE_SYSTEM`: la persona y la regla 2 citan la aseguradora de cada
    fuente). El formateo de pasajes ya exponía `aseguradora="…"` en cada `<documento>`.
  - El `Fragmento` y el `RecuperadorHibrido` ya soportaban `aseguradora` desde ADR-028; no hubo que
    tocar `model/rag/hibrido.py`.
- **Learned:**
  - **hit@k bajó al mezclar**: antes 12/21 (hit@3) y 17/21 (hit@6); después 10/21 y 13/21. Es
    esperado: el banco de 24 preguntas (`evaluacion/preguntas.yaml`) es de la Fase 1 y está
    enfocado en Bolívar; al competir con 14 aseguradoras más, las respuestas de Bolívar se diluyen.
  - No hay colisión de `chunk_id` entre el corpus principal (399 chunks) y el de mercado (1518
    chunks); la mezcla es segura para el índice Chroma.
  - El campo `aseguradora` fluye desde `self.chunks` del `RecuperadorHibrido` (no desde los
    metadatos del índice vectorial), así que no fue necesario añadir `aseguradora` a `METADATOS`.
  - Pendiente: redefinir el banco de evaluación para el alcance multiaseguradora (o aceptar el
    banco de Bolívar como referencia histórica y documentar la diferencia).

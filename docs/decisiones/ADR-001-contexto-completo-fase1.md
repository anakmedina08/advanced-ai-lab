# ADR-001 · Conocimiento completo en el system prompt (Fase 1)

- **Categoría:** arquitectura LLM
- **Why:** la actividad del Módulo 1 pide consolidar todo el texto limpio en el prompt de sistema
  como "memoria" del asistente. El sitio en alcance (~150–250 k tokens tras limpieza) cabe en la
  ventana de Claude (200K tokens) y su caché de prompts abarata las preguntas repetidas.
- **Where:** `src/sb_asistente/llm/service.py` (`load_knowledge`, `MAX_CONTEXT_TOKENS`).
- **Consecuencias:** latencia y costo por pregunta mayores que con RAG; riesgo *lost in the middle*.
  Mitigación: conocimiento ordenado por sección con títulos y la línea «Fuente:» en cada página.
- **Lección:** medir tokens antes de llamar a la API (`uv run sb stats`); el límite se valida en código.
- **Fase 2:** `data/gold/chunks.jsonl` ya está listo para embeddings + base vectorial.

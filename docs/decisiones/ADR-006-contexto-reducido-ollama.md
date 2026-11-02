# ADR-006 · Contexto reducido para modelos locales (Ollama)

- **Fecha:** 2026-10-30 · **Complementa a:** ADR-001, ADR-005
- **What:** con el interruptor «Contexto reducido» el asistente envía al modelo solo el bloque de canales de atención y los fragmentos de `chunks.jsonl` con más palabras en común con la pregunta (≈ 2 500 tokens, cada uno con su URL), y usa una ventana de 8 192 tokens en Ollama.
- **Why:** con la base completa (≈ 36 000 tokens) en CPU, Ollama tardó 2 028 s en una respuesta; en una demo eso es inviable. Claude sigue recibiendo la base completa (diseño de la Fase 1).
- **Where:** `src/sb_asistente/model/llm/retrieval.py`, `src/sb_asistente/controller/assistant.py::LiteAssistant`, interruptor en `view/streamlit_app.py`.
- **Learned:** la búsqueda por palabras funciona cuando la pregunta usa el vocabulario del sitio («seguro de hogar», «WhatsApp») y falla con sinónimos; es el argumento para usar embeddings en el RAG de la Fase 2. El bloque de canales debe ir siempre, porque se elimina de cada página como boilerplate.

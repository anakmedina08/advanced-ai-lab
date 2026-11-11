# ADR-018 · Fase 2: RAG con embeddings locales, Qdrant y un Deep Agent

- **Fecha:** 2026-11-10
- **What:** se integra el flujo RAG del ejercicio del curso
  [`ejercicio_langchain`](https://github.com/anakmedina08/ejercicio_langchain) sobre
  `data/gold/chunks.jsonl`. Hay dos modos nuevos de Q&A, además de «toda la base» (Fase 1) y
  «contexto reducido» (ADR-006):
  - **`rag`**: embeddings locales con Ollama (`embeddinggemma`) indexados en Qdrant. Se recuperan los
    `RAG_TOP_K` fragmentos más parecidos y se responde con los mismos prompts v1–v4, anteponiendo
    siempre el bloque de canales.
  - **`agente`**: Deep Agent (`deepagents`). La herramienta `search_knowledge` busca en Qdrant y
    guarda cada fragmento en `/retrieved/`. El agente delega cada archivo al subagente `chunk-analyst`
    (en paralelo) y redacta la respuesta citando la fuente.
- **Why:** completar la tarea T-16 reutilizando lo que el equipo ya practicó en clase. Frente a las
  otras opciones de contexto:
  - Frente a «toda la base», el RAG envía unos 2 000 tokens en lugar de ~36 000, así que es más
    barato con Claude y viable con Ollama en CPU.
  - Frente al contexto reducido por palabras, los embeddings encuentran sinónimos y paráfrasis.
  - Los embeddings se calculan en local: el texto no sale del equipo.
- **Where:**
  - `model/llm/vector_store.py`: índice, huella del contenido y búsqueda.
  - `model/llm/agent.py`: herramienta de búsqueda y Deep Agent.
  - `model/llm/prompts.py`: `AGENT_SYSTEM` y `CHUNK_ANALYST_SYSTEM`.
  - `model/llm/assistants.py`: `RetrievalAssistant` (lo comparten «reducido» y «rag») y `AgentAssistant`.
  - `controller/assistant.py`: `rag_assistant`, `agent_assistant`, `build_assistant` y `MODES`.
  - CLI: `sb index` y el argumento `--modo`. Streamlit: selector «Modo de contexto».
  - `config.py`: `EMBEDDING_MODEL`, `QDRANT_DIR`, `QDRANT_COLLECTION` y `RAG_TOP_K`.
  - Pruebas: `tests/test_rag.py`.
- **Diferencias con el ejercicio original:**
  - No se vuelve a descargar ni a dividir: se usan los chunks de Gold, que ya traen URL, título y
    sección.
  - El índice se persiste en `data/gold/qdrant/` (ignorado por git) en vez de vivir en memoria. La
    colección lleva una huella SHA-256 de los chunks: si `sb process` los cambia, se recalcula. Si no,
    se reutiliza (unos 50 s la primera vez y unos 7 s después).
  - Los prompts del agente heredan las reglas de la Fase 1: no-información, citación, datos como
    datos y nada de datos personales.
  - La herramienta y el agente reciben el backend y la búsqueda por constructor. Así se prueban sin
    red con `DeterministicFakeEmbedding`, Qdrant en memoria y un backend falso.
- **Learned:**
  - `StateBackend` de Deep Agents solo funciona dentro de la ejecución del grafo. Por eso la
    herramienta recibe un backend inyectable para poder probarla aislada.
  - `QdrantVectorStore` vectoriza un texto de prueba cada vez que se abre, para validar la dimensión.
  - En Windows, el cliente Qdrant en disco hay que cerrarlo con `atexit`; si se cierra en `__del__`,
    falla al apagar el intérprete.
  - Con `llama3.2:3b`, el agente corre pero no sigue bien el flujo de herramientas: tarda ~2 min y
    citó un dominio inventado. Para el modo `agente` se recomienda Claude; el modo `rag` sí funciona
    bien con Ollama.

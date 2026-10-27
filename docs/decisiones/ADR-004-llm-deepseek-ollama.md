# ADR-004 · DeepSeek por API con Ollama como respaldo

> **Estado: reemplazada por [ADR-005](ADR-005-llm-claude-ollama.md)** (2026-10-24).

- **Categoría:** modelo
- **Why:** DeepSeek ofrece contexto largo a bajo costo (presupuesto del equipo: 10 USD). Ollama
  (`llama3.2:3b`) permite probar sin costo y sin enviar datos fuera de la máquina.
- **Where:** `config.LLM_PROVIDER`, `llm/service.build_llm` (cambiar de proveedor no cambia la lógica).
- **Riesgos:** la API es de un tercero: solo se le envía información pública. La clave vive en `.env`.
  El 3B local alucina más; sirve como contraste en la experimentación de prompts.
- **Hugging Face:** descartado para generación en este proyecto por restricciones del curso.

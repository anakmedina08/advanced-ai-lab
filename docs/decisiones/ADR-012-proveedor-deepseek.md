# ADR-012 · DeepSeek como proveedor alterno del LLM

- **Fecha:** 2026-11-06
- **What:** `LLM_PROVIDER` acepta `deepseek` (`langchain-deepseek`, modelo `deepseek-chat`, ventana de 64K tokens) además de `anthropic` y `ollama`. Claude sigue por defecto (ADR-005).
- **Why:** el equipo arranca con 10 USD de saldo en Anthropic; si el consumo de tokens lo exige, se cambia a DeepSeek solo con una variable, sin tocar prompts ni lógica.
- **Where:** `config.py` (`PROVIDERS`, `DEEPSEEK_*`), `model/llm/service.py` (`build_llm`, `context_budget`), `.env.example`.
- **Learned:** la base completa (~36K tokens) cabe en la ventana de DeepSeek; antes de cambiar de proveedor se corre `make eval` con ambos para comparar calidad y costo.

# ADR-010 · Claude sin `temperature` y con esfuerzo de razonamiento bajo

- **Fecha:** 2026-11-10
- **What:** `build_llm("anthropic")` ya no envía `temperature`. En su lugar envía
  `output_config={"effort": ANTHROPIC_EFFORT}`, con `low` por defecto y configurable en `.env`.
  Ollama conserva `temperature=0`.
- **Why:** la API respondía `400 · temperature is deprecated for this model` con
  `claude-haiku-5-5`. Los modelos actuales de Claude (Haiku 5.5, Sonnet 5.5, Opus 5.5…) rechazan
  los parámetros de muestreo (`temperature`, `top_p`, `top_k`) con valores distintos del
  predeterminado. Además, desde la versión de API `2026-10-21` los rechazan en todos los modelos.
  Estos modelos razonan antes de responder, y ese razonamiento cuenta dentro de `max_tokens`. Con
  esfuerzo `low` el razonamiento es corto: la respuesta es más rápida y barata y no se corta con
  1024 tokens.
- **Where:** `config.py` (`ANTHROPIC_EFFORT`), `model/llm/service.py` (`build_llm`),
  `tests/test_llm.py` (la petición a Claude no lleva `temperature`) y `.env.example`.
- **Learned:** el determinismo que antes daba la temperatura 0 ahora lo sostienen el prompt
  (reglas, formato fijo, ejemplos few-shot) y el esfuerzo bajo. Con Claude Haiku 5.5, una pregunta
  tardó 2.3 s con toda la base, 1.5 s en modo RAG y 16.6 s en modo agente, todas con fuente.

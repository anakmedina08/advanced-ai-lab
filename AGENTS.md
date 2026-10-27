# AGENTS.md · Reglas para agentes (Claude Code, GGA, Antigravity)

## Contexto
Asistente de conocimiento de **Seguros Bolívar** (información pública, alcance PERSONAS +
CANALES DE ATENCIÓN). Proyecto integrador de Técnicas Avanzadas de IA (UAO · Grupo 10).
Fase 1: scraping Medallion → conocimiento consolidado en el system prompt → Resumen, FAQ y
Q&A con LangChain + Streamlit. Fase 2: RAG con los chunks de `data/gold/chunks.jsonl`.

## Arquitectura (obligatoria)
- `src/sb_asistente/scraping/` → descubrir (robots + sitemap) y descargar a Bronze.
- `src/sb_asistente/processing/` → Silver (limpieza) y Gold (Markdown, corpus, chunks).
- `src/sb_asistente/llm/` → prompts versionados y servicio LangChain. **Ningún prompt fuera de `prompts.py`.**
- `src/sb_asistente/view/` → Streamlit; solo llama a `KnowledgeAssistant`, sin lógica de negocio.
- `pipeline.py` orquesta; `config.py` concentra rutas, alcance, umbrales y modelo (nada de números mágicos).
- Dependencias por constructor (sesión HTTP, LLM, reloj, sleep) para poder probar sin red ni API.

## Ética y datos (no negociable)
- Solo información **pública**. Respetar `robots.txt`, 1–2 s entre peticiones, User-Agent identificable.
- Prohibido: contenido tras login, portales transaccionales, datos personales (Ley 1581 de 2012),
  información interna de la compañía aunque un integrante tenga acceso por su trabajo.
- `data/` (raw, silver, gold) **nunca** se versiona. `.env` con `ANTHROPIC_API_KEY` **nunca** se versiona.

## Calidad
- Python 3.13 y **solo uv** (`uv add`, `uv run`); prohibido `pip` y `requirements.txt`.
- Type hints y docstrings en español en lo público. Pruebas AAA en `tests/` sin red ni API
  (fixtures HTML locales y `FakeListChatModel`).
- Prompts: temperatura 0, delimitación XML, regla de no-información y citación de la fuente.
- Sin notebooks.

## Comandos
```bash
uv sync
uv run sb discover && uv run sb scrape && uv run sb process   # Bronze → Silver → Gold
uv run sb stats
uv run sb ask "¿Cuál es el WhatsApp de atención?"
uv run sb eval --version v3
uv run streamlit run src/sb_asistente/view/streamlit_app.py
uv run pytest -v --cov && uv run ruff check . && uv run ruff format --check .
```

## Git
Gitflow (`main`, `develop`, `feature/*`), Conventional Commits, una PR por propósito con revisión
cruzada. Decisiones técnicas: registrar en **Engram** y espejo en `docs/decisiones/`.

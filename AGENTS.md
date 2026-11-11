# AGENTS.md · Reglas para agentes (Claude Code, GGA, Antigravity)

> **Fuente única de verdad:** [`CONSTITUTION.md`](CONSTITUTION.md). Este archivo resume las reglas
> que un agente debe respetar; si algo cambia, se actualiza primero la constitución.
> Spec del trabajo: [`openspec/specs/fase1-base-conocimiento/`](openspec/specs/fase1-base-conocimiento/)
> (`spec.md`, `plan.md`, `tasks.md`). Estándar del repo: skill `jan-project-standard`
> (se instala localmente en `.claude/skills/`; esa carpeta no se versiona).

## Contexto
Asistente de conocimiento de **Seguros Bolívar** (información pública, alcance PERSONAS +
CANALES DE ATENCIÓN). Proyecto integrador de Técnicas Avanzadas de IA (UAO · Grupo 10).
Fase 1: scraping Medallion → conocimiento consolidado en el system prompt → Resumen, FAQ y
Q&A con LangChain + Streamlit. Fase 2: RAG con los chunks de `data/gold/chunks.jsonl`
(embeddings Ollama + Qdrant en `vector_store.py`, Deep Agent en `agent.py`; ADR-009).

## Arquitectura MVC (obligatoria)
- **Modelo** `src/sb_asistente/model/`
  - `scraping/` → descubrir (robots + sitemap) y descargar a Bronze.
  - `processing/` → Silver (limpieza) y Gold (Markdown, corpus, chunks).
  - `llm/` → `prompts.py` (**ningún prompt fuera de aquí**), `service.py` (LangChain, `Answer`),
    `knowledge.py` (leer Gold), `keyword_search.py` y `vector_store.py` (recuperar fragmentos),
    `agent.py` (Deep Agent) y `assistants.py` (Q&A sobre contexto recuperado).
  - `evaluation.py` → banco de preguntas y métricas.
- **Controlador** `src/sb_asistente/controller/` → `pipeline.py` (etapas del scraping) y `assistant.py`
  (arma cada modo de Q&A con la configuración y orquesta la evaluación; sin lógica de contexto propia).
- **Vista** `src/sb_asistente/view/` → `streamlit_app.py` y `cli.py`; **solo llaman al controlador**, sin lógica de negocio.
- `config.py` concentra rutas, alcance, umbrales y modelo (nada de números mágicos).
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
- Prompts: delimitación XML, regla de no-información y citación de la fuente. Temperatura 0 solo en
  Ollama: Claude rechaza `temperature` (400); allí se usa `output_config.effort` (ADR-010).
- Sin notebooks.

## Comandos (`make help` lista todos)
```bash
make dev            # uv sync + hooks de pre-commit
make data           # scraping completo (≈ 4 min, respeta robots.txt)
make process        # Bronze → Silver → Gold sin red
make index          # Fase 2: embeddings de los chunks en Qdrant (Ollama local)
make app            # uv run streamlit run app.py
make check          # ruff + formato + pytest (lo mismo que la CI)
make docker-build   # imagen multi-stage CPU
uv run sb ask "¿Cuál es el WhatsApp de atención?"
uv run sb ask "¿Qué cubre el SOAT?" --modo rag    # completo | reducido | rag | agente
```

## Búsqueda de código
Si `tgrep` está instalado, úsalo en lugar de `grep` (ver `.opencode/rules/tgrep.md`).

## Git
Gitflow (`main`, `develop`, `feature/*`), Conventional Commits, una PR por propósito con revisión
cruzada (Code Reviewer: Daniel Silva). Decisiones técnicas: registrar en **Engram** y espejo en
`docs/decisiones/` (formato What / Why / Where / Learned); actualizar `CONSTITUTION.md` en el mismo commit.

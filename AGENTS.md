# AGENTS.md · Reglas para agentes (Claude Code, GGA, Antigravity)

> **Fuente única de verdad:** [`CONSTITUTION.md`](CONSTITUTION.md). Este archivo resume las reglas
> que un agente debe respetar; si algo cambia, se actualiza primero la constitución.
> Spec del trabajo: [`openspec/specs/fase1-base-conocimiento/`](openspec/specs/fase1-base-conocimiento/)
> (`spec.md`, `plan.md`, `tasks.md`). Estándar del repo: skill `jan-project-standard`
> (`.claude/skills/jan-project-standard/`).

## Contexto
Asistente de conocimiento de **Seguros Bolívar** (información pública, alcance PERSONAS +
CANALES DE ATENCIÓN). Proyecto integrador de Técnicas Avanzadas de IA (UAO · Grupo 10).
Fase 1: scraping Medallion → conocimiento consolidado en el system prompt → Resumen, FAQ y
Q&A con LangChain + Streamlit. Fase 2: RAG con los chunks de `data/gold/chunks.jsonl`.

## Arquitectura MVC (obligatoria)
- **Modelo** `src/sb_asistente/model/`
  - `scraping/` → descubrir (robots + sitemap) y descargar a Bronze.
  - `processing/` → Silver (limpieza) y Gold (Markdown, corpus, chunks).
  - `llm/` → prompts versionados, servicio LangChain y contexto reducido. **Ningún prompt fuera de `prompts.py`.**
  - `evaluation.py` → banco de preguntas y métricas.
- **Controlador** `src/sb_asistente/controller/` → `pipeline.py` (etapas del scraping) y `assistant.py` (Q&A, evaluación).
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
- Prompts: temperatura 0, delimitación XML, regla de no-información y citación de la fuente.
- Sin notebooks.

## Comandos (`make help` lista todos)
```bash
make dev            # uv sync + hooks de pre-commit
make data           # scraping completo (≈ 4 min, respeta robots.txt)
make process        # Bronze → Silver → Gold sin red
make app            # uv run streamlit run app.py
make check          # ruff + formato + pytest (lo mismo que la CI)
make docker-build   # imagen multi-stage CPU
uv run sb ask "¿Cuál es el WhatsApp de atención?"
```

## Búsqueda de código
Si `tgrep` está instalado, úsalo en lugar de `grep` (ver `.opencode/rules/tgrep.md`).

## Git
Gitflow (`main`, `develop`, `feature/*`), Conventional Commits, una PR por propósito con revisión
cruzada (Code Reviewer: Daniel Silva). Decisiones técnicas: registrar en **Engram** y espejo en
`docs/decisiones/` (formato What / Why / Where / Learned); actualizar `CONSTITUTION.md` en el mismo commit.

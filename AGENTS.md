# AGENTS.md · Reglas para agentes (Claude Code, GGA, Antigravity)

> **Fuente única de verdad:** [`CONSTITUTION.md`](CONSTITUTION.md). Este archivo resume las reglas
> que un agente debe respetar; si algo cambia, se actualiza primero la constitución.
> Spec del trabajo: [`openspec/specs/fase2-producto-unico/`](openspec/specs/fase2-producto-unico/)
> (activa) y [`fase1-base-conocimiento/`](openspec/specs/fase1-base-conocimiento/) (`spec.md`, `plan.md`,
> `tasks.md`). Requisitos de ambos cursos y su evidencia: [`docs/requisitos.md`](docs/requisitos.md). Estándar del repo: skill `jan-project-standard`
> (`.claude/skills/jan-project-standard/`).

## Contexto
Asistente de conocimiento de **Seguros Bolívar** (información pública, alcance PERSONAS +
CANALES DE ATENCIÓN). Proyecto integrador de Técnicas Avanzadas de IA (UAO · Grupo 10).
Fase 1: scraping Medallion → conocimiento consolidado en el system prompt → Resumen, FAQ y
Q&A con LangChain + Streamlit. Fase 2 (producto único, ADR-009): este repositorio sirve a los cursos
de Técnicas (módulo de conocimiento) y de Gestión (módulo de recomendación), con API FastAPI y RAG.
Modos de Q&A: completo, reducido, rag (Qdrant, `vector_store.py`) y agente (Deep Agents, `agent.py`; ADR-018).

## Arquitectura MVC (obligatoria)
- **Modelo** `src/sb_asistente/model/`
  - `scraping/` → descubrir (robots + sitemap) y descargar a Bronze.
  - `processing/` → Silver (limpieza) y Gold (Markdown, corpus, chunks).
  - `llm/` → `prompts.py` (**ningún prompt fuera de aquí**), `service.py` (LangChain, `Answer`),
    `knowledge.py` (leer Gold), `keyword_search.py` y `vector_store.py` (recuperar fragmentos),
    `agent.py` (Deep Agent) y `assistants.py` (Q&A sobre contexto recuperado).
  - `evaluation.py` → banco de preguntas y métricas.
  - `recomendador/` → datos sintéticos, contrato de datos, líneas base y métricas (curso de Gestión).
  - `vision/` → YOLO (`deteccion.py`), difuminado de personas (`privacidad.py`), escena con Claude
    (`escena.py`) y plan objeto/situación → respuesta (`seguros.py`); extra opcional `uv sync --extra vision`.
    La foto no se guarda y las personas se difuminan antes de salir del equipo (ADR-020).
- **Controlador** `src/sb_asistente/controller/` → `pipeline.py` (scraping), `assistant.py` (arma los modos de Q&A y orquesta la evaluación) y `recomendador.py`.
- **Vista** `src/sb_asistente/view/` → `api.py` (FastAPI) con `schemas.py` (Pydantic), `api_client.py` (httpx),
  `anotaciones.py`, `streamlit_app.py` (navegación) con `app_pages/` y `ui.py`, y `cli.py`;
  **solo llaman al controlador**, sin lógica de negocio. Toda entrada de la API es un modelo Pydantic.
- `config.py` concentra rutas, alcance, umbrales y modelo (nada de números mágicos).
- Dependencias por constructor (sesión HTTP, LLM, reloj, sleep) para poder probar sin red ni API.

## Ética y datos (no negociable)
- Solo información **pública**. Respetar `robots.txt`, 1–2 s entre peticiones, User-Agent identificable.
- Prohibido: contenido tras login, portales transaccionales, datos personales (Ley 1581 de 2012),
  información interna de la compañía aunque un integrante tenga acceso por su trabajo.
- `data/` (raw, silver, gold) **nunca** se versiona. `.env` (claves de Anthropic/DeepSeek y token de eventos) **nunca** se versiona.

## Subagentes (`.claude/agents/`) y telemetría
| Subagente | Modelo | Cuándo |
|---|---|---|
| `arquitecto` | opus | antes de un plan no trivial o si el mismo error se repite; solo lectura, nunca escribe código |
| `explorador` | haiku | mapear el repo o encontrar llamadas sin llenar el contexto del líder |
| `probador` | haiku | después de cada cambio: ruff, formato y pytest con cobertura |
| `revisor` | sonnet | antes de cada commit o PR: revisa el diff contra estas reglas |
| `guardian-datos` | haiku | cambios en scraping, datos, API o configuración |
| `ml-recomendador` | sonnet | historias HU del recomendador (worktree aislado) |
| `documentador` | sonnet | al cerrar una tarea: README, ADR, tasks y `docs/requisitos.md` |

Los hooks de `.claude/settings.json` registran cada evento (sin prompts ni contenido) en
`logs/agent-events.jsonl` y, con `AGENT_EVENTS_URL`/`AGENT_EVENTS_TOKEN` en `.env`, lo publican en
el panel de yellowdata.com.co/casos. No desactivar los hooks ni enviar datos privados por ellos.

## RAG, agente y RPC
- La vista nueva es `view/rpc.py` (JSON-RPC 2.0); todo método nuevo se registra en `METODOS` con su
  modelo Pydantic de parámetros y su prueba en `tests/test_rpc.py`.
- Las tools del agente viven en `model/agente.py` y reciben sus dependencias inyectadas; nunca leen
  `.env` ni archivos fuera de `data/gold/`.
- Antes de cambiar la recuperación (`model/rag/`), correr `uv run sb rag evaluar` y registrar el hit@k.
- `data/vector/` y `data/memoria/` no se versionan (contienen texto de usuarios y del sitio).

## Skills
- Propias en `.claude/skills/<nombre>/SKILL.md` (`make skill-new`); externas con `make skill-add`
  (quedan en `.agents/skills/` y `skills-lock.json`). Validar con `make skills`.
- Solo `metadata.uso: asistente` llega al chat público; cambiar una skill a ese uso requiere PR revisado
  por `revisor` y `guardian-datos`.
- La skill `operar-asistente` resume cómo levantar y depurar cada parte del producto.

## Calidad
- Python 3.13 y **solo uv** (`uv add`, `uv run`); prohibido `pip` y `requirements.txt`.
- Type hints y docstrings en español en lo público. Pruebas AAA en `tests/` sin red ni API
  (fixtures HTML locales y `FakeListChatModel`).
- Prompts: delimitación XML, regla de no-información y citación de la fuente. Temperatura 0 solo en
  Ollama: Claude rechaza `temperature` (400); allí se usa `output_config.effort` (ADR-019).
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
make api            # API FastAPI en http://127.0.0.1:8000/docs
make reco           # datos sintéticos + validación + líneas base del recomendador
uv run sb ask "¿Cuál es el WhatsApp de atención?"
uv run sb ask "¿Qué cubre el SOAT?" --modo rag    # completo | reducido | rag | agente
```

## Búsqueda de código
Si `tgrep` está instalado, úsalo en lugar de `grep` (ver `.opencode/rules/tgrep.md`).

## Git
Gitflow (`main`, `develop`, `feature/*`), Conventional Commits, una PR por propósito con revisión
cruzada (Code Reviewer: Daniel Silva). Decisiones técnicas: registrar en **Engram** y espejo en
`docs/decisiones/` (formato What / Why / Where / Learned); actualizar `CONSTITUTION.md` en el mismo commit.

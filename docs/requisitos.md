# Matriz de requisitos · Técnicas Avanzadas y Gestión de Proyectos

Cada requisito de los dos cursos con su evidencia en este repositorio. Estados:
**✅ cumplido** · **🟡 en curso** · **⏳ pendiente** (con su tarea en `openspec/specs/*/tasks.md`).
La regla del equipo es que ningún requisito quede sin evidencia: si algo cambia, el subagente
`documentador` actualiza esta tabla en el mismo Pull Request.

## Comunes a los dos cursos (gobernanza y herramientas)

| Requisito | Estado | Evidencia |
|---|---|---|
| Repositorio público con licencia | ✅ | GitHub `anakmedina08/advanced-ai-lab`, [`LICENSE`](../LICENSE) (MIT) · ADR-009 |
| Python 3.13 con `uv` (sin pip ni requirements.txt) | ✅ | `pyproject.toml`, `uv.lock`, `.python-version` |
| Arquitectura MVC | ✅ | `src/sb_asistente/{model,controller,view}` · ADR-007 |
| Type hints y docstrings | ✅ | regla `ANN` y `D` de Ruff en `pyproject.toml` |
| Pydantic | ✅ | `src/sb_asistente/view/schemas.py` · ADR-010 |
| FastAPI | ✅ | `src/sb_asistente/view/api.py`, `uv run sb api` → `/docs` · ADR-010 |
| RPC (JSON-RPC 2.0) | ✅ | `POST /rpc`, `view/rpc.py`, `rpc.descubrir`, `make rpc-demo` · ADR-015 |
| LangSmith (trazas y dataset de evaluación) | 🟡 | `LANGSMITH_*` en `.env`, etiquetas por turno, `make langsmith-dataset`; falta cargar la clave y correr un experimento |
| Pruebas AAA sin red ni API, cobertura ≥ 85 % | ✅ | `tests/` (359 pruebas), `make check`, umbral en la CI |
| Ruff (lint y formato) | ✅ | `make lint`, `make format-check` |
| pre-commit con hook de GGA | ✅ | `.pre-commit-config.yaml` (higiene, Ruff, `uv lock --check`, GGA, bloqueo de datos y secretos) |
| Conventional Commits | ✅ | hook `commit-msg` → `scripts/check_commit_msg.py` |
| CI en GitHub Actions | ✅ | `.github/workflows/ci.yml` (calidad, build Docker, evento al panel) |
| Docker multi-stage | ✅ | `Dockerfile`, `make docker-build` · ADR-008 |
| Gitflow y Pull Requests con Code Reviewer | ✅ | ramas `main`/`develop`/`feat/*`, `.github/pull_request_template.md` |
| Proteger `main` (PR + CI en verde) | ⏳ | T-15 |
| Dependabot y labels | ✅ | `.github/dependabot.yml`, `.github/labels.yml` |
| Spec versionada (Spec-Driven Development) | ✅ | `openspec/specs/fase1-…/` y `fase2-producto-unico/` (spec, plan, tasks) |
| `CONSTITUTION.md` (fuente única de verdad) | ✅ | [`CONSTITUTION.md`](../CONSTITUTION.md) |
| `AGENTS.md` | ✅ | [`AGENTS.md`](../AGENTS.md) |
| Engram (memoria de decisiones) | 🟡 | `docs/decisiones/` ADR-001 a ADR-012; registrar ADR-009 a 012 en Engram: T-29 |
| Skill del estándar del repositorio | ✅ | `.claude/skills/jan-project-standard/` |
| Skills propias y de terceros (Claude Code, OpenCode, skills.sh) | ✅ | `.claude/skills/`, `model/skills.py`, `make skills`, `make skill-new`, `make skill-add`, `opencode.json` · ADR-014 |
| Subagentes de Claude Code | ✅ | `.claude/agents/` (7 subagentes) · ADR-011 |
| Hooks de Claude Code y trazabilidad de agentes | ✅ | `.claude/settings.json`, `scripts/agent_events.py`, `logs/agent-events.jsonl` |
| Panel en vivo del desarrollo con agentes | 🟡 | código listo en yellowdata.com.co/casos; publicar y cargar secretos: T-22 |
| Tablero Kanban público | 🟡 | `scripts/crear_kanban.py` (fases 1 y 2) y `scripts/crear_kanban_gestion.py` (HU); crear el Project público en GitHub |
| Diagrama del flujo de inferencia en el README | ✅ | [`README.md`](../README.md#flujo-de-inferencia) |
| Ética de datos (robots.txt, Ley 1581, sin datos reales versionados) | ✅ | `docs/alcance.md`, `.gitignore`, hook `forbid-data-and-secrets`, validación en `schemas.py` |

## Técnicas Avanzadas de IA en Modelos de Lenguaje (módulo de conocimiento)

| Requisito | Estado | Evidencia |
|---|---|---|
| Web scraping ético de la empresa | ✅ | `model/scraping/`, `scripts/scrape_empresa.py`, `make data` |
| Arquitectura Medallion con metadatos | ✅ | `model/processing/`, `controller/pipeline.py` |
| Resumen, FAQ y Q&A con LangChain | ✅ | `model/llm/service.py`, `/resumen`, `/faq`, `/preguntas`, `sb ask/summary/faq` |
| Prompts versionados con citación de fuente | ✅ | `model/llm/prompts.py` (v1–v4) |
| Evaluación con banco de preguntas | ✅ | `evaluacion/preguntas.yaml` (24), `make eval` |
| Comparar versiones de prompt con Claude e informe | ⏳ | T-14, `informe/main.tex` |
| Proveedor de LLM intercambiable | ✅ | Anthropic / DeepSeek / Ollama · ADR-005, ADR-012 |
| Contexto reducido para modelos locales | ✅ | `model/llm/retrieval.py` · ADR-006 |
| Base de datos vectorial | ✅ | Chroma persistente (`data/vector/`), `sb rag indexar` · ADR-016 |
| Fase 2: RAG con embeddings | 🟡 | recuperación híbrida BM25 + vectores (`model/rag/`), hit@6 = 16/21 solo con BM25 (`sb rag evaluar`); falta medir con `nomic-embed-text`: T-34 |
| Tools (function calling) | ✅ | `buscar_conocimiento`, `recomendar_seguros`, `clasificar_intencion` (`model/agente.py`) · ADR-017 |
| Salidas estructuradas | ✅ | `RespuestaAgente` (Pydantic, `ToolStrategy`) con validación de fuentes · ADR-017 |
| Memoria persistente | ✅ | `SqliteSaver` por conversación (`data/memoria/`), `agente.historial`, `agente.olvidar` · ADR-017 |
| Clasificador de intención | 🟡 | línea base por reglas en `model/intencion.py` (en uso en el chat); modelo entrenado: T-27 |
| Chat con orquestador (Q&A, recomendador, clasificador) | ✅ | `POST /chat`, `controller/chat.py`, pestaña de chat en yellowdata.com.co/casos · ADR-013 |

## Gestión de Proyectos en IA y CD (módulo de recomendación)

| Requisito | Estado | Evidencia |
|---|---|---|
| M1 · Taller de código heredado (AI Doctors) | ✅ | repositorio aparte `daalrasi/gpia-m1-ai-doctors` (otro caso) |
| M2 · Propuesta con backlog, criterios Dado/Cuando/Entonces, CPM y Gantt | ✅ | `docs/gestion/propuesta-m2.pdf`, `docs/gestion/backlog.json`, `docs/gestion/propuesta/build.py` |
| Datos sintéticos con contrato de datos (sin PII) | ✅ | `model/recomendador/sintetico.py`, `contrato.py`, `sb reco generar/validar` |
| Líneas base y métricas (Recall@5, NDCG@5) | ✅ | `popularidad.py`, `metricas.py`, `particion.py`, `sb reco baseline` |
| Servicio de recomendación por API | ✅ | `/recomendaciones/{cliente_id}` (línea base por segmento) |
| Modelo e5-small + LightGBM (Recall@5 ≥ 0,70) | ⏳ | T-23 |
| MLflow | ⏳ | T-24 |
| Auditoría de sesgo | ⏳ | T-25 |
| Front web | 🟡 | chat público listo (yellowdata.com.co/casos/asistente-seguros/chat); consola del asesor: T-26 |
| Recomendación por perfil descrito (sin identificación) | ✅ | `recomendar_por_perfil`, `POST /chat` |
| Despliegue de la API | ⏳ | `passenger_wsgi.py` listo para cPanel: T-33; imagen Docker con la API: T-28 |

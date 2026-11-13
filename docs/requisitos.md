# Matriz de requisitos · Gestión de Proyectos y Técnicas Avanzadas

Cada requisito de los dos cursos con su evidencia en este repositorio. Estados:
**✅ cumplido** · **🟡 en curso** · **⏳ pendiente** (con su tarea en `openspec/specs/*/tasks.md`).
La regla del equipo es que ningún requisito quede sin evidencia: si algo cambia, el subagente
`documentador` actualiza esta tabla en el mismo Pull Request. La interfaz la muestra en
**Sustentación › Entregables por curso** (`view/app_pages/sustentacion.py`).

## Gestión de Proyectos en IA y CD

| Requisito | Estado | Evidencia |
|---|---|---|
| M1 · Taller de código heredado (AI Doctors) | ✅ | repositorio aparte `daalrasi/gpia-m1-ai-doctors` (otro caso) |
| M2 · Propuesta con backlog, criterios Dado/Cuando/Entonces, CPM y Gantt | ✅ | `docs/gestion/propuesta-m2.pdf`, `docs/gestion/backlog.json`, `docs/gestion/propuesta/build.py` |
| Módulo 3 · Git: Gitflow con `main`, `develop` y ramas `feature/*` | ✅ | ramas del repositorio, Conventional Commits con hook `commit-msg` (`scripts/check_commit_msg.py`) |
| Módulo 3 · Pull Requests con revisor (Reviewers) y responsable (Assignees) | ✅ | 20 PR con revisión cruzada (Katherine ↔ Daniel), `.github/pull_request_template.md` |
| Módulo 3 · Proteger `main` (PR + CI en verde) | ⏳ | Settings › Branches: T-15 |
| Spec-Driven Development (SDD) | ✅ | `openspec/specs/` (spec, plan y tasks por funcionalidad, requisitos R1–R32 con escenarios y pruebas) |
| GitHub Projects (tablero Kanban) | ✅ | proyecto «Gestion» generado desde los `tasks.md` con `scripts/crear_kanban.py`; issues con responsable |
| Tareas que no se harán: «Close as not planned» | 🟡 | criterio: cerrar como *not planned* (no como hechas) lo que no se hará; por validar con el equipo |
| Pruebas unitarias (mínimo 120), AAA sin red ni API | ✅ | `tests/` (cerca de 490 casos), `uv run pytest --collect-only -q`, cobertura ≥ 85 % en la CI |
| FastAPI con contratos Pydantic | ✅ | `view/api.py`, `view/schemas.py`, `uv run sb api` → `/docs` · ADR-010 |
| API con visión: `POST /fotos` con YOLO L | ✅ | `yolo26l` elegido por comparación (`docs/evaluacion-resultados.md` §4), `lifespan`, cliente `httpx` · ADR-020 |
| MLflow (bitácora de experimentos) | 🟡 | `sb mlflow ui`, página Panel del equipo › Experimentos (asistente, recuperación y líneas base) · ADR-022; falta el LightGBM (T-71) |
| Datos sintéticos con contrato de datos (sin PII) | ✅ | `model/recomendador/sintetico.py`, `contrato.py`, `sb reco generar/validar` |
| Líneas base y métricas (Recall@5, NDCG@5) | ✅ | `popularidad.py`, `metricas.py`, `particion.py`, `sb reco baseline` (segmento: Recall@5 = 0,639) |
| Servicio de recomendación por API | ✅ | `/recomendaciones/{cliente_id}` (línea base por segmento) |
| Recomendación por perfil descrito (sin identificación) | ✅ | `recomendar_por_perfil`, `POST /chat`, foto «¿qué hago?» |
| Modelo e5-small + LightGBM (Recall@5 ≥ 0,70) | ⏳ | T-23 |
| Auditoría de sesgo | ⏳ | T-25 |
| Front web | 🟡 | chat público listo (yellowdata.com.co/casos/asistente-seguros/chat); consola del asesor: T-26 |
| Despliegue de la API | ⏳ | `passenger_wsgi.py` listo para cPanel: T-33; imagen Docker con la API: T-28 |

## Técnicas Avanzadas de IA en Modelos de Lenguaje

| Requisito | Estado | Evidencia |
|---|---|---|
| Módulo 2 · LangChain: Resumen, FAQ y Q&A | ✅ | `model/llm/service.py`, `/resumen`, `/faq`, `/preguntas`, `sb ask/summary/faq` |
| Web scraping ético de la empresa | ✅ | `model/scraping/`, `scripts/scrape_empresa.py`, `make data` |
| Arquitectura Medallion con metadatos | ✅ | `model/processing/`, `controller/pipeline.py` |
| Prompts versionados con citación de fuente | ✅ | `model/llm/prompts.py` (v1–v4) |
| Evaluación con banco de preguntas | ✅ | `evaluacion/preguntas.yaml` (25), `make eval`, `docs/evaluacion-resultados.md` |
| Comparar versiones de prompt con Claude e informe | ✅ | v3: cita de fuente 100 % frente a 20 % de v1 · `informe/main.tex` · T-14 |
| Proveedor de LLM intercambiable | ✅ | Anthropic / DeepSeek / Ollama · ADR-005, ADR-012; Claude sin `temperature` · ADR-019 |
| Contexto reducido para modelos locales | ✅ | `model/llm/keyword_search.py` · ADR-006 |
| Base de datos vectorial | ✅ | Chroma (`data/vector/`, ADR-016) y Qdrant (`data/gold/qdrant/`, ADR-018) |
| Módulo 2 · RAG con embeddings | ✅ | modos «rag» y «agente» (ADR-018), híbrido BM25 + vectores (ADR-016); hit@k de 4 métodos (T-34, T-65) |
| Tools (function calling) | ✅ | `buscar_conocimiento`, `recomendar_seguros`, `clasificar_intencion` (`model/agente.py`) · ADR-017 |
| Agente con subagentes (Deep Agents) | ✅ | `model/llm/agent.py`, subagente `chunk-analyst` · ADR-018 |
| Salidas estructuradas | ✅ | `RespuestaAgente` y `Escena` (Pydantic) · ADR-017, ADR-020 |
| Memoria persistente | ✅ | `SqliteSaver` por conversación (`data/memoria/`), `agente.historial`, `agente.olvidar` · ADR-017 |
| Modelo multimodal (visión) con privacidad | ✅ | foto «¿qué hago?»: YOLO difumina personas y Claude entiende la situación · ADR-020 |
| Clasificador de intención | 🟡 | línea base por reglas en `model/intencion.py` (en uso en el chat); modelo entrenado: T-27 |
| Chat con orquestador (Q&A, recomendador, clasificador) | ✅ | `POST /chat`, `controller/chat.py`, pestaña de chat en yellowdata.com.co/casos · ADR-013 |

## Comunes a los dos cursos (gobernanza y herramientas)

| Requisito | Estado | Evidencia |
|---|---|---|
| Repositorio público con licencia | ✅ | GitHub `anakmedina08/advanced-ai-lab`, [`LICENSE`](../LICENSE) (MIT) · ADR-009 |
| Python 3.13 con `uv` (sin pip ni requirements.txt) | ✅ | `pyproject.toml`, `uv.lock`, `.python-version` |
| Arquitectura MVC | ✅ | `src/sb_asistente/{model,controller,view}` · ADR-007 |
| Type hints y docstrings | ✅ | regla `ANN` y `D` de Ruff en `pyproject.toml` |
| RPC (JSON-RPC 2.0) | ✅ | `POST /rpc`, `view/rpc.py`, `rpc.descubrir`, `make rpc-demo` · ADR-015 |
| Interfaz web para el cliente y para el equipo | ✅ | Streamlit en dos áreas, chat con fuentes, tema corporativo neutro · ADR-021 |
| LangSmith (trazas y dataset de evaluación) | 🟡 | `LANGSMITH_*` en `.env`, `make langsmith-dataset`; falta la clave: T-66 |
| Ruff (lint y formato) | ✅ | `make lint`, `make format-check` |
| pre-commit con hook de GGA | ✅ | `.pre-commit-config.yaml` (higiene, Ruff, `uv lock --check`, GGA, bloqueo de datos y secretos) |
| CI en GitHub Actions | ✅ | `.github/workflows/ci.yml` (calidad, build Docker, evento al panel) |
| Docker multi-stage | ✅ | `Dockerfile`, `make docker-build` · ADR-008 |
| Dependabot y labels | ✅ | `.github/dependabot.yml`, `.github/labels.yml` |
| `CONSTITUTION.md` (fuente única de verdad) | ✅ | [`CONSTITUTION.md`](../CONSTITUTION.md) |
| `AGENTS.md` | ✅ | [`AGENTS.md`](../AGENTS.md) |
| Decisiones registradas (ADR) | ✅ | `docs/decisiones/` ADR-001 a ADR-022 |
| Engram (memoria de decisiones) | ⏳ | Engram 1.20 instalado; registrar los ADR: T-29 |
| Skill del estándar del repositorio | ✅ | `.claude/skills/jan-project-standard/` |
| Skills propias y de terceros (Claude Code, OpenCode, skills.sh) | ✅ | `.claude/skills/`, `model/skills.py`, `make skills`, `make skill-new`, `make skill-add`, `opencode.json` · ADR-014 |
| Subagentes de Claude Code | ✅ | `.claude/agents/` (7 subagentes) · ADR-011 |
| Hooks de Claude Code y trazabilidad de agentes | ✅ | `.claude/settings.json`, `scripts/agent_events.py`, `logs/agent-events.jsonl` |
| Panel en vivo del desarrollo con agentes | 🟡 | código listo en yellowdata.com.co/casos; publicar y cargar secretos: T-22 |
| Diagrama del flujo de inferencia en el README | ✅ | [`README.md`](../README.md#flujo-de-inferencia) |
| Ética de datos (robots.txt, Ley 1581, sin datos reales versionados) | ✅ | `docs/alcance.md`, `.gitignore`, hook `forbid-data-and-secrets`, validación en `schemas.py`, personas difuminadas en fotos |

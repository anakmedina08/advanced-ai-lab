# Matriz de requisitos · Gestión de Proyectos y Técnicas Avanzadas

Cada requisito de los dos cursos con su evidencia en este repositorio. Estados:
**✅ cumplido** · **🟡 en curso** · **⏳ pendiente** · **⛔ no planeado** (cerrado como *not planned* con su motivo).
La regla del equipo es que ningún requisito quede sin evidencia: si algo cambia, el subagente
`documentador` actualiza esta tabla en el mismo Pull Request. Actualizada para los anuncios 006
(Técnicas, Módulo 2) y 007 (Gestión, Módulo 3) del 13 de noviembre de 2026; guion en
[`sustentacion.md`](sustentacion.md). La interfaz la muestra en
**Sustentación › Entregables por curso** (`view/app_pages/sustentacion.py`).

## Gestión de Proyectos en IA y CD

| Requisito | Estado | Evidencia |
|---|---|---|
| M1 · Taller de código heredado (AI Doctors) | ✅ | repositorio aparte `daalrasi/gpia-m1-ai-doctors` (otro caso) |
| M2 · Propuesta con backlog, criterios Dado/Cuando/Entonces, CPM y Gantt | ✅ | `docs/gestion/propuesta-m2.pdf`, `docs/gestion/backlog.json`, `docs/gestion/propuesta/build.py` |
| Módulo 3 · Git: Gitflow con `main`, `develop` y ramas `feature/*` | ✅ | ramas del repositorio, Conventional Commits con hook `commit-msg` (`scripts/check_commit_msg.py`) |
| Módulo 3 · Pull Requests con revisor (Reviewers) y responsable (Assignees) | 🟡 | 61 PR fusionadas, cada historia con responsable, revisor (Daniel), `Closes #N` y CI; Daniel aprobó 30 de las 40 PR de historias, faltan #163 a #181 · `.github/pull_request_template.md` |
| Mínimo 40 PR fusionadas con revisión (piso de 8 por integrante) | 🟡 | 48 PR fusionadas (≥ 40) y 0 abiertas; falta la aprobación registrada en las 40 últimas y el piso de 8 PR propias de Daniel |
| Mínimo 40 especificaciones SDD (spec, plan y tasks) | ✅ | 45 en `openspec/specs/` (`find openspec -name spec.md`), una por historia, escritas antes del código y vinculadas a su issue y PR |
| Frontend desacoplado (sin Streamlit) | ✅ | React + Vite + TypeScript en `frontend/` (SPEC-022 a 032): estados, Network visible, foto con confianza, CI propia |
| Backend en 3 capas con /health y errores HTTP | ✅ | `model/vision` → `controller/vision` → `view/api.py`; `GET /health`, `ErrorOut` 400/404/422/500/503 (SPEC-007, 008) |
| Módulo 3 · Proteger `main` (PR + CI en verde) | ✅ | rama protegida: exige PR y el check «Ruff + Pytest», sin force push ni borrado (T-15) |
| Spec-Driven Development (SDD) | ✅ | `openspec/specs/` (spec, plan y tasks por funcionalidad, requisitos R1–R32 con escenarios y pruebas) |
| GitHub Projects (tablero Kanban) | ✅ | proyecto «Gestion» generado desde los `tasks.md` con `scripts/crear_kanban.py`; issues con responsable |
| Tareas que no se harán: «Close as not planned» | ✅ | las tareas fuera del alcance de los Módulos 2 y 3 se cerraron como *not planned* con su motivo (T-22, T-23, T-25, T-26, T-27, T-29, T-33, T-66, T-71); 0 issues abiertos |
| Pruebas unitarias (mínimo 120), AAA sin red ni API | ✅ | `tests/` (más de 640 casos de Python y 44 del frontend con Vitest), `uv run pytest --collect-only -q`, cobertura ≥ 85 % en la CI |
| FastAPI con contratos Pydantic | ✅ | `view/api.py`, `view/schemas.py`, `uv run sb api` → `/docs` · ADR-010 |
| API con visión: `POST /fotos` con YOLO L | ✅ | `yolo26l` elegido por comparación (`docs/evaluacion-resultados.md` §4), `lifespan`, cliente `httpx` · ADR-020 |
| MLflow: servidor en 5050, 3 corridas comparables y Model Registry | ✅ | `make mlflow-server`; experimento `vision-yolo` (3 corridas con P, R, F1, mAP, latencia p95 y throughput, artefactos y tags); `sb-yolo-difuminado@produccion` (SPEC-033 a 035) · ADR-022 |
| Model Card | ✅ | [`model-card.md`](model-card.md) (SPEC-037) |
| Diagrama de arquitectura (Archify) | ✅ | [`arquitectura.html`](arquitectura.html) generado con Archify (tipo *architecture*, perfil *showcase*, evidencia del repositorio por componente); fuente [`arquitectura.json`](arquitectura.json) (SPEC-038, SPEC-048) |
| Kanban con WIP, AC, Fibonacci y métricas | ✅ | límites WIP de 2 en *In progress* e *In review* en el tablero, plantilla de historia, puntos en «Estimate», milestone M3 y [`kanban.md`](kanban.md) con WIP, throughput, edad y cycle time (SPEC-040) |
| Datos sintéticos con contrato de datos (sin PII) | ✅ | `model/recomendador/sintetico.py`, `contrato.py`, `sb reco generar/validar` |
| Líneas base y métricas (Recall@5, NDCG@5) | ✅ | `popularidad.py`, `metricas.py`, `particion.py`, `sb reco baseline` (segmento: Recall@5 = 0,639) |
| Servicio de recomendación por API | ✅ | `/recomendaciones/{cliente_id}` (línea base por segmento) |
| Recomendación por perfil descrito (sin identificación) | ✅ | `recomendar_por_perfil`, `POST /chat`, foto «¿qué hago?» |
| Modelo e5-small + LightGBM (Recall@5 ≥ 0,70) | ⛔ | no planeado para el Módulo 3 (T-23, T-71): queda para el Módulo 4 |
| Auditoría de sesgo | ⛔ | no planeada para el Módulo 3 (T-25); los sesgos del modelo de la API están en la [Model Card](model-card.md) |
| Front web | ✅ | frontend propio React (SPEC-022 a 032); el chat de yellowdata.com.co sigue disponible |
| Despliegue reproducible | ✅ | `docker compose build` construye la API y el frontend; los contenedores responden (`/health` ok y nginx sirve la SPA) · `docker-compose.yml` (SPEC-041, SPEC-048); cPanel no planeado (T-33) |

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
| Clasificador de intención | ✅ | reglas en `model/intencion.py` y router de 5 rutas (32/32 en `evaluacion/router.yaml`, SPEC-012); el modelo entrenado (T-27) no está planeado |
| Chat con orquestador (Q&A, recomendador, clasificador) | ✅ | `POST /chat`, `controller/chat.py`, pestaña de chat en yellowdata.com.co · ADR-013 |
| M2 · Memoria corto plazo: checkpointer + thread_id persistente | ✅ | `SqliteSaver`, hilo recuperado tras reinicio (`tests/test_sesiones.py`), checkpoints (time travel) por REST (SPEC-020) |
| M2 · Gestión del contexto: trim_messages + SummarizationMiddleware | ✅ | recorte por tokens y resumen con umbrales en `config.py` (SPEC-016) |
| M2 · Memoria largo plazo: Store con namespace y search() | ✅ | `SqliteStore`, namespace `(usuarios, id, perfil)`, `dynamic_prompt` (SPEC-015) |
| M2 · Herramienta determinista CSV con @tool y Pydantic | ✅ | `consultar_datos` / `ConsultaDatos` (SPEC-011) |
| M2 · RAG sobre Qdrant (ANN, payload, cita) e híbrido | ✅ | `model/rag/qdrant.py` + BM25 con RRF (SPEC-013) |
| M2 · Router (directo, datos, RAG, mixto) | ✅ | `model/router.py`, banco 32/32, tools por ruta, sin LLM fuera de alcance (SPEC-012, 017) |
| M2 · Blindaje del RAG contra inyección indirecta | ✅ | delimitación, escape, marca de sospecha y documento de prueba (SPEC-014) |
| M2 · Frontend propio con streaming, sesiones y errores | ✅ | React + SSE (SPEC-019, 022 a 032) |
| M2 · Trazas (LangSmith o logs equivalentes) | ✅ | logs estructurados equivalentes: `data/logs/turnos.jsonl` con latencia por tool, `sb trazas`, `X-Request-ID` (SPEC-009, 021); LangSmith sin clave |
| M2 · Diagramas: grafo del agente, checkpointer vs. Store, router | ✅ | [`arquitectura.md`](arquitectura.md), [`arquitectura.html`](arquitectura.html) (SPEC-038) |
| M2 · Evaluación del retrieval (recall@10, nDCG@10) | ✅ | 21 consultas etiquetadas, 5 métodos, MLflow (SPEC-036) · [`evaluacion-resultados.md`](evaluacion-resultados.md) §5 |

## Comunes a los dos cursos (gobernanza y herramientas)

| Requisito | Estado | Evidencia |
|---|---|---|
| Repositorio público con licencia | ✅ | GitHub `anakmedina08/advanced-ai-lab`, [`LICENSE`](../LICENSE) (MIT) · ADR-009 |
| Python 3.13 con `uv` (sin pip ni requirements.txt) | ✅ | `pyproject.toml`, `uv.lock`, `.python-version` |
| Arquitectura MVC | ✅ | `src/sb_asistente/{model,controller,view}` · ADR-007 |
| Type hints y docstrings | ✅ | regla `ANN` y `D` de Ruff en `pyproject.toml` |
| RPC (JSON-RPC 2.0) | ✅ | `POST /rpc`, `view/rpc.py`, `rpc.descubrir`, `make rpc-demo` · ADR-015 |
| Interfaz web | ✅ | producto: frontend React desacoplado (Módulo 2); Streamlit solo como herramienta interna del equipo (ADR-021) |
| LangSmith (trazas y dataset de evaluación) | ⛔ | no planeado sin clave del equipo (T-66): reemplazado por las trazas locales (SPEC-021) |
| Ruff (lint y formato) | ✅ | `make lint`, `make format-check` |
| pre-commit con hook de GGA | ✅ | `.pre-commit-config.yaml` (higiene, Ruff, `uv lock --check`, GGA, bloqueo de datos y secretos) |
| CI en GitHub Actions | ✅ | `.github/workflows/ci.yml` (calidad, build Docker, evento al panel) |
| Docker multi-stage | ✅ | `Dockerfile`, `make docker-build` · ADR-008 |
| Dependabot y labels | ✅ | `.github/dependabot.yml`, `.github/labels.yml` |
| `CONSTITUTION.md` (fuente única de verdad) | ✅ | [`CONSTITUTION.md`](../CONSTITUTION.md) |
| `AGENTS.md` | ✅ | [`AGENTS.md`](../AGENTS.md) |
| Decisiones registradas (ADR) | ✅ | `docs/decisiones/` ADR-001 a ADR-022 |
| Engram (memoria de decisiones) | ⛔ | no planeado (T-29): las decisiones quedan en `docs/decisiones/` (ADR-001 a ADR-022) |
| Skill del estándar del repositorio | ✅ | `.claude/skills/jan-project-standard/` |
| Skills propias y de terceros (Claude Code, OpenCode, skills.sh) | ✅ | `.claude/skills/`, `model/skills.py`, `make skills`, `make skill-new`, `make skill-add`, `opencode.json` · ADR-014 |
| Subagentes de Claude Code | ✅ | `.claude/agents/` (7 subagentes) · ADR-011 |
| Hooks de Claude Code y trazabilidad de agentes | ✅ | `.claude/settings.json`, `scripts/agent_events.py`, `logs/agent-events.jsonl` |
| Panel en vivo del desarrollo con agentes | ⛔ | no planeado (T-22): los eventos quedan en `logs/agent-events.jsonl` |
| Diagrama del flujo de inferencia en el README | ✅ | [`README.md`](../README.md#flujo-de-inferencia) |
| Ética de datos (robots.txt, Ley 1581, sin datos reales versionados) | ✅ | `docs/alcance.md`, `.gitignore`, hook `forbid-data-and-secrets`, validación en `schemas.py`, personas difuminadas en fotos |

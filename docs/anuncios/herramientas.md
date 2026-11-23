# Catálogo de herramientas por materia

Estado de cada herramienta según los anuncios del profesor, con el anuncio que lo fija. El
auditor (K4) falla si el proyecto usa una herramienta ⛔.

**Estados:**
- ✅ **exigida:** debe usarse o demostrarse.
- ⚠️ **permitida / deseable:** suma, no resta.
- ⛔ **no permitida:** no debe aparecer en el proyecto.

## 551462 · Técnicas Avanzadas de IA

| Herramienta | Paquete | Estado | Desde | Reemplazo / nota | En el proyecto |
|---|---|---|---|---|---|
| streamlit | `streamlit` | ⛔ no permitida | 006 | Frontend propio (React, Next.js, Vue, Svelte) + backend/API | ❌ **está en `pyproject.toml`, `app.py` y `make app`** |
| gradio | `gradio` | ⛔ no permitida | 006 | Frontend propio | no |
| pip / requirements.txt | — | ⛔ no permitida | 001 | uv (Python 3.13) | no |
| Notebooks como entrega | — | ⛔ no permitida | 001 | Scripts `.py` modularizados | no (`*.ipynb` ignorado) |
| Diapositivas / PowerPoint | — | ⛔ no permitida | 001 | Demo en vivo | no |
| uv + Python 3.13 | — | ✅ exigida | 001 | — | ✅ |
| pytest, PEP 8, docstrings, plantilla de PR | — | ✅ exigida | 001 | — | ✅ |
| OpenCode | — | ✅ exigida | 004 | Consola agéntica del curso | ✅ `opencode.json` |
| Engram | — | ✅ exigida | 004 | Memoria de decisiones entre sesiones | 🟡 citado en AGENTS/README; falta evidencia de uso |
| OpenSpec / GitHub Spec-Kit (SDD) | — | ✅ exigida | 004 | — | ✅ `openspec/` (48 specs) |
| GGA (hook de pre-commit) | — | ✅ exigida | 004 | Audita el staging contra AGENTS.md | ✅ hook `gga` |
| Skills (SKILL.md, skills.sh) | — | ✅ exigida | 004 | Incluye la del curso `jan-project-standard` | ✅ |
| SkillSpector | — | ⚠️ recomendada | 004 | Auditar skills antes de autorizarlas | ❌ |
| Ollama + `nomic-embed-text-v2-moe` | — | ⚠️ taller | 004 | — | 🟡 usamos `embeddinggemma` (también vista en clase) |
| Scrapling | — | ⚠️ permitida | 004 | Scraping del corpus | ❌ (usamos requests, ADR-003) |
| LangChain + LangGraph (`create_agent`, middleware, `@tool`, `dynamic_prompt`) | — | ✅ exigida | 006 | — | ✅ |
| Checkpointer SqliteSaver/PostgresSaver + Store con namespace | — | ✅ exigida | 006 | — | ✅ |
| `trim_messages` / SummarizationMiddleware | — | ✅ exigida | 006 | — | ✅ `model/agente.py` |
| Pydantic / structured outputs | — | ✅ exigida | 006 | — | ✅ |
| Qdrant (HNSW, filtros de payload) | — | ✅ exigida | 006 | — | ✅ |
| LangSmith | — | ✅ exigida | 006 | Observa, no orquesta | ✅ proyecto `sb-asistente` |
| FastAPI (backend del agente) | — | ✅ exigida | 006 | — | ✅ |
| recall@10 / nDCG@10 con 20–30 consultas | — | ✅ exigida | 006 | — | ✅ `model/rag/evaluacion.py` |
| JEV · System One (gatekeeper del router) | — | ⚠️ deseable | 006 | Choice, Noul, Score, Box | ❌ |
| LLM Wiki / OKF | — | ⚠️ deseable | 006 | Paradigma alternativo al RAG | ❌ |
| Deep Agents | — | ⚠️ deseable | 006 | — | ✅ |
| Ragas | — | ⚠️ deseable | 006 | — | ❌ |
| Time travel (replay/fork) | — | ⚠️ deseable | 006 | — | 🟡 verificar |
| Vercel/Netlify + Render/Fly.io/HF Spaces | — | ⚠️ deseable | 006 | — | ❌ |
| Playwright (tests de UI) | — | ⚠️ deseable | 006 | — | ❌ |
| WhatsApp / Telegram | — | ✅ exigida en M3 | 001 | Despliegue en canal real | ❌ |
| OpenFang | — | ✅ exigida en M3 | 001 | Sistema operativo de agentes con adaptadores de canales (Telegram, WhatsApp) | ❌ planeado (oleada 4) |
| ReAct + Function Calling | — | ✅ exigida en M3 | 001 | — | ✅ |

## 551475 · Gestión de Proyectos en IA y CD

| Herramienta | Paquete | Estado | Desde | Reemplazo / nota | En el proyecto |
|---|---|---|---|---|---|
| streamlit, gradio, dash | `streamlit`, `gradio`, `dash` | ⛔ no permitida | 007 | Cliente desacoplado (React, Next, Vue, Svelte, Angular, Astro, HTML/JS) | ❌ **streamlit en el repo** |
| Notebooks / Colab / Kaggle | — | ⛔ no permitida | 007 | `.py` en `src/` y `tests/` | no |
| pip / requirements.txt | — | ⛔ no permitida | 007 | uv | no |
| Pesos binarios en git (.pt, .h5, .onnx, .joblib) | — | ⛔ no permitida | 007 | Script de descarga, Git LFS o DVC | no (ignorados) |
| Capturas de MLflow | — | ⛔ no permitida | 007 | UI viva | no |
| FastAPI (REST) o gRPC | — | ✅ exigida | 007 | Una de las dos | ✅ FastAPI (+ JSON-RPC) |
| Modelo MaaS (Hugging Face Hub / ModelScope) | — | ✅ exigida | 007 | `org/modelo@rev` | ✅ YOLO26 |
| MLflow (servidor, 3 runs comparables, Model Registry) | — | ✅ exigida | 007 | — | ✅ |
| GitHub Projects (4 columnas, WIP, Fibonacci 1:1, métricas) | — | ✅ exigida | 007 | Tablero público, enlazado en el README | 🟡 verificar que sea público |
| SDD: ≥ 40 specs con spec/plan/tasks | — | ✅ exigida | 007 | Piso de 8 por persona | ✅ 48 · ❓ reparto por persona |
| ≥ 40 PR fusionadas con revisión | — | ✅ exigida | 007 | Piso de 8 por persona | ✅ · ❓ reparto por persona |
| pytest (≥ 120), ruff, uv, Docker CPU, GitHub Actions | — | ✅ exigida | 007 | — | ✅ |
| Archify | — | ✅ exigida | 007 | Diagrama en `docs/` | ✅ |
| Model Card | — | ✅ exigida | 007 | `docs/model-card.md` | ✅ |
| OpenCode (`opencode.json` V2), MCP | — | ✅ exigida | 005 | — | ✅ |
| Engram | — | ✅ exigida | 005 | — | 🟡 |
| SkillSpector | — | ⚠️ recomendada | 005 | — | ❌ |
| ADR por decisión, AGENTS.md + GGA | — | ⚠️ deseable | 007 | — | ✅ |
| HF Spaces o Docker multi-stage | — | ⚠️ deseable | 007 | — | ✅ multi-stage |
| Logs estructurados + latencia | — | ⚠️ deseable | 007 | — | 🟡 |
| GitLab (proyecto + `.gitlab-ci.yml` lint → test → build → deploy) | — | ✅ exigida | 008 | GitHub Actions se acepta para el pipeline, pero la demo abre GitLab | ❌ |
| GitLab Container Registry / Docker Hub (imagen con tags) | — | ✅ exigida | 008 | — | ❌ (`push: false`) |
| Droplet / VPS con Docker y firewall | — | ✅ exigida | 008 | DigitalOcean en el laboratorio | ❌ |
| Proxy inverso con HTTPS (Nginx, Caddy o Traefik) | — | ✅ exigida | 008 | — | ❌ |
| Deploy por SSH con healthcheck | — | ✅ exigida | 008 | — | ❌ (el HEALTHCHECK del Dockerfile ya existe) |
| Variables de CI enmascaradas (`SSH_KEY`, `REGISTRY_USER`/`REGISTRY_PASS`, `CI_JOB_TOKEN`) | — | ✅ exigida | 008 | — | ❌ |
| GitLab MCP en OpenCode | — | ✅ exigida | 008 | `opencode mcp list` → *connected* | ❌ |
| GitLab CLI | `glab` | ✅ exigida | 008 | `glab auth status`, `glab pipeline status` | ❌ |
| Docker-in-Docker en CI | — | ✅ exigida | 008 | build de la imagen en el pipeline | ❌ |
| GitLab Generic Packages (modelo) | — | ⚠️ si aplica | 008 | Nuestro modelo viene de Hugging Face (MaaS) | ❓ |
| VS Code | — | ✅ exigida | 008 | Abierto en la raíz con terminal | ❓ el equipo usa Antigravity |
| Videos, diapositivas, capturas como evidencia | — | ⛔ no permitida | 008 | Demo en vivo | no |

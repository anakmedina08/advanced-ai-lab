# CONSTITUTION — Asistente Seguros Bolívar

> **Verdad central del proyecto.** Este documento define el propósito, el stack, la
> estructura, las convenciones y el flujo de trabajo de `Asistente Seguros Bolívar`. Si algo aquí
> contradice al código, el código manda **y este archivo se actualiza**.

> ⚠️ **Directiva de mantenimiento:** cada vez que se realicen cambios significativos
> (nuevas funcionalidades, cambios arquitectónicos, adición de clases/módulos o ajustes
> de tecnologías), **se debe actualizar este archivo en el mismo commit** para mantener
> la verdad central del proyecto bien documentada.

---

## 0. Identidad del proyecto

| Campo | Valor |
|-------|-------|
| **Nombre** | Asistente Seguros Bolívar |
| **Descripción** | Asistente de conocimiento sobre la información pública de Seguros Bolívar: scraping Medallion + Q&A con LangChain. |
| **Repositorio** | https://github.com/anakmedina08/advanced-ai-lab |
| **Autoría** | Daniel Silva y Katherine Medina (UAO) |
| **Licencia** | MIT |
| **Rama principal** | `main` |
| **Estado** | Fase 1 entregada · Fase 2 (RAG) en desarrollo |

## 1. Propósito y no-propósito

### Propósito

Responder preguntas de clientes personas sobre Seguros Bolívar (productos, coberturas y canales de
atención) a partir **solo** de la información pública del sitio oficial, **citando la página de
origen**. Proyecto integrador del curso Técnicas Avanzadas de IA en Modelos de Lenguaje (UAO).

### No-propósito

No vende, cotiza ni tarifica seguros; no usa información interna de la compañía ni datos personales;
no reemplaza a un asesor. No redistribuye el contenido extraído (`data/` no se versiona).

## 2. Alcance

### Dentro del alcance

- Páginas públicas de **personas** y **canales de atención** de www.segurosbolivar.com.
- Pipeline Medallion (Bronze → Silver → Gold) con metadatos: URL, título, sección, fecha y hash.
- Q&A, Resumen y FAQ con LangChain (Claude por API u Ollama local), con cita de la fuente.
- Interfaz Streamlit con el proceso de scraping visible y pestaña de evaluación.
- Fase 2: RAG con embeddings locales (Ollama) en Qdrant y un Deep Agent con subagentes sobre `chunks.jsonl`.

### Fuera del alcance (por ahora)

- Empresas, proveedores, reaseguradores, portales transaccionales y contenido tras login.
- Blog y PDFs (reservados para el RAG de la Fase 2).

## 3. Stack técnico

| Categoría | Tecnología |
|-----------|------------|
| **Lenguaje** | Python 3.13+ |
| **Gestor de paquetes y entorno** | [`uv`](https://docs.astral.sh/uv/) |
| **Build backend** | `uv_build` (src-layout) |
| **Paquete Python** | `sb_asistente` (MVC: `model/`, `controller/`, `view/`) |
| **Scraping** | `requests` + `BeautifulSoup` + `trafilatura` (sin Selenium: el sitio es SSR) |
| **LLM** | LangChain · Claude Haiku (API de Anthropic) · DeepSeek (alterno) · Ollama `llama3.2:3b` (local) |
| **API** | FastAPI + Pydantic v2 (`view/api.py`, `view/schemas.py`), `uv run sb api` |
| **Recomendador** | pandas + numpy (datos sintéticos, líneas base); M3: multilingual-e5-small + LightGBM + MLflow |
| **Interfaz** | Front web (consume la API), Streamlit (`app.py`) y CLI `sb` |
| **Testing** | [`pytest`](https://docs.pytest.org/) (AAA, sin red ni API) |
| **Linting / Formato** | [Ruff](https://docs.astral.sh/ruff/) |
| **Pre-commit** | higiene + Ruff + `uv lock --check` + GGA (revisión con IA contra `AGENTS.md`) + Conventional Commits |
| **Contenedor** | Docker multi-stage (CPU), `make docker-build` |
| **CI/CD** | [GitHub Actions](.github/workflows/ci.yml) |
| **Dependencias automáticas** | [Dependabot](.github/dependabot.yml) |
| **Especificación** | OpenSpec (`openspec/`: `spec.md`, `plan.md`, `tasks.md`) |
| **Memoria del agente** | Engram (espejo versionado en `docs/decisiones/`) |
| **Agentes** | Claude Code con 7 subagentes (`.claude/agents/`) y hooks de telemetría (`.claude/settings.json`) |

> ⚠️ **Regla dura:** toda gestión de dependencias y entornos pasa por `uv`. Está
> **prohibido** `pip` y `requirements.txt`.

## 4. Estructura del repositorio

```text
advanced-ai-lab/
├── app.py                         # entrada de Streamlit: uv run streamlit run app.py
├── src/sb_asistente/
│   ├── config.py                  # rutas, alcance, cortesía del scraper y modelo (sin números mágicos)
│   ├── model/                     # M · lógica de negocio
│   │   ├── scraping/              #   discover (robots + sitemap) · fetch (Bronze)
│   │   ├── processing/            #   clean (Silver) · gold (Markdown, corpus, chunks)
│   │   ├── llm/                   #   prompts · service · knowledge · keyword_search · vector_store · agent · assistants
│   │   ├── evaluation.py          #   banco de preguntas y métricas
│   │   └── recomendador/          #   sintético · contrato · líneas base · métricas (Gestión)
│   ├── controller/                # C · casos de uso
│   │   ├── pipeline.py            #   descubrir → extraer → limpiar → deduplicar → enriquecer
│   │   ├── assistant.py           #   arma los modos completo/reducido/rag/agente, evaluación
│   │   └── recomendador.py        #   generar, validar, comparar y recomendar
│   └── view/                      # V · presentación
│       ├── api.py · schemas.py    #   API FastAPI + contratos Pydantic
│       ├── streamlit_app.py       #   consola interna
│       └── cli.py                 #   comando `sb`
├── scripts/                       # scrape_empresa.py, crear_kanban.py, check_commit_msg.py
├── tests/                         # pytest por capa (AAA, fixtures HTML, LLM falso)
├── evaluacion/preguntas.yaml      # banco de 24 preguntas
├── openspec/                      # Spec-Driven Development (spec, plan, tasks)
├── docs/                          # requisitos, arquitectura, decisiones (ADR / Engram), gestion (M2), capturas
├── informe/                       # artículo IEEE (LaTeX)
├── data/raw · silver · gold       # Medallion (NO versionado)
├── Dockerfile · .dockerignore     # imagen multi-stage CPU
├── .github/                       # PR/issue templates, CI, Dependabot, labels
├── .claude/                       # agents/ (subagentes) · settings.json (hooks) · skills/
├── .opencode/rules/               # reglas para agentes (tgrep)
├── AGENTS.md · .gga               # reglas para agentes y revisión GGA en pre-commit
├── CONSTITUTION.md                # este archivo — verdad central
├── README.md · CONTRIBUTING.md · CODE_OF_CONDUCT.md · LICENSE
├── Makefile                       # interfaz de comandos (make help)
├── pyproject.toml · uv.lock · .python-version
└── .pre-commit-config.yaml
```

## 5. Convenciones de código

- **Estilo:** PEP 8 y PEP 257, impuesto por **Ruff** (`line-length = 110`, comillas dobles).
- **Tipado:** anotaciones en funciones y firmas públicas.
- **Nomenclatura:** `snake_case` (funciones/variables), `PascalCase` (clases), `UPPER_CASE` (constantes).
- **Docstrings:** en español, en módulos, clases y funciones públicas.
- **Pruebas:** `pytest` con el patrón **AAA**; sin red ni API (fixtures HTML y `FakeListChatModel`).
- **Idioma:** UI, comentarios y commits en español; identificadores en inglés o español consistente por módulo.
- **Reglas propias:**
  - **MVC estricto:** las vistas solo hablan con `controller/`; nunca construyen modelos ni prompts.
  - **Ningún prompt fuera de `model/llm/prompts.py`**; temperatura 0 en Ollama (Claude no la acepta: esfuerzo `low`, ADR-019); delimitación XML; regla de no-información; cita de la URL.
  - **Scraping ético:** respetar `robots.txt`, 1,5 s entre peticiones, User-Agent identificable, solo información pública.
  - **Datos:** `data/` y `.env` nunca se versionan (el hook `forbid-data-and-secrets` lo impide).
  - **Dependencias por constructor** (sesión HTTP, LLM, reloj, sleep) para probar sin red.

## 6. Calidad y automatización

| Herramienta | Rol | Comando |
|-------------|-----|---------|
| `uv` | Entornos y dependencias | `make install` |
| Ruff | Lint + formato | `make lint` / `make format` |
| `pytest` | Pruebas (≈ 150, sin red) | `make test` |
| `pre-commit` | Hooks antes de cada commit (incluye GGA) | `make pre-commit` |
| Docker | Imagen multi-stage CPU | `make docker-build` / `make docker-run` |
| GitHub Actions | CI (lint + formato + pruebas + build Docker) | `.github/workflows/ci.yml` |

- Ningún commit se salta los hooks (`--no-verify` está prohibido salvo causa justificada y documentada).
- La **CI debe estar en verde** antes de fusionar un Pull Request.
- Toda dependencia nueva entra con `uv add` / `uv add --dev` (nunca editando `uv.lock` a mano).

## 7. Repositorio y Git

- **Remoto:** `https://github.com/anakmedina08/advanced-ai-lab` (público)
- **Rama principal:** `main` (estable, solo recibe Pull Requests)
- **Estrategia de ramas:** `feat/...`, `fix/...`, `docs/...`, `refactor/...`, `test/...`, `chore/...`; integración vía Pull Request.
- **Revisión:** toda PR la aprueba el Code Reviewer (Daniel Silva) antes de fusionar.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/) —
  `feat:`, `fix:`, `docs:`, `refactor:`, `style:`, `test:`, `chore:` (validado por el hook `commit-msg`).
- **Tablero:** GitHub Projects público, generado desde `openspec/specs/fase1-base-conocimiento/tasks.md`.

## 8. Flujo diario (commit + push)

```bash
git status
make check
git add -A
git commit -m "tipo: mensaje descriptivo"
git push
```

## 9. Historial de decisiones técnicas

| Fecha | Decisión | Motivo |
|-------|----------|--------|
| 2026-10-24 | Conocimiento completo en el system prompt (Fase 1); RAG en Fase 2 ([ADR-001](docs/decisiones/ADR-001-contexto-completo-fase1.md)) | Requisito de la actividad; el corpus cabe en el contexto |
| 2026-10-24 | Alcance personas + canales ([ADR-002](docs/decisiones/ADR-002-alcance-personas-canales.md)) | Responder dudas de clientes; blog y PDFs a Fase 2 |
| 2026-10-24 | `requests` + trafilatura, sin Selenium ([ADR-003](docs/decisiones/ADR-003-requests-sin-selenium.md)) | El sitio entrega HTML renderizado en servidor |
| 2026-10-24 | Claude por API con Ollama local de respaldo ([ADR-005](docs/decisiones/ADR-005-llm-claude-ollama.md)) | Calidad y costo bajo; opción local sin enviar datos |
| 2026-10-30 | Contexto reducido para modelos locales ([ADR-006](docs/decisiones/ADR-006-contexto-reducido-ollama.md)) | En CPU, la base completa tardaba ~30 min por respuesta |
| 2026-11-01 | Estructura MVC (`model/`, `controller/`, `view/`) como el proyecto de Gestión ([ADR-007](docs/decisiones/ADR-007-estructura-mvc.md)) | Bajo acoplamiento: la vista solo habla con el controlador |
| 2026-11-01 | Imagen Docker multi-stage CPU y estándar `jan-project-standard` ([ADR-008](docs/decisiones/ADR-008-docker-multistage-y-estandar.md)) | Reproducibilidad y gobernanza del repositorio |
| 2026-11-06 | Un solo repositorio público para Técnicas y Gestión ([ADR-009](docs/decisiones/ADR-009-repositorio-unico.md)) | Mismo producto y misma gobernanza en ambos cursos |
| 2026-11-06 | API REST con FastAPI + Pydantic ([ADR-010](docs/decisiones/ADR-010-api-fastapi-pydantic.md)) | Front real y validación en la frontera |
| 2026-11-06 | Subagentes de Claude Code y telemetría en vivo ([ADR-011](docs/decisiones/ADR-011-subagentes-y-telemetria.md)) | Desarrollo con agentes visible y trazable |
| 2026-11-06 | DeepSeek como proveedor alterno ([ADR-012](docs/decisiones/ADR-012-proveedor-deepseek.md)) | Controlar el costo de tokens |
| 2026-11-10 | Claude sin `temperature` (la API la rechaza con 400) y con esfuerzo `low` ([ADR-019](docs/decisiones/ADR-019-claude-sin-temperatura.md)) | Los modelos actuales de Claude eliminaron los parámetros de muestreo |
| 2026-11-10 | Fase 2: RAG con Ollama + Qdrant y Deep Agent, adaptado de `ejercicio_langchain` ([ADR-018](docs/decisiones/ADR-018-rag-qdrant-deep-agents.md)) | Contexto ~2K tokens en vez de ~36K; embeddings locales |

## 10. Notas y tareas pendientes

- [x] Fase 2: RAG con embeddings sobre `data/gold/chunks.jsonl` (modos `rag` y `agente`).
- [ ] Evaluar `rag` y `agente` con Claude frente a la Fase 1 (`sb eval --modo rag`).
- [ ] Ejecutar `make eval` con Claude y completar el análisis del informe.
- [ ] Proteger `main` en GitHub (requerir PR y CI en verde).

## 11. Configuración local (no trackear)

> Configuración específica de la máquina local. **NO incluir en commits.**

Dentro de la carpeta de proyectos, `~/.gitconfig` aplica:

```ini
[includeIf "gitdir:~/Repos/"]
    path = ~/.gitconfig-personal
```

`~/.gitconfig-personal`:

```ini
[user]
    name = <Tu Nombre>
    email = <tu-correo>
[core]
    sshCommand = ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes
```

> Ajusta la carpeta y tus datos. Guía completa (macOS/Windows) en el skill
> `jan-project-standard` → `references/git-identity.md`.

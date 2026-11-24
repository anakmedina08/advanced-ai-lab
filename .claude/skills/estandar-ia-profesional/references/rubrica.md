# Rúbrica de auditoría — 66 verificaciones

El agente la aplica **con sus propias herramientas** (leer archivos, listar con glob, buscar texto),
sin ejecutar scripts de la skill ni código del proyecto. Cada fila dice **dónde mirar** y **qué
cuenta como cumplido**.

**Cómo puntuar:**
- Por dimensión: `% = pesos cumplidos / pesos posibles × 100`. El global suma todas las filas.
- Nivel según el % (ver `niveles-madurez.md`): N1 por debajo de 40, N2 de 40 a 69, N3 de 70 a 89, N4 desde 90.
- **Ante la duda, ❌.** Una verificación solo es ✅ con evidencia concreta (ruta y, si aplica, la línea encontrada).

Rutas ignoradas al buscar: `.git/`, `.venv/`, `node_modules/`, `data/`, `dist/`, `build/` y `__pycache__/`.

## 1 · Fundamentos (18)
| ID | Peso | Verificación | Dónde mirar · qué cuenta como ✅ |
|---|---|---|---|
| F1 | 3 | `requires-python` declarado | `pyproject.toml` contiene `requires-python` |
| F2 | 3 | Lockfile versionado | existe `uv.lock`, `poetry.lock` o `pdm.lock` |
| F3 | 1 | Python fijado | existe `.python-version` |
| F4 | 2 | src-layout | existe `src/*/__init__.py` |
| F5 | 3 | Makefile con `help` y `check` | `Makefile` tiene líneas que empiezan por `help:` y `check:` |
| F6 | 2 | pre-commit | existe `.pre-commit-config.yaml` |
| F7 | 3 | README, LICENSE y CONSTITUTION | existen los tres |
| F8 | 1 | `.editorconfig` | existe |

## 2 · Calidad de código y pruebas (17)
| ID | Peso | Verificación | Dónde mirar · qué cuenta como ✅ |
|---|---|---|---|
| C1 | 3 | Ruff | `ruff` en `pyproject.toml`, `Makefile` o `.pre-commit-config.yaml` |
| C2 | 3 | Tipos en el flujo | `ty check`, `mypy`, `pyright` o `basedpyright` en `Makefile`, `pyproject.toml` o pre-commit |
| C3 | 3 | pytest | existe `tests/` **y** `pytest` está configurado o en el Makefile |
| C4 | 3 | Cobertura mínima | `fail_under` / `--cov-fail-under` en la configuración **o** en `.github/workflows/*.yml` |
| C5 | 2 | Marcadores de pruebas | `markers =` en `[tool.pytest.ini_options]` o `pytest.ini` |
| C6 | 2 | Pruebas de API | algún `tests/**/*.py` usa `TestClient`, `schemathesis` o `httpx.AsyncClient` |
| C7 | 1 | Docstrings exigidos | el `select` de Ruff incluye `"D"` |

## 3 · Seguridad y cadena de suministro (19)
| ID | Peso | Verificación | Dónde mirar · qué cuenta como ✅ |
|---|---|---|---|
| S1 | 2 | SECURITY.md | en la raíz o en `.github/` |
| S2 | 3 | Secretos fuera del repo | `.gitignore` tiene una línea `.env` **y** existe `.env.example` |
| S3 | 3 | Escaneo de secretos | `gitleaks`, `detect-secrets` o `trufflehog` en pre-commit o en workflows |
| S4 | 2 | Dependabot / Renovate | `.github/dependabot.yml` o `renovate.json` |
| S5 | 3 | Auditoría de vulnerabilidades | `pip-audit`, `osv-scanner`, `safety check` o `uv audit` en workflows |
| S6 | 2 | Análisis estático | workflow con `codeql`, **o** `bandit` / regla `"S"` de Ruff |
| S7 | 2 | CODEOWNERS | `.github/CODEOWNERS` o `CODEOWNERS` |
| S8 | 1 | Permisos mínimos | algún workflow tiene `permissions:` al inicio de línea |
| S9 | 1 | SBOM | workflow que menciona `cyclonedx`, `syft` o `sbom` |

## 4 · CI/CD y releases (16)
| ID | Peso | Verificación | Dónde mirar · qué cuenta como ✅ |
|---|---|---|---|
| R1 | 3 | CI | existe `.github/workflows/*.yml` |
| R2 | 3 | Paridad local ↔ CI | un workflow corre `make check` o `pre-commit run`, **o** corre `ruff` **y** `pytest` |
| R3 | 2 | CHANGELOG | existe `CHANGELOG.md` |
| R4 | 2 | Releases SemVer | workflow con `release-please`, `semantic-release`, `git-cliff` o `action-gh-release` |
| R5 | 2 | Docker multi-stage | `Dockerfile` con `FROM … AS …` |
| R6 | 1 | Healthcheck | `HEALTHCHECK` / `healthcheck` en Docker o compose, **o** una ruta `"/health"` en `src/` |
| R7 | 1 | Caché en CI | workflow con `cache` o `setup-uv` |
| R8 | 2 | Entrega continua con entornos | algún workflow declara `environment:` (staging/produccion) para desplegar · guía `github-cicd.md` |

## 5 · Documentación y decisiones (14)
| ID | Peso | Verificación | Dónde mirar · qué cuenta como ✅ |
|---|---|---|---|
| D1 | 2 | Índice de docs | `docs/README.md` o `docs/index.md` |
| D2 | 3 | ADRs | al menos 3 archivos `docs/**/ADR-*.md` o `docs/adr/*.md` |
| D3 | 1 | Índice o plantilla de ADRs | `docs/decisiones/README.md`, `docs/adr/README.md` o `docs/decisiones/plantilla.md` |
| D4 | 2 | Diagrama de arquitectura | `docs/arquitectura*` o algún `docs/**/*.mmd` |
| D5 | 2 | Guías de contribución | `CONTRIBUTING.md` **y** `CODE_OF_CONDUCT.md` |
| D6 | 2 | Runbook | `docs/runbook.md`, `docs/operacion.md` o `RUNBOOK.md` |
| D7 | 2 | Contexto para agentes | `AGENTS.md` o `CLAUDE.md` |

## 6 · Proceso y trazabilidad (16)
| ID | Peso | Verificación | Dónde mirar · qué cuenta como ✅ |
|---|---|---|---|
| P1 | 2 | Plantilla de PR | `.github/pull_request_template.md` |
| P2 | 2 | Plantillas de issue | al menos 2 archivos `.github/ISSUE_TEMPLATE/*.yml` |
| P3 | 3 | Specs | carpeta `openspec/`, `specs/` o `.specify/` |
| P4 | 2 | Conventional Commits con hook | pre-commit menciona `commit-msg`, `conventional`, `commitizen` o `commitlint` |
| P5 | 2 | Definition of Done | "Definition of Done", "Definición de hecho/terminado" o "DoD" en `CONTRIBUTING.md`, la plantilla de PR o `CONSTITUTION.md` |
| P6 | 1 | Estrategia de ramas | «Gitflow» o «trunk-based» nombrado en `CONTRIBUTING.md` o `CONSTITUTION.md` (mencionar `develop` no basta) |
| P7 | 1 | Labels declarativas | `.github/labels.yml` |
| P8 | 1 | Matriz requisito ↔ evidencia | `docs/requisitos.md` o `docs/trazabilidad.md` |
| P9 | 2 | Solo `main` y `develop` permanentes | un workflow borra las ramas fusionadas (`git/refs/heads` / `--delete`) **y** el agente confirma con `git ls-remote --heads origin` que solo quedan `main`, `develop` y ramas con PR abierto · guía `github-cicd.md` |

## 7 · IA/ML responsable (21)
| ID | Peso | Verificación | Dónde mirar · qué cuenta como ✅ |
|---|---|---|---|
| M1 | 3 | Model card | `**/model-card*.md` o `**/MODEL_CARD*.md` |
| M2 | 2 | Data card | `**/data-card*.md` o `**/datasheet*.md` |
| M3 | 3 | Golden set | carpeta `evaluacion/`, `evals/`, `eval/` o `tests/evals/` |
| M4 | 2 | Experimentos | `mlflow` o `wandb` en `pyproject.toml` o `Makefile` |
| M5 | 3 | Evals en CI | workflow con la palabra `eval`/`evals`, `evaluacion`, `promptfoo`, `deepeval` o `ragas` |
| M6 | 2 | Prompts como código | `**/prompts*.py` o carpeta `prompts/` |
| M7 | 2 | Observabilidad LLM | `langsmith`, `opentelemetry` o `langfuse` en la configuración o en `.env.example` |
| M8 | 2 | Privacidad | "Ley 1581", "habeas data", "GDPR" o "PII" en `CONSTITUTION.md`, `README.md`, `SECURITY.md` o `docs/**/*.md` (AGENTS.md no cuenta: son instrucciones, no política) |
| M9 | 1 | Sesgo | "sesgo", "bias", "equidad" o "fairness" en `docs/**/*.md` |
| M10 | 1 | Registro de modelos | `register_model` o `registered_model_alias` en `src/` o `scripts/`, o mención de "Model Registry" en `scripts/` |

## 8 · Gobernanza de agentes de IA (16)
| ID | Peso | Verificación | Dónde mirar · qué cuenta como ✅ |
|---|---|---|---|
| G1 | 3 | Política de uso de IA | `docs/politica-uso-ia.md`, `AI_POLICY.md` o `docs/ai-policy.md` |
| G2 | 3 | Agente sin secretos | `.claude/settings.json` u `opencode.json` deniegan `Read(./.env…)` |
| G3 | 2 | Atribución explícita | `.claude/settings.json` define `attribution` o `includeCoAuthoredBy` |
| G4 | 2 | Filtro de trailers de IA | algún `scripts/*.py` elimina `Co-Authored-By` de Claude/Anthropic y está en el hook `commit-msg` |
| G5 | 2 | Skills propias | al menos 2 `SKILL.md` en `.claude/skills/*/` o `.agents/skills/*/` |
| G6 | 1 | Subagentes | algún `.claude/agents/*.md` |
| G7 | 1 | Skills de terceros fijadas | existe `skills-lock.json` |
| G8 | 2 | Revisión humana obligatoria | existe `.github/CODEOWNERS` (un texto que pida aprobación no basta) |

## Formato del informe que entrega el agente

```markdown
# Informe de madurez — <repo> · <fecha>
**Global: NN % · N?**

| Dimensión | % | Nivel |
|---|---:|---|

## Brechas priorizadas (peso 3 primero)
| ID | Peso | Brecha | Cómo cerrarla | Guía |

## Evidencia
- ✅ F1 — pyproject.toml:5 `requires-python = ">=3.13"`
- ❌ S3 — sin gitleaks/detect-secrets en pre-commit ni workflows
```

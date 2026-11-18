# Informe de madurez — `advanced-ai-lab` · 2026-11-17

**Puntaje global: 63.8 % · N2 Gestionado**

| Dimensión | Puntaje | Nivel | |
|---|---:|---|---|
| 1. Fundamentos | 100.0 % | N4 Optimizado | `████████████████████` |
| 2. Calidad de código y pruebas | 70.6 % | N3 Definido | `██████████████░░░░░░` |
| 3. Seguridad y cadena de suministro | 31.6 % | N1 Inicial | `██████░░░░░░░░░░░░░░` |
| 4. CI/CD y releases | 62.5 % | N2 Gestionado | `████████████░░░░░░░░` |
| 5. Documentación y decisiones | 85.7 % | N3 Definido | `█████████████████░░░` |
| 6. Proceso y trazabilidad | 68.8 % | N2 Gestionado | `██████████████░░░░░░` |
| 7. IA/ML responsable | 76.2 % | N3 Definido | `███████████████░░░░░` |
| 8. Gobernanza de agentes de IA | 43.8 % | N2 Gestionado | `█████████░░░░░░░░░░░` |
| 9. Requisitos del curso o cliente | 25.0 % | N1 Inicial | `█████░░░░░░░░░░░░░░░` |

## Brechas priorizadas (mayor peso primero)

| ID | Peso | Brecha | Cómo cerrarla | Guía |
|---|---:|---|---|---|
| C2 | 3 | Verificación de tipos (ty / mypy / pyright) en el flujo | Agregar `ty check` a make check y CI | `references/calidad.md` |
| S3 | 3 | Escaneo de secretos (gitleaks / detect-secrets / trufflehog) | Agregar hook gitleaks | `references/seguridad.md` |
| S5 | 3 | Auditoría de vulnerabilidades (pip-audit / osv-scanner) en CI | Workflow seguridad.yml con pip-audit | `references/seguridad.md` |
| M5 | 3 | Puerta de regresión de evaluación en CI | Workflow evals.yml con umbral | `references/ia-ml.md` |
| G1 | 3 | Política de uso de IA documentada | Copiar plantilla politica-uso-ia.md | `references/gobernanza-ia.md` |
| K1 | 3 | Índice de anuncios del curso | Paso 0: registrar el último anuncio en docs/anuncios/README.md | `references/anuncios.md` |
| K2 | 3 | Resumen por cada anuncio registrado | Crear los resúmenes que faltan | `references/anuncios.md` |
| K4 | 3 | Sin herramientas no permitidas por el curso (⛔ en docs/anuncios/herramientas.md) | Migrar a la herramienta que la reemplaza y registrar un ADR | `references/anuncios.md` |
| C5 | 2 | Pirámide de pruebas con marcadores (unit/integration/e2e) | Declarar markers en pytest | `references/calidad.md` |
| S1 | 2 | SECURITY.md (política de reporte) | Copiar plantilla SECURITY.md | `references/seguridad.md` |
| S6 | 2 | Análisis estático de seguridad (CodeQL / Bandit / Ruff S) | Activar CodeQL o reglas S de Ruff | `references/seguridad.md` |
| S7 | 2 | CODEOWNERS (revisores obligatorios) | Crear .github/CODEOWNERS | `references/seguridad.md` |
| R3 | 2 | CHANGELOG.md | Generar con git-cliff o release-please | `references/entrega.md` |
| R4 | 2 | Releases automatizados con SemVer (release-please / semantic-release / git-cliff) | Workflow release.yml | `references/entrega.md` |
| R8 | 2 | Entrega continua con entornos de GitHub (environment:) | Workflow deploy.yml con environment staging/produccion | `references/github-cicd.md` |
| D6 | 2 | Runbook de operación (levantar, diagnosticar, recuperar) | docs/runbook.md | `references/documentacion.md` |
| P5 | 2 | Definition of Done explícita | Sección DoD en CONTRIBUTING | `references/proceso.md` |
| P9 | 2 | Solo main y develop permanentes (borrado automático de ramas fusionadas) | Workflow ramas.yml + 'Automatically delete head branches' | `references/github-cicd.md` |
| M2 | 2 | Data card / datasheet del conjunto de datos | docs/data-card.md | `references/ia-ml.md` |
| G3 | 2 | Atribución de IA definida explícitamente (attribution) | attribution en .claude/settings.json | `references/gobernanza-ia.md` |
| G4 | 2 | Filtro de trailers de IA en commit-msg | scripts/limpiar_trailers_ia.py | `references/gobernanza-ia.md` |
| G8 | 2 | Revisión humana obligatoria (CODEOWNERS o regla de aprobación) | CODEOWNERS + protección de rama | `references/gobernanza-ia.md` |
| S9 | 1 | SBOM generado (CycloneDX / syft) | Generar SBOM en el release | `references/seguridad.md` |
| P6 | 1 | Estrategia de ramas documentada (Gitflow / trunk) | Documentar ramas | `references/proceso.md` |

## Detalle

### 1. Fundamentos — 100.0 % (N4 Optimizado)
- ✅ **F1** pyproject.toml con metadatos y requires-python *(peso 3)*
- ✅ **F2** Lockfile versionado (uv.lock / poetry.lock) *(peso 3)*
- ✅ **F3** Versión de Python fijada (.python-version) *(peso 1)*
- ✅ **F4** src-layout (src/<paquete>/) *(peso 2)*
- ✅ **F5** Makefile con help y check *(peso 3)*
- ✅ **F6** pre-commit configurado *(peso 2)*
- ✅ **F7** README, LICENSE y CONSTITUTION.md *(peso 3)*
- ✅ **F8** .editorconfig *(peso 1)*

### 2. Calidad de código y pruebas — 70.6 % (N3 Definido)
- ✅ **C1** Linter y formateador (Ruff) *(peso 3)*
- ❌ **C2** Verificación de tipos (ty / mypy / pyright) en el flujo *(peso 3)*
- ✅ **C3** Pruebas con pytest *(peso 3)*
- ✅ **C4** Umbral de cobertura obligatorio *(peso 3)*
- ❌ **C5** Pirámide de pruebas con marcadores (unit/integration/e2e) *(peso 2)*
- ✅ **C6** Pruebas de contrato o de API (TestClient / schemathesis) *(peso 2)*
- ✅ **C7** Docstrings exigidos por el linter (pydocstyle D) *(peso 1)*

### 3. Seguridad y cadena de suministro — 31.6 % (N1 Inicial)
- ❌ **S1** SECURITY.md (política de reporte) *(peso 2)*
- ✅ **S2** Secretos fuera del repo (.env ignorado + .env.example) *(peso 3)*
- ❌ **S3** Escaneo de secretos (gitleaks / detect-secrets / trufflehog) *(peso 3)*
- ✅ **S4** Actualización automática de dependencias (Dependabot / Renovate) *(peso 2)*
- ❌ **S5** Auditoría de vulnerabilidades (pip-audit / osv-scanner) en CI *(peso 3)*
- ❌ **S6** Análisis estático de seguridad (CodeQL / Bandit / Ruff S) *(peso 2)*
- ❌ **S7** CODEOWNERS (revisores obligatorios) *(peso 2)*
- ✅ **S8** Permisos mínimos en workflows (permissions:) *(peso 1)*
- ❌ **S9** SBOM generado (CycloneDX / syft) *(peso 1)*

### 4. CI/CD y releases — 62.5 % (N2 Gestionado)
- ✅ **R1** Workflow de CI *(peso 3)*
- ✅ **R2** Paridad local ↔ CI (la CI corre make check / pre-commit) *(peso 3)*
- ❌ **R3** CHANGELOG.md *(peso 2)*
- ❌ **R4** Releases automatizados con SemVer (release-please / semantic-release / git-cliff) *(peso 2)*
- ✅ **R5** Contenedor reproducible (Dockerfile multi-stage) *(peso 2)*
- ✅ **R6** Healthcheck del servicio *(peso 1)*
- ✅ **R7** Caché de dependencias en CI *(peso 1)*
- ❌ **R8** Entrega continua con entornos de GitHub (environment:) *(peso 2)*

### 5. Documentación y decisiones — 85.7 % (N3 Definido)
- ✅ **D1** Carpeta docs/ con índice *(peso 2)*
- ✅ **D2** ADRs (al menos 3) *(peso 3)*
- ✅ **D3** Plantilla e índice de ADRs *(peso 1)*
- ✅ **D4** Diagrama de arquitectura versionado *(peso 2)*
- ✅ **D5** CONTRIBUTING.md y CODE_OF_CONDUCT.md *(peso 2)*
- ❌ **D6** Runbook de operación (levantar, diagnosticar, recuperar) *(peso 2)*
- ✅ **D7** AGENTS.md / CLAUDE.md para agentes *(peso 2)*

### 6. Proceso y trazabilidad — 68.8 % (N2 Gestionado)
- ✅ **P1** Plantilla de PR con checklist *(peso 2)*
- ✅ **P2** Plantillas de issue (bug / historia / spike) *(peso 2)*
- ✅ **P3** Desarrollo guiado por specs (openspec/ o specs/) *(peso 3)*
- ✅ **P4** Conventional Commits validado por hook *(peso 2)*
- ❌ **P5** Definition of Done explícita *(peso 2)*
- ❌ **P6** Estrategia de ramas documentada (Gitflow / trunk) *(peso 1)*
- ✅ **P7** Labels declarativas *(peso 1)*
- ✅ **P8** Matriz de requisitos ↔ evidencia *(peso 1)*
- ❌ **P9** Solo main y develop permanentes (borrado automático de ramas fusionadas) *(peso 2)*

### 7. IA/ML responsable — 76.2 % (N3 Definido)
- ✅ **M1** Model card *(peso 3)*
- ❌ **M2** Data card / datasheet del conjunto de datos *(peso 2)*
- ✅ **M3** Banco de evaluación versionado (golden set) *(peso 3)*
- ✅ **M4** Seguimiento de experimentos (MLflow / W&B) *(peso 2)*
- ❌ **M5** Puerta de regresión de evaluación en CI *(peso 3)*
- ✅ **M6** Prompts versionados como código *(peso 2)*
- ✅ **M7** Observabilidad de LLM (LangSmith / OpenTelemetry / Langfuse) *(peso 2)*
- ✅ **M8** Privacidad y datos personales documentados (Ley 1581 / GDPR / PII) *(peso 2)*
- ✅ **M9** Evaluación de sesgo / equidad *(peso 1)*
- ✅ **M10** Registro de modelos con alias/versiones *(peso 1)*

### 8. Gobernanza de agentes de IA — 43.8 % (N2 Gestionado)
- ❌ **G1** Política de uso de IA documentada *(peso 3)*
- ✅ **G2** Agente sin acceso a secretos ni datos (permissions.deny) *(peso 3)*
- ❌ **G3** Atribución de IA definida explícitamente (attribution) *(peso 2)*
- ❌ **G4** Filtro de trailers de IA en commit-msg *(peso 2)*
- ✅ **G5** Skills propias con metadatos validados *(peso 2)*
- ✅ **G6** Subagentes especializados definidos *(peso 1)*
- ✅ **G7** Skills de terceros fijadas por hash (lockfile) *(peso 1)*
- ❌ **G8** Revisión humana obligatoria (CODEOWNERS o regla de aprobación) *(peso 2)*

### 9. Requisitos del curso o cliente — 25.0 % (N1 Inicial)
- ❌ **K1** Índice de anuncios del curso *(peso 3)*
- ❌ **K2** Resumen por cada anuncio registrado *(peso 3)*
- ✅ **K3** Sin requisitos pendientes sin plan (❌ / ❓) en docs/requisitos.md *(peso 3)*
- ❌ **K4** Sin herramientas no permitidas por el curso (⛔ en docs/anuncios/herramientas.md) *(peso 3)*

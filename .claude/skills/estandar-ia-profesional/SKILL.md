---
name: estandar-ia-profesional
description: Lleva un repositorio de IA/ML a nivel profesional con un modelo de madurez de 8 dimensiones (fundamentos, calidad, seguridad y cadena de suministro, CI/CD y releases, documentación, proceso, IA/ML responsable y gobernanza de agentes). Audita con puntaje, prioriza brechas y aplica mejoras sin destruir lo existente. Úsala para auditar o elevar la madurez de un repo, ordenar su CI/CD en GitHub y dejar solo main y develop, preparar un proyecto para producción o revisión, endurecer seguridad y CI, agregar evals, model/data cards, política de uso de IA o reglas para agentes. Complementa (no reemplaza) a jan-project-standard.
license: MIT
compatibility: Skill solo de instrucciones y plantillas (no ejecuta scripts propios). Para aplicar mejoras en el proyecto se recomienda uv, git, gh y pre-commit.
metadata:
  uso: desarrollo
  autor: Daniel Silva y Katherine Medina
  version: "1.0"
---

# Estándar profesional para proyectos de IA

> **Idea central:** un proyecto profesional no se reconoce por los archivos que tiene, sino por
> lo que **impide**: secretos filtrados, regresiones del modelo, dependencias vulnerables,
> decisiones sin registro, agentes sin control y cambios sin revisión humana.
> Esta skill **mide** esos controles, **prioriza** lo que falta y lo **aplica** paso a paso.

`jan-project-standard` deja la base: uv, Ruff, Makefile, CONSTITUTION.md y GitHub. Esta skill parte de
ahí y la lleva a nivel de producción. Si el repo no tiene la base, primero se aplica Jan (o la
dimensión 1 de aquí) y luego se sigue con esta skill.

> **Skill limpia, sin intermediarios.** Esta skill **no trae scripts ni delega su ejecución**: son
> instrucciones, una rúbrica y plantillas. El agente audita y aplica con sus propias herramientas
> (leer, buscar, editar), a la vista del usuario. Lo que deba automatizarse (la auditoría en CI,
> el filtro de commits) se instala **como código del proyecto**, con sus pruebas, y nunca depende
> de la carpeta de la skill.

---

## Qué agrega frente a jan-project-standard

| Capacidad | Jan | Esta skill |
|---|---|---|
| Scaffolding Python (uv, Ruff, src-layout, Makefile) | ✅ | Lo verifica (dimensión 1) |
| Ejecución | Delega en scripts propios (`new_project.py`, `setup_git_identity.py`) | **Sin scripts en la skill**: el agente trabaja con sus herramientas y deja visible cada cambio |
| Auditoría | FALTA / DIFIERE / OK | **Rúbrica de 66 verificaciones con peso, puntaje 0-100, nivel N1-N4 y evidencia por ítem** |
| Puerta de madurez en CI | — | ✅ Como código del proyecto (`make madurez MINIMO=80`), no de la skill |
| Tipos y cobertura obligatoria | `ty` opcional | Tipos en `make check`, umbral de cobertura y pirámide de pruebas |
| Seguridad y cadena de suministro | Dependabot | + gitleaks, pip-audit, CodeQL, SBOM, CODEOWNERS, `permissions:` mínimos, SECURITY.md |
| Releases y GitHub | — | SemVer, CHANGELOG automático, entornos staging/producción, despliegue por imagen y **solo `main` y `develop` como ramas permanentes** (limpieza automática) |
| Operación | — | Runbook, healthcheck, Docker multi-stage |
| IA/ML | — | Model card, data card, golden set, **puerta de evals en CI**, prompts como código, observabilidad, privacidad (Ley 1581), sesgo y registro de modelos |
| Gobernanza de agentes | AGENTS.md | + política de uso de IA, `permissions.deny`, atribución controlada, filtro de trailers, skills con hash y revisión humana obligatoria |
| Proceso | Plantillas PR/issue | + specs, Definition of Done, matriz requisito ↔ evidencia |

---

## Reglas de convivencia (obligatorias)

1. **Medir antes de tocar.** Siempre empezar con la auditoría (rúbrica o `make madurez`) y mostrar el informe.
2. **No destruir.** Nada existente se borra ni se sobrescribe; se completa y se fusiona.
   Si un archivo del usuario difiere de la plantilla, gana el del usuario y se le **añade** lo que falte.
3. **Un cambio por brecha.** Cada brecha se resuelve en su propia rama y PR con Conventional Commits,
   de modo que se pueda revisar y revertir por separado.
4. **El humano aprueba y publica.** El agente prepara ramas y commits, pero **no hace push, no
   fusiona PRs y no cambia la configuración de GitHub** (protección de ramas, secretos) sin
   aprobación explícita en el chat.
5. **Sin secretos ni datos.** Nunca leer `.env` ni `data/`, ni pegar llaves en archivos o mensajes.
6. **La constitución manda.** Toda decisión que cambie arquitectura, stack o proceso se registra en
   `CONSTITUTION.md` (historial) y, si es relevante, en un ADR, **en el mismo PR**.

---

## Flujo de trabajo

### Requisitos externos (opcional)

Si el proyecto tiene requisitos de un cliente o de un curso, la auditoría los incluye **sin que esta
skill tenga que saber de dónde vienen**:

- Si existe `docs/requisitos.md`, sus filas ❌ o ❓ se agregan a las brechas, con prioridad según su fecha límite.
- Si existe un catálogo de herramientas no permitidas (por ejemplo `docs/anuncios/herramientas.md`),
  cualquier herramienta ⛔ presente en el proyecto se reporta **antes** que las demás brechas.

Cómo se llenan esos archivos es responsabilidad de otra skill o del equipo: por ejemplo, una skill
que lea los anuncios de un curso o las actas de un cliente.

### Paso 1 · Auditar (solo lectura)

1. Si el proyecto ya tiene su propio auditor (`make madurez`), se ejecuta ese y se usa su informe.
2. Si no, el agente aplica la rúbrica de [`references/rubrica.md`](references/rubrica.md):
   - recorre las 66 verificaciones con sus herramientas de lectura y búsqueda;
   - anota la evidencia de cada una (ruta y línea, o el motivo del ❌);
   - calcula el puntaje con los pesos.

   No se ejecuta código del proyecto ni se usa la red.
3. Entrega el informe con el formato de la rúbrica:
   - **puntaje global** y **nivel** de cada dimensión;
   - **brechas ordenadas por peso**, cada una con cómo cerrarla y su guía en `references/`;
   - evidencia ✅ / ❌ por verificación.

Los niveles son: **N1 Inicial** (<40 %), **N2 Gestionado** (40-69 %), **N3 Definido** (70-89 %) y
**N4 Optimizado** (≥90 %). El significado de cada nivel está en [`references/niveles-madurez.md`](references/niveles-madurez.md).

### Paso 2 · Proponer un plan por oleadas

Se presenta al usuario una tabla con las brechas agrupadas en tres oleadas:

| Oleada | Criterio | Ejemplos |
|---|---|---|
| **1 · Riesgo** | Peso 3 en seguridad, gobernanza o calidad | gitleaks, pip-audit, política de IA, cobertura, tipos |
| **2 · Confiabilidad** | Puertas de CI y operación | evals en CI, CODEOWNERS, runbook, releases |
| **3 · Excelencia** | Peso 1-2 restante | SBOM, data card, labels, sesgo |

**No se aplica nada hasta que el usuario elige la oleada o las brechas.**

### Paso 3 · Aplicar brecha por brecha

Por cada brecha aprobada:

1. Crear la rama `chore/<id>-<tema>` (por ejemplo `chore/s3-gitleaks`), o `feat/` si agrega funcionalidad.
2. Leer la plantilla de `assets/plantillas/` si existe, adaptarla al proyecto (nombres, rutas, comandos) y fusionarla con lo existente usando las herramientas de edición.
3. Agregar o ajustar el target del `Makefile` y el paso de CI, para mantener la paridad local ↔ CI.
4. Correr `make check` (y `pre-commit run --all-files`).
5. Volver a verificar esa fila de la rúbrica (o `make madurez`) y confirmar que pasó a ✅.
6. Hacer commit con Conventional Commits, por ejemplo `ci(seguridad): agregar escaneo de secretos con gitleaks`.
7. Entregar al usuario el resumen y los comandos para que **él** haga push y abra el PR.

### Paso 4 · Fijar el nivel alcanzado

Cuando el proyecto llega al nivel objetivo:

- Se versiona el informe en `docs/madurez.md`.
- **Opcional:** se instala un auditor **como código del proyecto**, por ejemplo `scripts/auditar_madurez.py` con sus pruebas y el target `make madurez`. Lo escribe el agente en un PR propio, a partir de la rúbrica. Con eso, la CI impide retroceder:
  ```yaml
  - run: make madurez MINIMO=80
  ```
- Se registra en el historial de `CONSTITUTION.md`, con fecha, nivel y puntaje.

---

## Las 8 dimensiones (resumen)

| # | Dimensión | Pregunta que responde | Guía |
|---|---|---|---|
| 1 | Fundamentos | ¿Cualquiera lo instala y corre igual? | [`fundamentos.md`](references/fundamentos.md) |
| 2 | Calidad y pruebas | ¿Un cambio roto se detecta antes del merge? | [`calidad.md`](references/calidad.md) |
| 3 | Seguridad y cadena de suministro | ¿Qué impide filtrar secretos o heredar una CVE? | [`seguridad.md`](references/seguridad.md) |
| 4 | CI/CD y releases | ¿Cada versión es reproducible, trazable y desplegable? | [`entrega.md`](references/entrega.md), [`github-cicd.md`](references/github-cicd.md) |
| 5 | Documentación y decisiones | ¿Se entiende el porqué y cómo operarlo a las 3 a.m.? | [`documentacion.md`](references/documentacion.md) |
| 6 | Proceso y trazabilidad | ¿Cada línea de código viene de una historia aprobada y el repo queda limpio? | [`proceso.md`](references/proceso.md), [`github-cicd.md`](references/github-cicd.md) |
| 7 | IA/ML responsable | ¿Sabemos cuándo el modelo empeora y a quién afecta? | [`ia-ml.md`](references/ia-ml.md) |
| 8 | Gobernanza de agentes | ¿Qué puede y qué no puede hacer un agente en este repo? | [`gobernanza-ia.md`](references/gobernanza-ia.md) |

La rúbrica detallada (qué archivo mirar y qué cuenta como ✅) está en [`rubrica.md`](references/rubrica.md). Las guías se cargan **solo cuando se trabaja esa dimensión** (divulgación progresiva).

---

## Plantillas incluidas (`assets/plantillas/`)

| Plantilla | Cierra | Destino |
|---|---|---|
| `SECURITY.md` | S1 | raíz |
| `CODEOWNERS` | S7, G8 | `.github/` |
| `workflows/seguridad.yml` | S5, S6, S8, S9 | `.github/workflows/` |
| `workflows/evals.yml` | M5 | `.github/workflows/` |
| `workflows/release.yml` + `cliff.toml` | R3, R4 | `.github/workflows/`, raíz |
| `workflows/ramas.yml` | P9 | `.github/workflows/` |
| `pre-commit-extra.yaml` | S3, C2, G4 | fusionar en `.pre-commit-config.yaml` (el filtro G4 se escribe en `scripts/` según `gobernanza-ia.md`) |
| `data-card.md` | M2 | `docs/` |
| `runbook.md` | D6 | `docs/` |
| `adr.md` | D3 | `docs/decisiones/plantilla.md` |
| `politica-uso-ia.md` | G1 | `docs/` |
| `claude-settings.json` | G2, G3 | fusionar en `.claude/settings.json` |
| `definition-of-done.md` | P5 | sección de `CONTRIBUTING.md` y checklist del PR |

---

## Checklist de salida (Definition of Done de la skill)

- [ ] Informe de madurez versionado en `docs/madurez.md`, con fecha.
- [ ] Ninguna dimensión en N1 y el global en N3 o más.
- [ ] `make check` y la CI en verde, con la puerta `--minimo` activa.
- [ ] Cada brecha cerrada tiene su PR, aprobado por un humano.
- [ ] `CONSTITUTION.md` registra el nivel alcanzado y las decisiones tomadas.
- [ ] Sin secretos, datos personales ni artefactos pesados en el historial (`gitleaks detect`).

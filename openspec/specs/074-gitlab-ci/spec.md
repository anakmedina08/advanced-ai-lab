# SPEC-074 · Espejo en GitLab y pipeline de lint + test (Módulo 4, Parte 1)

> Curso: Gestión de Proyectos en IA y CD (551475) · Story points: **3** · Responsable: Daniel
> Silva · Anuncio [008](../../../docs/anuncios/551475-anuncio-008.md) · Historia M4-01 · Plan en
> [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md). Decisión:
> [ADR-033](../../../docs/decisiones/ADR-033-espejo-gitlab.md).

## Problema
La sustentación del Módulo 4 (sábado 28/11) se demuestra en GitLab: pipeline, Container Registry
y deploy. El repositorio vive en GitHub (PR, revisión cruzada, Kanban) y GitLab gratuito no trae
código de GitHub por sí solo (el *pull mirror* y «CI/CD for external repositories» son Premium).

## Historia
**Como** equipo, **queremos** que cada push a `develop` o `main` en GitHub llegue a GitLab y corra
allí lint, pruebas y detección de secretos, **para** demostrar el pipeline del M4 sin cambiar dónde
trabajamos.

## Requisitos
- **R074.1** Un workflow de GitHub DEBE copiar `develop` y `main` a `gitlab.com/daalrasi/advanced-ai-lab`
  en cada push, con una deploy key de escritura limitada a ese proyecto (secret `GITLAB_ESPEJO_KEY`).
- **R074.2** El workflow DEBE verificar la huella oficial ED25519 de gitlab.com antes de conectarse.
- **R074.3** Sin el secret, el workflow DEBE avisar y terminar sin error (los forks y las PR no fallan).
- **R074.4** `.gitlab-ci.yml` DEBE correr `ruff check`, `ruff format --check` y `pytest` con cobertura
  ≥ 85 % (igual que GitHub Actions), con uv y Python 3.13, y publicar JUnit y cobertura.
- **R074.5** El pipeline DEBE incluir la plantilla de detección de secretos de GitLab.
- **R074.6** Ningún archivo de CI DEBE contener llaves ni tokens.

## Criterios de aceptación
- **AC1** · **Dado** un push a `develop` en GitHub, **cuando** termina el workflow, **entonces** el
  mismo commit está en GitLab y su pipeline (lint + test + secret detection) queda en verde.
- **AC2** · **Dado** que falta el secret, **cuando** corre el workflow, **entonces** avisa y no falla.

## Fuera de alcance
Build, Container Registry y deploy al Droplet: SPEC-075 (Parte 2).

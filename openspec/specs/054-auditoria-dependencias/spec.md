# SPEC-054 · Auditoría de dependencias, CodeQL y SBOM

> Curso: Gestión M4 (CI/CD) · Técnicas M3 (seguridad) · Story points: **5** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
Dependabot actualiza versiones, pero nadie verificaba si las dependencias instaladas tienen vulnerabilidades conocidas. Una corrida de `pip-audit` sobre `uv.lock` encontró 7 avisos en 3 paquetes (chromadb, opentelemetry-api y soupsieve). Tampoco había análisis estático de seguridad ni inventario de dependencias (SBOM).

## Historia
**Como** equipo, **quiero** que la CI revise las vulnerabilidades de las dependencias y el código, **para** no desplegar algo con fallas conocidas y poder responder qué versión de cada librería usamos.

## Requisitos
- **R054.1** El job `dependencias` DEBE correr `pip-audit` sobre lo exportado de `uv.lock` y fallar ante cualquier vulnerabilidad no aceptada.
- **R054.2** Las vulnerabilidades aceptadas DEBEN listarse en `seguridad/vulnerabilidades-aceptadas.txt` con motivo y fecha de revisión.
- **R054.3** Las vulnerabilidades con versión corregida DEBEN resolverse actualizando el lock.
- **R054.4** El job `codeql` DEBE analizar Python y TypeScript.
- **R054.5** Los pushes a `main` DEBEN publicar un SBOM CycloneDX como artefacto.
- **R054.6** `make auditar-deps` DEBE reproducir la auditoría localmente.

## Criterios de aceptación
- **AC1** · **Dado** una dependencia con una CVE corregida, **cuando** corre la CI, **entonces** el job falla hasta actualizarla.
- **AC2** · **Dado** el lock actual, **cuando** se ejecuta `make auditar-deps`, **entonces** no hay vulnerabilidades sin aceptar.
- **AC3** · **Dado** un push a `main`, **cuando** termina el workflow, **entonces** hay un artefacto `sbom`.

## Fuera de alcance
Retirar Chroma (historia aparte: el agente lo usa para la comparación de recuperación, ADR-016/018).

## Métricas de éxito
0 vulnerabilidades sin aceptar; CodeQL sin alertas altas; SBOM en cada release.

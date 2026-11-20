# Política de uso de IA en el proyecto

> Asistente Seguros Bolívar · Daniel Silva y Katherine Medina · vigente desde el 17/11/2026 (SPEC-056).
> Si cambia la configuración de los agentes, esta política se actualiza en el mismo PR.

## 1. Dos usos distintos de la IA

| Uso | Qué es | Dónde está |
|---|---|---|
| **IA en el producto** | El asistente responde con un LLM (Claude Haiku, DeepSeek u Ollama), RAG, agente con memoria y YOLO para fotos | `src/sb_asistente/`, [Model Card](model-card.md) |
| **IA para desarrollar** | Agentes de código que ayudan a escribir, revisar y documentar | `.claude/`, `opencode.json`, `AGENTS.md` |

Esta política trata sobre todo el segundo uso. El primero se rige por la Model Card, el alcance de
datos (`docs/alcance.md`) y la Ley 1581 de 2012.

## 2. Herramientas autorizadas para desarrollar

| Herramienta | Para qué |
|---|---|
| Claude Code y OpenCode | Explorar, escribir y probar código; redactar specs y documentación |
| Subagentes (`.claude/agents/`): `arquitecto`, `documentador`, `explorador`, `guardian-datos`, `ml-recomendador`, `probador`, `revisor` | Tareas acotadas con herramientas mínimas |
| Skills (`.claude/skills/`) | Procedimientos repetibles: estándar del curso (`jan-project-standard`), estándar profesional, seguimiento de anuncios, operación |
| GGA en pre-commit | Revisión con IA del staging contra `AGENTS.md` |
| Engram | Memoria de decisiones entre sesiones (espejo en `docs/decisiones/`) |

## 3. Qué puede y qué no puede hacer un agente

| Puede | Requiere aprobación humana en el momento | Prohibido |
|---|---|---|
| Leer el código, buscar, proponer cambios | `git push` | Leer `.env`, `.env.*` o `data/` (`permissions.deny`) |
| Crear ramas y preparar cambios locales | `gh pr create` y `gh pr merge` | Reescribir el historial (`git filter-repo`) |
| Correr pruebas, linters, `make madurez` | Publicar, desplegar o gastar saldo de API en evals | Enviar datos personales a servicios externos |
| Redactar specs, ADR y documentación | Instalar una skill de terceros (se audita antes) | Cambiar la configuración de GitHub (protección de ramas, secretos) |

La configuración que hace cumplir esta tabla está en `.claude/settings.json` (`deny` y `ask`).

## 4. Revisión y responsabilidad

- Todo cambio, escrito con o sin IA, entra por un PR con la plantilla del curso y la aprobación del otro integrante (CODEOWNERS).
- **Quien hace el commit y quien aprueba responden por el cambio como si lo hubieran escrito.** En la sustentación, cada integrante debe poder explicar su parte del código (anuncio 007 de Gestión).
- Las skills de terceros se revisan antes de instalarlas y quedan fijadas por hash en `skills-lock.json`.

## 5. Atribución

- Los commits y PRs van **a nombre de las personas** y sin coautor de IA ([ADR-023](decisiones/ADR-023-atribucion-ia.md)): `attribution` vacío y el hook `limpiar-trailers-ia`.
- El uso de IA **no se oculta**: se declara en este documento, en el README (sección «Uso de IA») y en cada entrega académica, indicando las herramientas y en qué partes se usaron.

## 6. Datos y privacidad

- Solo datos públicos del sitio de Seguros Bolívar, respetando robots.txt.
- Datos sintéticos para el recomendador.
- Nada de datos personales en prompts, trazas de LangSmith, conjuntos de evaluación ni en el repo.
- Las fotos difuminan a las personas antes de salir del equipo.

## 7. Revisión de esta política

Se revisa al inicio de cada módulo, cuando cambia la configuración de los agentes o ante un incidente.

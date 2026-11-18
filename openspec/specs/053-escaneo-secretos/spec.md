# SPEC-053 · Escaneo de secretos con gitleaks en cada commit y en la CI

> Curso: Gestión M4 (CI/CD y credenciales) · Técnicas M3 (seguridad) · Story points: **3** · Responsable: Daniel ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
La única barrera contra secretos era `detect-private-key` y un hook propio para `.env`. Una llave de API pegada en un archivo de código o en un YAML no se detectaba. El M4 de Gestión trata CI/CD y credenciales.

## Historia
**Como** equipo, **quiero** que gitleaks revise cada commit y cada PR, **para** que ninguna llave llegue al repositorio público.

## Requisitos
- **R053.1** El hook `gitleaks` DEBE correr en pre-commit sobre lo que está en staging.
- **R053.2** El workflow `seguridad.yml` DEBE correr gitleaks sobre el historial completo en cada PR, push y cada semana.
- **R053.3** `make secretos` DEBE revisar el árbol completo localmente.
- **R053.4** El historial actual DEBE quedar verificado sin hallazgos antes de activar la puerta.

## Criterios de aceptación
- **AC1** · **Dado** un archivo con una llave de API, **cuando** se intenta el commit, **entonces** gitleaks lo bloquea.
- **AC2** · **Dado** un PR, **cuando** corre la CI, **entonces** el job «Escaneo de secretos» aparece y pasa en verde.

## Fuera de alcance
Rotación de llaves (no hay hallazgos que rotar).

## Métricas de éxito
0 hallazgos en el historial (`gitleaks git --log-opts=--all`) y en el árbol.

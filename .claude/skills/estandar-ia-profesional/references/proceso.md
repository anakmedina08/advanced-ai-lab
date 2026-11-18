# 6 · Proceso y trazabilidad

**Cadena de trazabilidad:** historia (issue) → spec (`openspec/specs/NNN-*`) → rama → commits
convencionales → PR con plantilla → CI verde → aprobación humana → merge → release.

## P3 · Specs
Cada historia relevante tiene una carpeta de spec con tres archivos:
- `spec.md`: qué y por qué, con criterios de aceptación verificables.
- `plan.md`: cómo.
- `tasks.md`: checklist.

El PR enlaza la spec y el issue.

## P5 · Definition of Ready / Done
Ver `assets/plantillas/definition-of-done.md`. La DoD se copia como checklist en la plantilla de PR,
para que se marque en cada PR y no quede solo en un documento.

## P6 · Ramas
**Gitflow ligero:**
- `main`: producción, solo releases.
- `develop`: integración.
- `feature/*`, `fix/*`, `chore/*`: trabajo diario.
- `hotfix/*`: desde `main`.

Los PRs apilados se permiten si la CI corre también sobre `feature/**`.

Tamaño de PR: idealmente **menos de 400 líneas** cambiadas. Si es más grande, se parte.

## P8 · Matriz requisito ↔ evidencia
`docs/requisitos.md` contiene una tabla con requisito, estado (✅/🟡/❌) y evidencia (ruta, PR o comando).
Es la herramienta de una sustentación o auditoría.

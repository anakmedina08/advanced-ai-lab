# ADR-026 · Solo `main` y `develop` como ramas permanentes

- **Fecha:** 2026-11-18
- **What:** el repositorio solo conserva `main` (producción) y `develop` (integración). Cada `feature/NNN-…`
  vive lo que dura su PR. `.github/workflows/ramas.yml` borra la rama de un PR fusionado y publica cada semana
  un reporte de las ramas que sobran. `CONTRIBUTING.md` documenta el flujo Gitflow con PRs apilados.
- **Why:** recomendación del profesor para dejar el repositorio limpio y legible. Con más de 40 PRs por curso,
  las ramas fusionadas que se quedaban vivas tapaban las que están en revisión.
- **Decisiones de diseño:**
  - **No se borra nada con PR abierto,** ni si la rama es la *cabeza* de un PR, ni si es la *base* de un PR
    apilado. Borrar la base cerraría el PR de arriba.
  - **Permisos mínimos:** `contents: read` por defecto; solo el job que borra pide `contents: write`.
  - **Nunca se tocan** `main`, `develop` ni ramas que vienen de un fork.
  - El reporte semanal **no borra**: lista las ramas sobrantes para que una persona decida.
- **Where:** `.github/workflows/ramas.yml`, `CONTRIBUTING.md`, `CONSTITUTION.md` (historial), SPEC-057.
- **Learned:** la opción del repositorio *Automatically delete head branches* hace lo mismo, pero no queda
  versionada ni revisable. El workflow deja la regla en el código y protege los PRs apilados.

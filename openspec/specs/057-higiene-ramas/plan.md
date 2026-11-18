# Plan · SPEC-057 · Solo main y develop como ramas permanentes

## Diseño
Workflow con `GITHUB_TOKEN` (`contents: write`) y `gh api` para borrar la referencia de la rama.

## Decisiones
- Borrar solo al fusionar (no al cerrar): un PR cerrado sin fusionar puede reabrirse.
- Doble red: el ajuste del repo y el workflow; si uno falla, el otro limpia.
- Puerta de madurez de la CI: de 65 a 80.

## Contrato
Workflow `.github/workflows/ramas.yml`: eventos `pull_request.closed`, `schedule` (lunes) y `workflow_dispatch`.

## Riesgos
- PRs apilados: si la rama base se borra, GitHub reapunta los PRs hijos a la base anterior. Conviene fusionar en orden.

## Alternativas descartadas
- Borrado manual periódico: depende de la memoria de las personas.

## Estrategia de pruebas
Validación del YAML y prueba en el repo con un PR de prueba fusionado (la rama desaparece) y uno cerrado sin fusionar (la rama queda).

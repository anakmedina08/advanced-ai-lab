# Plan · SPEC-031 · CI del frontend: tipos, pruebas y build

## Diseño
Job nuevo en `.github/workflows/ci.yml` con `working-directory: frontend` y caché de npm.

## Decisiones
- `npm ci` con lockfile: instalación reproducible.

## Contrato
Job «Frontend».

## Riesgos
- Minutos de CI: se usa caché de npm.

## Alternativas descartadas
- Un workflow aparte: se prefiere un solo CI visible en la PR.

## Estrategia de pruebas
La propia PR muestra el job. Pruebas AAA sin red ni API de pago.

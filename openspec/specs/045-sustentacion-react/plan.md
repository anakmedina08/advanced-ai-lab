# Plan · SPEC-045 · Entregables por curso en React

## Diseño
Endpoint sobre `controller/proyecto`; página con pestañas y filtros.

## Decisiones
- La fuente única sigue siendo `docs/requisitos.md`.

## Contrato
`ProyectoOut`.

## Riesgos
- Cifras costosas: se calculan al pedirlas (milisegundos).

## Alternativas descartadas
- Copiar la tabla al frontend: se desactualiza.

## Estrategia de pruebas
Pytest del endpoint y Vitest del filtro. Pruebas AAA sin red ni API de pago.

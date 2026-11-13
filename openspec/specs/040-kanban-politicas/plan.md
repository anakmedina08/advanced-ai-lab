# Plan · SPEC-040 · Políticas del tablero Kanban: WIP, historias y métricas

## Diseño
GitHub CLI para leer issues y PR; cálculo con fechas de creación, inicio y cierre.

## Decisiones
- Cycle time desde la primera rama/PR hasta el cierre del issue.

## Contrato
—

## Riesgos
- Datos de un solo día de trabajo intenso: se explica el contexto.

## Alternativas descartadas
- Insights de GitHub: no calcula cycle time por historia.

## Estrategia de pruebas
Pruebas de las funciones de métricas con fechas fijas. Pruebas AAA sin red ni API de pago.

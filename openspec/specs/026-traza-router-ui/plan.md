# Plan · SPEC-026 · Panel de la decisión del router, tools y fuentes

## Diseño
Componente `PanelDecision` que recibe `DecisionOut` y `tiempos_tools`.

## Decisiones
- Desplegable con `<details>` nativo: accesible sin JavaScript extra.

## Contrato
Usa `AgenteOut.decision`, `pasos`, `tiempos_tools`.

## Riesgos
- Mucha información: se resume en la insignia y el detalle va plegado.

## Alternativas descartadas
- Mostrar todo el JSON: ilegible.

## Estrategia de pruebas
Pruebas del componente con Testing Library. Pruebas AAA sin red ni API de pago.

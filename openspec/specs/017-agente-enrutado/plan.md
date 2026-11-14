# Plan · SPEC-017 · Agente con router: tools por ruta y decisión visible

## Diseño
`ContextoTurno` en `create_agent(context_schema=…)`; middleware `filtrar_tools` con `wrap_model_call`.

## Decisiones
- El router decide y el LLM ejecuta: control determinista con flexibilidad en la redacción.

## Contrato
`POST /agente/mensajes {mensaje, conversacion_id, usuario_id?} → AgenteOut{salida, decision, pasos, fuentes_descartadas}`

## Riesgos
- Si el router se equivoca, la ruta `cautela` deja todas las tools.

## Alternativas descartadas
- Un StateGraph con nodos por ruta: más código para el mismo comportamiento.

## Estrategia de pruebas
`tests/test_agente.py` (modelo guionado) y `tests/test_api_agente.py`. Pruebas AAA sin red ni API de pago.

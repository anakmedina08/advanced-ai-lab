# Plan · SPEC-020 · Sesiones: historial, checkpoints (time travel) y borrado por REST

## Diseño
Métodos `historial`, `checkpoints`, `olvidar` y `perfil` del controlador; vistas finas.

## Decisiones
- SQLite en `data/memoria/`: persistencia real sin servidor.

## Contrato
`ConversacionOut`, `CheckpointOut`, `PerfilOut`

## Riesgos
- Exponer historiales sin autenticación: el id es aleatorio y el proyecto es local/académico.

## Alternativas descartadas
- Solo JSON-RPC: el frontend REST tendría que hablar dos protocolos.

## Estrategia de pruebas
`tests/test_api_agente.py`. Pruebas AAA sin red ni API de pago.

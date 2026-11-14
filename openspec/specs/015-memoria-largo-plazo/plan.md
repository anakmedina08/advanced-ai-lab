# Plan · SPEC-015 · Memoria de largo plazo con Store y namespace por usuario

## Diseño
`model/memoria.py` (extracción y `PerfilStore`), middleware `dynamic_prompt` en `model/agente.py`, `context_schema` con `usuario_id`.

## Decisiones
- Extracción por reglas: predecible y sin costo; solo hechos que el usuario dice explícitamente.
- El Store vive en `data/memoria/` (no versionado).

## Contrato
`ContextoTurno{usuario_id, ruta, tools}`; namespace `("usuarios", usuario_id, "perfil")`

## Riesgos
- Guardar datos personales: solo nombre y empresa dichos por el usuario, con borrado disponible.

## Alternativas descartadas
- `InMemoryStore`: no sobrevive al reinicio (no se acepta como persistencia).

## Estrategia de pruebas
`tests/test_memoria.py` con `InMemoryStore` y `SqliteStore` en `tmp_path`. Pruebas AAA sin red ni API de pago.

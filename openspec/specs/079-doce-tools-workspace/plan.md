# Plan · SPEC-079

1. **Fábrica de tools extra.** Nuevo módulo `model/herramientas.py` con
   `crear_tools_extra(...)` que devuelve las 12 tools con sus dependencias inyectadas (recuperador,
   catálogo, perfil store, acceso, canales, visión, OCR). Sin red en pruebas.
2. **Tools estáticas** (`listar_productos`, `citar_fuente`, `explicar_termino`, `guia_tramite`,
   `checklist_siniestro`) con datos derivados del corpus/catálogo, con URL de origen.
3. **Tools de estado** (`guardar_perfil`, `ver_perfil`, `olvidar_datos`, `estado_codigo_acceso`)
   sobre `PerfilStore` y `controller.acceso.estado`.
4. **Tools de medios** (`analizar_foto`, `leer_documento`) envolviendo visión/OCR, con dobles.
5. **HITL** (`escalar_a_humano`) envolviendo `canales_para` con el servicio `pqr`.
6. **Registro.** Extender `controller/agente.py` para concatenar las tools extra a las 8 actuales
   y llegar a 20.
7. **Workspace.** `workspace/SOUL.md`, `workspace/USER.md`, `workspace/MEMORY.md`,
   `workspace/AGENTS.md` y `workspace/bitacora.md` (bitácora diaria) versionados y coherentes con
   `AGENTS.md`/`CONSTITUTION.md`.
8. **Pruebas.** `tests/test_herramientas.py` (AAA, sin red, `FakeListChatModel`, stores falsos) y
   `tests/test_workspace.py` (existe y no baja madurez).

## Orden de dependencias
Las tools estáticas (2) no dependen de nada y van primero. Las de estado (3) dependen del `BaseStore`
inyectado. El MCP (SPEC-078) depende de que estas tools existan.

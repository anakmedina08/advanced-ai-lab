# Plan · SPEC-072

1. **Modelo** `model/acceso.py`: `CodigosAcceso` en SQLite (`data/acceso/codigos.sqlite`), solo
   hashes; `crear`, `estado`, `consumir` (un `UPDATE` condicionado), `listar`, `revocar`.
2. **Controlador** `controller/acceso.py`: `exigir` (respeta `ACCESO_CODIGO_OBLIGATORIO`), `estado`,
   `crear`, `listar`, `revocar`.
3. **Vista**: `Metodo.usa_llm` en JSON-RPC, código `-32003`, método `acceso.estado`; dependencia
   `requiere_codigo` en las rutas REST con LLM, `/fotos` solo con `interpretar`/`responder`,
   `GET /acceso/estado`, CORS con `X-Codigo-Acceso`; `sb acceso crear|listar|revocar`.
4. Pruebas `tests/test_acceso.py` y `make check`.
5. Yellowdata (su repositorio): pedir el código al abrir el chat y reenviarlo en el encabezado.

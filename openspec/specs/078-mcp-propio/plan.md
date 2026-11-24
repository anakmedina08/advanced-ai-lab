# Plan · SPEC-078

1. **Dependencia.** `uv add mcp` (o extra opcional `mcp`). Crear `src/sb_asistente/mcp/__init__.py`
   y `server.py` con `crear_mcp(...)` que envuelve las 20 tools como tools MCP.
2. **Montaje.** En `view/api.py`, montar `mcp.streamable_http_app()` en `/mcp` (sin tocar los
   endpoints REST ni el JSON-RPC). En `view/dependencias.py`, inyectar las dependencias reales.
3. **Loopback.** En `deploy/docker-compose.prod.yml`, publicar el servicio `api` solo en
   `127.0.0.1:8000:8000` (junto al `command` existente). Documentar en `docs/openclaw.md`.
4. **Gateway.** Registrar `mcp.servers.sb-asistente` con `openclaw mcp add` (streamable HTTP) y
   verificar `openclaw mcp doctor sb-asistente --probe`.
5. **Pruebas.** `tests/test_mcp.py` (fábrica sin red, `tools/list` con dobles) y que `make check`
   siga en verde.

## Orden de dependencias
Depende de SPEC-079 (las 20 tools) y de SPEC-077 (gateway vivo). El paso 4 es el último y toca el
Droplet; los pasos 1–3 y 5 son locales y no tocan producción.

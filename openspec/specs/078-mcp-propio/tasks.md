# Tareas · SPEC-078

- [x] T078.1 `uv add mcp` y `src/sb_asistente/mcp/server.py` con `crear_mcp(...)` (Daniel Silva)
- [x] T078.2 Montaje `/mcp` en `view/api.py` (streamable HTTP, lifespan) + `app_mcp()`
- [x] T078.3 Publicar `api` en loopback (`127.0.0.1:8000:8000`) en `deploy/docker-compose.prod.yml`
- [x] T078.4 `tests/test_mcp.py` (sin red) y `make check` en verde
- [ ] T078.5 Registrar `mcp.servers.sb-asistente` en el gateway y `openclaw mcp doctor --probe` (Daniel Silva)
- [ ] T078.6 Probar por WhatsApp una consulta que invoque una tool y cite fuente (equipo)

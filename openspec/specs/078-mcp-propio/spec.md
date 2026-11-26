# SPEC-078 · MCP propio que expone las tools al gateway de OpenClaw

> Curso: Técnicas Avanzadas de IA (551462) · Story points: **8** · Responsable: Daniel Silva ·
> Anuncio: [551462 · 007](../../../docs/anuncios/551462-anuncio-007.md) (ítem 3.4, 5 %) · Depende de
> [SPEC-077](../077-openclaw-gateway/spec.md) (gateway) y de las 20 tools de
> [SPEC-079](../079-doce-tools-workspace/spec.md).

## Problema
El ítem 3.4 pide un **skill o MCP propio conectado al gateway**. Hoy OpenClaw responde por WhatsApp
con el agente genérico de DeepSeek: no sabe de Seguros Bolívar ni puede consultar el corpus,
recomendar, leer un documento o escalar. Hace falta un MCP propio que exponga las tools del
asistente a OpenClaw, con trazabilidad (ítem 1.1).

## Decisión de arquitectura
- El servidor MCP usa el SDK `mcp` (FastMCP) de Python, **montado dentro de la API FastAPI** con
  transporte **Streamable HTTP** en `/mcp`. Corre en el contenedor `api` (ya desplegado), reusa el
  paquete `sb_asistente` y no requiere un proceso aparte.
- OpenClaw se conecta como cliente MCP: `mcp.servers.sb-asistente` con
  `url: "http://127.0.0.1:8000/mcp"` y `transport: "streamable-http"`. Para eso el servicio `api`
  se publica **solo en loopback** (`127.0.0.1:8000:8000`), sin exponerlo a internet.
- Las tools quedan como `<server>__<tool>` (p. ej. `sb-asistente__buscar_conocimiento`) y pasan por
  las políticas de tools del gateway.

## Requisitos
- **R078.1** DEBE existir `src/sb_asistente/mcp/server.py` con una fábrica `crear_mcp(...)` que
  exponga las 20 tools (o las que tengan sentido por canal) como tools MCP, con sus dependencias
  inyectadas.
- **R078.2** El MCP DEBE montarse en la API FastAPI (`/mcp`, streamable HTTP) y DEBE responder a
  `initialize` y `tools/list` sin red ni claves.
- **R078.3** La definición DEBE registrarse en la configuración del gateway
  (`mcp.servers.sb-asistente`), validada y verificada con `openclaw mcp doctor sb-asistente --probe`.
- **R078.4** Las tools MCP DEBEN respetar las mismas reglas de privacidad (datos por `usuario_id`,
  nunca texto crudo de documentos) y de fuentes (cita de URL).
- **R078.5** El cambio de `deploy/` (publicar `api` en loopback) NO DEBE romper la pila del M4; se
  documenta en `docs/openclaw.md`.

## Criterios de aceptación
- **AC1** · `curl http://127.0.0.1:8000/mcp` responde el endpoint streamable HTTP y `tools/list`
  devuelve las tools esperadas.
- **AC2** · Desde el Droplet, `openclaw mcp doctor sb-asistente --probe` lista las tools y no da
  errores de conexión.
- **AC3** · Un mensaje por WhatsApp del tipo «¿Qué cubre el SOAT?» invoca
  `sb-asistente__buscar_conocimiento` y la respuesta cita la URL.
- **AC4** · La API sigue **sin** estar expuesta a internet (solo loopback) y la pila del M4 sigue
  verde (`make check` en CI).

## Riesgos
| Riesgo | Mitigación |
|---|---|
| El `api` en producción usa embeddings `fake` | Corregir `EMBEDDINGS_PROVIDER=voyage` antes de la demo (SPEC-069, prioridad 1 del handoff) |
| Publicar `api` en loopback interfiere con Caddy | Es un puerto loopback distinto de 80/443; no cambia la red interna |
| El gateway y la API viven en redes distintas | OpenClaw usa `network_mode: host`; `127.0.0.1:8000` es el loopback del Droplet, alcanzable |
| `uv add mcp` agrega peso a la imagen | SDK ligero; alternativa: extra opcional `mcp` |

## Fuera de alcance
Corrección de embeddings en producción (SPEC-069) y la bitácora de experimentos (ADR-022).

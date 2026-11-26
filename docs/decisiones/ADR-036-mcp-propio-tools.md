# ADR-036 · MCP propio (adaptador delgado en `view/`) y 12 tools adicionales

- **Fecha:** 2026-11-24
- **Categoría:** producto · integración · arquitectura · seguridad
- **What:** el asistente expone sus tools por un **MCP propio** montado en la API (`/mcp`,
  streamable HTTP, solo loopback), y suma **12 tools** (`model/herramientas.py`) para llegar a las
  20 de la rúbrica. El servidor MCP es un **adaptador delgado** (`view/mcp.py`) que envuelve los
  `BaseTool` de LangChain (de `crear_tools`/`crear_tools_extra`) sin duplicar su lógica.
- **Why:**
  - Ítem 3.4 de la rúbrica: un skill o **MCP propio conectado al gateway** de OpenClaw.
  - Ítem 1.1: **20 tools** `@tool` (había 8). Las 12 nuevas envuelven lógica que ya existía
    (visión, OCR, perfil, acceso, catálogo, fuentes, canales) y 4 son contenido propio con fuente.
  - **No duplicar lógica:** la versión previa reescribía los cuerpos de las tools en el MCP y ya
    derivaba (mensajes y formato distintos). El adaptador delega en el `BaseTool` original.
- **Alternativas descartadas:**
  - Reescribir las tools dentro del MCP: duplicación y *drift* (lo que rechazó la revisión GGA).
  - Generar las firmas con `exec`: preserva tipos, pero añade metaprogramación frágil.
  - Exponer las tools de perfil por MCP: el gateway no autentica por usuario; quedan fuera.
- **Where:**
  - `src/sb_asistente/model/herramientas.py` (fábrica `crear_tools_extra` con reloj y perfil
    inyectados; el `usuario_id` de perfil sale de `runtime.context`, nunca del modelo).
  - `src/sb_asistente/view/mcp.py` (`crear_mcp`, `app_mcp`); `controller/agente.py`
    (`tools_mcp`, `recuperador_cached`, `escalar_a_humano`).
  - `deploy/Caddyfile` (bloquea `/mcp` en la URL pública) y `deploy/docker-compose.prod.yml`
    (API solo en loopback).
- **Learned:**
  - `mcp` 2.x renombró `FastMCP` → `MCPServer`; `list_tools`/`call_tool` son asíncronos.
  - Starlette no corre el *lifespan* del sub-app al montarlo: hay que componer
    `router.lifespan_context` a mano en el lifespan de la API.
  - `streamable_http_app` valida el `Host` contra `allowed_hosts` (vacío → 421); se limita al
    loopback. Caddy además bloquea `/mcp` por si se llega por `api.$DOMINIO`.
  - Para inyectar `usuario_id` sin exponerlo al modelo se usa `runtime: ToolRuntime` (de
    `langgraph.prebuilt.tool_node`), que LangChain excluye del schema del modelo.
  - El recuperador se comparte entre el agente y el MCP con `recuperador_cached()` (una sola
    instancia, sin cargarlo dos veces en el arranque).
  - El MCP se monta en el *lifespan* de la API y queda fuera del OpenAPI (la ruta se añade en
    tiempo de ejecución); si no hay corpus (p. ej. en CI) el montaje falla en silencio dentro de un
    `try/except` y la API sigue sirviendo el resto de endpoints.

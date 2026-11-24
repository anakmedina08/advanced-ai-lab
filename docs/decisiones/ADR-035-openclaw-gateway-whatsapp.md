# ADR-035 · WhatsApp por OpenClaw (dispositivo vinculado), y la Cloud API queda como alternativa

- **Fecha:** 2026-11-23
- **Categoría:** producto · integración · infraestructura · seguridad · costos
- **What:** el canal de WhatsApp de la sustentación final del M3 (anuncio 551462-007) pasa a
  **OpenClaw**, que se conecta como **dispositivo vinculado** escaneando un QR (el mecanismo de
  WhatsApp Web, vía Baileys). El gateway corre en un contenedor aparte en el Droplet, atado a
  loopback y con token. El webhook de la Cloud API (ADR-032, SPEC-073) se conserva como alternativa
  documentada, pero **no** es el canal evaluado.
- **Why:**
  - **Lo exige la rúbrica del anuncio 007** (ítems 3.1 Gateway OpenClaw y 3.2 WhatsApp vinculado):
    se pide `openclaw.json`, modelo primario y *fallbacks*, `bind: loopback`, token y allowlist
    E.164. El webhook de Cloud API no cubre esos ítems.
  - **Compatibilidad:** un número registrado en la Cloud API de Meta **no** se puede vincular
    después a OpenClaw. La SIM nueva se registró en WhatsApp Business para poder vincularla; jamás
    se toca el número personal.
  - **Un solo motor de demo:** OpenClaw orquesta el mismo agente (después, vía el MCP propio,
    SPEC-078) y concentra la trazabilidad que pide el bloque 3 de la rúbrica.
- **Alternativas descartadas:**
  - Cloud API como canal evaluado: no cumple 3.1/3.2 y ya estaba hecha (SPEC-073); se deja de
    respaldo, no se borra.
  - Instalación nativa de OpenClaw en el Droplet: el usuario `deploy` no tiene `sudo` y no hay Node
    en el host; compilar desde fuente pide 6 GB de RAM y el Droplet tiene 2 GB.
  - `gateway.bind: loopback` con `ports:` en Docker: no funciona (Docker entrega el tráfico a la IP
    del contenedor y el socket solo escucha el loopback interno); se usa `network_mode: host`.
- **Where:**
  - `deploy/openclaw/docker-compose.openclaw.yml` y `openclaw.env.example`
  - `openspec/specs/077-openclaw-gateway/` (spec, plan, tareas)
  - `docs/openclaw.md` (manual de operación)
  - Configuración y credenciales en el Droplet (`/home/deploy/openclaw`, volumen
    `openclaw_estado`), nunca en el repositorio.
- **Learned:**
  - Con 1 vCPU y 16 plugins, el event loop se degradaba y el socket de WhatsApp daba 408
    («QR refs attempts ended»). Se fijó `plugins.deny` y quedaron solo `deepseek`, `memory-core` y
    `whatsapp`; el login ya no muere.
  - El modelo por defecto de la imagen es `openai/gpt-6-astra`; hay que declarar
    `agents.defaults.model.primary` (hoy `deepseek/deepseek-v4-pro`) y un *fallback*.
  - `gateway.auth.token` no se toma solo de `OPENCLAW_GATEWAY_TOKEN`: se escribe con `config set`
    y pide reinicio.
  - El primer arranque tarda 2–3 min y exige `gateway.mode` antes de levantar (se fija con un
    contenedor de un solo uso).

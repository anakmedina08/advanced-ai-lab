# Plan · SPEC-077

1. **Repositorio (sin tocar el servidor).** `deploy/openclaw/docker-compose.openclaw.yml` con la
   imagen prearmada `ghcr.io/openclaw/openclaw`, volumen de estado, `restart: unless-stopped` y el
   puerto publicado **solo** en `127.0.0.1`. `deploy/openclaw/openclaw.env.example` con los nombres
   de las variables (token, llave de Anthropic, números del allowlist), sin valores.
2. **Servidor: gateway vivo.** En `/home/deploy/openclaw`, `docker compose up -d`, generar el token,
   fijar `gateway.bind=loopback`, modelo primario Claude y *fallback*. Verificar `/healthz` y que
   18789 no responda desde fuera.
3. **Servidor: WhatsApp.** Instalar el plugin `@openclaw/whatsapp`, fijar `dmPolicy=allowlist` y
   `allowFrom`, y vincular por QR **en sesión interactiva** con el celular de la SIM. Confirmar con
   `openclaw channels status`.
4. **Endurecimiento.** `tools.deny`, `fs.workspaceOnly` y sandbox; `openclaw security audit` y
   `openclaw doctor` hasta dejarlos limpios. Guardar la salida del audit como evidencia.
5. **Documentación.** `docs/openclaw.md` (instalación, vinculación, operación y recuperación),
   ADR-035 que declara OpenClaw como canal y deja SPEC-073 como alternativa, y actualización de
   `CONSTITUTION.md` y `docs/requisitos.md` en el mismo commit.
6. **Ensayo.** Prueba desde dos teléfonos: uno dentro del allowlist y otro fuera (AC2 y AC3).

## Orden de dependencias
El paso 3 depende del 2 (el gateway debe existir antes de vincular). El SPEC-078 (MCP con las tools)
depende de que el paso 3 esté verde: primero el canal responde «algo», después responde «lo nuestro».

## Decisiones tomadas
- **Contenedor, no instalación nativa:** el usuario `deploy` no tiene `sudo` y no hay Node en el host.
- **Imagen prearmada, no build:** compilar desde fuente pide 6 GB de RAM y el Droplet tiene 2 GB.
- **Proyecto de Compose aparte:** para que un deploy del curso no recree ni tumbe el gateway.
- **Fallback sin DeepSeek por ahora:** `DEEPSEEK_API_KEY` está vacía; se usa un segundo modelo de
  Anthropic como *fallback* y se cambia a DeepSeek apenas haya llave.

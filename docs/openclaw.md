# OpenClaw · gateway y canal de WhatsApp

> Manual de operación del canal exigido por el [anuncio 551462-007](anuncios/551462-anuncio-007.md).
> Spec: [SPEC-077](../openspec/specs/077-openclaw-gateway/spec.md). Despliegue de la aplicación:
> [`despliegue.md`](despliegue.md).
>
> ⚠️ **Nunca** se pegan el token del gateway ni las llaves de API en el chat, en el repositorio ni en
> un log. Las credenciales de la sesión de WhatsApp viven solo en el volumen del servidor.

## Qué es y por qué

OpenClaw se conecta a WhatsApp como **dispositivo vinculado** (el mismo mecanismo de WhatsApp Web,
vía Baileys): se escanea un QR desde *WhatsApp → Dispositivos vinculados*. **No** es la Cloud API de
Meta, y **un número registrado en la Cloud API ya no se puede vincular a OpenClaw**.

| Pieza | Dónde |
|---|---|
| Gateway | contenedor `openclaw-gateway`, proyecto de Compose `openclaw`, en `/home/deploy/openclaw` |
| Configuración | `~/.openclaw/openclaw.json` **dentro** del contenedor (volumen `openclaw_estado`) |
| Credenciales de WhatsApp | `~/.openclaw/credentials/whatsapp/<cuenta>/creds.json`, en el mismo volumen |
| Puerto | `18789`, publicado **solo** en `127.0.0.1` del Droplet |

## 0 · Antes de empezar

- La SIM nueva, **activa y registrada en WhatsApp Business**, con el celular a la mano.
- Acceso SSH al Droplet como `deploy` (no tiene `sudo`, pero sí Docker).
- La llave de Anthropic.
- Los números de los invitados en E.164 (`+57...`) para el *allowlist*.

## 1 · Subir la configuración al servidor

El servidor **solo acepta la llave privada `~/.ssh/gitlab_deploy`**: sin `-i` (o sin el bloque
`Host` en `~/.ssh/config`) responde `Permission denied (publickey)`. El bloque ya está configurado,
así que `droplet` y la IP funcionan como alias:

```sshconfig
# ~/.ssh/config
Host 178.128.11.124 droplet
  HostName 178.128.11.124
  User deploy
  IdentityFile ~/.ssh/gitlab_deploy
  IdentitiesOnly yes
```

Desde el Mac, en la raíz del repositorio:

```bash
rsync -av deploy/openclaw/ droplet:~/openclaw/

# sin el bloque en ~/.ssh/config, la forma explícita equivalente:
rsync -av -e 'ssh -i ~/.ssh/gitlab_deploy' deploy/openclaw/ deploy@178.128.11.124:~/openclaw/
```

En el servidor, crear el archivo de variables (se queda ahí, nunca vuelve al repositorio):

```bash
ssh deploy@178.128.11.124
cd ~/openclaw
cp openclaw.env.example openclaw.env
chmod 600 openclaw.env
openssl rand -hex 32          # token del gateway → pegarlo en OPENCLAW_GATEWAY_TOKEN
nano openclaw.env             # token + ANTHROPIC_API_KEY
```

## 2 · Levantar el gateway

```bash
cd ~/openclaw
docker compose -f docker-compose.openclaw.yml up -d
docker compose -f docker-compose.openclaw.yml ps
```

Atajo para el resto del manual:

```bash
alias oc='docker compose -f ~/openclaw/docker-compose.openclaw.yml exec gateway openclaw'
```

El **primer arranque tarda ~2–3 min** en este Droplet (registra 78 plugins y arranca diagnósticos).
No está colgado: `docker logs -f openclaw-gateway` lo va contando. Cuando termina aparece
`[gateway] ready` y entonces:

```bash
curl -fsS http://127.0.0.1:18789/healthz     # {"ok":true,"status":"live"}
```

> **Si el gateway dice `Gateway start blocked: existing config is missing gateway.mode`** (fue el
> caso del primer arranque), es un huevo y gallina: `config set` exige un gateway escuchando y el
> gateway no arranca sin la clave. Se resuelve con un contenedor de un solo uso sobre el mismo
> volumen:
>
> ```bash
> docker compose -f docker-compose.openclaw.yml stop gateway
> docker compose -f docker-compose.openclaw.yml run --rm --no-deps \
>   --entrypoint openclaw gateway config set gateway.mode local
> docker compose -f docker-compose.openclaw.yml up -d
> ```
>
> Si en cambio sale con código **78**, es el esquema estricto: una clave desconocida. Diagnóstico:
> `oc doctor` y, si hace falta, `oc doctor --fix`.

## 3 · Bind en loopback, token y modelo

```bash
oc config set gateway.mode local
oc config set gateway.bind loopback          # R077.2 · las imágenes traen bind expuesto por defecto
oc config get gateway.bind

# Modelo primario y fallback (R077.4). Confirmar primero los refs exactos disponibles:
oc models list
```

> ⚠️ **`gateway.bind: loopback` exige `network_mode: host` en el Compose.** Con `ports:` no funciona:
> Docker entrega el tráfico a la IP del contenedor y el socket solo escucha el loopback de *dentro*,
> así que `curl` devuelve *empty reply* aunque el gateway diga `ready`. Con la red del host, el
> loopback del contenedor es el del Droplet y el puerto queda en `127.0.0.1:18789` sin exponerse.

El modelo por defecto de la imagen es **`openai/gpt-6-astra`**, que no sirve: hay que declararlo.

```bash
# Lo que se esté usando. Con solo la llave de DeepSeek:
oc config set agents.defaults.model.primary "deepseek/deepseek-v4-pro"
oc config set agents.defaults.model.fallbacks '["deepseek/deepseek-flash"]'
oc config get agents.defaults.model

# Con Claude por API sería: anthropic/claude-... (confirmar el ref con `oc models list`).
```

> El token entra por `OPENCLAW_GATEWAY_TOKEN` desde `openclaw.env`, pero hay que escribirlo en la
> configuración para que el gateway lo exija (no lo toma solo del entorno):
>
> ```bash
> docker compose -f ~/openclaw/docker-compose.openclaw.yml exec -T gateway \
>   sh -c 'openclaw config set gateway.auth.token "$OPENCLAW_GATEWAY_TOKEN"'
> docker compose -f ~/openclaw/docker-compose.openclaw.yml restart gateway   # el token sí pide reinicio
> ```
>
> `oc config get gateway.auth` lo muestra redactado. `/healthz` queda sin autenticar a propósito
> (es el chequeo de vida); el resto de la API exige el token.

Comprobar que el puerto **no** está expuesto, desde el Mac:

```bash
nc -z -w 5 178.128.11.124 18789 && echo "EXPUESTO ⛔" || echo "cerrado ✅"
```

Para abrir la Control UI sin exponer nada, túnel SSH desde el Mac y luego `http://127.0.0.1:18789`:

```bash
ssh -L 18789:127.0.0.1:18789 deploy@178.128.11.124
```

## 4 · WhatsApp: plugin, allowlist y QR

El runtime de WhatsApp es un **plugin aparte**:

```bash
oc plugins install @openclaw/whatsapp
```

Política de acceso **antes** de vincular (R077.5):

```bash
oc config set channels.whatsapp.enabled true
oc config set channels.whatsapp.dmPolicy allowlist
oc config set channels.whatsapp.allowFrom '["+57XXXXXXXXXX"]'   # E.164, uno por invitado
oc config get channels.whatsapp
```

### Vincular el número (el paso delicado)

> La documentación de OpenClaw advierte que en hosts headless **el QR puede vencer en tránsito**. Se
> escanea en vivo, desde la terminal, con el celular en la mano. Nada de capturas ni de reenviar el
> QR por chat.

```bash
# En una sesión SSH interactiva, con el celular desbloqueado y WhatsApp Business abierto en
# Ajustes → Dispositivos vinculados → Vincular un dispositivo:
docker compose -f ~/openclaw/docker-compose.openclaw.yml exec gateway openclaw channels login --channel whatsapp
```

Si el QR vence, se vuelve a ejecutar el mismo comando. Verificación:

```bash
oc channels status
oc channels status --probe
```

## 5 · Endurecimiento (ítem 4.2 de la rúbrica)

```bash
oc security audit
```

Se corrigen los hallazgos en orden de severidad. Las rutas exactas de `tools.deny`,
`fs.workspaceOnly` y sandbox se consultan en el esquema vivo antes de fijarlas:

```bash
oc config schema | less          # o la Control UI por el túnel SSH
```

Guardar la salida del audit como evidencia de la sustentación (sin secretos).

## 6 · Operación diaria

```bash
oc channels status                 # ¿sigue vinculado?
oc logs --follow                   # qué está pasando
oc doctor                          # diagnóstico completo
curl -fsS http://127.0.0.1:18789/healthz    # vivo
curl -fsS http://127.0.0.1:18789/readyz     # listo, con los canales
docker stats --no-stream openclaw-gateway   # RAM (el Droplet tiene 2 GB)
```

### Si deja de responder

1. `oc channels status --probe` y `oc doctor`.
2. `docker compose -f ~/openclaw/docker-compose.openclaw.yml restart gateway`.
3. Si quedó un *lock* tras una caída, `oc doctor` lo identifica y dice cómo recuperarlo. **No** se
   borran archivos de estado ni de credenciales a mano.
4. Re-vincular solo como último recurso: implica QR otra vez y el celular a la mano.

> Reiniciar el contenedor **no** pide QR de nuevo: la sesión vive en el volumen `openclaw_estado`.

## 6½ · MCP propio (ítem 3.4, SPEC-078)

El asistente expone sus tools por un servidor **MCP** montado en la API (`/mcp`, streamable HTTP).
Para que OpenClaw las use, la API se publica **solo en loopback** (`127.0.0.1:8000:8000`, ya en
`deploy/docker-compose.prod.yml`) y el gateway se conecta como cliente:

```bash
# en el Droplet, una vez desplegada la API con el MCP (uv add mcp ya incluido):
docker compose -f ~/openclaw/docker-compose.openclaw.yml exec -T gateway \
  openclaw mcp add sb-asistente \
  --url http://127.0.0.1:8000/mcp --transport streamable-http

docker compose -f ~/openclaw/docker-compose.openclaw.yml exec -T gateway \
  openclaw mcp doctor sb-asistente --probe
```

Las tools quedan como `sb-asistente__<tool>` (p. ej. `sb-asistente__buscar_conocimiento`) y pasan
por las políticas de tools del gateway. Verificación local del endpoint:

```bash
curl -sS -X POST http://127.0.0.1:8000/mcp \
  -H 'content-type: application/json' \
  -H 'accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe","version":"0"}}}'
```

> El MCP se monta en el *lifespan* de la API y solo si el corpus está disponible: sin `data/gold/`
> (p. ej. en CI) `/mcp` simplemente no existe y el resto de la API sigue funcionando.

## 7 · El día de la demo

- [ ] Los números de los invitados ya están en `allowFrom` (si alguien llega sin registrar, su
      mensaje se bloquea en silencio; el respaldo es `dmPolicy: pairing`, que exige aprobar en vivo).
- [ ] `oc channels status` en verde esa mañana.
- [ ] `docker stats` con holgura de RAM.
- [ ] Un mensaje de prueba desde un teléfono del allowlist y otro desde uno que no esté (AC2 y AC3).
- [ ] El Droplet **no se destruye** hasta después de la sustentación del M4 de Gestión (11:00).

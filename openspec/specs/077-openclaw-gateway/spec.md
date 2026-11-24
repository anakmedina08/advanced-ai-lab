# SPEC-077 · Gateway de OpenClaw y canal de WhatsApp en el Droplet

> Curso: Técnicas Avanzadas de IA (551462) · Story points: **8** · Responsable: Daniel Silva ·
> Anuncio: [551462 · 007](../../../docs/anuncios/551462-anuncio-007.md) (ítems 3.1, 3.2 y 4.2 de la
> rúbrica = 25 %) · Reemplaza como canal evaluado a [SPEC-073](../073-whatsapp-webhook/spec.md).
> Documentación oficial: [channels/whatsapp](https://docs.openclaw.ai/channels/whatsapp),
> [gateway/configuration](https://docs.openclaw.ai/gateway/configuration),
> [install/docker](https://docs.openclaw.ai/install/docker).

## Problema
El anuncio 007 exige que el asistente atienda por WhatsApp a través de **OpenClaw**, que se conecta
como **dispositivo vinculado** (QR de WhatsApp Web, Baileys). El webhook de la Cloud API de Meta
(SPEC-073) no sirve para la entrega: son mecanismos incompatibles y **un número registrado en la
Cloud API ya no se puede vincular a OpenClaw**. Hoy no existe nada de OpenClaw en el proyecto, y el
Droplet no tiene Node ni el usuario `deploy` tiene `sudo`.

## Restricciones del entorno
- Droplet Ubuntu 24.04, **2 GB de RAM** (≈ 1,1 GB libres) y 2 GB de swap; ya corren `api`,
  `frontend`, `caddy` y `yellowdata`.
- El usuario `deploy` **no tiene `sudo`**, pero sí maneja Docker. ⇒ OpenClaw corre **en contenedor**,
  con la **imagen prearmada** (`ghcr.io/openclaw/openclaw`); compilar desde fuente pide 6 GB de RAM.
- El mismo Droplet sostiene la sustentación del M4 de Gestión a las 11:00: **nada puede tumbar la
  pila actual**. ⇒ OpenClaw vive en su propio proyecto de Compose, en `/home/deploy/openclaw`.

## Requisitos
- **R077.1** El gateway DEBE correr como contenedor con reinicio automático, con su estado
  persistente en un volumen (`/home/node/.openclaw`), y DEBE sobrevivir a un reinicio del Droplet.
- **R077.2** El gateway DEBE escuchar **solo en loopback**: `gateway.bind` en `loopback` y el puerto
  publicado como `127.0.0.1:18789:18789`. Las imágenes de contenedor traen *bind* expuesto por
  defecto, así que el valor se fija explícitamente.
- **R077.3** El acceso al gateway DEBE exigir **token** (`gateway.auth.token` vía
  `OPENCLAW_GATEWAY_TOKEN`). El token vive en el `.env` del servidor y en las variables de CI;
  **nunca** en el repositorio ni en un log.
- **R077.4** El modelo primario DEBE declararse explícitamente en
  `agents.defaults.model.primary` (la imagen trae `openai/gpt-6-astra` por defecto) y DEBE haber al
  menos un *fallback* en `agents.defaults.model.fallbacks`. Con la llave disponible hoy, el primario
  es `deepseek/deepseek-v4-pro` y el *fallback* `deepseek/deepseek-flash`; si se carga la llave de
  Anthropic, el primario pasa a un `anthropic/claude-...`.
- **R077.5** El canal de WhatsApp DEBE quedar vinculado por QR con el número de la SIM nueva en
  **WhatsApp Business**, con `dmPolicy: "allowlist"` y `allowFrom` en formato **E.164**.
- **R077.6** Las credenciales de la sesión vinculada (`~/.openclaw/credentials/whatsapp/<cuenta>/creds.json`)
  **NO DEBEN** versionarse nunca, ni salir en logs ni en capturas.
- **R077.7** `openclaw security audit` DEBE quedar sin hallazgos de severidad alta, con
  `tools.deny`, `fs.workspaceOnly` y sandbox según la [línea base endurecida](https://docs.openclaw.ai/gateway/security/hardened-baseline).
- **R077.8** El repositorio DEBE versionar la configuración reproducible del gateway
  (`deploy/openclaw/`) y su manual de operación (`docs/openclaw.md`), **sin secretos**.
- **R077.9** La configuración DEBE validar contra el esquema de OpenClaw: una clave desconocida hace
  que el gateway **se niegue a arrancar** (código 78). Se edita con `openclaw config set` y se
  verifica con `openclaw doctor`.

## Criterios de aceptación
- **AC1** · **Dado** el gateway corriendo, **cuando** se consulta `http://127.0.0.1:18789/healthz`
  desde el Droplet, **entonces** responde 200; **y** desde fuera del Droplet el puerto 18789 **no**
  responde.
- **AC2** · **Dado** el número de la SIM vinculado, **cuando** un teléfono de `allowFrom` escribe
  «¿Qué cubre el SOAT?», **entonces** llega una respuesta de Claude por WhatsApp en menos de 30 s.
- **AC3** · **Dado** un número que **no** está en `allowFrom`, **cuando** escribe, **entonces** el
  gateway lo bloquea y lo registra como `Inbound message blocked (reason=...)`, sin responder.
- **AC4** · `openclaw security audit` no reporta hallazgos de severidad alta.
- **AC5** · **Dado** un reinicio del contenedor, **cuando** vuelve a arrancar, **entonces** la sesión
  de WhatsApp sigue vinculada (no pide QR otra vez).

## Riesgos
| Riesgo | Mitigación |
|---|---|
| **El QR vence en tránsito** en un host headless (lo advierte la propia documentación) | Vincular desde una sesión SSH **interactiva** con el celular de la SIM en la mano; nunca por captura de pantalla ni reenviando el QR por chat |
| WhatsApp bloquea el número | Se corre con la **SIM nueva**, jamás con el número personal; volumen de mensajes bajo y sin envíos masivos |
| Los invitados escriben desde números que no están en `allowFrom` | Recoger los números en la pestaña 2 de la hoja **antes** del sábado; dejar `pairing` documentado como respaldo en vivo |
| Los 2 GB de RAM no alcanzan | Imagen prearmada (sin build), swap de 2 GB y `docker stats` antes de la demo |
| Un `docker compose down` de la pila del curso se lleva el gateway | Proyecto de Compose **aparte**, en otro directorio y sin red compartida |

## Fuera de alcance
Las tools del asistente dentro de OpenClaw (van en el MCP propio, SPEC-078) y el workspace del
agente (`SOUL.md`, `USER.md`, `MEMORY.md` y bitácora, SPEC-079). El webhook de la Cloud API
(SPEC-073) se conserva como alternativa documentada, sin borrarlo.

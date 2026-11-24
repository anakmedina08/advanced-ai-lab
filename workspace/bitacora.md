# Bitácora diaria de Yelo

> Registro de trabajo día a día (ítem 3.3 de la rúbrica). Una entrada por sesión de trabajo, con
> qué se hizo y qué quedó pendiente. No se escriben secretos ni datos personales aquí.

Formato de cada entrada:

```
## AAAA-MM-DD — <resumen de una línea>

### Hecho
- ...

### Pendiente
- ...
```

---

## 2026-11-23 — Gateway OpenClaw + WhatsApp vinculado + 20 tools

### Hecho
- Registrado el anuncio 007 de Técnicas (OpenClaw como canal, 20 tools, workspace, MCP propio).
- Gateway de OpenClaw en el Droplet: contenedor con imagen prearmada, `bind: loopback`, token,
  `network_mode: host` y solo 3 plugins (DeepSeek + memoria + WhatsApp) para no saturar la única
  vCPU.
- WhatsApp vinculado por QR con la SIM nueva (`linked, running, healthy`), `dmPolicy: allowlist`.
- Specs abiertos: SPEC-077 (gateway), SPEC-078 (MCP propio), SPEC-079 (12 tools + workspace).
- **20 tools** implementadas: 8 originales + 12 en `model/herramientas.py`, cableadas al agente
  en `controller/agente.py`. `make check` en verde (2122 pruebas).
- Workspace del agente: `SOUL.md`, `USER.md`, `MEMORY.md`, `AGENTS.md` y esta bitácora.
- ADR-035 (OpenClaw como canal) y `CONSTITUTION.md` actualizados.

### Pendiente
- MCP propio (SPEC-078): servidor FastMCP montado en `/mcp` y registrado en OpenClaw.
- Embeddings `voyage` en producción y reindexado (arregla el «Error interno del servidor»).
- t-SNE o UMAP del corpus.
- HITL (`escalar_a_humano` ya existe; falta el flujo de confirmación) y `openclaw security audit`.
- Recoger los números E.164 de los invitados y cargarlos en `allowFrom` antes del 28/11.

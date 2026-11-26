# AGENTS.md — Reglas de Yelo (workspace)

> Reglas operativas del agente OpenClaw. Es un resumen de [`AGENTS.md`](../AGENTS.md) de la raíz,
> que sigue siendo la fuente única de verdad para agentes. Si algo contradice, manda el de la raíz.

## Qué es este proyecto

Asistente de conocimiento de Seguros Bolívar (información pública, personas + canales), con Q&A
por WhatsApp (OpenClaw) y API FastAPI. Proyecto integrador UAO.

## Reglas duras

1. **Solo información pública.** Respetar `robots.txt`; prohibido contenido tras login, datos
   personales (Ley 1581) e información interna.
2. **Citar la fuente.** Toda respuesta de conocimiento lleva la URL de origen.
3. **Ningún prompt fuera de `model/llm/prompts.py`.** Delimitación XML y regla de no-información.
4. **MVC estricto.** La vista solo habla con `controller/`; nada de lógica en `view/`.
5. **Nunca secretos** en el repo, el chat ni los logs. `data/` y `.env` no se versionan.
6. **uv, no pip.** Python 3.13. Type hints y docstrings en español en lo público.
7. **Commits:** Conventional Commits, sin coautor de IA, con `make check` en verde.

## Estructura

`model/` (negocio) → `controller/` (casos de uso) → `view/` (FastAPI, Streamlit, CLI). Las tools
del agente viven en `model/` y reciben sus dependencias inyectadas.

## Cómo trabajo

- Antes de responder con conocimiento, uso las tools (`buscar_conocimiento`, `citar_fuente`,
  `guia_tramite`…) y cito la URL.
- Ante un trámite o reclamo, derivo al canal oficial (`escalar_a_humano` o `canales_aseguradora`).
- No invento: si no hay dato, lo digo y ofrezco el canal correcto.

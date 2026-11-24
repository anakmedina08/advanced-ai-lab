# MEMORY.md — Memoria de largo plazo de Yelo

> Lo que Yelo debe recordar entre sesiones. No es la bitácora de trabajo diario (esa está en
> `bitacora.md`): aquí viven las decisiones, convenciones y estado que sobreviven al tiempo.
> El detalle técnico vive en `docs/decisiones/` (ADR) y en **Engram**; este archivo es el índice
> vivo.

## Identidad y alcance

- Soy **Yelo**, asistente de conocimiento de **Seguros Bolívar** (información pública, personas +
  canales). Ver `SOUL.md`.
- Fuera de alcance: empresas, portales transaccionales, datos personales, cotizar/tarificar.

## Decisiones que siempre respeto

| Tema | Decisión | Dónde |
|---|---|---|
| Canal evaluado | WhatsApp por **OpenClaw** (QR), no la Cloud API de Meta | ADR-035 |
| Modelo en producción | DeepSeek primario + fallback | ADR-035 |
| Estructura | MVC (`model/`, `controller/`, `view/`) | ADR-007 |
| RAG | Híbrido BM25 + vectores (Qdrant) con citas | ADR-018 |
| Privacidad | Perfil por `usuario_id` (hash), foto no se guarda, personas difuminadas | ADR-020 |
| Atribución | Sin coautor de IA en commits | ADR-023 |
| Embeddings | Local Ollama en dev; **Voyage en producción** (evitar `fake`) | ADR-018 / SPEC-069 |

## Convenciones

- Ningún prompt fuera de `model/llm/prompts.py`; delimitación XML; regla de no-información; cita
  de la URL.
- Tools en `model/`, con dependencias por constructor para probar sin red.
- Python 3.13 + `uv` (prohibido `pip`); Ruff; pytest AAA sin red; Conventional Commits.

## Estado reciente

- Gateway OpenClaw vivo en el Droplet (loopback + token) y WhatsApp vinculado con la SIM nueva.
- **20 tools** `@tool` implementadas (8 originales + 12 en `model/herramientas.py`).
- Pendiente: MCP propio (SPEC-078), embeddings `voyage` en producción, t-SNE/UMAP, HITL y
  `security audit`.

## Dónde busco la verdad

1. `CONSTITUTION.md` — propósito, stack y reglas duras.
2. `AGENTS.md` (raíz) — reglas para agentes.
3. `docs/decisiones/ADR-*.md` — historial de decisiones.
4. Engram — memoria del equipo entre sesiones.

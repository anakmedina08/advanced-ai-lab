# ADR-011 · Subagentes de Claude Code y telemetría de agentes en vivo

- **Fecha:** 2026-11-06
- **What:** siete subagentes versionados en `.claude/agents/` (arquitecto·opus asesor de solo lectura; explorador, probador y guardián de datos·haiku; revisor, ml-recomendador y documentador·sonnet). Hooks en `.claude/settings.json` llaman a `scripts/agent_events.py`, que registra cada evento en `logs/agent-events.jsonl` y, con `AGENT_EVENTS_URL` y `AGENT_EVENTS_TOKEN`, lo publica en el panel de yellowdata.com.co/casos. La CI publica su resultado.
- **Why:** mostrar en vivo cómo se construye el producto con agentes (spec → líder → subagentes → barandas → revisor humano), delegar búsquedas y pruebas en modelos baratos para ahorrar tokens del líder, y dejar evidencia trazable para ambos cursos.
- **Where:** `.claude/agents/*.md`, `.claude/settings.json`, `scripts/agent_events.py`, `tests/test_agent_events.py`, job `notificar` de `.github/workflows/ci.yml`.
- **Learned:** el panel es público, así que el evento se sanea en el origen (sin prompts, contenido, salidas ni comandos completos; rutas de `data/` y `.env` omitidas) y se vuelve a validar en el servidor. El hook nunca bloquea la sesión: ante cualquier error sale con código 0.

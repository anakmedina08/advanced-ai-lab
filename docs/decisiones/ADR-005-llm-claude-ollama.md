# ADR-005 · Claude (API de Anthropic) con Ollama como respaldo

- **Fecha:** 2026-10-24 · **Reemplaza a:** ADR-004
- **What:** el asistente usa Claude por la API de Anthropic (`ChatAnthropic`, temperatura 0, `claude-haiku-5-5` por defecto, configurable con `ANTHROPIC_MODEL`). Ollama (`llama3.2:3b`) queda como alternativa local y gratuita.
- **Why:** el equipo unifica herramientas: Claude Code es el agente de desarrollo y revisión (GGA `PROVIDER="claude"`, Engram `setup claude-code`) y Claude es el modelo del producto. La ventana de 200K tokens cubre la base completa de la Fase 1 (ADR-001) y la caché de prompts abarata repetir el mismo *system prompt*.
- **Where:** `src/sb_asistente/llm/service.py::build_llm`, `config.py`, `.env.example`.
- **Learned:** la suscripción de Claude Code no da acceso a la API; la app necesita su propia `ANTHROPIC_API_KEY` con créditos. Haiku se usa para las corridas de evaluación (costo bajo); Sonnet puede compararse como experimento.

# Decisiones técnicas (espejo de Engram)

Engram guarda la memoria del proyecto en `~/.engram/engram.db`, **local en cada máquina**. Para
que el equipo y el docente vean las decisiones, cada una se registra en Engram **y** se copia aquí.

## Instalación y uso (macOS)
```bash
brew install gentleman-programming/tap/engram
engram --version
engram setup claude-code       # Claude Code lee/escribe memorias vía MCP
engram tui                     # navegar lo recordado
engram doctor                  # diagnóstico
```
En Claude Code: *"Registra en Engram la decisión ADR-001…"*; en una sesión nueva: *"¿Qué decidimos
sobre el contexto de la Fase 1?"* → el agente la recupera con `mem_context`/búsqueda.

Formato de cada registro (Clase 3): **título, categoría, Why, Where y lección aprendida**.

| ID | Decisión | Fecha |
|---|---|---|
| [ADR-001](ADR-001-contexto-completo-fase1.md) | Conocimiento completo en el system prompt (Fase 1); RAG en Fase 2 | 2026-10-24 |
| [ADR-002](ADR-002-alcance-personas-canales.md) | Alcance PERSONAS + CANALES; blog y PDFs a Fase 2 | 2026-10-24 |
| [ADR-003](ADR-003-requests-sin-selenium.md) | `requests` + trafilatura (SSR), sin Selenium | 2026-10-24 |
| [ADR-004](ADR-004-llm-deepseek-ollama.md) | ~~DeepSeek por API~~ · reemplazada por ADR-005 | 2026-10-24 |
| [ADR-005](ADR-005-llm-claude-ollama.md) | Claude (API de Anthropic) con Ollama local como respaldo | 2026-10-24 |

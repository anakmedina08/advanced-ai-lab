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
| [ADR-006](ADR-006-contexto-reducido-ollama.md) | Contexto reducido para que Ollama responda en CPU | 2026-10-30 |
| [ADR-007](ADR-007-estructura-mvc.md) | Estructura MVC igual a la del proyecto de Gestión | 2026-11-01 |
| [ADR-008](ADR-008-docker-multistage-y-estandar.md) | Docker multi-stage y estándar jan-project-standard | 2026-11-01 |
| [ADR-009](ADR-009-repositorio-unico.md) | Un solo repositorio público para los dos cursos | 2026-11-06 |
| [ADR-010](ADR-010-api-fastapi-pydantic.md) | API REST con FastAPI, Pydantic y type hints | 2026-11-06 |
| [ADR-011](ADR-011-subagentes-y-telemetria.md) | Subagentes de Claude Code y telemetría en vivo | 2026-11-06 |
| [ADR-012](ADR-012-proveedor-deepseek.md) | DeepSeek como proveedor alterno del LLM | 2026-11-06 |

## Cómo registrar una decisión nueva en Engram

1. Escribir el ADR aquí con el formato **What / Why / Where / Learned**.
2. En Claude Code (con `engram setup claude-code` hecho), pedir:
   *«Guarda en Engram la decisión del archivo docs/decisiones/ADR-00X-….md como tipo decision,
   proyecto advanced-ai-lab»*. El agente la guarda con `mem_save`.
3. Verificar con `engram tui` (o preguntando en una sesión nueva: *«¿Qué decidimos sobre …?»*).

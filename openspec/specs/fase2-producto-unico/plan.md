# Plan · Fase 2 — Producto único

## Arquitectura

```mermaid
flowchart TB
    FE[Front web · yellowdata.com.co/casos] -->|HTTP| API[view/api.py · FastAPI + Pydantic]
    ST[view/streamlit_app.py] --> CA
    CLI[view/cli.py · sb] --> CA & CR
    API --> CA[controller/assistant.py] & CP[controller/pipeline.py] & CR[controller/recomendador.py]
    CA --> LLM[model/llm · Anthropic / DeepSeek / Ollama]
    CP --> MED[model/scraping + processing · Medallion]
    CR --> REC[model/recomendador · sintético, contrato, líneas base, métricas]
    subgraph Agentes[Desarrollo con agentes]
      L[Claude Code · líder] --> SA[.claude/agents · 7 subagentes]
      L --> H[hooks · scripts/agent_events.py]
      H --> LOG[(logs/agent-events.jsonl)]
      H -->|Bearer token| EV[yellowdata /api/agent-events]
      CI[GitHub Actions] -->|evento CI| EV
    end
    EV --> FE
```

## Decisiones
- ADR-009 repositorio único (público) · ADR-010 FastAPI + Pydantic · ADR-011 subagentes y
  telemetría · ADR-012 DeepSeek como proveedor alterno.

## Cómo se verifica cada requisito
| Requisito | Pruebas |
|---|---|
| R7 API | `tests/test_api.py` (TestClient, dobles del LLM; 422/404/503) |
| R8 Recomendador | `tests/test_reco_*.py` (contrato, sintético, métricas, CLI, top-k) |
| R9 Proveedor | `tests/test_llm.py` + `context_budget` por proveedor |
| R10 Agentes | `tests/test_agent_events.py` (saneo, rutas privadas, token) |

## Riesgos
- Costo de tokens: modelo `claude-haiku-5-5` por defecto, caché de prompt, contexto reducido y
  saldo inicial de 10 USD; DeepSeek si el costo sube.
- Exposición pública del panel: solo eventos saneados y escritura con token.
- cPanel con un solo proceso Node: eventos en memoria + archivo `.data/agent-events.jsonl`.

# ADR-010 · API REST con FastAPI, Pydantic y type hints

- **Fecha:** 2026-11-06
- **What:** nueva vista `view/api.py` (FastAPI) con contratos en `view/schemas.py` (Pydantic v2): `/salud`, `/pipeline`, `/preguntas`, `/resumen`, `/faq` y `/recomendaciones/{cliente_id}`. Se levanta con `uv run sb api` (documentación en `/docs`).
- **Why:** pedido en clase para pasar de Streamlit a un front real; Pydantic valida en la frontera (campos desconocidos, rangos, proveedor) y rechaza preguntas con correo, teléfono o documento (Ley 1581) antes de gastar tokens.
- **Where:** `src/sb_asistente/view/api.py`, `view/schemas.py`, `tests/test_api.py`.
- **Learned:** el LLM se inyecta con `Depends` (`get_responder`, `get_asistente`), así las pruebas usan dobles con `dependency_overrides` y no gastan saldo. Streamlit se mantiene como consola interna.

# ADR-007 · Estructura MVC igual a la del proyecto de Gestión

- **Fecha:** 2026-11-01
- **What:** el paquete `sb_asistente` se reorganiza en `model/` (scraping, processing, llm, evaluation), `controller/` (`pipeline.py` y `assistant.py`) y `view/` (`streamlit_app.py` y `cli.py`), igual que `gpia-m1-ai-doctors`.
- **Why:** bajo acoplamiento y alta cohesión: las vistas solo hablan con el controlador; si cambia el proveedor de LLM o el formato de entrada, se toca un solo módulo. Los dos repositorios del equipo quedan con la misma forma, lo que facilita revisar y sustentar.
- **Where:** `src/sb_asistente/{model,controller,view}/`; pruebas por capa en `tests/` (`test_controller.py` nuevo).
- **Learned:** el refactor se hizo con `git mv` para conservar el historial de cada archivo; los parches de prueba (`monkeypatch`) referencian rutas de módulo y hubo que actualizarlos junto con los imports.

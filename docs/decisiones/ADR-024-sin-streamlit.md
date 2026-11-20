# ADR-024 · Streamlit retirado del proyecto; la única interfaz web es el frontend React

- **Fecha:** 2026-11-17
- **Reemplaza:** la parte de [ADR-021](ADR-021-interfaz-empresarial.md) que mantenía Streamlit como
  herramienta interna del equipo. Las dos áreas y el tema neutro de ADR-021 siguen vigentes en el frontend React.
- **What:** se eliminaron la dependencia `streamlit` y estos archivos y targets:
  - `app.py`;
  - `view/streamlit_app.py`, `view/ui.py` y `view/app_pages/`;
  - `.streamlit/`;
  - el target `make app`;
  - las pruebas de AppTest.

  La API (`view/api.py`, `view/rpc.py`) y el frontend React (`frontend/`) cubren las 8 páginas,
  según la paridad verificada en SPEC-046.
- **Why:**
  - Técnicas, anuncio 006: «Streamlit y Gradio quedan prohibidos desde el Módulo 2».
  - Gestión, anuncio 007: «no se acepta Streamlit» y la regla prevalece sobre menciones anteriores.

  Tenerlo como herramienta interna ya no era defendible en la sustentación.
- **Where:**
  - `pyproject.toml` y `uv.lock`.
  - `Makefile` y `Dockerfile`.
  - `tests/test_proyecto.py`: se conservan las pruebas del modelo y del controlador.
  - README, AGENTS, CONSTITUTION y `docs/arquitectura.md`.
  - `docs/anuncios/herramientas.md` (K4).
- **Learned:**
  - Con MVC, retirar una vista no tocó el modelo ni el controlador: solo comentarios.
  - El auditor (K4) vigila que el paquete no vuelva a entrar como dependencia.

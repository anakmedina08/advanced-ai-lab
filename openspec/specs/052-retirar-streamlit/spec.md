# SPEC-052 · Retirar Streamlit del proyecto

> Curso: Técnicas M2/M3 (anuncio 006) · Gestión M3/M4 (anuncio 007) · Story points: **5** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
Streamlit está prohibido desde el M2 de Técnicas y «no se acepta» en Gestión (anuncio 007, que prevalece sobre menciones anteriores). Seguía en el repo como herramienta interna (ADR-021): dependencia en `pyproject.toml`, `app.py`, `make app`, `view/streamlit_app.py`, `view/ui.py`, `view/app_pages/`, `.streamlit/` y la imagen Docker. El frontend React ya cubre las 8 páginas (SPEC-046, paridad).

## Historia
**Como** equipo, **quiero** que Streamlit desaparezca del proyecto, **para** que la entrega cumpla la regla de las dos materias y el único cliente sea el frontend desacoplado.

## Requisitos
- **R052.1** `streamlit` NO DEBE ser dependencia del proyecto ni importarse en `src/` ni en `tests/`.
- **R052.2** DEBEN eliminarse `app.py`, `view/streamlit_app.py`, `view/ui.py`, `view/app_pages/`, `.streamlit/` y el target `make app`.
- **R052.3** La imagen Docker NO DEBE copiar archivos de Streamlit.
- **R052.4** Las pruebas del modelo y del controlador que usaban las páginas DEBEN conservarse; solo se retiran las pruebas de la interfaz Streamlit (la paridad la cubre Vitest).
- **R052.5** README, AGENTS, CONSTITUTION y la arquitectura DEBEN describir el frontend React como única interfaz web.
- **R052.6** Un ADR DEBE reemplazar la parte de ADR-021 que mantenía Streamlit.

## Criterios de aceptación
- **AC1** · **Dado** `uv sync`, **cuando** se lista el entorno, **entonces** `streamlit` no está instalado.
- **AC2** · **Dado** `make madurez`, **cuando** se evalúa K4, **entonces** está en ✅.
- **AC3** · **Dado** `make check` y `npm test`, **cuando** se ejecutan, **entonces** pasan en verde.

## Fuera de alcance
Cambios visuales del frontend.

## Métricas de éxito
K4 en ✅; 0 referencias a Streamlit en código; suite verde.

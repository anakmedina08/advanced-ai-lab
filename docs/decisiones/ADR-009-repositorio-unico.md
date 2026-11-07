# ADR-009 · Un solo repositorio público para los dos cursos

- **Fecha:** 2026-11-06
- **What:** `advanced-ai-lab` (público) pasa a ser el repositorio único del Asistente Seguros Bolívar. El recomendador de Gestión vive en `src/sb_asistente/model/recomendador/` con su controlador, CLI (`sb reco`) y pruebas; los entregables M2 (backlog, propuesta, EDA) en `docs/gestion/`. El repositorio del M1 (AI Doctors) sigue aparte porque es otro caso.
- **Why:** Técnicas exige repositorio público y ambos cursos trabajan sobre el mismo producto; un solo repo evita duplicar gobernanza (CI, pre-commit, spec, ADR, Kanban) y deja que cada entrega muestre el producto completo. Los datos no se versionan, así que publicar el código no expone información de la compañía.
- **Where:** `src/sb_asistente/model/recomendador/`, `controller/recomendador.py`, `docs/gestion/`, `docs/requisitos.md`.
- **Learned:** las tablas sintéticas van en `data/recomendador/` y no en `data/raw/`, para no mezclarlas con el HTML de Bronze. Al docente de Gestión se le comparte el enlace del repositorio público.

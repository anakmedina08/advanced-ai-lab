# ADR-025 · Auditor de madurez como código del proyecto y puerta en la CI

- **Fecha:** 2026-11-17
- **What:** `scripts/auditar_madurez.py` evalúa el repositorio en 9 dimensiones con 70 verificaciones
  ponderadas. Son la rúbrica de la skill `estandar-ia-profesional` más K1-K4 de
  `seguimiento-anuncios-curso`. La CI ejecuta `make madurez MINIMO=N`: si el puntaje baja de N, el job falla.
- **Why:** las mejoras de calidad, seguridad y gobernanza se perdían sin una medida. El equipo
  decidió que la skill fuera solo instrucciones (sin scripts propios), así que la automatización
  vive en el proyecto, con sus pruebas, y la CI no depende de la carpeta de la skill.
- **Decisiones de diseño:**
  - **Solo lectura de archivos:** no ejecuta código del proyecto ni usa la red.
  - **Umbral bajo al inicio:** 60, y sube con cada oleada de mejoras para que nunca retroceda.
  - **Ante la duda, ❌:**
    - la privacidad (M8) no cuenta por lo que diga AGENTS.md;
    - la estrategia de ramas (P6) debe nombrarse;
    - la revisión humana (G8) exige CODEOWNERS.
  - **P9 tiene un límite:** solo verifica el workflow de limpieza de ramas. Que el remoto tenga solo
    `main` y `develop` lo confirma una persona con `git ls-remote`.
- **Where:**
  - `scripts/auditar_madurez.py`.
  - `tests/test_auditar_madurez.py`.
  - `Makefile` (target `madurez`).
  - `.github/workflows/ci.yml`.
  - `docs/madurez.md`.
- **Learned:** las verificaciones por texto se inflan con menciones de paso. Cada una necesita una prueba que demuestre que **no** pasa con evidencia débil.

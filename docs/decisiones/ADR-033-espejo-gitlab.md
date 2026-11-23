# ADR-033 · GitHub como repositorio principal y GitLab como espejo para CI/CD y despliegue

- **Fecha:** 2026-11-21
- **Categoría:** proceso · CI/CD · seguridad
- **What:** GitHub sigue siendo donde se trabaja (PR, revisión cruzada, Kanban, GitHub Actions). Un
  workflow copia `develop` y `main` a `gitlab.com/daalrasi/advanced-ai-lab`, donde corre el pipeline
  del Módulo 4 (lint, test, secretos; luego build, Registry y deploy).
- **Why:**
  - El Módulo 4 se demuestra en GitLab (Anuncio 008), pero mover el trabajo de GitHub perdería el
    historial de PR, revisiones y el tablero de los módulos anteriores.
  - En GitLab gratuito el *pull mirror* y «CI/CD for external repositories» son Premium: el empuje lo
    hace GitHub.
  - **Deploy key** y no un token personal: solo puede escribir en ese proyecto; si se filtra, no da
    acceso a la cuenta. Se verifica la huella oficial de gitlab.com antes de conectar.
  - Cuentas personales del equipo con el correo institucional como secundario y público: el docente
    identifica a cada integrante y las cuentas no se pierden al terminar la maestría.
- **Alternativas descartadas:**
  - Trabajar solo en GitLab: se pierde la trazabilidad de los módulos 1–3.
  - Token personal de GitLab en GitHub: demasiados permisos.
- **Where:** `.github/workflows/espejo-gitlab.yml`, `.gitlab-ci.yml`, `tests/test_ci_gitlab.py`.

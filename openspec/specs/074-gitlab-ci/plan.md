# Plan · SPEC-074

1. `.github/workflows/espejo-gitlab.yml`: checkout completo, deploy key desde el secret, verificación
   de la huella de gitlab.com y `git push --force` de la rama.
2. `.gitlab-ci.yml`: etapas `lint` y `test`, imagen `ghcr.io/astral-sh/uv:python3.13-bookworm-slim`,
   caché de uv por `uv.lock`, reportes JUnit y Cobertura, plantilla Secret-Detection.
3. Pruebas `tests/test_ci_gitlab.py` que validan los dos YAML.
4. Configuración manual (equipo): proyecto público en GitLab, deploy key con escritura, secret en GitHub.

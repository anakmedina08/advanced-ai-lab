# 4 · CI/CD y releases

## R1-R2 · CI con paridad local
La CI ejecuta **los mismos comandos** que `make check`: `ruff check`, `ruff format --check`,
`ty check` y `pytest --cov`. Si un comando existe solo en la CI, el desarrollador lo descubre
tarde; si existe solo en el Makefile, la CI no protege.

## R3-R4 · Versionado semántico y CHANGELOG
Como ya se usan Conventional Commits, la versión se calcula sola:
- `feat` → minor.
- `fix` → patch.
- `feat!` o `BREAKING CHANGE` → major.

Hay dos opciones:
- **release-please** (`assets/plantillas/workflows/release.yml`): mantiene abierto un PR "chore(main): release x.y.z" con el CHANGELOG. Al fusionarlo crea el tag y el GitHub Release.
- **git-cliff** (`cliff.toml`): genera el `CHANGELOG.md` localmente con `make changelog`.

La versión vive en `pyproject.toml` y se expone en `/health` o `/version`.

## R5-R6 · Contenedor y salud
- Dockerfile multi-stage: un *builder* con uv y un *runtime* slim, con usuario no root, `HEALTHCHECK` y sin `.env` dentro de la imagen.
- `/health` responde 200 con el estado de las dependencias (LLM, índice vectorial, BD) sin exponer secretos.

## R7 · Caché
Usar `astral-sh/setup-uv` con `enable-cache: true`, `actions/setup-node` con `cache: npm` y `cache-from: type=gha` para Docker.

## Entornos
`develop` → staging (opcional) y `main` → producción. El despliegue se hace solo desde un tag o un release, nunca desde una rama de feature.

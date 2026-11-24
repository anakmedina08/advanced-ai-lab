# 2 · Calidad de código y pruebas

## C2 · Tipos

`ty` (de Astral) es el más rápido y encaja con uv. mypy en modo estricto es la alternativa madura.

```toml
# pyproject.toml
[dependency-groups]
dev = ["ty>=0.0.1a", "pytest-cov>=6"]
```
```make
types: ## Verifica tipos
	uv run ty check src
check: lint format-check types test
```

Se empieza en `src/` y se amplía a `tests/` cuando esté en verde. Si hay muchos errores
heredados, se registra la línea base y se impide que crezca, en lugar de apagar el chequeo.

## C4 · Cobertura obligatoria

```toml
[tool.coverage.report]
fail_under = 85
show_missing = true
skip_covered = true
```

La CI corre `pytest --cov`. El umbral vive en `pyproject.toml` para que local y CI coincidan.
**Nunca se baja el umbral para que pase un PR:** se escriben las pruebas que faltan.

## C5 · Pirámide de pruebas

```toml
[tool.pytest.ini_options]
markers = [
  "unit: rápida, sin red ni disco",
  "integration: toca BD, índice vectorial o archivos",
  "e2e: flujo completo por la API",
  "llm: llama a un modelo real (se excluye en CI por defecto)",
]
addopts = "-m 'not llm'"
```

Proporción orientativa: 70 % unit, 20 % integration y 10 % e2e. Las pruebas `llm` corren en el
workflow de evals (M5), no en cada push.

## C6 · Contrato de la API

- FastAPI: `TestClient` por endpoint, con casos felices, 422 de validación y errores de dominio.
- Opcional: `schemathesis run http://localhost:8000/openapi.json` genera casos desde el esquema OpenAPI.

## C7 · Docstrings

Agregar `"D"` a `select` de Ruff con la convención `google` o `pep257`. Las pruebas pueden ignorarla (`"tests/**" = ["D"]`).

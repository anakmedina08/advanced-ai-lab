# =============================================================================
# Asistente Seguros Bolívar — automatización de tareas
# =============================================================================

SHELL := /bin/bash

.DEFAULT_GOAL := help
.PHONY: help install dev pre-commit-install pre-commit lint format format-check test check build clean \
	data process app eval docker-build docker-run

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Sincroniza el entorno virtual e instala dependencias
	uv sync

dev: install pre-commit-install ## Prepara el entorno de desarrollo (sync + hooks)

pre-commit-install: ## Instala los hooks de pre-commit en el repositorio local
	uv run pre-commit install

pre-commit: ## Ejecuta todos los hooks de pre-commit sobre el repositorio
	uv run pre-commit run --all-files

lint: ## Ejecuta Ruff (lint)
	uv run ruff check .

format: ## Formatea el código con Ruff
	uv run ruff format .

format-check: ## Verifica el formato sin modificarlo
	uv run ruff format --check .

test: ## Ejecuta las pruebas (sin red ni API)
	uv run pytest

check: lint format-check test ## Verificación completa (lint + formato + pruebas)

data: ## Scraping completo: descubrir → Bronze → Silver → Gold (~4 min, respeta robots.txt)
	uv run python scripts/scrape_empresa.py

process: ## Reprocesa Bronze → Silver → Gold sin volver a la web (segundos)
	uv run python scripts/scrape_empresa.py --solo-proceso

app: ## Abre la interfaz Streamlit en http://localhost:8501
	uv run streamlit run app.py

eval: ## Evalúa el banco de preguntas (PROVIDER=anthropic|ollama, VERSION=v1..v4)
	uv run sb eval --provider $(or $(PROVIDER),anthropic) --version $(or $(VERSION),v3)

docker-build: ## Construye la imagen Docker multi-stage (CPU)
	docker build -t sb-asistente .

docker-run: ## Corre la imagen montando data/ (Ollama del host vía host.docker.internal)
	docker run --rm -p 8501:8501 -v "$$(pwd)/data:/app/data" --env-file .env \
		-e OLLAMA_HOST=http://host.docker.internal:11434 sb-asistente

build: ## Construye el paquete (sdist + wheel)
	uv build

clean: ## Limpia cachés y artefactos
	rm -rf .pytest_cache .ruff_cache .mypy_cache dist build htmlcov .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

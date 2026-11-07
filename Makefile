# =============================================================================
# Asistente Seguros Bolívar — automatización de tareas
# =============================================================================

SHELL := /bin/bash

.DEFAULT_GOAL := help
.PHONY: help api reco agentes chat skills skill-new skill-find skill-add install dev pre-commit-install pre-commit lint format format-check test check build clean \
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

eval: ## Evalúa el banco de preguntas (PROVIDER=anthropic|deepseek|ollama, VERSION=v1..v4)
	uv run sb eval --provider $(or $(PROVIDER),anthropic) --version $(or $(VERSION),v3)

api: ## Levanta la API FastAPI en http://127.0.0.1:8000/docs
	uv run sb api

reco: ## Recomendador: genera datos sintéticos, valida el contrato y mide las líneas base
	uv run sb reco generar
	uv run sb reco validar
	uv run sb reco baseline

chat: ## Un turno del chat en la terminal: make chat MSG="¿Qué seguro me sirve si tengo moto?"
	uv run sb chat "$(MSG)"

skills: ## Lista y valida las skills (.claude/skills, .agents/skills, .opencode/skills)
	uv run sb skills listar

skill-new: ## Crea una skill propia: make skill-new NAME=mi-skill DESC="Qué hace" USO=asistente|desarrollo
	uv run sb skills nueva $(NAME) --descripcion "$(DESC)" --uso $(or $(USO),desarrollo)

skill-find: ## Busca skills existentes en el directorio abierto (skills.sh): make skill-find Q=fastapi
	npx -y skills find $(Q)

skill-add: ## Instala una skill existente para Claude Code y OpenCode: make skill-add REPO=owner/repo SKILL=nombre
	npx -y skills add $(REPO) --skill $(SKILL) -a claude-code -a opencode -y
	uv run sb skills validar

agentes: ## Muestra los últimos eventos de agentes registrados por los hooks
	@tail -n 20 logs/agent-events.jsonl 2>/dev/null || echo "Aún no hay eventos (se crean al usar Claude Code en este repo)"

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

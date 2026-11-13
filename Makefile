# =============================================================================
# Asistente Seguros Bolívar — automatización de tareas
# =============================================================================

SHELL := /bin/bash

.DEFAULT_GOAL := help
.PHONY: help api frontend frontend-build mlflow-server mlflow-yolo mlflow-registro vision foto mlflow mlflow-importar reco agentes chat skills skill-new skill-find skill-add rag rag-buscar agente rpc-demo langsmith-dataset install dev pre-commit-install pre-commit lint format format-check test check build clean \
	data process index app eval docker-build docker-run

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

index: ## Fase 2: embeddings de los chunks en Qdrant (requiere: ollama pull embeddinggemma)
	uv run sb index

app: ## Abre la interfaz Streamlit en http://localhost:8501
	uv run streamlit run app.py

eval: ## Evalúa el banco (PROVIDER=anthropic|deepseek|ollama, VERSION=v1..v4, MODO=completo|reducido|rag|agente)
	uv run sb eval --provider $(or $(PROVIDER),anthropic) --version $(or $(VERSION),v3) --modo $(or $(MODO),completo)

api: ## Levanta la API FastAPI en http://127.0.0.1:8000/docs
	uv run sb api

frontend: ## Frontend propio (React + Vite) en http://localhost:5173 (requiere Node 20+)
	cd frontend && npm install --no-audit --no-fund && npm run dev

frontend-build: ## Compila el frontend (tsc + vite build) en frontend/dist
	cd frontend && npm ci --no-audit --no-fund && npm run build

mlflow: ## Abre la bitácora de experimentos en http://127.0.0.1:5050 (requiere uv sync --extra mlflow)
	uv run --extra mlflow sb mlflow ui

mlflow-yolo: ## Evalúa YOLO (3 corridas comparables) y lo registra en MLflow (experimento vision-yolo)
	MLFLOW_TRACKING_URI=http://127.0.0.1:5050 uv run --extra vision --extra mlflow python scripts/evaluar_yolo.py

mlflow-registro: ## Registra el YOLO de la API en el Model Registry (sb-yolo-difuminado@produccion)
	MLFLOW_TRACKING_URI=http://127.0.0.1:5050 uv run --extra vision --extra mlflow python scripts/registrar_yolo.py

mlflow-server: ## Servidor de tracking MLflow en http://127.0.0.1:5050 (export MLFLOW_TRACKING_URI=http://127.0.0.1:5050)
	uv run --extra mlflow sb mlflow servidor

mlflow-importar: ## Carga en MLflow las evaluaciones guardadas en evaluacion/ (sin llamar al LLM)
	uv run --extra mlflow sb mlflow importar

vision: ## Instala el extra de visión (ultralytics + torch CPU, ~1 GB) para POST /fotos y sb foto
	uv sync --extra vision

foto: ## Foto → ¿qué hago? (YOLO + Claude + RAG): make foto IMG=ruta.jpg
	uv run --extra vision sb foto "$(IMG)" --interpretar --responder

reco: ## Recomendador: genera datos sintéticos, valida el contrato y mide las líneas base
	uv run sb reco generar
	uv run sb reco validar
	uv run sb reco baseline

rag: ## Indexa los fragmentos Gold en Chroma (data/vector/) con los embeddings de EMBEDDINGS_PROVIDER
	uv run sb rag indexar

rag-buscar: ## Prueba la búsqueda híbrida: make rag-buscar Q="whatsapp de atención"
	uv run sb rag buscar "$(Q)"

agente: ## Turno del agente con memoria: make agente MSG="..." CONV=mi-conversacion
	uv run sb agente "$(MSG)" --conversacion $(or $(CONV),cli-local)

rpc-demo: ## Llama a JSON-RPC (requiere make api en otra terminal)
	curl -s -X POST http://127.0.0.1:8000/rpc -H 'Content-Type: application/json' \
	  -d '{"jsonrpc":"2.0","method":"rpc.descubrir","id":1}' | python3 -m json.tool | head -40

langsmith-dataset: ## Sube el banco de 24 preguntas como dataset de LangSmith
	uv run python scripts/langsmith_dataset.py

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

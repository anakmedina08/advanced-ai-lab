# syntax=docker/dockerfile:1
# Imagen multi-stage y CPU del asistente de Seguros Bolívar.
#   Etapa 1 (builder): resuelve dependencias con uv desde uv.lock (con herramientas de build).
#   Etapa 2 (runtime): solo Python + el .venv ya armado + el código; sin uv, sin cachés.
# Los datos (data/) NO van en la imagen: el contenido es de Seguros Bolívar y se monta como volumen.

# ---------- Etapa 1: builder ----------
FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0
WORKDIR /app

# Dependencias primero (capa cacheable: solo cambia si cambia el lock)
COPY pyproject.toml uv.lock README.md LICENSE ./
RUN uv sync --frozen --no-dev --no-install-project

# Código del paquete (editable: config.py ubica data/ relativo a /app)
COPY src/ src/
RUN uv sync --frozen --no-dev

# ---------- Etapa 2: runtime ----------
FROM python:3.13-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    LLM_PROVIDER=ollama
RUN useradd --create-home appuser
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY app.py ./
COPY src/ src/
COPY scripts/ scripts/
COPY evaluacion/preguntas.yaml evaluacion/preguntas.yaml
COPY .streamlit/ .streamlit/
RUN mkdir -p data/raw data/silver data/gold && chown -R appuser data evaluacion

USER appuser
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

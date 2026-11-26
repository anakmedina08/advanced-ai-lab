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
RUN uv sync --frozen --no-dev --no-install-project --extra voyage

# Código del paquete (editable: config.py ubica data/ relativo a /app)
COPY src/ src/
RUN uv sync --frozen --no-dev --extra voyage

# Visión (SPEC-081): ultralytics con PyTorch de CPU. El torch del lock trae las librerías de GPU
# (varios GB); aquí se instala la variante CPU. Va DESPUÉS de `uv sync`, que borra lo que no está en
# el lock. Misma versión que uv.lock. Los pesos (yolo26l.pt) no van en la imagen: viven en data/modelos.
RUN uv pip install --python /app/.venv/bin/python --torch-backend cpu "ultralytics==8.4.216"

# ---------- Etapa 2: runtime ----------
FROM python:3.13-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    LLM_PROVIDER=ollama
# Tesseract (OCR local) para identificar la aseguradora en un recibo o carátula (SPEC-071);
# libgl1 y libglib2.0-0 los pide OpenCV, que usa YOLO (SPEC-081)
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-spa libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home appuser
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY app.py ./
COPY src/ src/
COPY scripts/ scripts/
COPY evaluacion/ evaluacion/
COPY .streamlit/ .streamlit/
COPY .claude/skills/ .claude/skills/
RUN mkdir -p data/raw data/silver data/gold && chown -R appuser data evaluacion

USER appuser
# Desde el Módulo 2 el producto es la API (el frontend React es otro servicio). Streamlit queda
# como herramienta interna: docker run -p 8501:8501 sb-asistente streamlit run app.py --server.port=8501
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["sb", "api", "--host", "0.0.0.0", "--port", "8000"]

"""Configuración central: rutas, alcance del scraping y parámetros del LLM.

Los secretos (API keys) NUNCA viven aquí: se leen de `.env` con python-dotenv.
"""

import os
import re
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

# --- Rutas Medallion (las tres ignoradas por git) -------------------------------------
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
BRONZE_DIR: Final[Path] = DATA_DIR / "raw"  # HTML crudo + capture.jsonl
SILVER_DIR: Final[Path] = DATA_DIR / "silver"  # texto limpio por página
GOLD_DIR: Final[Path] = DATA_DIR / "gold"  # Markdown enriquecido + corpus + chunks
CAPTURE_LOG: Final[Path] = BRONZE_DIR / "capture.jsonl"
CORPUS_JSONL: Final[Path] = GOLD_DIR / "corpus.jsonl"
CHUNKS_JSONL: Final[Path] = GOLD_DIR / "chunks.jsonl"
KNOWLEDGE_MD: Final[Path] = GOLD_DIR / "conocimiento_seguros_bolivar.md"

# --- Sitio fuente ------------------------------------------------------------------------
BASE_URL: Final[str] = "https://www.segurosbolivar.com"
ROBOTS_URL: Final[str] = f"{BASE_URL}/robots.txt"
SITEMAP_URL: Final[str] = f"{BASE_URL}/sitemap.xml"
USER_AGENT: Final[str] = (
    "UAO-TAAML-Grupo10/0.1 (proyecto academico, Universidad Autonoma de Occidente; "
    "asistente de conocimiento sobre informacion publica)"
)
REQUEST_DELAY_S: Final[float] = 1.5  # cortesía: 1–2 s entre peticiones (Clase 2)
REQUEST_TIMEOUT_S: Final[float] = 15.0
MAX_RETRIES: Final[int] = 2

# --- Alcance de la Fase 1: PERSONAS + CANALES DE ATENCIÓN --------------------------------
# Se excluyen: empresas, proveedores, reaseguradores, legales extensos y portales
# transaccionales. Los artículos del blog se reservan para el RAG de la Fase 2.
EXCLUDE_PATTERNS: Final[tuple[str, ...]] = (
    r"^/empresas(/|$)",
    r"^/proveedores(/|$)",
    r"^/reaseguradores",
    r"^/wps/",
    r"^/header-portal",
    r"^/home$",
    r"^/mapa-sitio",
    r"^/ley-sector-minero",
    r"^/ley-fatca",
    r"^/facturacion-electronica",
    r"^/documentos-del-sistema-de-gobierno-corporativo",
    r"^/politicas-de-privacidad",
    r"^/terminos-y-condiciones",
    r"^/politicas-de-uso",
    r"^/directorio-seguros-empresas",
    r"^/seguro-medico-internacional-corporate",
    r"^/seguro-salud-empleados",
    r"^/validar-polizas-cumplimiento",
    r"^/blog(/|$)",
    r"^/informes-financieros",  # listado de estados financieros en PDF: no responde dudas de clientes
    r"^/conecta$",  # APIs para desarrolladores, fuera del alcance personas
)

# Clasificación temática por ruta (metadato `seccion` en Gold); la primera coincidencia gana.
SECTION_RULES: Final[tuple[tuple[str, str], ...]] = (
    (r"^/$|^/quienes-somos|^/informes-financieros|^/comunicaciones", "institucional"),
    (
        r"canales-de-atencion|pqrs|defensor-consumidor|sistema-de-atencion|medios-de-pago"
        r"|descargar-soat|directorio|conecta|contingencias",
        "canales_y_servicio",
    ),
    (r"^/arl", "arl"),
    (r"^/clientes-davivienda", "seguros_davivienda"),
    (r"soat|vehiculo|autos|bicicleta", "movilidad"),
    (r"hogar|arrendamiento|mascota|en-casa", "hogar_y_mascotas"),
    (r"vida|renta|tutor|accidentes|tranquilidad|credito|ahorro", "vida_y_ahorro"),
    (r"salud|medico|cancer|coberturas", "salud"),
)
DEFAULT_SECTION: Final[str] = "otros"

# --- Limpieza y chunking -----------------------------------------------------------------
BOILERPLATE_MIN_SHARE: Final[float] = 0.5  # línea en >=50 % de páginas ⇒ boilerplate
MIN_PAGE_CHARS: Final[int] = 200  # páginas más cortas se descartan (vacías o redirecciones)
CHUNK_MAX_CHARS: Final[int] = 1500
CHUNK_OVERLAP_CHARS: Final[int] = 150
CHARS_PER_TOKEN_ES: Final[float] = 3.6  # estimación conservadora para español

# --- LLM -----------------------------------------------------------------------------------
PROVIDERS: Final[tuple[str, ...]] = ("anthropic", "deepseek", "ollama")
LLM_PROVIDER: Final[str] = os.getenv("LLM_PROVIDER", "anthropic")  # anthropic | deepseek | ollama
# DeepSeek cobra solo por tokens y es compatible con LangChain; ventana de 64K tokens (la base cabe).
DEEPSEEK_MODEL: Final[str] = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_CONTEXT_TOKENS: Final[int] = 65_536
ANTHROPIC_MODEL: Final[str] = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")
LLM_MAX_OUTPUT_TOKENS: Final[int] = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "1024"))
OLLAMA_MODEL: Final[str] = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
# Ollama recorta en silencio todo lo que pase de num_ctx (por defecto, unos pocos miles de tokens):
# hay que ampliarlo para que la base completa (~44K tokens) entre en el contexto.
OLLAMA_NUM_CTX: Final[int] = int(os.getenv("OLLAMA_NUM_CTX", "65536"))
CONTEXT_OUTPUT_RESERVE: Final[int] = 4096  # tokens reservados para instrucciones, pregunta y respuesta
# Temperatura 0 (determinismo, Clase 4) SOLO para Ollama: la API de Claude rechaza con 400
# `temperature`/`top_p`/`top_k` en los modelos actuales (Haiku 5.5, Sonnet 5.5, Opus 5.5...).
LLM_TEMPERATURE: Final[float] = 0.0
# En Claude, el razonamiento interno se controla con el esfuerzo (low | medium | high | xhigh | max).
# Para Q&A factual sobre un contexto dado basta "low": menos tokens de razonamiento, más rápido y barato.
ANTHROPIC_EFFORT: Final[str] = os.getenv("ANTHROPIC_EFFORT", "low")
MAX_CONTEXT_TOKENS: Final[int] = int(os.getenv("MAX_CONTEXT_TOKENS", "200000"))
LITE_NUM_CTX: Final[int] = 8192  # ventana de Ollama en los modos de contexto reducido, RAG y agente
LITE_MAX_TOKENS: Final[int] = 2500  # tope de tokens de fragmentos en el modo de contexto reducido

# --- Fase 2 · RAG (embeddings locales con Ollama + Qdrant) -----------------------------------
EMBEDDING_MODEL: Final[str] = os.getenv("EMBEDDING_MODEL", "embeddinggemma:latest")
QDRANT_DIR: Final[Path] = GOLD_DIR / "qdrant"  # índice persistido en disco (ignorado por git)
QDRANT_COLLECTION: Final[str] = "chunks_seguros_bolivar"
RAG_TOP_K: Final[int] = int(os.getenv("RAG_TOP_K", "4"))  # fragmentos recuperados por búsqueda

# --- Visión: foto → seguro sugerido (YOLO; extra opcional `uv sync --extra vision`) ---------
# Pesos fuera de git (*.pt): Ultralytics los descarga la primera vez si no existen.
_yolo_env = Path(os.getenv("YOLO_MODEL_PATH", str(DATA_DIR / "modelos" / "yolo26n.pt")))
YOLO_MODEL_PATH: Final[Path] = _yolo_env if _yolo_env.is_absolute() else PROJECT_ROOT / _yolo_env
YOLO_CONFIDENCE: Final[float] = float(os.getenv("YOLO_CONFIDENCE", "0.35"))  # descarta detecciones dudosas
MAX_IMAGE_BYTES: Final[int] = 8 * 1024 * 1024  # 8 MB por foto
# Privacidad: las personas detectadas no se reportan ni se dibujan (Ley 1581 de 2012).
VISION_IGNORED_CLASSES: Final[frozenset[str]] = frozenset({"person"})
API_URL: Final[str] = os.getenv("SB_API_URL", "http://127.0.0.1:8000")  # cliente HTTP (view/api_client)

# --- RAG: base vectorial (Chroma) y recuperación híbrida -------------------------------------
VECTOR_DIR: Final[Path] = DATA_DIR / "vector"  # Chroma persistente (no versionado)
VECTOR_COLLECTION: Final[str] = "sb_conocimiento"
# ollama: nomic-embed-text local (como en clase) · voyage: API de Voyage AI (recomendada por
# Anthropic, que no tiene embeddings propios) · fake: determinístico para pruebas sin red.
EMBEDDINGS_PROVIDERS: Final[tuple[str, ...]] = ("ollama", "voyage", "fake")
EMBEDDINGS_PROVIDER: Final[str] = os.getenv("EMBEDDINGS_PROVIDER", "ollama")
EMBEDDINGS_MODEL: Final[str] = os.getenv("EMBEDDINGS_MODEL", "nomic-embed-text")
VOYAGE_MODEL: Final[str] = os.getenv("VOYAGE_MODEL", "voyage-multilingual-2")
RAG_K: Final[int] = int(os.getenv("RAG_K", "6"))
RRF_K: Final[int] = 60  # constante de Reciprocal Rank Fusion (Cormack et al., 2009)

# --- Agente: memoria persistente y trazas -----------------------------------------------------
MEMORY_DB: Final[Path] = DATA_DIR / "memoria" / "checkpoints.sqlite"
MEMORY_MAX_MESSAGES: Final[int] = 20  # mensajes del historial que el agente relee por turno
LANGSMITH_PROJECT: Final[str] = os.getenv("LANGSMITH_PROJECT", "sb-asistente")

# --- Recomendador (curso de Gestión) -------------------------------------------------------
# Carpeta propia para no mezclar las tablas sintéticas con el HTML de Bronze (data/raw).
RECO_DIR: Final[Path] = DATA_DIR / "recomendador"
RECO_N_CLIENTES: Final[int] = 20_000
RECO_SEMILLA: Final[int] = 42
RECO_K: Final[int] = 5
RECO_SEGMENTO: Final[tuple[str, ...]] = ("vehiculo", "vivienda", "tiene_mascota", "tiene_credito")
RECO_MODELO_BASE: Final[str] = "intfloat/multilingual-e5-small"

EVAL_QUESTIONS: Final[Path] = PROJECT_ROOT / "evaluacion" / "preguntas.yaml"
EVAL_RESULTS: Final[Path] = PROJECT_ROOT / "evaluacion" / "resultados.csv"


def compile_patterns(patterns: tuple[str, ...]) -> list[re.Pattern[str]]:
    """Compila una tupla de expresiones regulares."""
    return [re.compile(p) for p in patterns]

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
LLM_PROVIDER: Final[str] = os.getenv("LLM_PROVIDER", "anthropic")  # anthropic | ollama
ANTHROPIC_MODEL: Final[str] = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")
LLM_MAX_OUTPUT_TOKENS: Final[int] = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "1024"))
OLLAMA_MODEL: Final[str] = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
# Ollama recorta en silencio todo lo que pase de num_ctx (por defecto, unos pocos miles de tokens):
# hay que ampliarlo para que la base completa (~44K tokens) entre en el contexto.
OLLAMA_NUM_CTX: Final[int] = int(os.getenv("OLLAMA_NUM_CTX", "65536"))
CONTEXT_OUTPUT_RESERVE: Final[int] = 4096  # tokens reservados para instrucciones, pregunta y respuesta
LLM_TEMPERATURE: Final[float] = 0.0  # tareas factuales: determinismo (Clase 4)
MAX_CONTEXT_TOKENS: Final[int] = int(os.getenv("MAX_CONTEXT_TOKENS", "200000"))

EVAL_QUESTIONS: Final[Path] = PROJECT_ROOT / "evaluacion" / "preguntas.yaml"
EVAL_RESULTS: Final[Path] = PROJECT_ROOT / "evaluacion" / "resultados.csv"


def compile_patterns(patterns: tuple[str, ...]) -> list[re.Pattern[str]]:
    """Compila una tupla de expresiones regulares."""
    return [re.compile(p) for p in patterns]

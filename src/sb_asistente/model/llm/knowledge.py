"""Acceso a la base de conocimiento de Gold que usan todos los modos de Q&A.

- ``load_knowledge``: el Markdown consolidado completo (modo «completo», Resumen y FAQ), validando
  que quepa en la ventana de contexto.
- ``load_chunks``: los fragmentos de ``chunks.jsonl`` (modos «reducido», «rag» y «agente»).
- ``channels_block``: el bloque de canales de atención, que los modos con contexto recuperado
  anteponen siempre porque responde muchas preguntas de servicio.
"""

import json
import re
from pathlib import Path

from sb_asistente.config import CHUNKS_JSONL, KNOWLEDGE_MD, MAX_CONTEXT_TOKENS
from sb_asistente.model.processing.gold import estimate_tokens

PIPELINE_HINT = "Ejecute primero el pipeline: uv run python scripts/scrape_empresa.py (o make data)"


class KnowledgeTooLargeError(ValueError):
    """El conocimiento consolidado no cabe en el presupuesto de contexto configurado."""


def _require(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"No existe {path}. {PIPELINE_HINT}")


def read_knowledge(path: Path = KNOWLEDGE_MD) -> str:
    """Lee el conocimiento consolidado sin validar su tamaño."""
    _require(path)
    return path.read_text(encoding="utf-8")


def load_knowledge(path: Path = KNOWLEDGE_MD, max_tokens: int = MAX_CONTEXT_TOKENS) -> str:
    """Carga el conocimiento consolidado y valida que quepa en el presupuesto de contexto."""
    text = read_knowledge(path)
    tokens = estimate_tokens(text)
    if tokens > max_tokens:
        raise KnowledgeTooLargeError(
            f"El conocimiento tiene ~{tokens:,} tokens y el límite es {max_tokens:,}. "
            "Reduzca el alcance o aumente MAX_CONTEXT_TOKENS."
        )
    return text


def load_chunks(path: Path = CHUNKS_JSONL) -> list[dict[str, object]]:
    """Lee ``chunks.jsonl`` de Gold."""
    _require(path)
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def channels_block(knowledge: str) -> str:
    """Extrae el bloque de canales de atención (pie de página) del conocimiento consolidado.

    Ese bloque se quita de cada página como boilerplate y queda una sola vez al inicio de la base.
    """
    match = re.search(r"^## Canales de atención.*?(?=^## |\Z)", knowledge, flags=re.MULTILINE | re.DOTALL)
    return match.group(0).strip() + "\n" if match else ""


def load_channels(path: Path = KNOWLEDGE_MD) -> str:
    """Bloque de canales de atención leído del conocimiento consolidado."""
    return channels_block(read_knowledge(path))

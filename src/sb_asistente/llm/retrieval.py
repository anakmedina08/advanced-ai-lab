"""Contexto reducido para modelos locales: elige los chunks de Gold más parecidos a la pregunta.

La Fase 1 envía **toda** la base en el *system prompt* (Claude lo resuelve en segundos). En un
modelo local sobre CPU (Ollama) eso tarda decenas de minutos, así que este modo selecciona solo los
fragmentos con más palabras en común con la pregunta. Cada fragmento conserva su URL para que la
respuesta pueda citar la fuente. Es un adelanto sencillo (por palabras, sin embeddings) del RAG de la
Fase 2.
"""

import json
import re
import unicodedata
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

from sb_asistente.config import CHUNKS_JSONL

STOPWORDS = frozenset(
    [
        "a",
        "al",
        "como",
        "con",
        "cual",
        "cuales",
        "cuando",
        "de",
        "del",
        "el",
        "en",
        "es",
        "esta",
        "este",
        "la",
        "las",
        "lo",
        "los",
        "me",
        "mi",
        "mis",
        "o",
        "para",
        "por",
        "que",
        "se",
        "si",
        "su",
        "sus",
        "un",
        "una",
        "uno",
        "y",
        "yo",
        "tengo",
        "tiene",
        "puedo",
        "hay",
        "donde",
        "cuanto",
        "cuanta",
        "cuantos",
        "ser",
        "son",
    ]
)


def normalize_words(text: str) -> list[str]:
    """Minúsculas, sin tildes y sin palabras vacías."""
    plain = unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()
    return [w for w in re.findall(r"[a-z0-9]+", plain) if w not in STOPWORDS and len(w) > 1]


def load_chunks(path: Path = CHUNKS_JSONL) -> list[dict[str, object]]:
    """Lee ``chunks.jsonl`` de Gold."""
    if not path.is_file():
        raise FileNotFoundError(f"No existe {path}. Ejecute: uv run python scripts/scrape_empresa.py")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def score(question_words: Iterable[str], chunk: dict[str, object]) -> int:
    """Cuántas palabras de la pregunta aparecen en el título, la ruta o el texto del chunk."""
    words = Counter(normalize_words(f"{chunk['title']} {chunk.get('breadcrumb', '')} {chunk['text']}"))
    return sum(1 for w in set(question_words) if words[w])


def select_context(question: str, chunks: list[dict[str, object]], max_tokens: int = 2500) -> str:
    """Arma un contexto con los chunks más relevantes, sin pasar de ``max_tokens``.

    Returns:
        Markdown con un bloque por chunk (título, ``Fuente: URL`` y texto), o cadena vacía si
        ninguna palabra coincide.

    """
    if max_tokens <= 0:
        raise ValueError("max_tokens debe ser positivo.")
    q = normalize_words(question)
    ranked = sorted(((score(q, c), i, c) for i, c in enumerate(chunks)), key=lambda t: (-t[0], t[1]))
    parts: list[str] = []
    used = 0
    for points, _, chunk in ranked:
        tokens = int(chunk.get("tokens_est", 0))
        if points == 0 or used + tokens > max_tokens:
            continue
        parts.append(f"### {chunk['title']}\nFuente: {chunk['url']}\n\n{chunk['text']}\n")
        used += tokens
    return "\n".join(parts)


def channels_block(knowledge: str) -> str:
    """Extrae el bloque de canales de atención (pie de página) del conocimiento consolidado.

    Ese bloque se quita de cada página como boilerplate y queda una sola vez al inicio de la base;
    en el modo reducido se agrega siempre porque es la respuesta a muchas preguntas de servicio.
    """
    match = re.search(r"^## Canales de atención.*?(?=^## |\Z)", knowledge, flags=re.MULTILINE | re.DOTALL)
    return match.group(0).strip() + "\n" if match else ""

"""Fragmentos que alimentan el RAG: los ``chunks.jsonl`` de Gold más el bloque de canales.

El pie de página del sitio (WhatsApp, línea nacional, #322, sede, Defensor del Consumidor) se
quita de cada página como texto repetido y queda una sola vez en el conocimiento consolidado.
Sin este fragmento extra, la búsqueda no encontraría las respuestas de servicio más pedidas.
"""

from pathlib import Path

from sb_asistente.config import CHUNKS_JSONL, KNOWLEDGE_MD
from sb_asistente.model.llm.retrieval import channels_block, load_chunks
from sb_asistente.model.processing.gold import estimate_tokens

CANALES_ID = "canales-pie-de-pagina#000"


def fragmento_canales(knowledge_path: Path = KNOWLEDGE_MD) -> dict[str, object] | None:
    """Bloque de canales como fragmento citado a la portada del sitio, si existe."""
    if not knowledge_path.is_file():
        return None
    bloque = channels_block(knowledge_path.read_text(encoding="utf-8"))
    if not bloque:
        return None
    texto = "\n".join(line for line in bloque.splitlines()[1:] if not line.startswith("Fuente:")).strip()
    inicio = texto.upper().find("CANALES DE ATENCI")  # descarta el menú del pie y deja los canales
    texto = texto[inicio:] if inicio > 0 else texto
    return {
        "chunk_id": CANALES_ID,
        "doc_id": "canales-pie-de-pagina",
        "url": "https://www.segurosbolivar.com/",
        "title": "Canales de atención (pie de página del sitio)",
        "section": "canales_y_servicio",
        "breadcrumb": "Canales de atención",
        "text": texto,
        "tokens_est": estimate_tokens(texto),
    }


def fragmentos_rag(
    chunks_path: Path = CHUNKS_JSONL, knowledge_path: Path = KNOWLEDGE_MD
) -> list[dict[str, object]]:
    """Fragmentos Gold + canales (sin duplicar si ya estuviera)."""
    chunks = load_chunks(chunks_path)
    canales = fragmento_canales(knowledge_path)
    if canales and all(c["chunk_id"] != CANALES_ID for c in chunks):
        chunks.append(canales)
    return chunks

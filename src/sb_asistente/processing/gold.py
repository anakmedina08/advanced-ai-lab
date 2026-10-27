"""Etapa 4 · Silver → Gold: Markdown enriquecido, corpus.jsonl, chunks y conocimiento consolidado.

- Un ``.md`` por página con metadatos (front-matter YAML): url, sección, fecha, hash.
- ``corpus.jsonl``: una línea por documento (insumo del RAG en la Fase 2).
- ``chunks.jsonl``: fragmentos por encabezado (##) con tope de tamaño y solapamiento.
- ``conocimiento_seguros_bolivar.md``: TODO el texto limpio, agrupado por sección, que
  va completo en el *system prompt* de la Fase 1 (requisito de la actividad).
"""

import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from sb_asistente.config import (
    CHARS_PER_TOKEN_ES,
    CHUNK_MAX_CHARS,
    CHUNK_OVERLAP_CHARS,
    DEFAULT_SECTION,
    SECTION_RULES,
)
from sb_asistente.scraping.discover import path_of

SECTION_TITLES: dict[str, str] = {
    "institucional": "Información institucional",
    "canales_y_servicio": "Canales de atención y servicio al cliente",
    "movilidad": "Seguros de movilidad (SOAT y vehículos)",
    "hogar_y_mascotas": "Seguros de hogar, arrendamiento y mascotas",
    "vida_y_ahorro": "Seguros de vida, accidentes y ahorro",
    "salud": "Seguros de salud",
    "arl": "ARL Seguros Bolívar",
    "seguros_davivienda": "Seguros para clientes Davivienda",
    "otros": "Otros temas",
}
SECTION_ORDER = list(SECTION_TITLES)


@dataclass(slots=True)
class GoldDoc:
    """Documento de la capa Gold."""

    doc_id: str
    url: str
    title: str
    description: str
    section: str
    fetched_at: str
    sha256: str
    text: str

    @property
    def tokens(self) -> int:
        """Estimación de tokens del texto."""
        return estimate_tokens(self.text)


def estimate_tokens(text: str) -> int:
    """Estimación de tokens para español (≈ 3,6 caracteres por token)."""
    return int(len(text) / CHARS_PER_TOKEN_ES) + 1 if text else 0


def classify_section(url: str, rules: Iterable[tuple[str, str]] = SECTION_RULES) -> str:
    """Asigna la sección temática según la ruta; la primera regla que coincide gana."""
    path = path_of(url)
    for pattern, section in rules:
        if re.search(pattern, path):
            return section
    return DEFAULT_SECTION


def text_hash(text: str) -> str:
    """Huella del contenido normalizado (para deduplicar páginas idénticas)."""
    return hashlib.sha256(re.sub(r"\s+", " ", text).strip().lower().encode()).hexdigest()


def dedupe_docs(docs: Iterable[GoldDoc]) -> tuple[list[GoldDoc], list[str]]:
    """Quita documentos con texto idéntico; conserva el primero. Devuelve también las URLs omitidas."""
    seen: set[str] = set()
    kept: list[GoldDoc] = []
    dropped: list[str] = []
    for doc in docs:
        key = text_hash(doc.text)
        if key in seen:
            dropped.append(doc.url)
        else:
            seen.add(key)
            kept.append(doc)
    return kept, dropped


def to_markdown(doc: GoldDoc) -> str:
    """Markdown con front-matter YAML de metadatos."""
    meta = {
        "doc_id": doc.doc_id,
        "url": doc.url,
        "title": doc.title,
        "description": doc.description,
        "section": doc.section,
        "fetched_at": doc.fetched_at,
        "sha256": doc.sha256,
        "tokens_est": doc.tokens,
    }
    front = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False).strip()
    body = doc.text if doc.text.lstrip().startswith("#") else f"# {doc.title}\n\n{doc.text}"
    return f"---\n{front}\n---\n\n{body}\n"


def chunk_doc(
    doc: GoldDoc, max_chars: int = CHUNK_MAX_CHARS, overlap: int = CHUNK_OVERLAP_CHARS
) -> list[dict[str, object]]:
    """Divide por encabezados y luego por tamaño; cada chunk lleva sus metadatos y su ruta."""
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")], strip_headers=False
    )
    size_splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_chars, chunk_overlap=overlap, separators=["\n\n", "\n", ". ", " ", ""]
    )
    pieces = size_splitter.split_documents(header_splitter.split_text(doc.text))
    chunks = []
    for i, piece in enumerate(pieces):
        content = piece.page_content.strip()
        if not content:
            continue
        breadcrumb = " > ".join(v for k, v in sorted(piece.metadata.items()) if k.startswith("h"))
        chunks.append(
            {
                "chunk_id": f"{doc.doc_id}#{i:03d}",
                "doc_id": doc.doc_id,
                "url": doc.url,
                "title": doc.title,
                "section": doc.section,
                "breadcrumb": breadcrumb,
                "text": content,
                "tokens_est": estimate_tokens(content),
            }
        )
    return chunks


def build_knowledge(docs: Iterable[GoldDoc], channels_text: str = "") -> str:
    """Consolida todo el conocimiento en un solo Markdown ordenado por sección.

    Cada página queda marcada con su título y su URL para que el LLM pueda citar la fuente.
    """
    by_section: dict[str, list[GoldDoc]] = {}
    for doc in docs:
        by_section.setdefault(doc.section, []).append(doc)
    parts = ["# Base de conocimiento · Seguros Bolívar (información pública)\n"]
    if channels_text:
        parts.append(
            "## Canales de atención (pie de página del sitio oficial)\n"
            f"Fuente: https://www.segurosbolivar.com/\n\n{channels_text}\n"
        )
    for section in SECTION_ORDER:
        if section not in by_section:
            continue
        parts.append(f"## {SECTION_TITLES[section]}\n")
        for doc in sorted(by_section[section], key=lambda d: d.url):
            body = re.sub(r"^#+\s*", "", doc.text, flags=re.MULTILINE)  # aplana títulos internos
            parts.append(f"### {doc.title}\nFuente: {doc.url}\n\n{body}\n")
    return "\n".join(parts).strip() + "\n"


def write_gold(docs: list[GoldDoc], gold_dir: Path, channels_text: str = "") -> dict[str, object]:
    """Escribe toda la capa Gold y devuelve un resumen con conteos y tokens."""
    pages_dir = gold_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    chunks: list[dict[str, object]] = []
    with (gold_dir / "corpus.jsonl").open("w", encoding="utf-8") as corpus:
        for doc in docs:
            (pages_dir / f"{doc.doc_id}.md").write_text(to_markdown(doc), encoding="utf-8")
            corpus.write(json.dumps(asdict(doc) | {"tokens_est": doc.tokens}, ensure_ascii=False) + "\n")
            chunks.extend(chunk_doc(doc))
    with (gold_dir / "chunks.jsonl").open("w", encoding="utf-8") as fh:
        for chunk in chunks:
            fh.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    knowledge = build_knowledge(docs, channels_text)
    (gold_dir / "conocimiento_seguros_bolivar.md").write_text(knowledge, encoding="utf-8")
    sections: dict[str, int] = {}
    for doc in docs:
        sections[doc.section] = sections.get(doc.section, 0) + 1
    summary = {
        "documentos": len(docs),
        "chunks": len(chunks),
        "tokens_conocimiento_est": estimate_tokens(knowledge),
        "documentos_por_seccion": dict(sorted(sections.items())),
    }
    (gold_dir / "resumen.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary

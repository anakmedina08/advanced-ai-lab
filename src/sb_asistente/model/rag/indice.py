"""Base vectorial persistente con Chroma sobre los fragmentos Gold (``chunks.jsonl``).

Cada fragmento se guarda con su ``chunk_id`` como identificador, así reindexar actualiza en vez
de duplicar. Junto al índice se escribe ``indice.json`` con el proveedor y el modelo de
embeddings: consultar con otro modelo daría distancias sin sentido, por eso se valida al abrir.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document

from sb_asistente.config import EMBEDDINGS_PROVIDER, VECTOR_COLLECTION, VECTOR_DIR
from sb_asistente.model.rag.embeddings import build_embeddings, model_name

LOTE = 128
METADATOS = ("chunk_id", "doc_id", "url", "title", "section", "breadcrumb")


class IndiceError(RuntimeError):
    """El índice no existe o fue creado con otros embeddings."""


@dataclass(frozen=True, slots=True)
class InfoIndice:
    """Lo que se sabe del índice persistido."""

    proveedor: str
    modelo: str
    fragmentos: int


def a_documento(chunk: dict[str, object]) -> Document:
    """Convierte un fragmento Gold en ``Document`` (texto con su título para mejor recuperación)."""
    texto = f"{chunk['title']}\n{chunk.get('breadcrumb') or ''}\n\n{chunk['text']}".strip()
    return Document(
        page_content=texto,
        metadata={k: str(chunk.get(k) or "") for k in METADATOS},
        id=str(chunk["chunk_id"]),
    )


def _info_path(directorio: Path) -> Path:
    return directorio / "indice.json"


def leer_info(directorio: Path = VECTOR_DIR) -> InfoIndice | None:
    """Metadatos del índice, o ``None`` si aún no existe."""
    ruta = _info_path(directorio)
    if not ruta.is_file():
        return None
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return InfoIndice(datos["proveedor"], datos["modelo"], int(datos["fragmentos"]))


def abrir(proveedor: str = EMBEDDINGS_PROVIDER, directorio: Path = VECTOR_DIR) -> Chroma:
    """Abre el índice persistido validando que use los mismos embeddings."""
    info = leer_info(directorio)
    if info is None:
        raise IndiceError(f"No hay índice en {directorio}. Ejecute: uv run sb rag indexar")
    if (info.proveedor, info.modelo) != (proveedor, model_name(proveedor)):
        raise IndiceError(
            f"El índice usa {info.proveedor}/{info.modelo} y se pidió {proveedor}/{model_name(proveedor)}. "
            "Reindexe con: uv run sb rag indexar --reset"
        )
    return Chroma(
        collection_name=VECTOR_COLLECTION,
        embedding_function=build_embeddings(proveedor),
        persist_directory=str(directorio),
    )


def indexar(
    chunks: list[dict[str, object]],
    proveedor: str = EMBEDDINGS_PROVIDER,
    directorio: Path = VECTOR_DIR,
    reset: bool = False,
) -> InfoIndice:
    """Indexa (o actualiza) los fragmentos en Chroma y guarda ``indice.json``."""
    if not chunks:
        raise ValueError("No hay fragmentos para indexar: ejecute antes `make data` o `make process`.")
    directorio.mkdir(parents=True, exist_ok=True)
    tienda = Chroma(
        collection_name=VECTOR_COLLECTION,
        embedding_function=build_embeddings(proveedor),
        persist_directory=str(directorio),
    )
    previa = leer_info(directorio)
    cambia_modelo = previa is not None and (previa.proveedor, previa.modelo) != (
        proveedor,
        model_name(proveedor),
    )
    if reset or cambia_modelo:
        tienda.reset_collection()
    documentos = [a_documento(c) for c in chunks]
    for inicio in range(0, len(documentos), LOTE):
        lote = documentos[inicio : inicio + LOTE]
        tienda.add_documents(lote, ids=[d.id for d in lote])
    info = InfoIndice(proveedor, model_name(proveedor), tienda._collection.count())  # noqa: SLF001
    _info_path(directorio).write_text(
        json.dumps(
            {"proveedor": info.proveedor, "modelo": info.modelo, "fragmentos": info.fragmentos}, indent=2
        ),
        encoding="utf-8",
    )
    return info

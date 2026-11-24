"""Dobles compartidos por las pruebas del corpus de mercado (SPEC-069): chunks Gold mínimos."""


def chunk_mercado(ident: str, aseguradora: str, seccion: str, texto: str) -> dict[str, object]:
    """Chunk Gold mínimo del corpus de mercado; ``ident`` es ``<doc>#<n>`` y la URL sale del doc."""
    doc = ident.split("#")[0]
    return {
        "chunk_id": ident,
        "doc_id": doc,
        "url": f"https://{aseguradora}.co/{doc}",
        "title": f"Página {ident}",
        "section": seccion,
        "breadcrumb": "",
        "text": texto,
        "aseguradora": aseguradora,
    }

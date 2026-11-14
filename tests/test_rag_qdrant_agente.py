"""Pruebas del RAG híbrido del agente sobre Qdrant (en memoria, embeddings falsos, sin red)."""

import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding

from sb_asistente.controller import agente
from sb_asistente.model.llm import vector_store
from sb_asistente.model.rag.hibrido import RecuperadorHibrido
from sb_asistente.model.rag.qdrant import BuscadorQdrant, filtro_payload

CHUNKS = [
    {
        "chunk_id": "soat#0",
        "url": "https://www.segurosbolivar.com/soat",
        "title": "SOAT",
        "section": "movilidad",
        "breadcrumb": "",
        "text": "El SOAT cubre gastos médicos por accidentes de tránsito.",
    },
    {
        "chunk_id": "hogar#0",
        "url": "https://www.segurosbolivar.com/hogar",
        "title": "Hogar",
        "section": "hogar_y_mascotas",
        "breadcrumb": "",
        "text": "El seguro de hogar cubre incendio, inundación y robo.",
    },
    {
        "chunk_id": "canales#0",
        "url": "https://www.segurosbolivar.com/canales",
        "title": "Canales",
        "section": "canales_y_servicio",
        "breadcrumb": "",
        "text": "WhatsApp de atención y línea #322.",
    },
]


@pytest.fixture
def buscador() -> BuscadorQdrant:
    cliente = vector_store.open_client()  # Qdrant en memoria
    store = vector_store.build_index(
        CHUNKS, DeterministicFakeEmbedding(size=16), cliente, collection="prueba"
    )
    return BuscadorQdrant(store)


def test_filtro_payload_apunta_a_los_metadatos():
    # Act
    filtro = filtro_payload({"section": "movilidad"})
    # Assert
    assert filtro.must[0].key == "metadata.section"
    assert filtro.must[0].match.value == "movilidad"


def test_sin_filtro_no_se_construye_condicion():
    # Assert
    assert filtro_payload(None) is None


def test_busqueda_con_filtro_solo_devuelve_esa_seccion(buscador):
    # Act
    docs = buscador.similarity_search("cobertura", k=3, filter={"section": "movilidad"})
    # Assert
    assert [d.metadata["chunk_id"] for d in docs] == ["soat#0"]


def test_documentos_conservan_url_y_chunk_id_para_citar(buscador):
    # Act
    docs = buscador.similarity_search("seguro", k=3)
    # Assert
    assert all(d.metadata["url"].startswith("https://www.segurosbolivar.com/") for d in docs)
    assert {d.metadata["chunk_id"] for d in docs} == {"soat#0", "hogar#0", "canales#0"}


def test_hibrido_fusiona_bm25_y_qdrant(buscador):
    # Arrange
    recuperador = RecuperadorHibrido(CHUNKS, buscador)
    # Act
    fragmentos = recuperador.buscar("SOAT accidentes", k=2)
    # Assert
    assert fragmentos[0].chunk_id == "soat#0"
    assert "bm25" in fragmentos[0].origen


def test_si_la_base_vectorial_falla_sigue_con_bm25():
    # Arrange
    class Caida:
        def similarity_search(self, query, k=4, filter=None):  # noqa: A002
            raise ConnectionError("Ollama apagado")

    recuperador = RecuperadorHibrido(CHUNKS, Caida())
    # Act
    fragmentos = recuperador.buscar("WhatsApp", k=1)
    # Assert
    assert fragmentos[0].chunk_id == "canales#0"
    assert fragmentos[0].origen == ("bm25",)


def test_recuperador_por_defecto_prefiere_qdrant(monkeypatch, tmp_path):
    # Arrange
    monkeypatch.setattr(agente, "fragmentos_rag", lambda _ruta: CHUNKS)
    monkeypatch.setattr(agente, "_qdrant", lambda *_: object())
    # Act
    _, modo = agente.recuperador_por_defecto(tmp_path / "chunks.jsonl", tmp_path / "qdrant")
    # Assert
    assert modo == "híbrido (BM25 + Qdrant)"


def test_sin_qdrant_ni_chroma_queda_solo_bm25(monkeypatch, tmp_path):
    # Arrange
    def sin_qdrant(*_):
        raise RuntimeError("sin Ollama")

    def sin_chroma():
        raise agente.indice.IndiceError("sin índice")

    monkeypatch.setattr(agente, "fragmentos_rag", lambda _ruta: CHUNKS)
    monkeypatch.setattr(agente, "_qdrant", sin_qdrant)
    monkeypatch.setattr(agente.indice, "abrir", sin_chroma)
    # Act
    _, modo = agente.recuperador_por_defecto(tmp_path / "chunks.jsonl", tmp_path / "qdrant")
    # Assert
    assert modo.startswith("solo BM25")


def test_coleccion_extra_compite_en_el_ranking_sin_tocar_la_principal():
    # Arrange
    embeddings = DeterministicFakeEmbedding(size=16)
    principal = vector_store.build_index(CHUNKS[:1], embeddings, vector_store.open_client(), collection="p")
    extra = vector_store.build_index(CHUNKS[1:], embeddings, vector_store.open_client(), collection="demo")
    buscador = BuscadorQdrant(principal, extra)
    # Act
    ids = {d.metadata["chunk_id"] for d in buscador.similarity_search("seguro", k=3)}
    # Assert
    assert ids == {"soat#0", "hogar#0", "canales#0"}
    assert principal.client.count(principal.collection_name).count == 1

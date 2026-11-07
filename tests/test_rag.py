"""Pruebas del RAG: índice Chroma persistente y recuperación híbrida (embeddings falsos, sin red)."""

import pytest

from sb_asistente.model.rag import indice
from sb_asistente.model.rag.embeddings import build_embeddings, model_name
from sb_asistente.model.rag.hibrido import RecuperadorHibrido, como_contexto

CHUNKS = [
    {
        "chunk_id": "canales#000",
        "doc_id": "canales",
        "url": "https://www.segurosbolivar.com/canales",
        "title": "Canales de atención",
        "section": "canales_y_servicio",
        "breadcrumb": "Contacto",
        "text": "Escríbanos por WhatsApp o marque #322 desde su celular para atención las 24 horas.",
    },
    {
        "chunk_id": "soat#000",
        "doc_id": "soat",
        "url": "https://www.segurosbolivar.com/soat",
        "title": "SOAT",
        "section": "movilidad",
        "breadcrumb": "Movilidad",
        "text": "El SOAT cubre gastos médicos de las víctimas de accidentes de tránsito.",
    },
    {
        "chunk_id": "hogar#000",
        "doc_id": "hogar",
        "url": "https://www.segurosbolivar.com/hogar",
        "title": "Seguro de hogar",
        "section": "hogar_y_mascotas",
        "breadcrumb": "Hogar",
        "text": "El seguro de hogar protege la vivienda y sus contenidos ante incendio y terremoto.",
    },
]


@pytest.fixture
def indexado(tmp_path):
    info = indice.indexar(CHUNKS, "fake", tmp_path)
    return tmp_path, info


def test_indexar_guarda_todos_los_fragmentos(indexado):
    _, info = indexado
    assert info.fragmentos == 3 and info.proveedor == "fake"


def test_reindexar_no_duplica(indexado):
    directorio, _ = indexado
    assert indice.indexar(CHUNKS, "fake", directorio).fragmentos == 3


def test_reset_vacia_antes_de_indexar(indexado):
    directorio, _ = indexado
    assert indice.indexar(CHUNKS[:1], "fake", directorio, reset=True).fragmentos == 1


def test_indexar_sin_fragmentos_falla(tmp_path):
    with pytest.raises(ValueError):
        indice.indexar([], "fake", tmp_path)


def test_abrir_sin_indice_falla(tmp_path):
    with pytest.raises(indice.IndiceError, match="sb rag indexar"):
        indice.abrir("fake", tmp_path)


def test_abrir_con_otros_embeddings_falla(indexado):
    directorio, _ = indexado
    with pytest.raises(indice.IndiceError, match="Reindexe"):
        indice.abrir("ollama", directorio)


def test_metadatos_y_id_del_documento():
    doc = indice.a_documento(CHUNKS[0])
    assert doc.id == "canales#000" and doc.metadata["url"].endswith("/canales")


def test_busqueda_hibrida_encuentra_termino_literal(indexado):
    directorio, _ = indexado
    recuperador = RecuperadorHibrido(CHUNKS, indice.abrir("fake", directorio))
    fragmentos = recuperador.buscar("¿Cuál es el #322 o el WhatsApp?", k=2)
    assert fragmentos[0].chunk_id == "canales#000" and "bm25" in fragmentos[0].origen


def test_busqueda_combina_ambas_fuentes(indexado):
    directorio, _ = indexado
    recuperador = RecuperadorHibrido(CHUNKS, indice.abrir("fake", directorio))
    origenes = {o for f in recuperador.buscar("seguro de hogar terremoto", k=3) for o in f.origen}
    assert origenes == {"bm25", "vector"}


def test_filtro_por_seccion(indexado):
    directorio, _ = indexado
    recuperador = RecuperadorHibrido(CHUNKS, indice.abrir("fake", directorio))
    assert {f.seccion for f in recuperador.buscar("seguro", k=3, seccion="movilidad")} == {"movilidad"}


def test_solo_bm25_sin_vectorial():
    fragmentos = RecuperadorHibrido(CHUNKS).buscar("SOAT accidentes", k=1)
    assert fragmentos[0].chunk_id == "soat#000" and fragmentos[0].origen == ("bm25",)


def test_puntajes_ordenados_de_mayor_a_menor(indexado):
    directorio, _ = indexado
    puntajes = [
        f.puntaje for f in RecuperadorHibrido(CHUNKS, indice.abrir("fake", directorio)).buscar("seguro", k=3)
    ]
    assert puntajes == sorted(puntajes, reverse=True)


@pytest.mark.parametrize(("consulta", "k"), [("  ", 3), ("seguro", 0), ("seguro", 21)])
def test_parametros_invalidos(consulta, k):
    with pytest.raises(ValueError):
        RecuperadorHibrido(CHUNKS).buscar(consulta, k=k)


def test_sin_fragmentos_falla():
    with pytest.raises(ValueError):
        RecuperadorHibrido([])


def test_contexto_incluye_fuente():
    contexto = como_contexto(RecuperadorHibrido(CHUNKS).buscar("SOAT", k=1))
    assert "Fuente: https://www.segurosbolivar.com/soat" in contexto


def test_embeddings_falsos_son_deterministicos():
    emb = build_embeddings("fake")
    assert emb.embed_query("hola") == emb.embed_query("hola") and model_name("fake") == "deterministic-256"


def test_proveedor_de_embeddings_desconocido():
    with pytest.raises(ValueError):
        build_embeddings("openai")


def test_bm25_con_corpus_minimo_no_pierde_coincidencias():
    dos = CHUNKS[:2]
    assert RecuperadorHibrido(dos).buscar("WhatsApp", k=1)[0].chunk_id == "canales#000"


def test_hit_at_k_con_banco_minimo():
    from sb_asistente.model.evaluation import EvalQuestion
    from sb_asistente.model.rag.evaluacion import hit_at_k

    banco = [
        EvalQuestion("C1", "canales", "¿Cuál es el WhatsApp?", ["#322"]),
        EvalQuestion("P1", "productos", "¿Qué cubre el SOAT?", ["inexistente"]),
        EvalQuestion("F1", "fuera", "¿Quién ganó el mundial?", [], fuera_de_alcance=True),
    ]
    r = hit_at_k(RecuperadorHibrido(CHUNKS), banco, k=2)
    assert (r.aciertos, r.total, r.fallos) == (1, 2, ("P1",)) and r.tasa == 0.5


def test_fragmento_de_canales_se_agrega(tmp_path):
    import json

    from sb_asistente.model.rag.fuentes import CANALES_ID, fragmentos_rag

    (tmp_path / "chunks.jsonl").write_text(json.dumps(CHUNKS[1], ensure_ascii=False) + "\n", encoding="utf-8")
    (tmp_path / "k.md").write_text(
        "# Base\n## Canales de atención (pie)\nFuente: https://www.segurosbolivar.com/\n\n"
        "Menú\nCANALES DE ATENCIÓN\nWhatsApp: 322 332 2322\n## Movilidad\nx\n",
        encoding="utf-8",
    )
    chunks = fragmentos_rag(tmp_path / "chunks.jsonl", tmp_path / "k.md")
    canales = next(c for c in chunks if c["chunk_id"] == CANALES_ID)
    assert canales["text"].startswith("CANALES DE ATENCIÓN") and "Menú" not in canales["text"]


def test_sin_conocimiento_no_agrega_canales(tmp_path):
    import json

    from sb_asistente.model.rag.fuentes import fragmentos_rag

    (tmp_path / "chunks.jsonl").write_text(json.dumps(CHUNKS[1], ensure_ascii=False) + "\n", encoding="utf-8")
    assert len(fragmentos_rag(tmp_path / "chunks.jsonl", tmp_path / "no.md")) == 1

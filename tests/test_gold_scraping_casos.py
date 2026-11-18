"""Casos tabulados de descubrimiento, alcance y capa Gold (SPEC-065).

El alcance (qué URLs se capturan) y la sección de cada página definen qué puede responder el
asistente; se fijan con rutas reales del sitio público.
"""

import pytest
import yaml

from sb_asistente.model.processing.gold import (
    SECTION_ORDER,
    SECTION_TITLES,
    GoldDoc,
    build_knowledge,
    chunk_doc,
    classify_section,
    dedupe_docs,
    estimate_tokens,
    text_hash,
    to_markdown,
)
from sb_asistente.model.scraping.discover import (
    SitemapEntry,
    build_robots,
    in_scope,
    parse_sitemap,
    path_of,
    select_urls,
)
from sb_asistente.model.scraping.fetch import slugify_path

BASE = "https://www.segurosbolivar.com"

# --- path_of ------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("url", "ruta"),
    [
        (f"{BASE}", "/"),
        (f"{BASE}/", "/"),
        (f"{BASE}/soat", "/soat"),
        (f"{BASE}/soat/", "/soat"),
        (f"{BASE}/a/b/", "/a/b"),
        (f"{BASE}/soat?x=1", "/soat"),
        (f"{BASE}/soat#coberturas", "/soat"),
    ],
)
def test_path_of(url, ruta):
    # Arrange
    # Act
    resultado = path_of(url)
    # Assert
    assert resultado == ruta


# --- in_scope -----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "ruta",
    [
        "/",
        "/soat",
        "/seguro-de-hogar",
        "/seguro-de-vida",
        "/arl",
        "/canales-de-atencion",
        "/empresas-de-familia",  # «empresas» solo excluye la carpeta exacta
        "/blogger",
        "/conecta-con-nosotros",
    ],
)
def test_rutas_de_personas_y_canales_estan_en_alcance(ruta):
    # Arrange
    # Act
    resultado = in_scope(f"{BASE}{ruta}")
    # Assert
    assert resultado is True


@pytest.mark.parametrize(
    "ruta",
    [
        "/empresas",
        "/empresas/pymes",
        "/proveedores",
        "/reaseguradores-x",
        "/wps/portal",
        "/home",
        "/mapa-sitio",
        "/ley-fatca",
        "/facturacion-electronica",
        "/politicas-de-privacidad",
        "/terminos-y-condiciones",
        "/blog",
        "/blog/articulo",
        "/informes-financieros/2025",
        "/conecta",
    ],
)
def test_rutas_excluidas_quedan_fuera_de_alcance(ruta):
    # Arrange
    # Act
    resultado = in_scope(f"{BASE}{ruta}")
    # Assert
    assert resultado is False


# --- classify_section ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("ruta", "seccion"),
    [
        ("/", "institucional"),
        ("/quienes-somos", "institucional"),
        ("/comunicaciones/noticias", "institucional"),
        ("/canales-de-atencion", "canales_y_servicio"),
        ("/pqrs", "canales_y_servicio"),
        ("/defensor-consumidor", "canales_y_servicio"),
        ("/medios-de-pago/reembolsos", "canales_y_servicio"),
        ("/descargar-soat", "canales_y_servicio"),  # gana la primera regla, no «soat»
        ("/arl", "arl"),
        ("/arl/afiliacion", "arl"),
        ("/clientes-davivienda/hogar", "seguros_davivienda"),
        ("/soat", "movilidad"),
        ("/seguro-de-autos", "movilidad"),
        ("/seguro-bicicleta", "movilidad"),
        ("/seguro-de-hogar", "hogar_y_mascotas"),
        ("/seguro-de-arrendamiento", "hogar_y_mascotas"),
        ("/seguro-de-mascotas", "hogar_y_mascotas"),
        ("/seguro-de-vida", "vida_y_ahorro"),
        ("/renta-voluntaria", "vida_y_ahorro"),
        ("/seguro-de-accidentes", "vida_y_ahorro"),
        ("/seguro-de-salud", "salud"),
        ("/cancer", "salud"),
        ("/contacto-prensa", "otros"),
    ],
)
def test_classify_section(ruta, seccion):
    # Arrange
    # Act
    resultado = classify_section(f"{BASE}{ruta}")
    # Assert
    assert resultado == seccion


def test_classify_section_acepta_reglas_propias():
    # Arrange
    reglas = [(r"^/x", "equis")]
    # Act
    resultado = classify_section(f"{BASE}/xyz", rules=reglas)
    # Assert
    assert resultado == "equis"


def test_toda_seccion_tiene_titulo_y_orden():
    # Arrange
    # Act
    secciones = {
        classify_section(f"{BASE}{r}")
        for r in ["/", "/arl", "/soat", "/pqrs", "/vida", "/salud", "/hogar", "/zzz"]
    }
    # Assert
    assert secciones <= set(SECTION_TITLES) and list(SECTION_TITLES) == SECTION_ORDER


# --- estimate_tokens y text_hash ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("texto", "tokens"), [("", 0), ("a", 1), ("abc", 1), ("abcd", 2), ("x" * 36, 11), ("x" * 3600, 1001)]
)
def test_estimate_tokens(texto, tokens):
    # Arrange
    # Act
    resultado = estimate_tokens(texto)
    # Assert
    assert resultado == tokens


@pytest.mark.parametrize(
    ("a", "b"),
    [("Hola mundo", "hola   mundo"), ("Hola\nmundo", "HOLA MUNDO"), ("  x  ", "x"), ("a\tb", "a b")],
)
def test_text_hash_ignora_espacios_y_mayusculas(a, b):
    # Arrange
    # Act
    iguales = text_hash(a) == text_hash(b)
    # Assert
    assert iguales


@pytest.mark.parametrize(("a", "b"), [("hola", "hola."), ("SOAT", "SOAP"), ("a b", "ab")])
def test_text_hash_distingue_contenido_distinto(a, b):
    # Arrange
    # Act
    iguales = text_hash(a) == text_hash(b)
    # Assert
    assert not iguales


# --- documentos Gold ----------------------------------------------------------------------------


def doc(i: int, texto: str = "Texto", seccion: str = "movilidad", titulo: str | None = None) -> GoldDoc:
    """Documento Gold mínimo con id, URL y título derivados de ``i``."""
    return GoldDoc(
        doc_id=f"d{i}",
        url=f"{BASE}/p{i}",
        title=titulo or f"Título {i}",
        description="desc",
        section=seccion,
        fetched_at="2026-11-01T00:00:00Z",
        sha256="abc",
        text=texto,
    )


def test_dedupe_conserva_el_primero_y_reporta_los_omitidos():
    # Arrange
    docs = [doc(1, "Igual"), doc(2, "igual "), doc(3, "Distinto")]
    # Act
    conservados, omitidos = dedupe_docs(docs)
    # Assert
    assert [d.doc_id for d in conservados] == ["d1", "d3"] and omitidos == [f"{BASE}/p2"]


def test_dedupe_sin_duplicados_no_omite_nada():
    # Arrange
    docs = [doc(i, f"texto {i}") for i in range(5)]
    # Act
    conservados, omitidos = dedupe_docs(docs)
    # Assert
    assert len(conservados) == 5 and omitidos == []


@pytest.mark.parametrize(
    ("clave", "valor"),
    [
        ("doc_id", "d1"),
        ("url", f"{BASE}/p1"),
        ("title", "Título 1"),
        ("section", "movilidad"),
        ("tokens_est", 2),
    ],
)
def test_to_markdown_lleva_metadatos_en_el_front_matter(clave, valor):
    # Arrange
    md = to_markdown(doc(1, "Texto"))
    # Act
    front = yaml.safe_load(md.split("---")[1])
    # Assert
    assert front[clave] == valor


@pytest.mark.parametrize(
    ("texto", "inicio_cuerpo"),
    [
        ("Texto plano", "# Título 1\n\nTexto plano"),
        ("# Ya tiene título\nx", "# Ya tiene título"),
        ("  # Con sangría", "  # Con sangría"),
    ],
)
def test_to_markdown_agrega_titulo_solo_si_falta(texto, inicio_cuerpo):
    # Arrange
    # Act
    cuerpo = to_markdown(doc(1, texto)).split("---\n\n", 1)[1]
    # Assert
    assert cuerpo.startswith(inicio_cuerpo)


def test_chunk_doc_conserva_la_ruta_de_encabezados():
    # Arrange
    texto = "# SOAT\nIntro\n## Coberturas\nGastos médicos\n### Topes\n800 SMLDV"
    # Act
    chunks = chunk_doc(doc(1, texto))
    # Assert
    assert [c["breadcrumb"] for c in chunks] == ["SOAT", "SOAT > Coberturas", "SOAT > Coberturas > Topes"]


@pytest.mark.parametrize(("largo", "maximo"), [(100, 1500), (4000, 1500), (4000, 500), (10_000, 1000)])
def test_chunk_doc_respeta_el_tamano_maximo(largo, maximo):
    # Arrange
    texto = " ".join(["palabra"] * (largo // 8))
    # Act
    chunks = chunk_doc(doc(1, texto), max_chars=maximo, overlap=50)
    # Assert
    assert chunks and all(len(c["text"]) <= maximo for c in chunks)


def test_chunk_doc_ids_unicos_y_ordenados():
    # Arrange
    texto = "\n\n".join(f"Párrafo {i} " + "x" * 400 for i in range(10))
    # Act
    ids = [c["chunk_id"] for c in chunk_doc(doc(7, texto), max_chars=500, overlap=0)]
    # Assert
    assert ids == sorted(set(ids)) and ids[0] == "d7#000"


@pytest.mark.parametrize("campo", ["doc_id", "url", "title", "section", "breadcrumb", "text", "tokens_est"])
def test_chunk_doc_cada_fragmento_lleva_sus_metadatos(campo):
    # Arrange
    # Act
    chunks = chunk_doc(doc(1, "# A\ntexto"))
    # Assert
    assert all(campo in c for c in chunks)


def test_build_knowledge_ordena_por_seccion_y_cita_fuentes():
    # Arrange
    docs = [doc(1, "vida", "vida_y_ahorro"), doc(2, "soat", "movilidad"), doc(3, "inst", "institucional")]
    # Act
    md = build_knowledge(docs)
    # Assert
    posiciones = [md.index(SECTION_TITLES[s]) for s in ("institucional", "movilidad", "vida_y_ahorro")]
    assert posiciones == sorted(posiciones) and f"Fuente: {BASE}/p2" in md


def test_build_knowledge_aplana_los_titulos_internos():
    # Arrange
    docs = [doc(1, "# Interno\n## Sub\ntexto")]
    # Act
    md = build_knowledge(docs)
    # Assert
    assert "\nInterno\nSub\ntexto" in md


@pytest.mark.parametrize(("canales", "incluido"), [("WhatsApp: 322", True), ("", False)])
def test_build_knowledge_incluye_los_canales_una_vez(canales, incluido):
    # Arrange
    # Act
    md = build_knowledge([doc(1)], channels_text=canales)
    # Assert
    assert ("## Canales de atención" in md) is incluido


# --- sitemap y robots ---------------------------------------------------------------------------

NS = 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'


def test_parse_sitemap_lee_urls_y_lastmod():
    # Arrange
    xml = (
        f"<urlset {NS}><url><loc> {BASE}/soat </loc><lastmod>2026-01-01</lastmod></url>"
        f"<url><loc>{BASE}/vida</loc></url></urlset>"
    )
    # Act
    urls, subs = parse_sitemap(xml)
    # Assert
    assert urls == [SitemapEntry(f"{BASE}/soat", "2026-01-01"), SitemapEntry(f"{BASE}/vida")] and subs == []


def test_parse_sitemap_lee_indices():
    # Arrange
    xml = (
        f"<sitemapindex {NS}><sitemap><loc>{BASE}/s1.xml</loc></sitemap>"
        f"<sitemap><loc>{BASE}/s2.xml</loc></sitemap></sitemapindex>"
    )
    # Act
    urls, subs = parse_sitemap(xml.encode())
    # Assert
    assert urls == [] and subs == [f"{BASE}/s1.xml", f"{BASE}/s2.xml"]


def test_parse_sitemap_omite_entradas_sin_loc():
    # Arrange
    xml = f"<urlset {NS}><url><lastmod>2026</lastmod></url><url><loc></loc></url></urlset>"
    # Act
    urls, _ = parse_sitemap(xml)
    # Assert
    assert urls == []


def test_parse_sitemap_no_resuelve_entidades_externas():
    # Arrange: XXE; el parser no debe leer archivos locales
    xml = (
        '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]>'
        f"<urlset {NS}><url><loc>&e;</loc></url></urlset>"
    )
    # Act
    urls, _ = parse_sitemap(xml)
    # Assert
    assert all("root:" not in u.url for u in urls)


ROBOTS = "User-agent: *\nDisallow: /privado\n"


@pytest.mark.parametrize(
    ("rutas", "motivos"),
    [
        (["/soat"], []),
        (["/soat", "/soat/"], ["duplicada"]),
        (["/privado/x"], ["robots.txt"]),
        (["/empresas"], ["fuera de alcance"]),
        (["/soat", "/privado", "/blog", "/soat"], ["robots.txt", "fuera de alcance", "duplicada"]),
    ],
)
def test_select_urls_explica_cada_descarte(rutas, motivos):
    # Arrange
    robots = build_robots(ROBOTS, f"{BASE}/robots.txt")
    entradas = [SitemapEntry(f"{BASE}{r}") for r in rutas]
    # Act
    _, descartadas = select_urls(entradas, robots, "bot")
    # Assert
    assert [m for _, m in descartadas] == motivos


def test_select_urls_conserva_el_orden():
    # Arrange
    robots = build_robots(ROBOTS, f"{BASE}/robots.txt")
    entradas = [SitemapEntry(f"{BASE}/{r}") for r in ("vida", "soat", "arl")]
    # Act
    seleccionadas, _ = select_urls(entradas, robots, "bot")
    # Assert
    assert [path_of(e.url) for e in seleccionadas] == ["/vida", "/soat", "/arl"]


# --- slugify_path -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("ruta", "slug"),
    [
        ("/", "index"),
        ("", "index"),
        ("/soat", "soat"),
        ("/a/b-c", "a__b-c"),
        ("/seguro de hogar", "seguro__de__hogar"),
        ("/ñandú", "__and__"),
        ("/../../etc/passwd", "__etc__passwd"),
        ("/a?x=1&y=2", "a__x__1__y__2"),
    ],
)
def test_slugify_path_produce_nombres_seguros(ruta, slug):
    # Arrange
    # Act
    resultado = slugify_path(ruta)
    # Assert
    assert resultado == slug


def test_slugify_path_corta_rutas_largas():
    # Arrange
    ruta = "/" + "a" * 500
    # Act
    resultado = slugify_path(ruta)
    # Assert
    assert len(resultado) == 150

"""Pruebas de limpieza (Silver), Gold y pipeline completo (patrón AAA, sin red)."""

import json

import pytest

from conftest import BASE, FIXTURES
from sb_asistente import pipeline
from sb_asistente.processing import clean, gold
from sb_asistente.scraping.discover import in_scope

HOGAR = (FIXTURES / "hogar.html").read_text(encoding="utf-8")
PAGES = [(FIXTURES / n).read_text(encoding="utf-8") for n in ("hogar.html", "soat.html", "quienes.html")]


def test_extract_meta_strips_brand_suffix():
    title, desc = clean.extract_meta(HOGAR)
    assert title == "Seguro de hogar"
    assert desc.startswith("Proteja")


def test_extract_footer_keeps_channels():
    footer = clean.extract_footer(HOGAR)
    assert "322 332 2322" in footer and "01 8000 123 322" in footer


def test_extract_footer_empty_when_missing():
    assert clean.extract_footer("<html><body><main>x</main></body></html>") == ""


def test_markdown_excludes_footer_nav_and_scripts():
    md = clean.html_to_markdown(HOGAR)
    assert "Cerrajería" in md
    assert "322 332 2322" not in md
    assert "var x" not in md
    assert "Empresas" not in md


def test_markdown_falls_back_to_plain_text():
    md = clean.html_to_markdown("<html><body><main><p>Corto</p></main></body></html>")
    assert md == "Corto"


def test_headings_of_reads_h1_to_h3():
    assert clean.headings_of(HOGAR)[:2] == ["Seguro de Hogar", "Beneficios de este seguro"]


def test_find_boilerplate_detects_repeated_banner():
    texts = [clean.html_to_markdown(p) for p in PAGES]
    boiler = clean.find_boilerplate(texts)
    cleaned = clean.remove_lines(texts[0], boiler)
    assert "Bolívar Conmigo" not in cleaned
    assert "Cerrajería" in cleaned


def test_find_boilerplate_needs_three_documents():
    assert clean.find_boilerplate(["a", "a"]) == set()


def test_remove_lines_collapses_blank_lines():
    assert clean.remove_lines("a\n\n\n\nb", set()) == "a\n\nb"


@pytest.mark.parametrize(
    ("path", "section"),
    [
        ("/", "institucional"),
        ("/quienes-somos", "institucional"),
        ("/canales-de-atencion", "canales_y_servicio"),
        ("/medios-de-pago/pse", "canales_y_servicio"),
        ("/soat", "movilidad"),
        ("/seguro-todo-riesgo-vehiculo", "movilidad"),
        ("/seguro-de-hogar", "hogar_y_mascotas"),
        ("/seguro-para-mascotas", "hogar_y_mascotas"),
        ("/renta-vitalicia", "vida_y_ahorro"),
        ("/seguro-de-salud", "salud"),
        ("/arl/como-afiliarse-arl", "arl"),
        ("/clientes-davivienda/maneje-tranquilo/soat", "seguros_davivienda"),
        ("/algo-raro", "otros"),
    ],
)
def test_classify_section(path, section):
    assert gold.classify_section(f"{BASE}{path}") == section


def _doc(doc_id="d", text="# T\n\n## A\nuno", section="movilidad", url=f"{BASE}/soat"):
    return gold.GoldDoc(doc_id, url, "Título", "desc", section, "2026-10-24T00:00:00", "abc", text)


def test_estimate_tokens_spanish():
    assert gold.estimate_tokens("") == 0
    assert gold.estimate_tokens("a" * 360) == 101


def test_dedupe_docs_ignores_whitespace_and_case():
    docs, dropped = gold.dedupe_docs([_doc("a", "Hola  Mundo"), _doc("b", "hola mundo", url="u2")])
    assert [d.doc_id for d in docs] == ["a"] and dropped == ["u2"]


def test_to_markdown_has_front_matter():
    md = gold.to_markdown(_doc())
    assert md.startswith("---\ndoc_id: d\n") and "section: movilidad" in md


def test_to_markdown_adds_title_when_missing():
    assert "# Título" in gold.to_markdown(_doc(text="sin titulo"))


def test_chunk_doc_splits_by_headers_with_breadcrumb():
    text = "# Seguro\n\n## Coberturas\n" + "Daños. " * 50 + "\n\n## Asistencias\nCerrajería 24 horas."
    chunks = gold.chunk_doc(_doc(text=text), max_chars=200, overlap=20)
    assert len(chunks) >= 3
    assert chunks[-1]["breadcrumb"].endswith("Asistencias")
    assert all(len(c["text"]) <= 260 for c in chunks)
    assert chunks[0]["chunk_id"] == "d#000"


def test_build_knowledge_groups_by_section_and_cites_url():
    knowledge = gold.build_knowledge(
        [_doc(), _doc("h", "Hogar", "hogar_y_mascotas", f"{BASE}/hogar")], "WhatsApp 322"
    )
    assert knowledge.index("Canales de atención") < knowledge.index("movilidad") < knowledge.index("hogar")
    assert f"Fuente: {BASE}/soat" in knowledge


def test_write_gold_outputs_all_artifacts(tmp_path):
    summary = gold.write_gold([_doc()], tmp_path, "canales")
    assert (tmp_path / "pages" / "d.md").is_file()
    assert json.loads((tmp_path / "corpus.jsonl").read_text().splitlines()[0])["doc_id"] == "d"
    assert (tmp_path / "chunks.jsonl").is_file()
    assert summary["documentos"] == 1 and summary["tokens_conocimiento_est"] > 0


def test_end_to_end_pipeline(tmp_path, session, monkeypatch):
    monkeypatch.setattr("sb_asistente.scraping.fetch.time.sleep", lambda s: None)
    bronze, silver, gold_dir = tmp_path / "raw", tmp_path / "silver", tmp_path / "gold"

    plan = pipeline.discover(session, bronze)
    stats = pipeline.scrape(session, bronze)
    summary = pipeline.process(bronze, silver, gold_dir)

    assert len(plan["seleccionadas"]) == 4
    assert stats == {"total": 4, "ok": 4, "fallidas": 0}
    assert summary["documentos"] == 3  # 4 páginas, una duplicada
    assert len(summary["descartadas_duplicadas"]) == 1
    knowledge = (gold_dir / "conocimiento_seguros_bolivar.md").read_text()
    assert knowledge.count("322 332 2322") == 1  # canales una sola vez
    assert "Bolívar Conmigo" not in knowledge  # banner repetido eliminado
    assert (bronze / "robots.txt").is_file()


# --- Estructura real de segurosbolivar.com (Angular SSR, footer dentro de <main>) -------
REAL = (FIXTURES / "real_hogar.html").read_text(encoding="utf-8")


def test_real_page_keeps_coverages_and_exclusions():
    md = clean.html_to_markdown(REAL)
    assert "¿Qué cubre?" in md and "arrendatarios" in md
    assert "Cerrajería" in md and "Plomería" in md


def test_real_page_removes_footer_inside_main_and_breadcrumb():
    md = clean.html_to_markdown(REAL)
    assert "322 332 2322" not in md
    assert "Inicio  Personas" not in md
    assert "Todos los derechos reservados" not in md


def test_real_footer_joins_labels_and_drops_copyright():
    footer = clean.extract_footer(REAL)
    assert "WhatsApp: 322 332 2322" in footer
    assert "Sede Administrativa: Av. Dorado No. 68B – 31, Bogotá" in footer
    assert "©" not in footer


def test_join_label_values():
    assert clean.join_label_values(["A:", "1", "B:", "C:", "2"]) == "A: 1\nB:\nC: 2"


def test_pdf_links_are_absolute_and_unique():
    html = '<a href="/doc.PDF">x</a><a href="/doc.PDF">y</a><a href="/otra">z</a>'
    assert clean.pdf_links(html) == ["https://www.segurosbolivar.com/doc.PDF"]


def test_real_page_pdf_link_found():
    assert clean.pdf_links(REAL)[0].endswith("Clausulado1.pdf")


def test_trim_noise_cuts_cross_sell_and_residue():
    md = (
        "## Seguro de hogar\n\n<u>Consulte</u> la app\n\n.\n\n- Cubre vidrios\n\n"
        "Otros seguros de su interés\n\nSeguro de vida\n- Ahorro"
    )
    out = clean.trim_noise(md)
    assert "Seguro de vida" not in out and "Ahorro" not in out
    assert "Consulte la app" in out and "Cubre vidrios" in out
    assert "\n.\n" not in out


@pytest.mark.parametrize(
    ("path", "title"),
    [
        ("/medios-de-pago/financiacion-de-seguros", "Medios de pago · Financiacion de seguros"),
        ("/seguros", "Seguros"),
        ("/", "Inicio"),
    ],
)
def test_title_from_path(path, title):
    assert clean.title_from_path(path) == title


@pytest.mark.parametrize("path", ["/informes-financieros", "/conecta"])
def test_out_of_scope_institutional_pages(path):
    assert in_scope(f"https://www.segurosbolivar.com{path}") is False


@pytest.mark.parametrize("marker", ["## Otros seguros de su interés", "**Otros seguros de su interés**"])
def test_trim_noise_detects_marker_as_heading_or_bold(marker):
    out = clean.trim_noise(f"## Hogar\n\n- Cubre vidrios\n\n{marker}\n\n### Seguro de vida\n- Ahorro")
    assert out.endswith("Cubre vidrios")


def test_process_reapplies_scope_without_rescraping(tmp_path, session, monkeypatch):
    monkeypatch.setattr("sb_asistente.scraping.fetch.time.sleep", lambda s: None)
    bronze = tmp_path / "raw"
    pipeline.discover(session, bronze)
    pipeline.scrape(session, bronze)
    monkeypatch.setattr(pipeline, "in_scope", lambda url: not url.endswith("/soat"))
    summary = pipeline.process(bronze, tmp_path / "silver", tmp_path / "gold")
    assert summary["descartadas_fuera_de_alcance"] == [f"{BASE}/soat"]
    assert summary["documentos"] == 2


# --- Métricas por etapa para la UI ---------------------------------------------------


@pytest.fixture
def built(tmp_path, session, monkeypatch):
    monkeypatch.setattr("sb_asistente.scraping.fetch.time.sleep", lambda s: None)
    bronze, silver, gold_dir = tmp_path / "raw", tmp_path / "silver", tmp_path / "gold"
    pipeline.discover(session, bronze)
    pipeline.scrape(session, bronze)
    pipeline.process(bronze, silver, gold_dir)
    return bronze, gold_dir


def test_stage_report_has_five_stages_in_order(built):
    etapas = [s["etapa"] for s in pipeline.stage_report(*built)]
    assert etapas == ["1. Descubrir", "2. Extraer", "3. Limpiar", "4. Deduplicar", "5. Enriquecer"]


def test_stage_report_marks_all_stages_done(built):
    assert all(s["hecha"] for s in pipeline.stage_report(*built))


def test_stage_report_counts_downloaded_pages(built):
    extraer = pipeline.stage_report(*built)[1]["metricas"]
    assert extraer["Páginas descargadas (200)"] == 4


def test_stage_report_counts_duplicates(built):
    dedup = pipeline.stage_report(*built)[3]["metricas"]
    assert dedup["Páginas duplicadas descartadas"] == 1


def test_stage_report_counts_gold_documents(built):
    enriquecer = pipeline.stage_report(*built)[4]["metricas"]
    assert enriquecer["Documentos"] == 3


def test_stage_report_without_data_is_empty_not_error(tmp_path):
    report = pipeline.stage_report(tmp_path / "raw", tmp_path / "gold")
    assert not any(s["hecha"] for s in report)


def test_corpus_table_has_required_metadata(built):
    fila = pipeline.corpus_table(built[1])[0]
    assert {"url", "titulo", "seccion", "fecha_captura", "sha256", "tokens"} <= set(fila)


def test_corpus_table_one_row_per_document(built):
    assert len(pipeline.corpus_table(built[1])) == 3


def test_corpus_table_without_gold_is_empty(tmp_path):
    assert pipeline.corpus_table(tmp_path) == []

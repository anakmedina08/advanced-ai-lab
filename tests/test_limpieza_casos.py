"""Casos tabulados de la limpieza Bronze → Silver (SPEC-061).

La calidad del RAG depende de lo que deja esta etapa: si el pie de página o la venta cruzada
se cuelan en los fragmentos, el agente cita la página equivocada.
"""

import pytest

from sb_asistente.model.processing.clean import (
    extract_footer,
    extract_meta,
    find_boilerplate,
    headings_of,
    join_label_values,
    pdf_links,
    remove_lines,
    title_from_path,
    trim_noise,
)

BASE = "https://www.segurosbolivar.com"

# --- title_from_path ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("ruta", "titulo"),
    [
        ("/", "Inicio"),
        ("", "Inicio"),
        ("/soat", "Soat"),
        ("/seguro-de-hogar", "Seguro de hogar"),
        ("/medios-de-pago/reembolsos", "Medios de pago · Reembolsos"),
        ("medios-de-pago/reembolsos/", "Medios de pago · Reembolsos"),
        ("/a/b/c", "A · B · C"),
        ("//doble//barra/", "Doble · Barra"),
        ("/arl-independiente", "Arl independiente"),
        ("/vida/seguro-de-vida-grupo", "Vida · Seguro de vida grupo"),
    ],
)
def test_title_from_path(ruta, titulo):
    # Arrange
    # Act
    resultado = title_from_path(ruta)
    # Assert
    assert resultado == titulo


# --- join_label_values --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("lineas", "esperado"),
    [
        ([], ""),
        (["WhatsApp:", "322 000"], "WhatsApp: 322 000"),
        (["Línea:", "601 000", "Sede:", "Bogotá"], "Línea: 601 000\nSede: Bogotá"),
        (["Texto suelto"], "Texto suelto"),
        (["A:", "B:"], "A:\nB:"),
        (["A:", "B:", "valor"], "A:\nB: valor"),
        (["valor", "A:"], "valor\nA:"),
        (["A:", "uno", "dos"], "A: uno\ndos"),
    ],
)
def test_join_label_values(lineas, esperado):
    # Arrange
    # Act
    resultado = join_label_values(lineas)
    # Assert
    assert resultado == esperado


# --- trim_noise ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("markdown", "esperado"),
    [
        ("Cubre daños.\n## Otros seguros de su interés\nSeguro de vida", "Cubre daños."),
        ("Cubre daños.\nOtros seguros de su interés\nSOAT", "Cubre daños."),
        ("Cubre daños.\n**Otros seguros de su interés**\nSOAT", "Cubre daños."),
        ("Cubre daños.\n> Otros seguros de su interés\nSOAT", "Cubre daños."),
        ("Uno\n.\nDos", "Uno\nDos"),
        ("<u>Subrayado</u> normal", "Subrayado normal"),
        ("Uno\n\n\n\nDos", "Uno\n\nDos"),
        ("  \nTexto\n  ", "Texto"),
        ("Sin marcador", "Sin marcador"),
        ("Otros seguros de su interés", ""),
    ],
)
def test_trim_noise(markdown, esperado):
    # Arrange
    # Act
    resultado = trim_noise(markdown)
    # Assert
    assert resultado == esperado


def test_trim_noise_acepta_marcadores_propios():
    # Arrange
    markdown = "Útil\nFIN\nbasura"
    # Act
    resultado = trim_noise(markdown, markers=("FIN",))
    # Assert
    assert resultado == "Útil"


def test_trim_noise_no_corta_si_el_marcador_esta_dentro_de_una_frase():
    # Arrange: el marcador debe ser la línea completa
    markdown = "Vea Otros seguros de su interés en la web\nsigue"
    # Act
    resultado = trim_noise(markdown)
    # Assert
    assert resultado == markdown


# --- find_boilerplate y remove_lines -----------------------------------------------------------


def _docs(n_con_menu, n_total):
    return [("Menú principal\n" if i < n_con_menu else "") + f"Contenido único {i}" for i in range(n_total)]


@pytest.mark.parametrize(
    ("con_menu", "total", "es_boilerplate"),
    [(3, 4, True), (5, 10, True), (2, 10, False), (4, 10, False), (10, 10, True)],
)
def test_find_boilerplate_por_proporcion(con_menu, total, es_boilerplate):
    # Arrange
    textos = _docs(con_menu, total)
    # Act
    hashes = find_boilerplate(textos)
    # Assert: la línea del menú se elimina solo si aparece en suficientes documentos
    assert (remove_lines("Menú principal", hashes) == "") is es_boilerplate


@pytest.mark.parametrize("total", [0, 1, 2])
def test_find_boilerplate_necesita_al_menos_tres_documentos(total):
    # Arrange
    textos = ["Menú"] * total
    # Act
    hashes = find_boilerplate(textos)
    # Assert
    assert hashes == set()


def test_find_boilerplate_nunca_marca_contenido_unico():
    # Arrange
    textos = _docs(10, 10)
    # Act
    hashes = find_boilerplate(textos)
    # Assert
    assert all(remove_lines(f"Contenido único {i}", hashes) for i in range(10))


@pytest.mark.parametrize(
    "variante",
    ["Menú principal", "menú principal", "MENÚ PRINCIPAL", "Menú, principal.", "  Menú principal  "],
)
def test_remove_lines_ignora_mayusculas_y_signos(variante):
    # Arrange
    hashes = find_boilerplate(["Menú principal\nA", "Menú principal\nB", "Menú principal\nC"])
    # Act
    resultado = remove_lines(variante, hashes)
    # Assert
    assert resultado == ""


def test_remove_lines_colapsa_lineas_en_blanco():
    # Arrange
    hashes = find_boilerplate(["X\n1", "X\n2", "X\n3"])
    # Act
    resultado = remove_lines("Antes\n\nX\n\n\nDespués", hashes)
    # Assert
    assert resultado == "Antes\n\nDespués"


def test_remove_lines_sin_boilerplate_conserva_el_texto():
    # Arrange
    texto = "Uno\nDos"
    # Act
    resultado = remove_lines(texto, set())
    # Assert
    assert resultado == texto


# --- extract_meta -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("html", "titulo", "descripcion"),
    [
        ("<title>SOAT | Seguros Bolívar</title>", "SOAT", ""),
        ("<title>SOAT | Seguros Bolivar</title>", "SOAT", ""),
        ("<title>  Hogar   seguro </title>", "Hogar seguro", ""),
        (
            "<title>Vida</title><meta name='description' content=' Proteja  a su familia '>",
            "Vida",
            "Proteja a su familia",
        ),
        ("<p>sin título</p>", "", ""),
        ("<meta name='description' content='Solo descripción'>", "", "Solo descripción"),
        ("<title>Seguros Bolívar | Inicio</title>", "Seguros Bolívar | Inicio", ""),
    ],
)
def test_extract_meta(html, titulo, descripcion):
    # Arrange
    # Act
    resultado = extract_meta(f"<html><head>{html}</head></html>")
    # Assert
    assert resultado == (titulo, descripcion)


# --- extract_footer -----------------------------------------------------------------------------


def test_extract_footer_une_etiquetas_y_quita_copyright():
    # Arrange
    html = "<footer><p>WhatsApp:</p><p>322 000</p><p>© 2026 Seguros</p></footer>"
    # Act
    resultado = extract_footer(html)
    # Assert
    assert resultado == "WhatsApp: 322 000"


@pytest.mark.parametrize(
    "ruido", ["<script>x()</script>", "<style>p{}</style>", "<button>Ir</button>", "<svg></svg>"]
)
def test_extract_footer_quita_etiquetas_de_ruido(ruido):
    # Arrange
    html = f"<footer><p>Línea: 601</p>{ruido}</footer>"
    # Act
    resultado = extract_footer(html)
    # Assert
    assert resultado == "Línea: 601"


def test_extract_footer_sin_pie_devuelve_vacio():
    # Arrange
    # Act
    resultado = extract_footer("<main>Contenido</main>")
    # Assert
    assert resultado == ""


# --- pdf_links ----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("enlaces", "esperado"),
    [
        ([], []),
        (["/docs/clausulado.pdf"], [f"{BASE}/docs/clausulado.pdf"]),
        (["/a.PDF"], [f"{BASE}/a.PDF"]),
        (["/a.pdf", "/a.pdf"], [f"{BASE}/a.pdf"]),
        (["/b.pdf", "/a.pdf"], [f"{BASE}/a.pdf", f"{BASE}/b.pdf"]),
        (["https://otro.com/x.pdf"], ["https://otro.com/x.pdf"]),
        (["/pagina", "/imagen.png"], []),
        (["/x.pdf?v=2"], [f"{BASE}/x.pdf?v=2"]),
    ],
)
def test_pdf_links(enlaces, esperado):
    # Arrange
    html = "".join(f'<a href="{e}">doc</a>' for e in enlaces)
    # Act
    resultado = pdf_links(html, base_url=BASE)
    # Assert
    assert resultado == esperado


def test_pdf_links_ignora_anclas_sin_href():
    # Arrange
    html = "<a>sin destino.pdf</a>"
    # Act
    resultado = pdf_links(html, base_url=BASE)
    # Assert
    assert resultado == []


# --- headings_of --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("html", "titulos"),
    [
        ("<main><h1>SOAT</h1><h2>Coberturas</h2><h3>Gastos</h3></main>", ["SOAT", "Coberturas", "Gastos"]),
        ("<main><h4>No cuenta</h4></main>", []),
        ("<main><h2>  Con   espacios </h2></main>", ["Con espacios"]),
        ("<main><h2></h2><h2>Lleno</h2></main>", ["Lleno"]),
        ("<header><h1>Menú</h1></header><main><h1>Real</h1></main>", ["Real"]),
        ("<nav><h2>Nav</h2></nav><main><h2>Real</h2></main>", ["Real"]),
        ("<main><h2>Real</h2></main><footer><h2>Pie</h2></footer>", ["Real"]),
    ],
)
def test_headings_of_solo_lee_el_contenido_principal(html, titulos):
    # Arrange
    # Act
    resultado = headings_of(f"<html><body>{html}</body></html>")
    # Assert
    assert resultado == titulos

"""Canales de atención por aseguradora y servicio (SPEC-070): extracción, privacidad y elección.

Cada prueba sigue Arrange / Act / Assert; el HTML es local y ninguna prueba sale a internet.
"""

import json
from pathlib import Path

import pytest

from sb_asistente.controller import mercado
from sb_asistente.model.memoria import extraer_aseguradora
from sb_asistente.model.mercado import canales
from sb_asistente.model.mercado.canales import CanalAgregado

URL = "https://www.aseguradora.co/canales-de-atencion"

PAGINA = """<html><body>
<header><a href="https://wa.me/573001234567">WhatsApp</a></header>
<section><h2>Asistencia en vehículos</h2><p>Desde tu celular marca <a href="tel:%23322">#322</a></p></section>
<section><h2>Asistencia hogar</h2><p>Plomería y cerrajería: 01 8000 911 360</p></section>
<section><h2>Salud</h2><p>Ambulancias y citas: (601) 418 8800</p></section>
<section><h2>Ventas</h2><p>Cotiza tu seguro: <a href="tel:6013078000">601 307 8000</a></p></section>
<script>var x = "#999";</script>
<!-- HFCM by 99 Robots - Snippet # 376: Organization -->
<!-- Snippet #377 -->
<p>Pedido &#123; y referencia #a12</p>
</body></html>"""


def test_canales_de_html_lee_whatsapp_tel_y_numeros_del_texto():
    # Arrange / Act
    encontrados = {(c.tipo, c.valor): c.servicio for c in canales.canales_de_html(PAGINA, URL)}
    # Assert
    assert encontrados[("whatsapp", "573001234567")] == "general"
    assert encontrados[("linea_corta", "#322")] == "autos"
    assert encontrados[("linea_nacional", "018000911360")] == "hogar"
    assert encontrados[("fijo", "576014188800")] == "salud"
    assert encontrados[("fijo", "576013078000")] == "ventas"
    assert ("linea_corta", "#999") not in encontrados  # el texto de los scripts no cuenta
    assert ("linea_corta", "#376") not in encontrados  # ni los comentarios HTML (caso real: MAPFRE)
    assert ("linea_corta", "#377") not in encontrados


@pytest.mark.parametrize(
    ("contexto", "servicio"),
    [
        ("Línea de asistencia para tu carro y grúa", "autos"),
        ("Choque leve, sin heridos", "autos"),
        ("Me chocaron en un semáforo", "autos"),
        ("SOAT: reclamaciones", "soat"),
        ("Hogar: cerrajería", "hogar"),
        ("Urgencias médicas y ambulancia", "salud"),
        ("ARL: reporte de accidente de trabajo", "arl"),
        ("Servicio exequial", "vida"),
        ("Radique su PQR o queja", "pqr"),
        ("Cotiza con un asesor comercial", "ventas"),
        ("Contáctanos", "general"),
    ],
)
def test_servicio_de_lee_el_contexto(contexto, servicio):
    # Arrange / Act / Assert
    assert canales.servicio_de(contexto) == servicio


@pytest.mark.parametrize(
    ("href", "esperado"),
    [
        ("tel:%23322", ("linea_corta", "#322")),
        ("tel:#345", ("linea_corta", "#345")),
        ("tel:018000911360", ("linea_nacional", "018000911360")),
        ("tel:+57 601 418 8800", ("fijo", "576014188800")),
        ("tel:3001234567", ("celular", "573001234567")),
        ("tel:12", None),
        ("tel:+1 555 123 4567", None),
    ],
)
def test_los_enlaces_tel_se_normalizan(href, esperado):
    # Arrange
    html = f'<a href="{href}">Llamar</a>'
    # Act
    hallados = [(c.tipo, c.valor) for c in canales.canales_de_html(html, URL)]
    # Assert
    assert hallados == ([esperado] if esperado else [])


def test_un_celular_de_una_sola_pagina_no_se_guarda():
    # Arrange: el WhatsApp del pie sale en 4 de 4 páginas; el celular de un asesor, en 1
    oficial = canales.Canal("whatsapp", "573001111111", "general", URL)
    asesor = canales.Canal("celular", "573109999999", "ventas", URL)
    linea = canales.Canal("linea_corta", "#322", "autos", URL)
    paginas = [[oficial], [oficial], [oficial, asesor, linea], [oficial]]
    # Act
    valores = [c.valor for c in canales.agregar_canales(paginas)]
    # Assert
    assert valores == ["573001111111", "#322"]


def _agregado(tipo: str, valor: str, *servicios: str) -> CanalAgregado:
    """Canal agregado mínimo para elegir."""
    return CanalAgregado(
        canales.desde_dict({"tipo": tipo, "valor": valor}).tipo, valor, set(servicios), [URL], 1
    )


DIRECTORIO = [
    _agregado("whatsapp", "573001234567", "general"),
    _agregado("linea_corta", "#322", "autos"),
    _agregado("linea_nacional", "018000911360", "hogar"),
    _agregado("fijo", "576014188800", "general"),
    _agregado("fijo", "576013078000", "ventas"),
]


@pytest.mark.parametrize(
    ("servicio", "primero"),
    [("autos", "#322"), ("hogar", "018000911360"), ("salud", "576014188800")],
)
def test_elegir_prefiere_el_canal_del_servicio_y_si_no_la_linea_general(servicio, primero):
    # Arrange / Act
    whatsapp, telefonos = canales.elegir(DIRECTORIO, servicio, 3)
    # Assert
    assert telefonos[0].valor == primero
    assert whatsapp is not None and whatsapp.valor == "573001234567"
    assert "576013078000" not in [t.valor for t in telefonos]  # ventas nunca atiende un siniestro


@pytest.mark.parametrize(
    ("canal", "uri"),
    [
        (_agregado("linea_corta", "#322"), "tel:%23322"),
        (_agregado("fijo", "576014188800"), "tel:+576014188800"),
        (_agregado("linea_nacional", "018000911360"), "tel:018000911360"),
    ],
)
def test_enlace_telefono_marca_desde_el_celular(canal, uri):
    # Arrange / Act / Assert
    assert canales.enlace_telefono(canal) == uri


def test_un_canal_sobrevive_la_ida_y_vuelta_a_json():
    # Arrange
    original = DIRECTORIO[1]
    # Act
    copia = canales.desde_dict(json.loads(json.dumps(canales.como_dict(original))))
    # Assert
    assert (copia.tipo, copia.valor, copia.servicios) == (original.tipo, original.valor, original.servicios)


def test_desde_dict_rechaza_un_tipo_desconocido():
    # Arrange / Act / Assert
    with pytest.raises(ValueError, match="desconocido"):
        canales.desde_dict({"tipo": "fax", "valor": "1"})


# --- Controlador: a dónde llevar a la persona ----------------------------------------------------


@pytest.fixture
def directorio(tmp_path: Path) -> Path:
    """canales.json con MAPFRE (WhatsApp, línea de autos y línea general)."""
    ruta = tmp_path / "canales.json"
    ruta.write_text(json.dumps({"mapfre": [canales.como_dict(c) for c in DIRECTORIO]}))
    return ruta


def test_canales_para_arma_el_enlace_de_whatsapp_con_el_resumen(directorio):
    # Arrange / Act
    r = mercado.canales_para("mapfre", "autos", "Choque leve, sin heridos", directorio)
    # Assert
    assert r["whatsapp"]["enlace"] == "https://wa.me/573001234567?text=Choque%20leve%2C%20sin%20heridos"
    assert r["telefonos"][0] == {
        "tipo": "linea_corta",
        "valor": "#322",
        "marcar": "tel:%23322",
        "especifico": True,
        "fuente": URL,
    }


def test_canales_para_deduce_el_servicio_del_resumen(directorio):
    # Arrange / Act
    r = mercado.canales_para(
        "mapfre", None, "Se dañó la cerradura de la casa: necesito un cerrajero", directorio
    )
    # Assert
    assert r["servicio"] == "hogar" and r["telefonos"][0]["valor"] == "018000911360"


def test_canales_para_sin_datos_devuelve_listas_vacias_y_el_sitio(tmp_path):
    # Arrange / Act
    r = mercado.canales_para("sura", "autos", "", tmp_path / "no-existe.json")
    # Assert
    assert r["whatsapp"] is None and r["telefonos"] == [] and r["sitio"].startswith("https://")


def test_canales_para_con_una_aseguradora_desconocida_lanza_keyerror(directorio):
    # Arrange / Act / Assert
    with pytest.raises(KeyError):
        mercado.canales_para("no-existe", "autos", "", directorio)


# --- Memoria: la aseguradora que la persona dice tener -------------------------------------------


@pytest.mark.parametrize(
    ("mensaje", "esperado"),
    [
        ("Tengo el SOAT con La Equidad", {"aseguradora": "La Equidad Seguros", "seguros": "soat"}),
        (
            "estoy asegurado con SURA para el carro y la casa",
            {"aseguradora": "Seguros SURA", "seguros": "autos, hogar"},
        ),
        ("mi póliza de hogar es de MAPFRE", {"aseguradora": "MAPFRE", "seguros": "hogar"}),
        ("soy cliente de Allianz", {"aseguradora": "Allianz"}),
        ("¿Qué cubre el SOAT de MAPFRE?", {}),  # pregunta, no dice que lo tenga
        ("tengo un perro", {}),  # no nombra aseguradora
    ],
)
def test_extraer_aseguradora_solo_si_la_persona_dice_tenerla(mensaje, esperado):
    # Arrange / Act / Assert
    assert extraer_aseguradora(mensaje) == esperado

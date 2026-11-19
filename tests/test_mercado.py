"""Corpus de mercado (SPEC-069): registro, alcance, secciones, WhatsApp, pipeline y comparación.

Cada prueba sigue Arrange / Act / Assert. Los sitios son dobles en memoria: ninguna prueba sale
a internet.
"""

import json
import os
from collections.abc import Iterator
from dataclasses import dataclass

import pytest

from dobles_mercado import chunk_mercado as chunk
from sb_asistente.controller import mercado
from sb_asistente.model.mercado import contactos, secciones
from sb_asistente.model.mercado.comparar import cobertura_por_seccion, comparar
from sb_asistente.model.mercado.registro import (
    Aseguradora,
    RegistroInvalidoError,
    cargar_registro,
    detectar,
    leer_registro,
)
from sb_asistente.model.rag.hibrido import RecuperadorHibrido

# --- Registro --------------------------------------------------------------------------------


def test_el_registro_real_carga_sin_errores_y_con_ids_unicos():
    # Arrange / Act
    registro = cargar_registro()
    # Assert
    ids = [a.id for a in registro]
    assert len(ids) == len(set(ids))
    assert "seguros-bolivar" in ids and "sura" in ids


def test_bolivar_usa_el_corpus_principal_y_no_se_vuelve_a_capturar():
    # Arrange
    bolivar = next(a for a in cargar_registro() if a.id == "seguros-bolivar")
    # Act / Assert
    assert bolivar.corpus_propio and not bolivar.hace_scraping


def test_las_aseguradoras_inactivas_no_hacen_scraping_pero_siguen_en_el_registro():
    # Arrange
    registro = cargar_registro()
    # Act
    inactivas = [a for a in registro if not a.activo]
    # Assert
    assert inactivas and all(not a.hace_scraping for a in inactivas)


def test_todos_los_sitios_del_registro_son_https():
    # Arrange / Act
    sitios = [a.sitio for a in cargar_registro() if a.sitio]
    # Assert
    assert sitios and all(s.startswith("https://") for s in sitios)


@pytest.mark.parametrize(
    ("toml", "mensaje"),
    [
        ('[[aseguradora]]\nid = "Sura"\nnombre = "Sura"', "id inválido"),
        ('[[aseguradora]]\nid = "sura"\nnombre = ""', "no tiene nombre"),
        ('[[aseguradora]]\nid = "sura"\nnombre = "Sura"\nsitio = "http://x.co"', "https"),
        ('[[aseguradora]]\nid = "sura"\nnombre = "Sura"\nprefijo = "co"', "prefijo"),
        ('[[aseguradora]]\nid = "a"\nnombre = "A"\n[[aseguradora]]\nid = "a"\nnombre = "B"', "repetido"),
        ('titulo = "sin bloques"', "no tiene bloques"),
        ('[[aseguradora]]\nid = "sura"\nnombre = "Sura"\nalias = "sura"', "alias debe ser una lista"),
    ],
)
def test_un_registro_mal_escrito_falla_al_cargar(toml, mensaje):
    # Arrange / Act / Assert
    with pytest.raises(RegistroInvalidoError, match=mensaje):
        leer_registro(toml)


def test_un_bloque_minimo_toma_los_valores_por_defecto():
    # Arrange
    toml = '[[aseguradora]]\nid = "nueva"\nnombre = "Nueva"\nsitio = "https://www.nueva.co/"'
    # Act
    [a] = leer_registro(toml)
    # Assert
    assert (a.sitio, a.activo, a.verificado, a.hace_scraping, a.dominio) == (
        "https://www.nueva.co",
        True,
        False,
        True,
        "www.nueva.co",
    )


# --- Detección de aseguradoras en un mensaje ---------------------------------------------------


@pytest.mark.parametrize(
    ("mensaje", "esperado"),
    [
        ("¿Qué cubre el SOAT de Sura?", ["sura"]),
        ("Compara Allianz con MAPFRE", ["allianz", "mapfre"]),
        ("cotiza con Seguros del Estado", ["seguros-del-estado"]),
        ("¿Liberty Seguros todavía existe?", ["hdi"]),
        ("mi BMI es normal", []),
        ("AXA Colpatria vs Bolívar", ["axa-colpatria", "seguros-bolivar"]),
        ("una respuesta positiva del estado", []),
        ("quiero asegurarme", []),
        ("la ARL Positiva cubre accidentes", ["positiva"]),
        ("planes de Colsanitas", ["colsanitas"]),
        ("BNP Paribas Cardif o Colmena", ["cardif", "colmena"]),
    ],
)
def test_detectar_encuentra_las_aseguradoras_nombradas_en_orden(mensaje, esperado):
    # Arrange
    registro = cargar_registro()
    # Act
    encontradas = detectar(mensaje, registro)
    # Assert
    assert encontradas == esperado


# --- Alcance, prioridad y secciones ----------------------------------------------------------

SITIO = "https://www.aseguradora.co"


@pytest.mark.parametrize(
    ("ruta", "dentro"),
    [
        ("/seguros/autos", True),
        ("/personas/seguro-de-hogar", True),
        ("/canales-de-atencion", True),
        ("/empresas/cumplimiento", False),
        ("/pymes", False),
        ("/blog/consejos-de-manejo", False),
        ("/noticias/2026/premio", False),
        ("/trabaja-con-nosotros", False),
        ("/politica-de-privacidad", False),
        ("/documentos/clausulado.pdf", False),
        ("/inversionistas", False),
        ("/en/about", False),
        ("/cotizar-soat", False),
        ("/seguros/autos/cotizador", False),
        ("/compra-tu-seguro", False),
        ("/pagos", False),
        ("/pago-en-linea", False),
        ("/pse", False),
        ("/radicar-siniestro", False),
        ("/reportar-siniestro", False),
        ("/formulario-de-reclamacion", False),
        ("/siniestros", True),
        ("/medios-de-pago", True),
        ("/compania", True),
    ],
)
def test_en_alcance_deja_personas_y_canales_y_saca_lo_demas(ruta, dentro):
    # Arrange / Act / Assert
    assert secciones.en_alcance(f"{SITIO}{ruta}") is dentro


@pytest.mark.parametrize(
    ("ruta", "dentro"),
    [
        ("/colombia/seguros/salud", True),
        ("/colombia", True),
        ("/mexico/seguros/salud", False),
        ("/colombiana", False),
    ],
)
def test_el_prefijo_limita_el_alcance_a_un_pais(ruta, dentro):
    # Arrange / Act / Assert
    assert secciones.en_alcance(f"{SITIO}{ruta}", prefijo="/colombia") is dentro


@pytest.mark.parametrize(
    ("ruta", "titulo", "seccion"),
    [
        ("/seguros/soat", "", "movilidad"),
        ("/personas/seguro-de-autos", "", "movilidad"),
        ("/seguro-de-hogar", "", "hogar_y_mascotas"),
        ("/seguro-mascotas", "", "hogar_y_mascotas"),
        ("/seguro-de-vida", "", "vida_y_ahorro"),
        ("/exequiales", "", "vida_y_ahorro"),
        ("/plan-complementario-de-salud", "", "salud"),
        ("/arl", "", "arl"),
        ("/canales-de-atencion", "", "canales_y_servicio"),
        ("/reclamaciones", "", "canales_y_servicio"),
        ("/quienes-somos", "", "institucional"),
        ("/", "", "institucional"),
        ("/producto-123", "Seguro de vida para tu familia", "vida_y_ahorro"),
        ("/producto-456", "Hola", "otros"),
    ],
)
def test_clasificar_seccion_usa_la_ruta_y_si_no_basta_el_titulo(ruta, titulo, seccion):
    # Arrange / Act / Assert
    assert secciones.clasificar_seccion(f"{SITIO}{ruta}", titulo) == seccion


def test_la_prioridad_captura_primero_las_paginas_de_producto():
    # Arrange
    urls = [
        f"{SITIO}/quienes-somos",
        f"{SITIO}/seguros/seguro-de-autos",
        f"{SITIO}/contacto",
        f"{SITIO}/soat",
    ]
    # Act
    primeras = secciones.ordenar_por_prioridad(urls, 2)
    # Assert
    assert primeras == [f"{SITIO}/seguros/seguro-de-autos", f"{SITIO}/soat"]


def test_ordenar_por_prioridad_no_repite_urls():
    # Arrange
    urls = [f"{SITIO}/soat", f"{SITIO}/soat", f"{SITIO}/hogar"]
    # Act / Assert
    assert len(secciones.ordenar_por_prioridad(urls, 10)) == 2


# --- WhatsApp oficial ------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("crudo", "esperado"),
    [
        ("573001234567", "573001234567"),
        ("+57 300 123 4567", "573001234567"),
        ("3001234567", "573001234567"),
        ("6017441234", "576017441234"),
        ("%2B573001234567", "573001234567"),
        ("12345", None),
        ("15551234567", None),
        ("", None),
    ],
)
def test_normalizar_numero_acepta_solo_numeros_de_colombia(crudo, esperado):
    # Arrange / Act / Assert
    assert contactos.normalizar_numero(crudo) == esperado


def test_whatsapp_de_html_lee_wa_me_y_api_whatsapp_sin_repetir():
    # Arrange
    html = """
    <a href="https://wa.me/573001234567">WhatsApp</a>
    <a href="https://api.whatsapp.com/send?phone=573001234567&text=hola">Otra vez</a>
    <a href="https://api.whatsapp.com/send?phone=+57 310 765 4321">Ventas</a>
    <a href="https://www.facebook.com/aseguradora">Facebook</a>
    """
    # Act
    numeros = contactos.whatsapp_de_html(html)
    # Assert
    assert numeros == ["573001234567", "573107654321"]


def test_el_whatsapp_principal_es_el_que_mas_paginas_enlazan():
    # Arrange
    paginas = [["573001111111", "573002222222"], ["573002222222"], ["573002222222", "573002222222"]]
    # Act / Assert
    assert contactos.whatsapp_principal(paginas)[0] == "573002222222"


def test_enlace_whatsapp_codifica_el_texto_del_caso():
    # Arrange / Act
    enlace = contactos.enlace_whatsapp("3001234567", "Hola: tengo una filtración en el techo")
    # Assert
    assert (
        enlace == "https://wa.me/573001234567?text=Hola%3A%20tengo%20una%20filtraci%C3%B3n%20en%20el%20techo"
    )


def test_enlace_whatsapp_rechaza_un_numero_extranjero():
    # Arrange / Act / Assert
    with pytest.raises(ValueError, match="no válido"):
        contactos.enlace_whatsapp("15551234567", "hola")


# --- Pipeline con un sitio en memoria --------------------------------------------------------


@dataclass
class Respuesta:
    """Respuesta HTTP mínima del doble."""

    status_code: int
    content: bytes


class SitioFalso:
    """Doble de requests.Session con rutas en memoria; registra lo que se pidió."""

    def __init__(self, rutas: dict[str, tuple[int, str]]) -> None:
        """Recibe ``url → (estado, cuerpo)``."""
        self.rutas = rutas
        self.pedidas: list[str] = []

    def get(self, url: str, *, timeout: float, headers: dict[str, str]) -> Respuesta:
        """Devuelve la ruta registrada o un 404."""
        self.pedidas.append(url)
        estado, cuerpo = self.rutas.get(url, (404, ""))
        return Respuesta(estado, cuerpo.encode())


def sin_pausa(_: float) -> None:
    """Sleep falso: las pruebas no esperan."""


def sitemap(*urls: str) -> str:
    """Sitemap XML con las URLs dadas."""
    filas = "".join(f"<url><loc>{u}</loc></url>" for u in urls)
    return f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{filas}</urlset>'


PAGINA = """<html><head><title>{titulo} | Aseguradora Prueba</title></head><body>
<header>Menú</header><main><h1>{titulo}</h1><p>{texto}</p></main>
<footer><a href="https://wa.me/573001234567">WhatsApp</a></footer></body></html>"""
TEXTO = "Cobertura de daños por agua, incendio y terremoto para su vivienda, con asistencia 24 horas. " * 4

ASEGURADORA = Aseguradora(
    id="prueba", nombre="Aseguradora Prueba", sitio=SITIO, alias=("aseguradora prueba",)
)


def sitio_completo() -> SitioFalso:
    """Sitio con robots.txt (una ruta prohibida), sitemap y una página de producto."""
    return SitioFalso(
        {
            f"{SITIO}/robots.txt": (200, f"User-agent: *\nDisallow: /privado\nSitemap: {SITIO}/mapa.xml"),
            f"{SITIO}/mapa.xml": (
                200,
                sitemap(
                    f"{SITIO}/seguro-de-hogar",
                    f"{SITIO}/privado/ofertas",
                    f"{SITIO}/empresas/cumplimiento",
                    "https://otro-sitio.com/seguro",
                ),
            ),
            f"{SITIO}/seguro-de-hogar": (200, PAGINA.format(titulo="Seguro de hogar", texto=TEXTO)),
        }
    )


def test_descubrir_respeta_robots_el_alcance_y_el_dominio(tmp_path):
    # Arrange
    sesion = sitio_completo()
    # Act
    plan = mercado.descubrir_una(mercado.ClienteCortes(sesion, sleep=sin_pausa), ASEGURADORA, tmp_path)
    # Assert
    elegidas = [e["url"] for e in plan["seleccionadas"]]
    motivos = {d["url"]: d["motivo"] for d in plan["descartadas"]}
    assert elegidas == [f"{SITIO}/seguro-de-hogar"]
    assert motivos[f"{SITIO}/privado/ofertas"] == "robots.txt"
    assert motivos[f"{SITIO}/empresas/cumplimiento"] == "fuera de alcance"
    assert plan["total_sitemap"] == 3  # la URL de otro dominio ni siquiera entra
    assert (tmp_path / "prueba" / "plan_captura.json").is_file()


def test_sin_robots_legible_no_se_captura_nada(tmp_path):
    # Arrange
    sesion = SitioFalso({f"{SITIO}/robots.txt": (503, "")})
    # Act
    plan = mercado.descubrir_una(mercado.ClienteCortes(sesion, sleep=sin_pausa), ASEGURADORA, tmp_path)
    # Assert
    assert plan["seleccionadas"] == [] and "robots.txt no disponible" in plan["estado"]


def test_sin_sitemap_se_informa_y_no_se_inventan_urls(tmp_path):
    # Arrange
    sesion = SitioFalso({f"{SITIO}/robots.txt": (200, "User-agent: *\nAllow: /")})
    # Act
    plan = mercado.descubrir_una(mercado.ClienteCortes(sesion, sleep=sin_pausa), ASEGURADORA, tmp_path)
    # Assert
    assert plan["estado"] == "sin sitemap con páginas del sitio"
    assert f"{SITIO}/sitemap.xml" in sesion.pedidas


def test_capturar_y_procesar_dejan_chunks_con_aseguradora_seccion_y_whatsapp(tmp_path):
    # Arrange
    sesion = sitio_completo()
    bronze, silver, gold_dir = tmp_path / "raw", tmp_path / "silver", tmp_path / "gold"
    mercado.descubrir(sesion, [ASEGURADORA], out_dir=bronze, sleep=sin_pausa)
    # Act
    captura = mercado.capturar(sesion, [ASEGURADORA], out_dir=bronze, sleep=lambda s: None)
    resumen = mercado.procesar([ASEGURADORA], bronze, silver, gold_dir)
    # Assert
    chunks = [json.loads(linea) for linea in (gold_dir / "chunks.jsonl").read_text().splitlines()]
    assert captura == {"prueba": {"total": 1, "ok": 1, "fallidas": 0}}
    assert resumen["prueba"]["documentos"] == 1
    assert resumen["prueba"]["whatsapp"] == ["573001234567"]
    assert {c["aseguradora"] for c in chunks} == {"prueba"}
    assert chunks[0]["section"] == "hogar_y_mascotas"
    assert chunks[0]["title"] == "Seguro de hogar"  # sin « | Aseguradora Prueba»
    assert chunks[0]["chunk_id"].startswith("prueba--")


def test_activas_filtra_por_ids_pedidos():
    # Arrange
    otra = Aseguradora(id="otra", nombre="Otra", sitio="https://www.otra.co")
    # Act / Assert
    assert [a.id for a in mercado.activas([ASEGURADORA, otra], ["otra"])] == ["otra"]


def test_aseguradoras_con_un_id_desconocido_lanza_keyerror():
    # Arrange / Act / Assert
    with pytest.raises(KeyError, match="no registrada"):
        mercado.aseguradoras(["no-existe"])


# --- Buscador con filtro por aseguradora y comparación ---------------------------------------


CHUNKS = [
    chunk("a#0", "sura", "hogar_y_mascotas", "El seguro de hogar cubre filtraciones de agua y humedad."),
    chunk("b#0", "allianz", "hogar_y_mascotas", "Hogar: cubre daños por agua, incendio y robo."),
    chunk("c#0", "mapfre", "movilidad", "SOAT y seguro de autos con grúa."),
    chunk("d#0", "sura", "movilidad", "Seguro de autos todo riesgo con grúa."),
]


def test_buscar_con_aseguradora_solo_devuelve_esa_compania():
    # Arrange
    buscador = RecuperadorHibrido(CHUNKS)
    # Act
    fragmentos = buscador.buscar("seguro de autos grúa", k=5, aseguradora="mapfre")
    # Assert
    assert [f.aseguradora for f in fragmentos] == ["mapfre"]


def test_buscar_sin_filtro_mantiene_el_comportamiento_anterior():
    # Arrange
    buscador = RecuperadorHibrido(CHUNKS)
    # Act
    fragmentos = buscador.buscar("agua", k=5)
    # Assert
    assert {f.aseguradora for f in fragmentos} == {"sura", "allianz"}


def test_buscar_combina_seccion_y_aseguradora():
    # Arrange
    buscador = RecuperadorHibrido(CHUNKS)
    # Act
    fragmentos = buscador.buscar("seguro", k=5, seccion="movilidad", aseguradora="sura")
    # Assert
    assert [f.chunk_id for f in fragmentos] == ["d#0"]


def test_comparar_pone_primero_a_las_que_publican_informacion():
    # Arrange
    buscador = RecuperadorHibrido(CHUNKS)
    elegidas = [
        Aseguradora("mapfre", "MAPFRE"),
        Aseguradora("sura", "SURA"),
        Aseguradora("allianz", "Allianz"),
    ]
    # Act
    ofertas = comparar(buscador, "filtraciones de agua en el hogar", elegidas, por_aseguradora=1)
    # Assert
    assert [o.aseguradora for o in ofertas] == ["sura", "allianz", "mapfre"]
    assert not ofertas[-1].tiene_informacion


@pytest.mark.parametrize(
    ("consulta", "aseguradoras", "por", "mensaje"),
    [
        (" ", [Aseguradora("sura", "SURA")], 1, "vacía"),
        ("hogar", [], 1, "al menos una"),
        ("hogar", [Aseguradora(f"a{i}", "A") for i in range(9)], 1, "como máximo"),
        ("hogar", [Aseguradora("sura", "SURA")], 4, "entre 1 y 3"),
    ],
)
def test_comparar_valida_sus_parametros(consulta, aseguradoras, por, mensaje):
    # Arrange
    buscador = RecuperadorHibrido(CHUNKS)
    # Act / Assert
    with pytest.raises(ValueError, match=mensaje):
        comparar(buscador, consulta, aseguradoras, por_aseguradora=por)


def test_cobertura_por_seccion_cuenta_documentos_no_chunks():
    # Arrange
    chunks = [*CHUNKS, chunk("a#1", "sura", "hogar_y_mascotas", "Otro fragmento del mismo documento.")]
    # Act
    cobertura = cobertura_por_seccion(chunks)
    # Assert
    assert cobertura["hogar_y_mascotas"] == {"sura": 1, "allianz": 1}
    assert cobertura["movilidad"] == {"mapfre": 1, "sura": 1}


def test_chunks_mercado_etiqueta_el_corpus_principal_como_bolivar(tmp_path):
    # Arrange
    principal = tmp_path / "chunks.jsonl"
    principal.write_text(json.dumps({**CHUNKS[0], "aseguradora": None}) + "\n")
    otro = tmp_path / "mercado.jsonl"
    otro.write_text(json.dumps(CHUNKS[2]) + "\n")
    # Act
    todos = mercado.chunks_mercado(otro, principal)
    # Assert
    assert [c["aseguradora"] for c in todos if c["chunk_id"] in ("a#0", "c#0")] == [
        "seguros-bolivar",
        "mapfre",
    ]


def test_comparar_deja_un_fragmento_por_pagina():
    # Arrange
    chunks = [
        chunk("x#0", "sura", "hogar_y_mascotas", "Hogar: cubre agua y humedad."),
        chunk("x#1", "sura", "hogar_y_mascotas", "Hogar: más sobre agua y humedad."),
        chunk("y#0", "sura", "hogar_y_mascotas", "Hogar digital: agua."),
    ]
    buscador = RecuperadorHibrido(chunks)
    # Act
    [oferta] = comparar(buscador, "agua humedad hogar", [Aseguradora("sura", "SURA")], por_aseguradora=2)
    # Assert
    assert sorted(f.url for f in oferta.fragmentos) == ["https://sura.co/x", "https://sura.co/y"]


def test_descubrir_hace_una_pausa_entre_cada_peticion(tmp_path):
    # Arrange
    sesion = sitio_completo()
    pausas: list[float] = []
    # Act
    mercado.descubrir(sesion, [ASEGURADORA], out_dir=tmp_path, sleep=pausas.append)
    # Assert
    assert len(sesion.pedidas) == 2  # robots.txt y el sitemap
    assert pausas == [mercado.REQUEST_DELAY_S]  # una pausa entre las dos peticiones


def test_cliente_cortes_no_espera_antes_de_la_primera_peticion():
    # Arrange
    pausas: list[float] = []
    cliente = mercado.ClienteCortes(SitioFalso({}), delay_s=1.5, sleep=pausas.append)
    # Act
    cliente.get(f"{SITIO}/a")
    cliente.get(f"{SITIO}/b")
    cliente.get(f"{SITIO}/c")
    # Assert
    assert pausas == [1.5, 1.5]


def test_un_sitemap_con_un_dominio_parecido_no_cuela_urls_ajenas(tmp_path):
    # Arrange
    sesion = SitioFalso(
        {
            f"{SITIO}/robots.txt": (200, "User-agent: *\nAllow: /"),
            f"{SITIO}/sitemap.xml": (
                200,
                sitemap(f"{SITIO}.evil.net/seguro-de-hogar", f"{SITIO}/seguro-de-hogar"),
            ),
        }
    )
    # Act
    plan = mercado.descubrir_una(mercado.ClienteCortes(sesion, sleep=sin_pausa), ASEGURADORA, tmp_path)
    # Assert
    assert [e["url"] for e in plan["seleccionadas"]] == [f"{SITIO}/seguro-de-hogar"]


def test_comparar_sin_aseguradoras_relevantes_devuelve_lista_vacia():
    # Arrange
    buscador = RecuperadorHibrido(CHUNKS)
    # Act
    ofertas = mercado.comparar_aseguradoras(buscador, "criptomonedas espaciales")
    # Assert
    assert ofertas == []


def test_detectar_aseguradoras_usa_el_registro_real():
    # Arrange / Act / Assert
    assert mercado.detectar_aseguradoras("¿MAPFRE o HDI?") == ["mapfre", "hdi"]


def test_una_verificacion_fallida_invalida_el_plan_anterior(tmp_path):
    # Arrange
    mercado.descubrir_una(mercado.ClienteCortes(sitio_completo(), sleep=sin_pausa), ASEGURADORA, tmp_path)
    caido = SitioFalso({f"{SITIO}/robots.txt": (503, "")})
    # Act
    mercado.descubrir_una(mercado.ClienteCortes(caido, sleep=sin_pausa), ASEGURADORA, tmp_path)
    capturado = mercado.capturar(caido, [ASEGURADORA], out_dir=tmp_path, sleep=sin_pausa)
    # Assert
    plan = json.loads((tmp_path / "prueba" / "plan_captura.json").read_text())
    assert plan["seleccionadas"] == [] and "robots.txt no disponible" in plan["estado"]
    assert capturado == {"prueba": {"total": 0, "ok": 0, "fallidas": 0}}
    assert caido.pedidas == [f"{SITIO}/robots.txt"]  # ninguna página del plan viejo


def test_los_sitemaps_hijos_de_otro_sitio_o_prohibidos_no_se_piden(tmp_path):
    # Arrange
    indice = (
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<sitemap><loc>{SITIO}/hijo.xml</loc></sitemap>"
        f"<sitemap><loc>{SITIO}/privado/hijo.xml</loc></sitemap>"
        "<sitemap><loc>https://otro-sitio.com/hijo.xml</loc></sitemap>"
        "</sitemapindex>"
    )
    sesion = SitioFalso(
        {
            f"{SITIO}/robots.txt": (200, f"User-agent: *\nDisallow: /privado\nSitemap: {SITIO}/indice.xml"),
            f"{SITIO}/indice.xml": (200, indice),
            f"{SITIO}/hijo.xml": (200, sitemap(f"{SITIO}/seguro-de-hogar")),
        }
    )
    # Act
    plan = mercado.descubrir_una(mercado.ClienteCortes(sesion, sleep=sin_pausa), ASEGURADORA, tmp_path)
    # Assert
    assert f"{SITIO}/privado/hijo.xml" not in sesion.pedidas
    assert "https://otro-sitio.com/hijo.xml" not in sesion.pedidas
    assert [e["url"] for e in plan["seleccionadas"]] == [f"{SITIO}/seguro-de-hogar"]


@pytest.mark.parametrize("solo", [["no-existe"], ["proagro"], ["seguros-bolivar"]])
def test_activas_rechaza_ids_desconocidos_o_sin_scraping(solo):
    # Arrange
    registro = cargar_registro()
    # Act / Assert
    with pytest.raises(KeyError, match="no hacen scraping"):
        mercado.activas(registro, solo)


def test_comparar_con_ids_repetidos_no_duplica_ofertas():
    # Arrange
    buscador = RecuperadorHibrido(CHUNKS)
    # Act
    ofertas = mercado.comparar_aseguradoras(buscador, "hogar agua", ["sura", "sura", "allianz"])
    # Assert
    assert [o.aseguradora for o in ofertas].count("sura") == 1


@pytest.fixture
def cache_limpia() -> Iterator[None]:
    """Vacía la caché del buscador de mercado antes y después (aunque la prueba falle)."""
    mercado._recuperador_para.cache_clear()
    try:
        yield
    finally:
        mercado._recuperador_para.cache_clear()


def test_sin_corpus_el_buscador_de_mercado_avisa_datos_no_listos(tmp_path, monkeypatch, cache_limpia):
    # Arrange
    monkeypatch.setattr(mercado, "CHUNKS_JSONL", tmp_path / "no-existe.jsonl")
    monkeypatch.setattr(mercado, "MERCADO_CHUNKS_JSONL", tmp_path / "tampoco.jsonl")
    monkeypatch.setattr(mercado, "chunks_mercado", lambda: [])
    # Act / Assert
    with pytest.raises(FileNotFoundError, match="make mercado"):
        mercado.recuperador_mercado()


def test_el_buscador_de_mercado_se_reconstruye_si_cambia_el_corpus(tmp_path, monkeypatch, cache_limpia):
    # Arrange
    corpus = tmp_path / "mercado.jsonl"
    corpus.write_text(json.dumps(CHUNKS[0]) + "\n")
    monkeypatch.setattr(mercado, "MERCADO_CHUNKS_JSONL", corpus)
    monkeypatch.setattr(mercado, "CHUNKS_JSONL", tmp_path / "principal.jsonl")
    monkeypatch.setattr(
        mercado, "chunks_mercado", lambda: [json.loads(x) for x in corpus.read_text().splitlines()]
    )
    primero = mercado.recuperador_mercado()
    # Act
    corpus.write_text(json.dumps(CHUNKS[0]) + "\n" + json.dumps(CHUNKS[2]) + "\n")
    os.utime(corpus, (corpus.stat().st_atime, corpus.stat().st_mtime + 10))
    segundo = mercado.recuperador_mercado()
    # Assert
    assert primero is not segundo and len(segundo.chunks) == 2


def test_un_sitemap_de_robots_en_otro_dominio_no_se_pide(tmp_path):
    # Arrange
    sesion = SitioFalso(
        {f"{SITIO}/robots.txt": (200, "User-agent: *\nSitemap: https://otro-sitio.com/mapa.xml")}
    )
    # Act
    plan = mercado.descubrir_una(mercado.ClienteCortes(sesion, sleep=sin_pausa), ASEGURADORA, tmp_path)
    # Assert
    assert sesion.pedidas == [f"{SITIO}/robots.txt"]
    assert plan["estado"] == "sin sitemap con páginas del sitio"


def test_leer_resumen_devuelve_lo_que_dejo_procesar_o_vacio(tmp_path):
    # Arrange
    vacio = tmp_path / "sin-datos"
    (tmp_path / "resumen.json").write_text(json.dumps({"sura": {"documentos": 4}}))
    # Act
    con_datos, sin_datos = mercado.leer_resumen(tmp_path), mercado.leer_resumen(vacio)
    # Assert
    assert con_datos == {"sura": {"documentos": 4}} and sin_datos == {}


def test_registro_con_datos_cuenta_los_documentos_del_corpus_principal(tmp_path):
    # Arrange
    principal = tmp_path / "chunks.jsonl"
    filas = [
        chunk("doc-a#0", "x", "salud", "t"),
        chunk("doc-a#1", "x", "salud", "t"),
        chunk("doc-b#0", "x", "salud", "t"),
    ]
    principal.write_text("".join(json.dumps(f) + "\n" for f in filas))
    # Act
    registro = {f["id"]: f for f in mercado.registro_con_datos(tmp_path, principal)}
    # Assert
    assert registro["seguros-bolivar"]["documentos"] == 2
    assert registro["sura"]["documentos"] == 0


@pytest.mark.parametrize(
    ("argumentos", "mensaje"),
    [
        (["mercado", "verificar", "--solo", "no-existe"], "no hacen scraping"),
        (["mercado", "comparar", "hogar", "--aseguradoras", "no-existe"], "no registrada"),
    ],
)
def test_la_cli_de_mercado_muestra_un_mensaje_en_vez_de_un_traceback(argumentos, mensaje, capsys):
    # Arrange
    from sb_asistente.view import cli

    # Act
    codigo = cli.main(argumentos)
    # Assert
    assert codigo == 1 and mensaje in capsys.readouterr().out


def test_el_whatsapp_de_una_sola_pagina_no_se_guarda_por_ser_posible_dato_personal():
    # Arrange: el del pie sale en las 4 páginas; el de un asesor, solo en una
    pie, asesor = "573001111111", "573109999999"
    paginas = [[pie], [pie], [pie, asesor], [pie]]
    # Act
    numeros = contactos.whatsapp_principal(paginas)
    # Assert
    assert numeros == [pie]


@pytest.mark.parametrize("seccion", ["hogar_y_mascotas", "movilidad", "canales_y_servicio", "otros"])
def test_validar_seccion_acepta_las_secciones_conocidas(seccion):
    # Arrange / Act / Assert
    assert mercado.validar_seccion(seccion) == seccion


def test_validar_seccion_rechaza_una_desconocida():
    # Arrange / Act / Assert
    with pytest.raises(ValueError, match="Sección desconocida"):
        mercado.validar_seccion("criptomonedas")


def test_la_cli_de_mercado_convierte_un_valor_invalido_en_mensaje(capsys, monkeypatch):
    # Arrange: buscador en memoria, la prueba no depende de data/ (que no se versiona)
    from sb_asistente.view import cli

    monkeypatch.setattr(mercado, "recuperador_mercado", lambda: RecuperadorHibrido(CHUNKS))

    ids = ["sura", "allianz", "mapfre", "hdi", "solidaria", "axa-colpatria", "cardif", "colmena", "zurich"]
    # Act
    codigo = cli.main(["mercado", "comparar", "hogar", "--aseguradoras", *ids])
    # Assert
    assert codigo == 1 and "como máximo" in capsys.readouterr().out

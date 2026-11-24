"""Casos tabulados del clasificador de intención (SPEC-059).

Cada tabla fija el comportamiento esperado de una regla con frases reales de clientes, para
que un cambio en los patrones muestre exactamente qué frase cambió de etiqueta.
"""

import pytest

from sb_asistente.model.intencion import Perfil, clasificar, extraer_perfil, normalizar

# --- normalizar ---------------------------------------------------------------------------------

NORMALIZACIONES = [
    ("Hola", "hola"),
    ("PÓLIZA", "poliza"),
    ("¿Qué cubre el SOAT?", "que cubre el soat"),
    ("  muchos    espacios  ", "muchos espacios"),
    ("línea\tde\natención", "linea de atencion"),
    ("Pingüino", "pinguino"),
    ("Ñandú", "nandu"),
    ("¡¡Urgente!!", "urgente"),
    ("seguro-de-hogar", "seguro de hogar"),
    ("A.R.L.", "a r l"),
    ("100% cubierto", "100 cubierto"),
    ("mascota_feliz", "mascota_feliz"),
    ("", ""),
    ("   ", ""),
    ("Café, té; agua.", "cafe te agua"),
]


@pytest.mark.parametrize(("entrada", "esperado"), NORMALIZACIONES)
def test_normalizar_quita_tildes_signos_y_espacios(entrada, esperado):
    # Arrange: la frase viene de la tabla
    # Act
    resultado = normalizar(entrada)
    # Assert
    assert resultado == esperado


@pytest.mark.parametrize("entrada", [e for e, _ in NORMALIZACIONES])
def test_normalizar_es_idempotente(entrada):
    # Arrange
    una_vez = normalizar(entrada)
    # Act
    dos_veces = normalizar(una_vez)
    # Assert
    assert dos_veces == una_vez


# --- clasificar: recomendación -----------------------------------------------------------------

RECOMENDACIONES = [
    "¿Qué seguro me recomiendan?",
    "Recomiéndeme un seguro",
    "Quiero una recomendación de seguros",
    "¿Qué me sugieren para mi familia?",
    "¿Me conviene un seguro de vida?",
    "¿Qué seguro me sirve si tengo moto?",
    "¿Qué seguros debo tener?",
    "¿Qué seguro debería comprar?",
    "¿Cuál seguro me conviene?",
    "¿Cuáles seguros debería tomar?",
    "¿Qué me ofrecen para el carro?",
    "¿Qué seguros necesito?",
]


@pytest.mark.parametrize("mensaje", RECOMENDACIONES)
def test_pedidos_de_recomendacion(mensaje):
    # Arrange: frase que pide consejo de producto
    # Act
    intencion = clasificar(mensaje)
    # Assert
    assert intencion.etiqueta == "recomendacion"


@pytest.mark.parametrize(
    ("mensaje", "confianza"),
    [
        ("¿Qué seguro me recomiendan?", 0.75),
        ("¿Qué seguro me recomiendan? tengo un perro", 0.9),
        ("Recomiéndeme algo, vivo en arriendo", 0.9),
        ("¿Qué seguros necesito? no tengo carro", 0.9),
        ("Sugiéranme un seguro", 0.75),
    ],
)
def test_la_recomendacion_es_mas_confiable_con_perfil(mensaje, confianza):
    # Arrange: con o sin datos de perfil en el mensaje
    # Act
    intencion = clasificar(mensaje)
    # Assert
    assert intencion.confianza == confianza


# --- clasificar: saludo ------------------------------------------------------------------------

SALUDOS = [
    "Hola",
    "hola!",
    "Buenos días",
    "buenas tardes",
    "Buenas noches",
    "Hey",
    "Saludos",
    "Gracias",
    "Muchas gracias",
    "ok",
    "Listo",
    "Perfecto",
    "chao",
    "Adiós",
]


@pytest.mark.parametrize("mensaje", SALUDOS)
def test_saludos_cortos(mensaje):
    # Arrange
    # Act
    intencion = clasificar(mensaje)
    # Assert
    assert (intencion.etiqueta, intencion.confianza, intencion.seccion) == ("saludo", 0.95, None)


@pytest.mark.parametrize(
    "mensaje",
    [
        "Hola, ¿qué cubre el SOAT?",
        "Buenos días, necesito el horario de las oficinas",
        "Gracias, ¿y la póliza de hogar?",
        "hola quiero saber de seguros",
    ],
)
def test_un_saludo_con_pregunta_de_seguros_no_es_saludo(mensaje):
    # Arrange: saludo seguido de vocabulario del dominio
    # Act
    intencion = clasificar(mensaje)
    # Assert
    assert intencion.etiqueta == "conocimiento"


def test_un_saludo_largo_sin_dominio_no_es_saludo():
    # Arrange: más de seis palabras
    mensaje = "hola cómo están todos ustedes en este bonito día"
    # Act
    intencion = clasificar(mensaje)
    # Assert
    assert intencion.etiqueta != "saludo"


# --- clasificar: fuera de alcance --------------------------------------------------------------

FUERA = [
    "¿Quién ganó el mundial?",
    "Hablemos de fútbol",
    "Dame una receta de arepas",
    "¿Cómo está el clima hoy?",
    "Recomiéndame una película",  # ojo: es recomendación (gana la regla de recomendación)
    "Cuéntame un chiste",
    "¿Cómo programar en Rust?",
    "Escribe código en python",
    "¿Quién es el presidente?",
    "¿Cuándo son las elecciones?",
    "¿A cuánto está el bitcoin?",
    "Compra acciones de Apple",
    "¿Cuál es mi horóscopo?",
    "Pon una canción",
]


@pytest.mark.parametrize("mensaje", [m for m in FUERA if "película" not in m])
def test_temas_ajenos_sin_vocabulario_de_seguros(mensaje):
    # Arrange
    # Act
    intencion = clasificar(mensaje)
    # Assert
    assert (intencion.etiqueta, intencion.confianza) == ("fuera_de_alcance", 0.9)


def test_pedir_una_pelicula_es_recomendacion_y_el_router_la_saca():
    # Arrange: la regla de recomendación tiene prioridad en el clasificador
    # Act
    intencion = clasificar("Recomiéndame una película")
    # Assert
    assert intencion.etiqueta == "recomendacion"


@pytest.mark.parametrize(
    "mensaje",
    [
        "¿El seguro cubre si me roban en el mundial?",
        "¿Hay seguro de viaje para ver fútbol?",
        "¿La póliza cubre el clima extremo?",
        "¿El SOAT cubre accidentes en elecciones?",
    ],
)
def test_tema_ajeno_con_vocabulario_de_seguros_es_conocimiento(mensaje):
    # Arrange
    # Act
    intencion = clasificar(mensaje)
    # Assert
    assert intencion.etiqueta == "conocimiento"


# --- clasificar: conocimiento y secciones -------------------------------------------------------

SECCIONES = [
    ("¿Cuál es el WhatsApp de atención?", "canales_y_servicio"),
    ("¿Cuál es la línea telefónica?", "canales_y_servicio"),
    ("¿Dónde queda la sede principal?", "canales_y_servicio"),
    ("¿Cómo radico una PQR?", "canales_y_servicio"),
    ("¿Cuál es el horario de las oficinas?", "canales_y_servicio"),
    ("¿Cómo contacto al defensor del consumidor?", "canales_y_servicio"),
    ("¿Qué cubre el SOAT?", "movilidad"),
    ("Seguro para mi moto", "movilidad"),
    ("¿Tienen asistencia de grúa para el vehículo?", "movilidad"),
    ("Seguro de hogar para mi apartamento", "hogar_y_mascotas"),
    ("¿Hay seguro para mi perro?", "hogar_y_mascotas"),
    ("Póliza para mi gato", "hogar_y_mascotas"),
    ("Seguro de vida con ahorro", "vida_y_ahorro"),
    ("Seguro de accidentes personales", "vida_y_ahorro"),
    ("Seguro para el crédito de educación", "vida_y_ahorro"),
    ("Seguro de salud con cobertura de cáncer", "salud"),
    ("¿Qué clínicas cubre la póliza de salud?", "salud"),
    ("Afiliación ARL para independiente", "arl"),
    ("¿Qué cubre la ARL en riesgos laborales?", "arl"),
]


@pytest.mark.parametrize(("mensaje", "seccion"), SECCIONES)
def test_conocimiento_detecta_la_seccion_del_sitio(mensaje, seccion):
    # Arrange
    # Act
    intencion = clasificar(mensaje)
    # Assert
    assert (intencion.etiqueta, intencion.seccion) == ("conocimiento", seccion)


@pytest.mark.parametrize(("mensaje", "_"), SECCIONES)
def test_conocimiento_con_dominio_tiene_confianza_entre_07_y_095(mensaje, _):
    # Arrange
    # Act
    intencion = clasificar(mensaje)
    # Assert
    assert 0.7 <= intencion.confianza <= 0.95


@pytest.mark.parametrize(
    "mensaje",
    ["¿Qué hago?", "necesito ayuda", "explíqueme por favor", "tengo una duda", "no entiendo"],
)
def test_sin_vocabulario_queda_en_conocimiento_con_confianza_baja(mensaje):
    # Arrange
    # Act
    intencion = clasificar(mensaje)
    # Assert
    assert (intencion.etiqueta, intencion.confianza) == ("conocimiento", 0.4)


def test_la_confianza_crece_con_el_vocabulario_y_se_topa_en_095():
    # Arrange: muchas palabras del dominio
    mensaje = "seguro póliza soat cobertura siniestro reclamación asegurado bolívar vehículo"
    # Act
    intencion = clasificar(mensaje)
    # Assert
    assert intencion.confianza == 0.95


@pytest.mark.parametrize("mensaje", ["", "   ", "\n\t"])
def test_mensaje_vacio_lanza_error(mensaje):
    # Arrange
    # Act / Assert
    with pytest.raises(ValueError, match="vacío"):
        clasificar(mensaje)


@pytest.mark.parametrize("mensaje", ["¿Qué cubre el SOAT?", "Hola", "¿Quién ganó el mundial?"])
def test_siempre_explica_la_decision_con_senales(mensaje):
    # Arrange
    # Act
    intencion = clasificar(mensaje)
    # Assert
    assert intencion.senales and all(isinstance(s, str) and s for s in intencion.senales)


# --- extraer_perfil -----------------------------------------------------------------------------

VEHICULOS = [
    ("Tengo un carro", "carro"),
    ("Manejo una camioneta", "carro"),
    ("Mi automóvil es viejo", "carro"),
    ("tengo vehículo", "carro"),
    ("Tengo moto", "moto"),
    ("Ando en motocicleta", "moto"),
    ("Mi carro es eléctrico", "electrico"),
    ("Tengo un híbrido", "electrico"),
    ("No tengo carro", "ninguno"),
    ("Vivo sin vehículo", "ninguno"),
    ("no tengo moto", "ninguno"),
    ("Me gusta caminar", None),
]


@pytest.mark.parametrize(("texto", "vehiculo"), VEHICULOS)
def test_perfil_vehiculo(texto, vehiculo):
    # Arrange
    # Act
    perfil = extraer_perfil(texto)
    # Assert
    assert perfil.vehiculo == vehiculo


VIVIENDAS = [
    ("Vivo en arriendo", "arrendada"),
    ("Mi apartamento es arrendado", "arrendada"),
    ("Alquilo una casa", "arrendada"),
    ("Pago renta cada mes", "arrendada"),
    ("Tengo casa propia", "propia"),
    ("Mi apartamento propio", "propia"),
    ("Vivo con mis papás", "familiar"),
    ("Vivo con mi familia", "familiar"),
    ("vivienda familiar", "familiar"),
    ("Vivo en Cali", None),
]


@pytest.mark.parametrize(("texto", "vivienda"), VIVIENDAS)
def test_perfil_vivienda(texto, vivienda):
    # Arrange
    # Act
    perfil = extraer_perfil(texto)
    # Assert
    assert perfil.vivienda == vivienda


MASCOTAS = [
    ("Tengo un perro", True),
    ("Tengo dos gatos", True),
    ("Mi perrita se llama Luna", None),  # «perrita» no está en la regla: se documenta el límite
    ("Tengo mascotas", True),
    ("No tengo mascota", False),
    ("Vivo sin perro", False),
    ("Me gustan las plantas", None),
]


@pytest.mark.parametrize(("texto", "mascota"), MASCOTAS)
def test_perfil_mascota(texto, mascota):
    # Arrange
    # Act
    perfil = extraer_perfil(texto)
    # Assert
    assert perfil.tiene_mascota is mascota


CREDITOS = [
    ("Tengo un crédito hipotecario", True),
    ("Pago un préstamo", True),
    ("Tengo hipoteca", True),
    ("El carro está en leasing", True),
    ("No tengo crédito", False),
    ("Vivo sin deuda", False),
    ("Ahorro cada mes", None),
]


@pytest.mark.parametrize(("texto", "credito"), CREDITOS)
def test_perfil_credito(texto, credito):
    # Arrange
    # Act
    perfil = extraer_perfil(texto)
    # Assert
    assert perfil.tiene_credito is credito


def test_perfil_completo_en_una_frase():
    # Arrange
    texto = "Tengo moto, vivo en arriendo, tengo un gato y pago un préstamo"
    # Act
    perfil = extraer_perfil(texto)
    # Assert
    assert perfil == Perfil(vehiculo="moto", vivienda="arrendada", tiene_mascota=True, tiene_credito=True)


@pytest.mark.parametrize(
    ("perfil", "conocido"),
    [
        (Perfil(), {}),
        (Perfil(vehiculo="carro"), {"vehiculo": "carro"}),
        (Perfil(tiene_mascota=False), {"tiene_mascota": False}),
        (Perfil(vivienda="propia", tiene_credito=True), {"vivienda": "propia", "tiene_credito": True}),
    ],
)
def test_conocido_solo_devuelve_lo_mencionado(perfil, conocido):
    # Arrange
    # Act
    resultado = perfil.conocido()
    # Assert
    assert resultado == conocido

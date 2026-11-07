"""Pruebas del clasificador de intención y del extractor de perfil (AAA, sin red)."""

import pytest

from sb_asistente.model.intencion import clasificar, extraer_perfil, normalizar


@pytest.mark.parametrize(
    ("mensaje", "esperada"),
    [
        ("¿Cuál es el WhatsApp de atención?", "conocimiento"),
        ("¿El seguro de hogar cubre terremoto?", "conocimiento"),
        ("¿Qué seguro me recomiendas si tengo carro y un perro?", "recomendacion"),
        ("Qué seguros me conviene tener", "recomendacion"),
        ("Hola", "saludo"),
        ("muchas gracias!", "saludo"),
        ("¿Quién ganó el mundial de fútbol?", "fuera_de_alcance"),
        ("Dame una receta de arepas", "fuera_de_alcance"),
    ],
)
def test_clasifica_intenciones(mensaje, esperada):
    assert clasificar(mensaje).etiqueta == esperada


def test_saludo_con_pregunta_de_seguros_es_conocimiento():
    assert clasificar("Hola, ¿cómo reclamo el SOAT?").etiqueta == "conocimiento"


def test_tema_ajeno_que_menciona_seguros_va_al_qa():
    assert clasificar("¿El seguro cubre si veo el mundial en el estadio?").etiqueta == "conocimiento"


def test_sin_vocabulario_va_al_qa_con_baja_confianza():
    resultado = clasificar("¿Dónde queda eso?")
    assert resultado.etiqueta == "conocimiento" and resultado.confianza < 0.5


def test_seccion_detectada():
    assert clasificar("¿Cuál es la línea de atención?").seccion == "canales_y_servicio"


def test_seccion_movilidad():
    assert clasificar("¿Cómo compro el SOAT de la moto?").seccion == "movilidad"


def test_mensaje_vacio_falla():
    with pytest.raises(ValueError):
        clasificar("   ")


def test_confianza_entre_cero_y_uno():
    assert 0 <= clasificar("¿Qué cubre el seguro de vida?").confianza <= 1


def test_recomendacion_con_perfil_sube_confianza():
    con = clasificar("Recomiéndame un seguro, tengo moto")
    sin = clasificar("Recomiéndame un seguro")
    assert con.confianza > sin.confianza


def test_perfil_carro_perro_arriendo_credito():
    perfil = extraer_perfil("Tengo carro, un perro, vivo en arriendo y tengo un crédito")
    assert perfil.conocido() == {
        "vehiculo": "carro",
        "vivienda": "arrendada",
        "tiene_mascota": True,
        "tiene_credito": True,
    }


def test_perfil_negaciones():
    perfil = extraer_perfil("No tengo carro ni mascota, sin credito")
    assert perfil.vehiculo == "ninguno" and perfil.tiene_credito is False


def test_perfil_electrico_y_casa_propia():
    perfil = extraer_perfil("Tengo un carro eléctrico y casa propia")
    assert perfil.vehiculo == "electrico" and perfil.vivienda == "propia"


def test_perfil_vacio():
    assert extraer_perfil("¿Qué es el SOAT?").conocido() == {}


def test_normalizar_quita_tildes_y_signos():
    assert normalizar("¿Pólizá  SOAT?") == "poliza soat"

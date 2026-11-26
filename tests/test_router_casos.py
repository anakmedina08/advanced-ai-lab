"""Casos tabulados del router de rutas del agente (SPEC-060).

El router decide qué tools ve el modelo en cada turno; un error aquí cuesta tokens (tools de
más) o respuestas pobres (tools de menos). Cada tabla cubre una rama de ``enrutar``.
"""

import pytest

from sb_asistente.model.router import (
    CONOCIMIENTO,
    MERCADO,
    TODAS,
    TOOLS_POR_RUTA,
    UMBRAL_CAUTELA,
    Decision,
    enrutar,
)

DATOS = [
    "¿Cuántas pólizas se vendieron?",
    "¿Cuántos clientes tenemos?",
    "Total de siniestros",
    "Suma de primas del año",
    "Promedio de reclamaciones",
    "Número de pólizas activas",
    "¿Cuántas pólizas de hogar hay?",
    "Ventas por canal",
    "¿Cuánto vendimos este trimestre?",
    "¿Qué hay en la cartera?",
    "Descarga el csv de pólizas",
    "Pólizas vendidas por canal",
    "monto total de primas",
    "cantidad de siniestros de autos",
]


@pytest.mark.parametrize("mensaje", DATOS)
def test_preguntas_numericas_van_a_datos(mensaje):
    # Arrange
    # Act
    decision = enrutar(mensaje)
    # Assert
    assert (decision.ruta, decision.tools, decision.confianza) == ("datos", ("consultar_datos",), 0.9)


MIXTOS = [
    "¿Cuántas pólizas se vendieron y qué dice el documento de hogar?",
    "Ventas por canal frente a lo que dice la página del SOAT",
    "Total de siniestros, según la política de reclamaciones",
    "¿Cuántos clientes hay? también qué dice el corpus de vida",
    "Promedio de primas y la meta del documento",
]


@pytest.mark.parametrize("mensaje", MIXTOS)
def test_datos_mas_documentos_van_a_mixto(mensaje):
    # Arrange
    # Act
    decision = enrutar(mensaje)
    # Assert
    assert (decision.ruta, decision.tools) == ("mixto", ("buscar_conocimiento", "consultar_datos"))


@pytest.mark.parametrize("mensaje", MIXTOS)
def test_mixto_explica_ambas_clausulas(mensaje):
    # Arrange
    # Act
    decision = enrutar(mensaje)
    # Assert
    assert [s.split(":")[0] for s in decision.senales] == ["datos", "documentos"]


DIRECTOS = [
    "Hola",
    "Buenas tardes",
    "Gracias",
    "Me llamo Ana",
    "Mi nombre es Pedro",
    "Trabajo en una panadería",
    "Vivo en Medellín",
    "¿Cómo me llamo?",
    "¿Dónde trabajo?",
    "¿Dónde vivo?",
    "¿Quién soy?",
    "¿Qué sabes de mí?",
    "¿Qué recuerdas de mí?",
    "Muchas gracias por todo",
]


@pytest.mark.parametrize("mensaje", DIRECTOS)
def test_saludos_y_memoria_personal_van_a_directo_sin_tools(mensaje):
    # Arrange
    # Act
    decision = enrutar(mensaje)
    # Assert
    assert (decision.ruta, decision.tools, decision.cautela) == ("directo", (), False)


@pytest.mark.parametrize(
    ("mensaje", "senal"),
    [
        ("Hola", "saludo"),
        ("Me llamo Ana", "dato personal o memoria"),
        ("¿Quién soy?", "dato personal o memoria"),
    ],
)
def test_directo_dice_por_que(mensaje, senal):
    # Arrange
    # Act
    decision = enrutar(mensaje)
    # Assert
    assert decision.senales == [senal]


@pytest.mark.parametrize(
    "mensaje",
    [
        "Me llamo Ana, ¿qué cubre el seguro de hogar?",
        "Vivo en Cali, ¿dónde queda la oficina de seguros?",
        "Trabajo en una obra, ¿qué cubre la ARL en accidentes?",
    ],
)
def test_dato_personal_con_pregunta_de_seguros_va_a_rag(mensaje):
    # Arrange
    # Act
    decision = enrutar(mensaje)
    # Assert
    assert decision.ruta == "rag" and decision.senales[0] == "dato personal + pregunta de seguros"


RAG = [
    "¿Qué cubre el SOAT?",
    "¿Cuál es el WhatsApp de atención?",
    "¿El seguro de hogar cubre inundaciones?",
    "¿Cómo reclamo un siniestro del vehículo?",
    "¿Hay asistencia de grúa?",
    "Seguro para mi mascota",
    "¿Qué cubre la póliza de vida?",
    "¿Cómo pago la prima?",
    "¿Tienen seguro de salud?",
    "¿Qué seguro me recomiendan si tengo moto?",
    "¿Qué seguros necesito?",
]


@pytest.mark.parametrize("mensaje", RAG)
def test_preguntas_de_seguros_van_a_rag_con_busqueda_y_recomendacion(mensaje):
    # Arrange
    # Act
    decision = enrutar(mensaje)
    # Assert
    assert (decision.ruta, decision.tools, decision.cautela) == (
        "rag",
        ("buscar_conocimiento", "recomendar_seguros", *CONOCIMIENTO, *MERCADO),
        False,
    )


FUERA = [
    "¿Quién ganó el mundial?",
    "Dame una receta",
    "Cuéntame un chiste",
    "Recomiéndame una película",
    "Sugiéreme una canción",
    "¿A cuánto está el bitcoin?",
    "¿Cómo está el clima?",
    "¿Quién es el presidente?",
]


@pytest.mark.parametrize("mensaje", FUERA)
def test_temas_ajenos_van_a_fuera_de_alcance_sin_tools(mensaje):
    # Arrange
    # Act
    decision = enrutar(mensaje)
    # Assert
    assert (decision.ruta, decision.tools) == ("fuera_de_alcance", ())


@pytest.mark.parametrize("mensaje", ["Recomiéndame una película", "Sugiéreme una canción"])
def test_recomendacion_ajena_se_explica(mensaje):
    # Arrange: el clasificador dice recomendación, el router la corrige
    # Act
    decision = enrutar(mensaje)
    # Assert
    assert decision.senales == ["tema ajeno sin vocabulario de seguros"] and decision.confianza == 0.85


CAUTELA = ["¿Qué hago?", "necesito ayuda", "tengo una duda", "explíqueme", "no entiendo nada"]


@pytest.mark.parametrize("mensaje", CAUTELA)
def test_sin_vocabulario_va_a_rag_con_cautela_y_todas_las_tools(mensaje):
    # Arrange
    # Act
    decision = enrutar(mensaje)
    # Assert
    assert (decision.ruta, decision.cautela, decision.tools) == ("rag", True, TODAS)


@pytest.mark.parametrize("mensaje", CAUTELA)
def test_la_cautela_ocurre_bajo_el_umbral(mensaje):
    # Arrange
    # Act
    decision = enrutar(mensaje)
    # Assert
    assert decision.confianza < UMBRAL_CAUTELA


@pytest.mark.parametrize("mensaje", DATOS + MIXTOS + DIRECTOS + RAG + FUERA + CAUTELA)
def test_toda_decision_es_coherente(mensaje):
    # Arrange
    # Act
    decision = enrutar(mensaje)
    # Assert: las tools salen de la tabla de la ruta (o todas, con cautela) y la confianza es válida
    esperadas = TODAS if decision.cautela else TOOLS_POR_RUTA[decision.ruta]
    assert isinstance(decision, Decision)
    assert decision.tools == esperadas
    assert 0.0 <= decision.confianza <= 1.0
    assert decision.senales


@pytest.mark.parametrize("ruta", list(TOOLS_POR_RUTA))
def test_las_tools_de_cada_ruta_existen(ruta):
    # Arrange
    # Act
    tools = TOOLS_POR_RUTA[ruta]
    # Assert
    assert set(tools) <= set(TODAS)


@pytest.mark.parametrize("ruta", ["directo", "fuera_de_alcance"])
def test_rutas_sin_tools_no_gastan_tokens_en_definiciones(ruta):
    # Arrange
    # Act
    tools = TOOLS_POR_RUTA[ruta]
    # Assert
    assert tools == ()


@pytest.mark.parametrize("mensaje", ["", "  ", "\n"])
def test_mensaje_vacio_lanza_error(mensaje):
    # Arrange
    # Act / Assert
    with pytest.raises(ValueError):
        enrutar(mensaje)


@pytest.mark.parametrize(
    "mensaje",
    [
        "Total de siniestros, según la política de reclamaciones",
        "Total de siniestros; según la política de reclamaciones",
        "Ventas por canal, qué dice el documento",
    ],
)
def test_la_coma_y_el_punto_y_coma_separan_clausulas(mensaje):
    # Arrange: regresión; antes normalizar() borraba el signo y la frase quedaba en una sola cláusula
    # Act
    decision = enrutar(mensaje)
    # Assert
    assert decision.ruta == "mixto"

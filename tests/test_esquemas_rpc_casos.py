"""Casos tabulados de los contratos de entrada de la API y del despachador JSON-RPC (SPEC-068).

La API es la frontera con el usuario: aquí se rechazan datos personales (Ley 1581), ids
inseguros y parámetros fuera de rango antes de tocar el modelo.
"""

import pytest
from pydantic import ValidationError

from sb_asistente.model.llm.service import Answer
from sb_asistente.model.rag.hibrido import RecuperadorHibrido
from sb_asistente.view import rpc
from sb_asistente.view.schemas import (
    AgenteIn,
    ChatIn,
    PreguntaIn,
    TemaIn,
    extraer_fuentes,
    rechazar_datos_personales,
)

SB = "https://www.segurosbolivar.com"

# --- datos personales ---------------------------------------------------------------------------

CON_DATOS = [
    "mi correo es ana@correo.com",
    "escríbanme a pedro.perez+seguros@empresa.co",
    "mi cédula es 1234567890",
    "cédula 1.234.567.890",
    "mi celular es 3001234567",
    "llámenme al 300 123 4567",
    "al 300-123-4567",
    "NIT 900123456",
    "teléfono 6012345678",
    "documento 12345678",
]


@pytest.mark.parametrize("texto", CON_DATOS)
def test_rechaza_correos_documentos_y_telefonos(texto):
    # Arrange
    # Act / Assert
    with pytest.raises(ValueError, match="datos personales"):
        rechazar_datos_personales(texto)


SIN_DATOS = [
    "¿Qué cubre el SOAT?",
    "¿Cuál es el WhatsApp #322?",
    "Tengo 2 carros y 3 motos",
    "Nací en 1990",
    "La prima es de 120000 pesos",  # seis dígitos: no es documento ni celular
    "Póliza del 2026",
    "Seguro de hogar de 80 m2",
    "Plan 123456",
]


@pytest.mark.parametrize("texto", SIN_DATOS)
def test_acepta_textos_sin_datos_personales(texto):
    # Arrange
    # Act
    resultado = rechazar_datos_personales(f"  {texto}  ")
    # Assert
    assert resultado == texto


# --- extraer_fuentes ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("texto", "fuentes"),
    [
        ("Sin enlaces", []),
        (f"Ver {SB}/soat.", [f"{SB}/soat"]),
        (f"Ver {SB}/soat, y {SB}/vida;", [f"{SB}/soat", f"{SB}/vida"]),
        (f"{SB}/soat {SB}/soat", [f"{SB}/soat"]),
        (f"[SOAT]({SB}/soat)", [f"{SB}/soat"]),
        ("Ver https://otro.com/x", []),
        ("Ver http://segurosbolivar.com/a: listo", ["http://segurosbolivar.com/a"]),
        (f'<a href="{SB}/b">', [f"{SB}/b"]),
        (f"{SB}/b {SB}/a", [f"{SB}/b", f"{SB}/a"]),
    ],
)
def test_extraer_fuentes(texto, fuentes):
    # Arrange
    # Act
    resultado = extraer_fuentes(texto)
    # Assert
    assert resultado == fuentes


# --- modelos de entrada -------------------------------------------------------------------------


def _invalido(modelo: type, **campos: object) -> None:
    """Verifica que el modelo rechace los campos."""
    with pytest.raises(ValidationError):
        modelo(**campos)


@pytest.mark.parametrize(
    "campos",
    [
        {"pregunta": "ab"},
        {"pregunta": "x" * 501},
        {"pregunta": "¿Qué cubre?", "version": "v9"},
        {"pregunta": "¿Qué cubre?", "modo": "turbo"},
        {"pregunta": "¿Qué cubre?", "proveedor": "openai"},
        {"pregunta": "¿Qué cubre?", "campo_extra": 1},
        {"pregunta": "mi celular es 3001234567"},
    ],
)
def test_pregunta_in_rechaza(campos):
    # Arrange / Act / Assert
    _invalido(PreguntaIn, **campos)


@pytest.mark.parametrize("proveedor", ["anthropic", "deepseek", "ollama", None])
def test_pregunta_in_acepta_proveedores_soportados(proveedor):
    # Arrange
    # Act
    entrada = PreguntaIn(pregunta="  ¿Qué cubre el SOAT?  ", proveedor=proveedor)
    # Assert
    assert (entrada.pregunta, entrada.version, entrada.modo) == ("¿Qué cubre el SOAT?", "v3", "reducido")


@pytest.mark.parametrize(("n", "valido"), [(0, False), (1, True), (15, True), (16, False)])
def test_tema_in_limita_n(n, valido):
    # Arrange
    # Act
    try:
        TemaIn(tema="SOAT", n=n)
        aceptado = True
    except ValidationError:
        aceptado = False
    # Assert
    assert aceptado is valido


@pytest.mark.parametrize(
    "campos",
    [
        {"mensaje": "", "conversacion_id": "hilo-0001"},
        {"mensaje": "x" * 801, "conversacion_id": "hilo-0001"},
        {"mensaje": "hola", "conversacion_id": "abc"},
        {"mensaje": "hola", "conversacion_id": "../../etc"},
        {"mensaje": "hola", "conversacion_id": "hilo con espacio"},
        {"mensaje": "hola", "conversacion_id": "hilo-0001", "usuario_id": "u"},
        {"mensaje": "hola", "conversacion_id": "hilo-0001", "proveedor": "gpt"},
        {"mensaje": "ana@correo.com", "conversacion_id": "hilo-0001"},
    ],
)
def test_agente_in_rechaza(campos):
    # Arrange / Act / Assert
    _invalido(AgenteIn, **campos)


def test_agente_in_valido():
    # Arrange
    # Act
    entrada = AgenteIn(mensaje=" hola ", conversacion_id="hilo-0001", usuario_id="usuario_01")
    # Assert
    assert (entrada.mensaje, entrada.usuario_id) == ("hola", "usuario_01")


@pytest.mark.parametrize(
    "campos",
    [
        {"mensaje": "hola", "modo": "magia"},
        {"mensaje": "hola", "cliente_id": "123456"},
        {"mensaje": "hola", "cliente_id": "C12345"},
        {"mensaje": "hola", "cliente_id": "c000123"},
        {"mensaje": "hola", "skill": "Mala_Skill"},
        {"mensaje": "hola", "skill": "x" * 65},
        {"mensaje": "hola", "k": 0},
        {"mensaje": "hola", "k": 11},
    ],
)
def test_chat_in_rechaza(campos):
    # Arrange / Act / Assert
    _invalido(ChatIn, **campos)


@pytest.mark.parametrize(
    "campos",
    [
        {"mensaje": "hola"},
        {"mensaje": "hola", "cliente_id": "C000123"},
        {"mensaje": "hola", "skill": "tono-cercano"},
        {"mensaje": "hola", "modo": "recomendador", "k": 10},
    ],
)
def test_chat_in_acepta(campos):
    # Arrange
    # Act
    entrada = ChatIn(**campos)
    # Assert
    assert entrada.mensaje == "hola"


# --- despachador JSON-RPC -----------------------------------------------------------------------

CHUNKS = [
    {
        "chunk_id": "c#0",
        "url": f"{SB}/canales",
        "title": "Canales",
        "section": "canales_y_servicio",
        "breadcrumb": "",
        "text": "WhatsApp de atención.",
    }
]


@pytest.fixture
def ctx() -> rpc.Contexto:
    """Contexto RPC con dobles: responde sin LLM y busca solo con BM25."""
    return rpc.Contexto(
        responder=lambda p, v, m, prov: Answer(f"Ver {SB}/canales", "qa", v, 0.123, 50),
        chat_qa=lambda prov: None,
        agente=lambda prov: None,
        recuperador=lambda: (RecuperadorHibrido(CHUNKS), "solo BM25"),
    )


def llamada(metodo: str, params: object = None, id_: object = 1) -> dict[str, object]:
    """Cuerpo JSON-RPC 2.0; omite ``params`` cuando es ``None``."""
    cuerpo = {"jsonrpc": "2.0", "method": metodo, "id": id_}
    if params is not None:
        cuerpo["params"] = params
    return cuerpo


@pytest.mark.parametrize(
    "cuerpo",
    [
        None,
        [],
        "texto",
        1,
        {},
        {"method": "x"},
        {"jsonrpc": "1.0", "method": "x"},
        {"jsonrpc": "2.0"},
        {"jsonrpc": "2.0", "method": 5},
    ],
)
def test_solicitudes_mal_formadas(ctx, cuerpo):
    # Arrange
    # Act
    respuesta = rpc.ejecutar(cuerpo, ctx)
    # Assert
    assert respuesta["error"]["code"] == rpc.INVALID_REQUEST


@pytest.mark.parametrize("id_", [True, 1.5, [1], {"a": 1}])
def test_ids_no_validos(ctx, id_):
    # Arrange
    # Act
    respuesta = rpc.ejecutar(llamada("sistema.salud", id_=id_), ctx)
    # Assert
    assert respuesta["error"]["code"] == rpc.INVALID_REQUEST


@pytest.mark.parametrize("id_", [1, "abc", None, 0])
def test_el_id_se_devuelve_tal_cual(ctx, id_):
    # Arrange
    # Act
    respuesta = rpc.ejecutar(llamada("clasificador.clasificar", {"mensaje": "hola"}, id_), ctx)
    # Assert
    assert respuesta["id"] == id_


def test_metodo_inexistente(ctx):
    # Arrange
    # Act
    respuesta = rpc.ejecutar(llamada("borrar.todo"), ctx)
    # Assert
    assert respuesta["error"]["code"] == rpc.METHOD_NOT_FOUND


@pytest.mark.parametrize("params", [[1, 2], "x", 3])
def test_params_debe_ser_objeto(ctx, params):
    # Arrange
    # Act
    respuesta = rpc.ejecutar(llamada("conocimiento.buscar", params), ctx)
    # Assert
    assert respuesta["error"]["code"] == rpc.INVALID_PARAMS


@pytest.mark.parametrize(
    ("metodo", "params", "campo"),
    [
        ("conocimiento.buscar", {"consulta": "x"}, "consulta"),
        ("conocimiento.buscar", {"consulta": "soat", "k": 21}, "k"),
        ("conocimiento.buscar", {"consulta": "soat", "otro": 1}, "otro"),
        ("agente.historial", {"conversacion_id": "../x"}, "conversacion_id"),
        ("recomendador.recomendar", {"cliente_id": "X1"}, "cliente_id"),
        ("recomendador.por_perfil", {"vehiculo": "avion"}, "vehiculo"),
        ("recomendador.por_perfil", {"k": 0}, "k"),
        ("clasificador.clasificar", {}, "mensaje"),
        ("agente.conversar", {"mensaje": "3001234567", "conversacion_id": "hilo-0001"}, "mensaje"),
    ],
)
def test_parametros_invalidos_dicen_que_campo_fallo(ctx, metodo, params, campo):
    # Arrange
    # Act
    respuesta = rpc.ejecutar(llamada(metodo, params), ctx)
    # Assert
    assert respuesta["error"]["code"] == rpc.INVALID_PARAMS
    assert campo in [e["campo"] for e in respuesta["error"]["data"]]


def test_una_notificacion_no_tiene_respuesta(ctx):
    # Arrange
    cuerpo = {"jsonrpc": "2.0", "method": "clasificador.clasificar", "params": {"mensaje": "hola"}}
    # Act
    respuesta = rpc.ejecutar(cuerpo, ctx)
    # Assert
    assert respuesta is None


@pytest.mark.parametrize(
    ("mensaje", "intencion"),
    [
        ("Hola", "saludo"),
        ("¿Qué cubre el SOAT?", "conocimiento"),
        ("¿Qué seguro me recomiendan?", "recomendacion"),
        ("Cuéntame un chiste", "fuera_de_alcance"),
    ],
)
def test_clasificar_por_rpc(ctx, mensaje, intencion):
    # Arrange
    # Act
    respuesta = rpc.ejecutar(llamada("clasificador.clasificar", {"mensaje": mensaje}), ctx)
    # Assert
    assert respuesta["result"]["intencion"] == intencion


def test_buscar_por_rpc_devuelve_fragmentos_con_su_origen(ctx):
    # Arrange
    # Act
    resultado = rpc.ejecutar(llamada("conocimiento.buscar", {"consulta": "WhatsApp", "k": 1}), ctx)["result"]
    # Assert
    assert resultado["modo"] == "solo BM25" and resultado["fragmentos"][0]["origen"] == ["bm25"]


def test_preguntar_por_rpc_extrae_las_fuentes(ctx):
    # Arrange
    # Act
    resultado = rpc.ejecutar(llamada("asistente.preguntar", {"pregunta": "¿Cuál es el WhatsApp?"}), ctx)[
        "result"
    ]
    # Assert
    assert (resultado["fuentes"], resultado["latencia_s"]) == ([f"{SB}/canales"], 0.12)


@pytest.mark.parametrize(
    ("excepcion", "codigo"),
    [
        (KeyError("no está"), rpc.NOT_FOUND),
        (FileNotFoundError("data/gold"), rpc.NOT_READY),
        (ValueError("mal"), rpc.INVALID_PARAMS),
        (RuntimeError("secreto interno"), rpc.INTERNAL_ERROR),
    ],
)
def test_las_excepciones_se_traducen_a_codigos(ctx, excepcion, codigo):
    # Arrange
    def falla():
        raise excepcion

    ctx.recuperador = falla
    # Act
    respuesta = rpc.ejecutar(llamada("conocimiento.buscar", {"consulta": "soat"}), ctx)
    # Assert
    assert respuesta["error"]["code"] == codigo


def test_el_error_interno_no_filtra_detalles(ctx):
    # Arrange
    def falla():
        raise RuntimeError("clave=sk-secreta")

    ctx.recuperador = falla
    # Act
    respuesta = rpc.ejecutar(llamada("conocimiento.buscar", {"consulta": "soat"}), ctx)
    # Assert
    assert "secreta" not in str(respuesta)


@pytest.mark.parametrize("metodo", sorted(rpc.METODOS))
def test_cada_metodo_se_describe_con_su_esquema(metodo):
    # Arrange
    # Act
    descritos = {d["metodo"]: d for d in rpc.descubrir()}
    # Assert
    assert descritos[metodo]["descripcion"] and descritos[metodo]["params"]["type"] == "object"


def test_rpc_descubrir_responde_por_el_despachador(ctx):
    # Arrange
    # Act
    respuesta = rpc.ejecutar(llamada("rpc.descubrir"), ctx)
    # Assert
    assert len(respuesta["result"]) == len(rpc.METODOS)

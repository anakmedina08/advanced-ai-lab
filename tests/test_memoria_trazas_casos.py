"""Casos tabulados de memoria de largo plazo, trazas locales y bitácora (SPEC-064).

Estas piezas tocan datos personales: se fija qué se recuerda, qué NUNCA se guarda (correos,
números largos) y que las trazas no llevan el texto ni el id real del hilo.
"""

import json

import pytest
from langgraph.store.memory import InMemoryStore

from sb_asistente.model.experimentos import BitacoraNula, Corrida, nombre_metrica
from sb_asistente.model.memoria import PerfilStore, bloque_perfil, extraer_hechos, namespace
from sb_asistente.model.trazas import TAMANO_MAXIMO, hash_hilo, linea_turno, registrar_turno, ultimas

# --- namespace ----------------------------------------------------------------------------------


@pytest.mark.parametrize("usuario", ["abcdef", "usuario_01", "a-b-c-d-e", "A" * 64, "123456", "Mixto_9-x"])
def test_namespace_acepta_ids_seguros(usuario):
    # Arrange
    # Act
    ns = namespace(usuario)
    # Assert
    assert ns == ("usuarios", usuario, "perfil")


@pytest.mark.parametrize(
    "usuario",
    [
        "",
        "abc",
        "abcde",
        "A" * 65,
        "con espacio",
        "../../etc",
        "usuario.01",
        "ñandú99",
        "a/b/c/d/e/f",
        "id;drop",
    ],
)
def test_namespace_rechaza_ids_inseguros(usuario):
    # Arrange
    # Act / Assert
    with pytest.raises(ValueError, match="usuario_id inválido"):
        namespace(usuario)


# --- extraer_hechos -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("mensaje", "nombre"),
    [
        ("Me llamo Ana", "Ana"),
        ("me llamo ana", "Ana"),
        ("Mi nombre es Pedro Pérez", "Pedro Pérez"),
        ("Me llamo José y tengo carro", "José"),
        ("Hola, me llamo Lucía.", "Lucía"),
        ("mi nombre es María José, gracias", "María José"),
        ("ME LLAMO ÑUSTA", "ÑUSTA"),
    ],
)
def test_extrae_el_nombre(mensaje, nombre):
    # Arrange
    # Act
    hechos = extraer_hechos(mensaje)
    # Assert
    assert hechos["nombre"] == nombre


@pytest.mark.parametrize(
    ("mensaje", "empresa"),
    [
        ("Trabajo en Ecopetrol", "Ecopetrol"),
        ("trabajo para una panadería, y tengo moto", "Una panadería"),
        ("Trabajo en el hospital y vivo en Cali", "El hospital"),
        ("trabajo en la alcaldía.", "La alcaldía"),
    ],
)
def test_extrae_la_empresa(mensaje, empresa):
    # Arrange
    # Act
    hechos = extraer_hechos(mensaje)
    # Assert
    assert hechos["empresa"] == empresa


@pytest.mark.parametrize(
    ("mensaje", "ciudad"),
    [
        ("Vivo en Cali", "Cali"),
        ("vivo en bogotá, en un apartamento", "Bogotá"),
        ("Vivo en Santa Marta y trabajo en el puerto", "Santa Marta"),
        ("vivo en Medellín!", "Medellín"),
    ],
)
def test_extrae_la_ciudad(mensaje, ciudad):
    # Arrange
    # Act
    hechos = extraer_hechos(mensaje)
    # Assert
    assert hechos["ciudad"] == ciudad


@pytest.mark.parametrize(
    "mensaje",
    [
        "Me llamo ana@correo.com",
        "Trabajo en ana@empresa.com",
        "Vivo en calle 12345678",
        "Trabajo en la empresa 900123456",
        "vivo en apto 55555",
    ],
)
def test_nunca_guarda_correos_ni_numeros_largos(mensaje):
    # Arrange
    # Act
    hechos = extraer_hechos(mensaje)
    # Assert
    assert not {"nombre", "empresa", "ciudad"} & set(hechos)


@pytest.mark.parametrize(
    ("mensaje", "clave", "valor"),
    [
        ("Tengo un perro", "tiene_mascota", "sí"),
        ("No tengo mascota", "tiene_mascota", "no"),
        ("Tengo moto", "vehiculo", "moto"),
        ("Vivo en arriendo", "vivienda", "arrendada"),
        ("Pago un préstamo", "tiene_credito", "sí"),
        ("No tengo crédito", "tiene_credito", "no"),
    ],
)
def test_traduce_el_perfil_de_seguros_a_texto(mensaje, clave, valor):
    # Arrange
    # Act
    hechos = extraer_hechos(mensaje)
    # Assert
    assert hechos[clave] == valor


@pytest.mark.parametrize("mensaje", ["¿Qué cubre el SOAT?", "Hola", "Gracias por la ayuda", ""])
def test_sin_hechos_explicitos_no_recuerda_nada(mensaje):
    # Arrange
    # Act
    hechos = extraer_hechos(mensaje)
    # Assert
    assert hechos == {}


# --- PerfilStore --------------------------------------------------------------------------------


def test_guardar_y_leer_el_perfil():
    # Arrange
    perfiles = PerfilStore(InMemoryStore())
    # Act
    perfiles.guardar("usuario01", {"nombre": "Ana", "ciudad": "Cali"})
    # Assert
    assert perfiles.leer("usuario01") == {"nombre": "Ana", "ciudad": "Cali"}


def test_guardar_actualiza_un_hecho_existente():
    # Arrange
    perfiles = PerfilStore(InMemoryStore())
    perfiles.guardar("usuario01", {"ciudad": "Cali"})
    # Act
    perfiles.guardar("usuario01", {"ciudad": "Pasto"})
    # Assert
    assert perfiles.leer("usuario01") == {"ciudad": "Pasto"}


def test_los_perfiles_de_usuarios_distintos_no_se_mezclan():
    # Arrange
    perfiles = PerfilStore(InMemoryStore())
    perfiles.guardar("usuario01", {"nombre": "Ana"})
    # Act
    perfiles.guardar("usuario02", {"nombre": "Luis"})
    # Assert
    assert perfiles.leer("usuario01") == {"nombre": "Ana"} and perfiles.leer("usuario02") == {
        "nombre": "Luis"
    }


@pytest.mark.parametrize("cantidad", [0, 1, 3])
def test_borrar_devuelve_cuantos_hechos_habia(cantidad):
    # Arrange
    perfiles = PerfilStore(InMemoryStore())
    perfiles.guardar("usuario01", {f"h{i}": "x" for i in range(cantidad)})
    # Act
    borrados = perfiles.borrar("usuario01")
    # Assert
    assert borrados == cantidad and perfiles.leer("usuario01") == {}


@pytest.mark.parametrize("operacion", ["leer", "borrar"])
def test_el_store_valida_el_id(operacion):
    # Arrange
    perfiles = PerfilStore(InMemoryStore())
    # Act / Assert
    with pytest.raises(ValueError):
        getattr(perfiles, operacion)("../x")


# --- bloque_perfil ------------------------------------------------------------------------------


def test_bloque_perfil_ordena_y_delimita():
    # Arrange
    hechos = {"nombre": "Ana", "ciudad": "Cali"}
    # Act
    bloque = bloque_perfil(hechos)
    # Assert
    assert bloque.splitlines()[1:] == ["- ciudad: Cali", "- nombre: Ana", "</perfil_usuario>"]
    assert bloque.startswith("<perfil_usuario nota=")


# --- trazas -------------------------------------------------------------------------------------


@pytest.mark.parametrize("hilo", ["hilo-1", "hilo-2", "", "x" * 500, "ñandú"])
def test_hash_hilo_es_corto_hexadecimal_y_estable(hilo):
    # Arrange
    # Act
    primero, segundo = hash_hilo(hilo), hash_hilo(hilo)
    # Assert
    assert primero == segundo and len(primero) == 10 and int(primero, 16) >= 0


def test_hash_hilo_distingue_hilos():
    # Arrange
    hilos = [f"hilo-{i}" for i in range(100)]
    # Act
    hashes = {hash_hilo(h) for h in hilos}
    # Assert
    assert len(hashes) == 100


TURNO = {
    "conversacion_id": "hilo-secreto-123",
    "pregunta": "mi cédula es 123456789",
    "decision": {"ruta": "rag", "cautela": True},
    "salida": {"respuesta": "texto privado", "fuentes": ["a", "b"], "confianza": "alta"},
    "tiempos_tools": [{"tool": "buscar_conocimiento", "ms": 12.0}],
    "fuentes_descartadas": ["x"],
}


@pytest.mark.parametrize(
    ("clave", "valor"),
    [
        ("ruta", "rag"),
        ("cautela", True),
        ("fuentes", 2),
        ("fuentes_descartadas", 1),
        ("confianza", "alta"),
        ("error", None),
        ("ms_total", 123.5),
        ("tools", [{"tool": "buscar_conocimiento", "ms": 12.0}]),
        ("hilo", hash_hilo("hilo-secreto-123")),
    ],
)
def test_linea_turno_resume_el_turno(clave, valor):
    # Arrange
    # Act
    linea = linea_turno(TURNO, ms_total=123.45)
    # Assert
    assert linea[clave] == valor


@pytest.mark.parametrize("secreto", ["hilo-secreto-123", "123456789", "texto privado", "cédula"])
def test_linea_turno_no_guarda_texto_ni_id(secreto):
    # Arrange
    # Act
    linea = linea_turno(TURNO, ms_total=1)
    # Assert
    assert secreto not in json.dumps(linea, ensure_ascii=False)


def test_linea_turno_tolera_un_turno_vacio():
    # Arrange
    # Act
    linea = linea_turno({}, ms_total=0, error="TimeoutError")
    # Assert
    assert (linea["ruta"], linea["fuentes"], linea["tools"], linea["error"]) == (None, 0, [], "TimeoutError")


def test_registrar_y_leer_las_ultimas(tmp_path):
    # Arrange
    ruta = tmp_path / "logs" / "turnos.jsonl"
    # Act
    for i in range(5):
        registrar_turno(ruta, {"i": i})
    # Assert
    assert [linea["i"] for linea in ultimas(ruta, n=3)] == [2, 3, 4]


def test_ultimas_sin_log_devuelve_vacio(tmp_path):
    # Arrange
    ruta = tmp_path / "no-existe.jsonl"
    # Act
    resultado = ultimas(ruta)
    # Assert
    assert resultado == []


def test_registrar_rota_el_log_grande(tmp_path):
    # Arrange
    ruta = tmp_path / "turnos.jsonl"
    ruta.write_text("x" * (TAMANO_MAXIMO + 1), encoding="utf-8")
    # Act
    registrar_turno(ruta, {"nuevo": True})
    # Assert
    assert ruta.with_suffix(".jsonl.1").is_file() and ultimas(ruta) == [{"nuevo": True}]


def test_registrar_conserva_tildes(tmp_path):
    # Arrange
    ruta = tmp_path / "turnos.jsonl"
    # Act
    registrar_turno(ruta, {"ruta": "información"})
    # Assert
    assert "información" in ruta.read_text(encoding="utf-8")


# --- bitácora de experimentos -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("nombre", "valido"),
    [
        ("recall@5", "recall_at_5"),
        ("ndcg@10", "ndcg_at_10"),
        ("hit_rate", "hit_rate"),
        ("latencia (s)", "latencia _s_"),
        ("precisión", "precisión"),
        ("a/b-c.d", "a/b-c.d"),
        ("x:y", "x_y"),
        ("tasa%", "tasa_"),
    ],
)
def test_nombre_metrica_es_valido_para_mlflow(nombre, valido):
    # Arrange
    # Act
    resultado = nombre_metrica(nombre)
    # Assert
    assert resultado == valido


@pytest.mark.parametrize(
    ("metodo", "argumentos", "esperado"),
    [
        ("registrar", (Corrida("exp", "corrida"),), None),
        ("existe", ("exp", "commit", "abc"), False),
        ("corridas", ("exp",), []),
    ],
)
def test_bitacora_nula_no_registra_nada(metodo, argumentos, esperado):
    # Arrange
    bitacora = BitacoraNula()
    # Act
    resultado = getattr(bitacora, metodo)(*argumentos)
    # Assert
    assert resultado == esperado


def test_corrida_tiene_valores_por_defecto_independientes():
    # Arrange
    primera, segunda = Corrida("e", "a"), Corrida("e", "b")
    # Act
    primera.parametros["x"] = 1
    # Assert
    assert segunda.parametros == {}


@pytest.mark.parametrize(
    "mensaje", ["Me llamo ana@correo.com", "mi nombre es pedro.perez@x.co", "Me llamo luis2024123"]
)
def test_no_guarda_la_parte_local_de_un_correo_como_nombre(mensaje):
    # Arrange: regresión; el patrón del nombre se detenía en la «@» y guardaba «Ana»
    # Act
    hechos = extraer_hechos(mensaje)
    # Assert
    assert "nombre" not in hechos

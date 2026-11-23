"""Casos tabulados de las métricas de evaluación (SPEC-063).

Las métricas deciden si un experimento mejora o empeora; un error aquí cambia las conclusiones
del curso. Se verifican contra valores calculados a mano.
"""

import math

import pandas as pd
import pytest

from sb_asistente.model.evaluation import RESULT_FILE, EvalQuestion, aggregate, keyword_hit
from sb_asistente.model.rag.evaluacion import ResultadoHit, es_relevante
from sb_asistente.model.rag.evaluacion import ndcg_at_k as ndcg_rag
from sb_asistente.model.rag.evaluacion import recall_at_k as recall_rag
from sb_asistente.model.recomendador.metricas import evaluar, ndcg_at_k, rango, recall_at_k
from sb_asistente.model.recomendador.particion import leave_last_out
from sb_asistente.model.recomendador.popularidad import RecomendadorPopularidad, RecomendadorSegmento

# --- keyword_hit --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("respuesta", "claves", "esperado"),
    [
        ("El SOAT cubre gastos médicos", ["soat", "medicos"], 1.0),
        ("El SOAT cubre gastos médicos", ["SOAT", "vida"], 0.5),
        ("El SOAT cubre gastos médicos", ["vida"], 0.0),
        ("Póliza de vida", ["poliza", "VIDA", "renta", "ahorro"], 0.5),
        ("Línea de atención", ["linea de atencion"], 1.0),
        ("", ["soat"], 0.0),
        ("cualquier cosa", [], None),
        ("Niño", ["nino"], 1.0),
        ("WhatsApp 322", ["322"], 1.0),
        ("seguros", ["seguro"], 1.0),  # coincidencia por subcadena
    ],
)
def test_keyword_hit(respuesta, claves, esperado):
    # Arrange
    # Act
    resultado = keyword_hit(respuesta, claves)
    # Assert
    assert resultado == esperado


def test_keyword_hit_acepta_generadores():
    # Arrange
    claves = (c for c in ["soat", "vida"])
    # Act
    resultado = keyword_hit("soat", claves)
    # Assert
    assert resultado == 0.5


# --- aggregate ----------------------------------------------------------------------------------


def fila(
    hit: float | None = 1.0, cita: bool = True, fallback_ok: bool = True, latencia: float = 1.0
) -> dict[str, object]:
    """Fila de resultados de evaluación con valores por defecto de un acierto."""
    return {"keyword_hit": hit, "cita_fuente": cita, "fallback_ok": fallback_ok, "latencia_s": latencia}


@pytest.mark.parametrize(
    ("filas", "clave", "esperado"),
    [
        ([fila()], "preguntas", 1),
        ([fila(), fila()], "preguntas", 2),
        ([fila(hit=1.0), fila(hit=0.0)], "keyword_hit_promedio", 0.5),
        ([fila(hit=None), fila(hit=0.5)], "keyword_hit_promedio", 0.5),
        ([fila(hit=None)], "keyword_hit_promedio", 0.0),
        ([fila(hit=1 / 3), fila(hit=1 / 3), fila(hit=1 / 3)], "keyword_hit_promedio", 0.333),
        ([fila(cita=True), fila(cita=False)], "tasa_cita_fuente", 0.5),
        ([fila(cita=False)] * 3, "tasa_cita_fuente", 0.0),
        ([fila(fallback_ok=True)] * 2 + [fila(fallback_ok=False)], "tasa_fallback_correcto", 0.667),
        ([fila(latencia=1.0), fila(latencia=2.0)], "latencia_promedio_s", 1.5),
        ([fila(latencia=0.123), fila(latencia=0.456)], "latencia_promedio_s", 0.29),
    ],
)
def test_aggregate(filas, clave, esperado):
    # Arrange
    # Act
    resumen = aggregate(filas)
    # Assert
    assert resumen[clave] == esperado


def test_aggregate_sin_filas_falla():
    # Arrange
    # Act / Assert
    with pytest.raises(ValueError, match="No hay filas"):
        aggregate([])


# --- nombre de archivos de resultados -----------------------------------------------------------


@pytest.mark.parametrize(
    ("nombre", "modelo", "version"),
    [
        ("resultados_claude_v1.csv", "claude", "v1"),
        ("resultados_claude-haiku_v3.csv", "claude-haiku", "v3"),
        ("resultados_llama3-2_v12.csv", "llama3-2", "v12"),
        ("resultados_deepseek_agente.csv", "deepseek", "agente"),
    ],
)
def test_result_file_reconoce_modelo_y_version(nombre, modelo, version):
    # Arrange
    # Act
    coincidencia = RESULT_FILE.match(nombre)
    # Assert
    assert (coincidencia["modelo"], coincidencia["version"]) == (modelo, version)


@pytest.mark.parametrize(
    "nombre",
    [
        "resultados.csv",
        "resultados_claude.csv",
        "resultados_Claude_v1.csv",
        "resultados_claude_v1.xlsx",
        "resultados_claude_vx.csv",
        "otros_claude_v1.csv",
        "resultados_claude_v1.csv.bak",
    ],
)
def test_result_file_ignora_nombres_ajenos(nombre):
    # Arrange
    # Act
    coincidencia = RESULT_FILE.match(nombre)
    # Assert
    assert coincidencia is None


def test_eval_question_por_defecto_esta_en_alcance():
    # Arrange
    # Act
    pregunta = EvalQuestion("q1", "soat", "¿Qué cubre?", ["soat"])
    # Assert
    assert pregunta.fuera_de_alcance is False


# --- métricas de recuperación del RAG -----------------------------------------------------------


@pytest.mark.parametrize(
    ("texto", "claves", "esperado"),
    [
        ("El SOAT cubre accidentes", ["soat", "accidentes"], True),
        ("El SOAT cubre accidentes", ["soat", "vida"], False),
        ("Póliza de VIDA", ["poliza", "vida"], True),
        ("cualquier texto", [], True),
        ("", ["x"], False),
    ],
)
def test_es_relevante_exige_todas_las_claves(texto, claves, esperado):
    # Arrange
    # Act
    resultado = es_relevante(texto, claves)
    # Assert
    assert resultado is esperado


@pytest.mark.parametrize(
    ("relevancias", "en_corpus", "k", "esperado"),
    [
        ([1, 0, 0], 1, 3, 1.0),
        ([0, 0, 0], 1, 3, 0.0),
        ([1, 1, 0], 2, 3, 1.0),
        ([1, 0, 0], 2, 3, 0.5),
        ([1, 1, 1], 5, 3, 1.0),  # el denominador es min(relevantes, k)
        ([1, 0, 1, 0], 4, 2, 0.5),
        ([0, 1], 1, 1, 0.0),  # fuera del top-k no cuenta
        ([1], 0, 1, 0.0),
        ([], 3, 5, 0.0),
    ],
)
def test_recall_rag(relevancias, en_corpus, k, esperado):
    # Arrange
    # Act
    resultado = recall_rag(relevancias, en_corpus, k)
    # Assert
    assert resultado == pytest.approx(esperado)


@pytest.mark.parametrize(
    ("relevancias", "en_corpus", "k", "esperado"),
    [
        ([1, 0, 0], 1, 3, 1.0),
        ([0, 1, 0], 1, 3, 1 / math.log2(3)),
        ([0, 0, 1], 1, 3, 0.5),
        ([1, 1, 0], 2, 3, 1.0),
        ([0, 1, 1], 2, 3, (1 / math.log2(3) + 0.5) / (1 + 1 / math.log2(3))),
        ([0, 0, 0], 2, 3, 0.0),
        ([1, 0], 0, 2, 0.0),
        ([0, 0, 1], 1, 2, 0.0),
    ],
)
def test_ndcg_rag(relevancias, en_corpus, k, esperado):
    # Arrange
    # Act
    resultado = ndcg_rag(relevancias, en_corpus, k)
    # Assert
    assert resultado == pytest.approx(esperado)


@pytest.mark.parametrize("relevancias", [[1, 0, 1, 0, 1], [0, 1, 1, 1, 0], [1, 1, 1, 1, 1], [0, 0, 0, 0, 1]])
def test_ndcg_rag_esta_entre_cero_y_uno(relevancias):
    # Arrange
    # Act
    resultado = ndcg_rag(relevancias, sum(relevancias), 5)
    # Assert
    assert 0.0 <= resultado <= 1.0


@pytest.mark.parametrize(("aciertos", "total", "tasa"), [(0, 0, 0.0), (3, 4, 0.75), (4, 4, 1.0), (0, 5, 0.0)])
def test_resultado_hit_tasa(aciertos, total, tasa):
    # Arrange
    resultado = ResultadoHit(k=4, aciertos=aciertos, total=total, fallos=())
    # Act
    valor = resultado.tasa
    # Assert
    assert valor == tasa


# --- métricas del recomendador ------------------------------------------------------------------

LISTA = ["vida", "hogar", "soat", "mascotas", "salud"]


@pytest.mark.parametrize(
    ("objetivo", "posicion"),
    [("vida", 1), ("hogar", 2), ("soat", 3), ("salud", 5), ("arl", None)],
)
def test_rango(objetivo, posicion):
    # Arrange
    # Act
    resultado = rango(LISTA, objetivo)
    # Assert
    assert resultado == posicion


@pytest.mark.parametrize(
    ("objetivo", "k", "esperado"),
    [
        ("vida", 1, 1.0),
        ("hogar", 1, 0.0),
        ("hogar", 2, 1.0),
        ("salud", 4, 0.0),
        ("salud", 5, 1.0),
        ("arl", 5, 0.0),
    ],
)
def test_recall_recomendador(objetivo, k, esperado):
    # Arrange
    # Act
    resultado = recall_at_k(LISTA, objetivo, k)
    # Assert
    assert resultado == esperado


@pytest.mark.parametrize(
    ("objetivo", "k", "esperado"),
    [
        ("vida", 5, 1.0),
        ("hogar", 5, 1 / math.log2(3)),
        ("soat", 5, 0.5),
        ("salud", 5, 1 / math.log2(6)),
        ("salud", 3, 0.0),
        ("arl", 5, 0.0),
    ],
)
def test_ndcg_recomendador(objetivo, k, esperado):
    # Arrange
    # Act
    resultado = ndcg_at_k(LISTA, objetivo, k)
    # Assert
    assert resultado == pytest.approx(esperado)


@pytest.mark.parametrize("k", [0, -1])
@pytest.mark.parametrize("metrica", [recall_at_k, ndcg_at_k])
def test_k_no_positivo_falla(metrica, k):
    # Arrange
    # Act / Assert
    with pytest.raises(ValueError, match="positivo"):
        metrica(LISTA, "vida", k)


def test_evaluar_promedia_solo_clientes_en_comun():
    # Arrange
    recomendaciones = {"a": ["vida", "soat"], "b": ["soat", "vida"], "c": ["hogar"]}
    objetivos = {"a": "vida", "b": "vida", "z": "vida"}
    # Act
    resumen = evaluar(recomendaciones, objetivos, k=2)
    # Assert
    assert resumen == {"clientes": 2, "recall@2": 1.0, "ndcg@2": round((1 + 1 / math.log2(3)) / 2, 4)}


def test_evaluar_sin_clientes_en_comun_falla():
    # Arrange
    # Act / Assert
    with pytest.raises(ValueError, match="en común"):
        evaluar({"a": ["vida"]}, {"b": "vida"})


# --- partición y líneas base --------------------------------------------------------------------


def polizas(*filas: tuple[str, str, str]) -> pd.DataFrame:
    """Tabla de pólizas a partir de tuplas (cliente, producto, fecha de inicio)."""
    return pd.DataFrame(
        [
            {"poliza_id": f"p{i}", "cliente_id": c, "product_id": p, "fecha_inicio": f}
            for i, (c, p, f) in enumerate(filas)
        ]
    )


def test_leave_last_out_retiene_la_poliza_mas_reciente():
    # Arrange
    tabla = polizas(("a", "soat", "2020-01-01"), ("a", "vida", "2024-01-01"), ("a", "hogar", "2022-01-01"))
    # Act
    entrenamiento, objetivos = leave_last_out(tabla)
    # Assert
    assert objetivos == {"a": "vida"} and sorted(entrenamiento["product_id"]) == ["hogar", "soat"]


def test_leave_last_out_deja_en_entrenamiento_a_quien_tiene_una_sola_poliza():
    # Arrange
    tabla = polizas(("a", "soat", "2020-01-01"), ("b", "vida", "2021-01-01"), ("b", "soat", "2022-01-01"))
    # Act
    entrenamiento, objetivos = leave_last_out(tabla)
    # Assert
    assert objetivos == {"b": "soat"} and set(entrenamiento["cliente_id"]) == {"a", "b"}


def test_leave_last_out_no_pierde_ni_duplica_polizas():
    # Arrange
    tabla = polizas(*[(c, f"prod{i}", f"202{i}-01-01") for c in "abc" for i in range(3)])
    # Act
    entrenamiento, objetivos = leave_last_out(tabla)
    # Assert
    assert len(entrenamiento) + len(objetivos) == len(tabla)


def test_popularidad_excluye_lo_que_el_cliente_ya_tiene():
    # Arrange
    tabla = polizas(("a", "soat", "x"), ("b", "soat", "x"), ("c", "vida", "x"), ("a", "hogar", "x"))
    modelo = RecomendadorPopularidad().fit(tabla)
    # Act
    recomendados = modelo.recomendar("a", k=5)
    # Assert
    assert recomendados == ["vida"]


@pytest.mark.parametrize(
    ("k", "esperado"), [(1, ["soat"]), (2, ["soat", "hogar"]), (9, ["soat", "hogar", "vida"])]
)
def test_popularidad_ordena_por_ventas_y_corta_en_k(k, esperado):
    # Arrange
    tabla = polizas(
        ("a", "soat", "x"),
        ("b", "soat", "x"),
        ("c", "soat", "x"),
        ("a", "hogar", "x"),
        ("b", "hogar", "x"),
        ("c", "vida", "x"),
    )
    modelo = RecomendadorPopularidad().fit(tabla)
    # Act
    recomendados = modelo.recomendar("nuevo", k=k)
    # Assert
    assert recomendados == esperado


def test_popularidad_sin_fit_falla():
    # Arrange
    modelo = RecomendadorPopularidad()
    # Act / Assert
    with pytest.raises(RuntimeError, match="fit"):
        modelo.recomendar("a")


def test_popularidad_sin_polizas_falla():
    # Arrange
    vacio = polizas()
    # Act / Assert
    with pytest.raises(ValueError, match="No hay pólizas"):
        RecomendadorPopularidad().fit(vacio.reindex(columns=["poliza_id", "cliente_id", "product_id"]))


def test_segmento_con_columnas_inexistentes_falla():
    # Arrange
    clientes = pd.DataFrame({"cliente_id": ["a"], "vehiculo": ["carro"]})
    # Act / Assert
    with pytest.raises(KeyError, match="inexistentes"):
        RecomendadorSegmento(clientes, ("vehiculo", "mascota"))


@pytest.mark.parametrize(("cliente", "conoce"), [("a", True), ("b", True), ("z", False)])
def test_segmento_conoce_solo_clientes_de_la_tabla(cliente, conoce):
    # Arrange
    clientes = pd.DataFrame({"cliente_id": ["a", "b"], "vehiculo": ["carro", "moto"]})
    modelo = RecomendadorSegmento(clientes, ("vehiculo",))
    # Act
    resultado = modelo.conoce(cliente)
    # Assert
    assert resultado is conoce

"""Pruebas de métricas, partición y líneas base."""

import math

import pandas as pd
import pytest

from sb_asistente.controller import recomendador
from sb_asistente.model.recomendador.metricas import evaluar, ndcg_at_k, rango, recall_at_k
from sb_asistente.model.recomendador.particion import leave_last_out
from sb_asistente.model.recomendador.popularidad import RecomendadorPopularidad, RecomendadorSegmento
from sb_asistente.view import cli


def polizas(filas):
    df = pd.DataFrame(filas, columns=["poliza_id", "cliente_id", "product_id", "fecha_inicio"])
    df["fecha_inicio"] = pd.to_datetime(df["fecha_inicio"])
    return df


TOY = polizas(
    [
        ("1", "A", "P01", "2020-01-01"),
        ("2", "A", "P10", "2021-01-01"),
        ("3", "B", "P01", "2020-05-01"),
        ("4", "C", "P04", "2019-01-01"),
        ("5", "C", "P07", "2022-01-01"),
        ("6", "C", "P01", "2020-01-01"),
    ]
)


@pytest.mark.parametrize(("lista", "esperado"), [(["x", "y", "z"], 2), (["x"], None)])
def test_rango(lista, esperado):
    assert rango(lista, "y") == esperado


def test_recall_at_k():
    assert recall_at_k(["a", "b", "c"], "c", 3) == 1.0
    assert recall_at_k(["a", "b", "c"], "c", 2) == 0.0


def test_ndcg_primera_posicion_vale_uno():
    assert ndcg_at_k(["a", "b"], "a", 5) == 1.0


def test_ndcg_segunda_posicion():
    assert math.isclose(ndcg_at_k(["a", "b"], "b", 5), 1 / math.log2(3))


@pytest.mark.parametrize("k", [0, -1])
def test_metricas_rechazan_k_invalido(k):
    with pytest.raises(ValueError):
        recall_at_k(["a"], "a", k)
    with pytest.raises(ValueError):
        ndcg_at_k(["a"], "a", k)


def test_evaluar_promedia():
    resultado = evaluar({"u1": ["a"], "u2": ["b"]}, {"u1": "a", "u2": "z"}, k=5)
    assert resultado == {"clientes": 2, "recall@5": 0.5, "ndcg@5": 0.5}


def test_evaluar_sin_clientes_comunes():
    with pytest.raises(ValueError):
        evaluar({"u1": ["a"]}, {"u2": "a"})


def test_leave_last_out_retiene_la_poliza_mas_reciente():
    entrenamiento, objetivos = leave_last_out(TOY)
    assert objetivos == {"A": "P10", "C": "P07"}
    assert "B" in set(entrenamiento["cliente_id"])  # una sola póliza: solo entrenamiento
    assert len(entrenamiento) == len(TOY) - 2


def test_popularidad_excluye_lo_que_ya_tiene():
    modelo = RecomendadorPopularidad().fit(TOY)
    assert modelo.ranking[0] == "P01"
    assert "P01" not in modelo.recomendar("A")


def test_popularidad_cliente_nuevo_recibe_ranking_global():
    modelo = RecomendadorPopularidad().fit(TOY)
    assert modelo.recomendar("NUEVO", k=2) == modelo.ranking[:2]


def test_popularidad_exige_fit():
    with pytest.raises(RuntimeError):
        RecomendadorPopularidad().recomendar("A")


def test_popularidad_rechaza_entrenamiento_vacio():
    with pytest.raises(ValueError):
        RecomendadorPopularidad().fit(TOY.iloc[0:0])


def test_segmento_usa_popularidad_del_segmento():
    clientes = pd.DataFrame({"cliente_id": ["A", "B", "C", "D"], "vehiculo": ["carro", "carro", "no", "no"]})
    entrenamiento = polizas(
        [("1", "A", "P10", "2020-01-01"), ("2", "C", "P07", "2020-01-01"), ("3", "C", "P04", "2020-01-01")]
    )
    modelo = RecomendadorSegmento(clientes, ("vehiculo",)).fit(entrenamiento)
    assert modelo.recomendar("B", k=1) == ["P10"]
    assert modelo.recomendar("D", k=1)[0] in {"P07", "P04"}


def test_segmento_columna_inexistente():
    with pytest.raises(KeyError):
        RecomendadorSegmento(pd.DataFrame({"cliente_id": ["A"]}), ("estrato",))


def test_cli_generar_validar_y_baseline(tmp_path, capsys):
    assert cli.main(["reco", "generar", "--clientes", "300", "--salida", str(tmp_path)]) == 0
    assert cli.main(["reco", "validar", "--entrada", str(tmp_path)]) == 0
    assert cli.main(["reco", "baseline", "--entrada", str(tmp_path)]) == 0
    salida = capsys.readouterr().out
    assert "Contrato de datos: OK" in salida and '"segmento"' in salida


def test_cli_sin_datos_explica_como_generarlos(tmp_path):
    with pytest.raises(FileNotFoundError, match="sb reco generar"):
        recomendador.leer_tablas(tmp_path)


def test_recomendar_cliente_devuelve_k_productos_nuevos(tmp_path):
    recomendador.generar(300, 7, tmp_path)
    cliente = recomendador.leer_tablas(tmp_path)["clientes"]["cliente_id"].iloc[0]
    resultado = recomendador.recomendar(cliente, 3, tmp_path)
    assert len(resultado) == 3
    assert {"product_id", "nombre", "linea", "razon"} <= set(resultado[0])


def test_recomendar_cliente_desconocido(tmp_path):
    recomendador.generar(300, 7, tmp_path)
    with pytest.raises(KeyError):
        recomendador.recomendar("NO-EXISTE", 3, tmp_path)


def test_recomendar_k_fuera_de_rango(tmp_path):
    with pytest.raises(ValueError):
        recomendador.recomendar("X", 0, tmp_path)


def test_recomendar_por_perfil(tmp_path):
    recomendador.generar(400, 3, tmp_path)
    items, similares = recomendador.recomendar_por_perfil({"vehiculo": "carro"}, 3, tmp_path)
    assert len(items) == 3 and similares > 0
    assert "clientes similares" in items[0]["razon"]


def test_recomendar_por_perfil_vacio_usa_popularidad(tmp_path):
    recomendador.generar(400, 3, tmp_path)
    items, similares = recomendador.recomendar_por_perfil({}, 2, tmp_path)
    assert len(items) == 2 and similares == 400


def test_recomendar_por_perfil_campo_invalido(tmp_path):
    with pytest.raises(KeyError):
        recomendador.recomendar_por_perfil({"estrato": 3}, 2, tmp_path)

"""Pruebas del generador sintético (patrón AAA, sin red)."""

import numpy as np
import pandas as pd
import pytest

from sb_asistente.model.recomendador.catalogo import CATALOGO, PRODUCT_IDS
from sb_asistente.model.recomendador.contrato import validar_dataset
from sb_asistente.model.recomendador.sintetico import (
    FECHA_CORTE,
    MAX_POLIZAS_POR_CLIENTE,
    aplicar_afinidades,
    generar_clientes,
    generar_dataset,
    pesos_base,
)


@pytest.fixture(scope="module")
def dataset():
    return generar_dataset(n_clientes=600, semilla=7)


def test_catalogo_tiene_ids_unicos_y_descripciones():
    assert len(set(PRODUCT_IDS)) == len(CATALOGO) == 19
    assert all(len(p.descripcion) > 60 for p in CATALOGO)


def test_misma_semilla_mismo_dataset():
    a = generar_dataset(200, semilla=3)
    b = generar_dataset(200, semilla=3)
    pd.testing.assert_frame_equal(a.polizas, b.polizas)


def test_semilla_distinta_cambia_datos():
    a = generar_dataset(200, semilla=3)
    b = generar_dataset(200, semilla=4)
    assert not a.clientes["edad"].equals(b.clientes["edad"])


def test_dataset_cumple_contrato(dataset):
    assert validar_dataset(dataset.tablas()) == []


def test_todo_cliente_tiene_al_menos_una_poliza(dataset):
    assert set(dataset.polizas["cliente_id"]) == set(dataset.clientes["cliente_id"])


def test_limite_de_polizas_por_cliente(dataset):
    assert dataset.polizas.groupby("cliente_id").size().max() <= MAX_POLIZAS_POR_CLIENTE


def test_sin_productos_repetidos_por_cliente(dataset):
    assert not dataset.polizas.duplicated(["cliente_id", "product_id"]).any()


def test_fechas_no_superan_el_corte(dataset):
    assert dataset.polizas["fecha_inicio"].max() <= FECHA_CORTE
    assert dataset.polizas["fecha_fin"].dropna().max() <= FECHA_CORTE


def test_autos_solo_para_clientes_con_carro(dataset):
    autos = dataset.polizas.query("product_id == 'P01'").merge(dataset.clientes, on="cliente_id")
    assert (autos["vehiculo"] == "carro").all()


def test_mascotas_solo_con_mascota(dataset):
    mascotas = dataset.polizas.query("product_id == 'P07'").merge(dataset.clientes, on="cliente_id")
    assert mascotas["tiene_mascota"].all()


def test_salud_internacional_solo_estratos_altos(dataset):
    intl = dataset.polizas.query("product_id == 'P13'").merge(dataset.clientes, on="cliente_id")
    assert (intl["estrato"] >= 5).all()


def test_edades_dentro_del_rango_del_producto(dataset):
    df = dataset.polizas.merge(dataset.clientes, on="cliente_id").merge(dataset.productos, on="product_id")
    assert ((df["edad"] >= df["edad_min"]) & (df["edad"] <= df["edad_max"])).all()


def test_sin_columnas_de_identificacion_personal(dataset):
    columnas = {c for df in dataset.tablas().values() for c in df.columns}
    assert not columnas & {"nombre_cliente", "documento", "email", "telefono", "direccion"}


@pytest.mark.parametrize("n", [0, -5])
def test_generar_clientes_rechaza_n_no_positivo(n):
    with pytest.raises(ValueError):
        generar_clientes(n, np.random.default_rng(0))


def test_pesos_base_respeta_elegibilidad():
    cliente = pd.Series(
        {
            "edad": 30,
            "estrato": 3,
            "vehiculo": "ninguno",
            "vivienda": "arrendada",
            "ciudad": "Cali",
            "canal_preferido": "digital",
            "arrienda_inmueble": False,
            "tiene_mascota": False,
            "num_hijos": 0,
            "estado_civil": "soltero",
            "tiene_credito": False,
            "ocupacion": "empleado",
            "cliente_banco_aliado": False,
        }
    )
    pesos = dict(zip(PRODUCT_IDS, pesos_base(cliente), strict=True))
    assert pesos["P01"] == pesos["P04"] == pesos["P07"] == pesos["P16"] == 0
    assert pesos["P05"] > 0


def test_afinidad_aumenta_peso_del_producto_relacionado():
    pesos = np.ones(len(PRODUCT_IDS))
    ajustados = aplicar_afinidades(pesos, {"P01"})
    assert ajustados[PRODUCT_IDS.index("P10")] > 1
    assert ajustados[PRODUCT_IDS.index("P04")] == 1

"""Pruebas del contrato de datos."""

import pandas as pd
import pytest

from sb_asistente.model.recomendador.contrato import validar_dataset, validar_integridad, validar_tabla
from sb_asistente.model.recomendador.sintetico import generar_dataset


@pytest.fixture
def tablas():
    return generar_dataset(150, semilla=11).tablas()


def test_tabla_valida_no_tiene_errores(tablas):
    assert validar_tabla(tablas["clientes"], "clientes") == []


def test_detecta_columna_pii(tablas):
    df = tablas["clientes"].assign(email="x@y.com")
    assert any("PII" in e for e in validar_tabla(df, "clientes"))


def test_detecta_columna_faltante(tablas):
    df = tablas["clientes"].drop(columns="estrato")
    assert any("faltan columnas" in e for e in validar_tabla(df, "clientes"))


def test_detecta_valor_fuera_de_dominio(tablas):
    df = tablas["clientes"].copy()
    df.loc[0, "vehiculo"] = "avion"
    assert any("fuera de dominio" in e for e in validar_tabla(df, "clientes"))


def test_detecta_rango_invalido(tablas):
    df = tablas["clientes"].copy()
    df.loc[0, "estrato"] = 9
    assert any("> 6" in e for e in validar_tabla(df, "clientes"))


def test_detecta_nulos_no_permitidos(tablas):
    df = tablas["polizas"].copy()
    df["product_id"] = df["product_id"].astype(object)
    df.loc[0, "product_id"] = None
    assert any("nulos" in e for e in validar_tabla(df, "polizas"))


def test_fecha_fin_puede_ser_nula(tablas):
    assert tablas["polizas"]["fecha_fin"].isna().any()
    assert validar_tabla(tablas["polizas"], "polizas") == []


def test_detecta_tipo_incorrecto(tablas):
    df = tablas["clientes"].assign(edad=tablas["clientes"]["edad"].astype(str))
    assert any("tipo" in e for e in validar_tabla(df, "clientes"))


def test_detecta_clave_duplicada(tablas):
    df = pd.concat([tablas["productos"], tablas["productos"].head(1)])
    assert any("duplicada" in e for e in validar_tabla(df, "productos"))


def test_tabla_desconocida():
    with pytest.raises(KeyError):
        validar_tabla(pd.DataFrame(), "ventas")


def test_integridad_detecta_cliente_inexistente(tablas):
    polizas = tablas["polizas"].copy()
    polizas.loc[0, "cliente_id"] = "C999999"
    assert any("clientes inexistentes" in e for e in validar_integridad({**tablas, "polizas": polizas}))


def test_integridad_detecta_producto_repetido(tablas):
    polizas = pd.concat([tablas["polizas"], tablas["polizas"].head(1)], ignore_index=True)
    assert any("mismo producto" in e for e in validar_integridad({**tablas, "polizas": polizas}))


def test_validar_dataset_completo(tablas):
    assert validar_dataset(tablas) == []

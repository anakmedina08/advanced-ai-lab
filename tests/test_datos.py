"""Pruebas de la herramienta determinista sobre los CSV (``model/datos.py``), con tablas pequeñas."""

import json

import pandas as pd
import pytest
from pydantic import ValidationError

from sb_asistente.model.datos import ConsultaDatos, DatosError, consultar, crear_tool_datos


@pytest.fixture
def tablas() -> dict[str, pd.DataFrame]:
    productos = pd.DataFrame(
        {
            "product_id": ["P01", "P04", "P07"],
            "nombre": ["Seguro de Autos Todo Riesgo", "Seguro de Hogar", "Seguro para Mascotas"],
            "linea": ["movilidad", "hogar", "mascotas"],
        }
    )
    clientes = pd.DataFrame(
        {
            "cliente_id": ["C1", "C2", "C3"],
            "ciudad": ["Cali", "Bogotá", "Cali"],
            "canal_preferido": ["digital", "asesor", "digital"],
            "fecha_vinculacion": pd.to_datetime(["2024-02-01", "2025-08-10", "2025-09-01"]),
        }
    )
    polizas = pd.DataFrame(
        {
            "poliza_id": ["Z1", "Z2", "Z3", "Z4", "Z5", "Z6"],
            "cliente_id": ["C1", "C1", "C2", "C3", "C3", "C2"],
            "product_id": ["P01", "P04", "P01", "P07", "P01", "P04"],
            "fecha_inicio": pd.to_datetime(
                ["2025-07-15", "2025-08-01", "2025-09-30", "2025-10-01", "2024-07-20", "2025-03-03"]
            ),
            "canal_venta": ["digital", "asesor", "asesor", "digital", "digital", "asesor"],
            "prima_mensual_cop": [100_000, 50_000, 120_000, 30_000, 90_000, 55_000],
        }
    )
    siniestros = pd.DataFrame(
        {
            "siniestro_id": ["S1", "S2"],
            "poliza_id": ["Z1", "Z3"],
            "fecha": pd.to_datetime(["2025-08-20", "2025-11-02"]),
            "monto_cop": [2_000_000, 500_000],
            "estado": ["pagado", "en_tramite"],
        }
    )
    return {"productos": productos, "clientes": clientes, "polizas": polizas, "siniestros": siniestros}


def test_polizas_vendidas_en_el_tercer_trimestre(tablas):
    # Arrange
    consulta = ConsultaDatos(metrica="polizas_vendidas", anio=2025, trimestre=3)
    # Act
    r = consulta_resultado = consultar(tablas, consulta)
    # Assert
    assert r.valor == 3  # Z1, Z2 y Z3 (Z4 es del T4 y Z5 de 2024)
    assert consulta_resultado.unidad == "pólizas"
    assert "sintética" in r.fuente


def test_coincide_con_el_calculo_hecho_a_mano_con_pandas(tablas):
    # Arrange
    p = tablas["polizas"]
    esperado = p.loc[(p.fecha_inicio.dt.year == 2025) & (p.product_id == "P01"), "prima_mensual_cop"].sum()
    # Act
    r = consultar(tablas, ConsultaDatos(metrica="primas_mensuales_cop", anio=2025, producto="autos"))
    # Assert
    assert r.valor == esperado == 220_000
    assert r.filtros["producto"].startswith("P01")


def test_agrupar_por_trimestre(tablas):
    # Act
    r = consultar(tablas, ConsultaDatos(metrica="polizas_vendidas", anio=2025, agrupar_por="trimestre"))
    # Assert
    assert r.grupos == {"2025-T1": 1.0, "2025-T3": 3.0, "2025-T4": 1.0}


def test_filtrar_por_canal_y_linea(tablas):
    # Act
    r = consultar(tablas, ConsultaDatos(metrica="polizas_vendidas", canal="asesor", linea="Hogar"))
    # Assert
    assert r.valor == 2  # Z2 y Z6


def test_siniestros_y_monto(tablas):
    # Act
    cantidad = consultar(tablas, ConsultaDatos(metrica="siniestros", anio=2025, trimestre=3))
    monto = consultar(tablas, ConsultaDatos(metrica="monto_siniestros_cop", anio=2025))
    # Assert
    assert cantidad.valor == 1
    assert monto.valor == 2_500_000


def test_clientes_con_un_producto(tablas):
    # Act
    r = consultar(tablas, ConsultaDatos(metrica="clientes", producto="P07"))
    # Assert
    assert r.valor == 1  # solo C3 tiene mascotas


def test_producto_inexistente_lista_los_validos(tablas):
    # Act / Assert
    with pytest.raises(DatosError, match="Productos válidos: P01"):
        consultar(tablas, ConsultaDatos(metrica="polizas_vendidas", producto="Seguro lunar"))


def test_linea_inexistente_es_un_error_y_no_un_cero(tablas):
    # Act / Assert
    with pytest.raises(DatosError, match="Líneas válidas"):
        consultar(tablas, ConsultaDatos(metrica="polizas_vendidas", linea="espacial"))


def test_trimestre_fuera_de_rango_lo_rechaza_pydantic():
    # Act / Assert
    with pytest.raises(ValidationError):
        ConsultaDatos(metrica="polizas_vendidas", trimestre=5)


def test_tool_expone_el_esquema_pydantic_y_devuelve_json(tablas):
    # Arrange
    herramienta = crear_tool_datos(lambda: tablas)
    # Act
    salida = json.loads(herramienta.invoke({"metrica": "polizas_vendidas", "anio": 2025, "trimestre": 3}))
    # Assert
    assert herramienta.name == "consultar_datos"
    assert herramienta.args_schema is ConsultaDatos
    assert salida["valor"] == 3


def test_tool_explica_los_errores_sin_romper(tablas):
    # Arrange
    herramienta = crear_tool_datos(lambda: tablas)
    # Act
    salida = json.loads(herramienta.invoke({"metrica": "polizas_vendidas", "producto": "Seguro lunar"}))
    # Assert
    assert "no encontrado" in salida["error"]


def test_tool_sin_datos_dice_como_generarlos():
    # Arrange
    def sin_datos() -> dict:
        raise FileNotFoundError

    herramienta = crear_tool_datos(sin_datos)
    # Act
    salida = json.loads(herramienta.invoke({"metrica": "clientes"}))
    # Assert
    assert "sb reco generar" in salida["error"]

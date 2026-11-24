"""Casos tabulados del contrato de datos y del catálogo del recomendador (SPEC-066).

El contrato es la puerta que impide entrenar con datos rotos o con PII (Ley 1581). Cada caso
rompe una sola regla sobre una cartera sintética válida y verifica que el contrato lo detecte.
"""

import pandas as pd
import pytest

from sb_asistente.model.recomendador.catalogo import CATALOGO, POR_ID, PRODUCT_IDS
from sb_asistente.model.recomendador.contrato import (
    COLUMNAS_PII_PROHIBIDAS,
    ESQUEMAS,
    validar_dataset,
    validar_integridad,
    validar_tabla,
)
from sb_asistente.model.recomendador.sintetico import generar_dataset


@pytest.fixture(scope="module")
def cartera() -> dict[str, pd.DataFrame]:
    """Cartera sintética válida, generada una vez por módulo."""
    return generar_dataset(n_clientes=150, semilla=7).tablas()


@pytest.fixture
def tablas(cartera: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Copia de la cartera que cada prueba puede romper sin afectar a las demás."""
    return {nombre: df.copy() for nombre, df in cartera.items()}


def test_la_cartera_sintetica_cumple_el_contrato(tablas):
    # Arrange
    # Act
    errores = validar_dataset(tablas)
    # Assert
    assert errores == []


@pytest.mark.parametrize("semilla", [1, 2, 3])
def test_cualquier_semilla_cumple_el_contrato(semilla):
    # Arrange
    tablas = generar_dataset(n_clientes=80, semilla=semilla).tablas()
    # Act
    errores = validar_dataset(tablas)
    # Assert
    assert errores == []


def test_misma_semilla_mismas_tablas():
    # Arrange
    a, b = generar_dataset(60, 11).tablas(), generar_dataset(60, 11).tablas()
    # Act
    iguales = all(a[n].equals(b[n]) for n in a)
    # Assert
    assert iguales


# --- PII ----------------------------------------------------------------------------------------


@pytest.mark.parametrize("columna", sorted(COLUMNAS_PII_PROHIBIDAS))
def test_rechaza_columnas_pii(tablas, columna):
    # Arrange
    tablas["clientes"][columna] = "dato"
    # Act
    errores = validar_tabla(tablas["clientes"], "clientes")
    # Assert
    assert any("PII" in e and columna in e for e in errores)


@pytest.mark.parametrize("columna", ["Email", "CEDULA", "Telefono"])
def test_la_pii_se_detecta_sin_importar_mayusculas(tablas, columna):
    # Arrange
    tablas["clientes"][columna] = "dato"
    # Act
    errores = validar_tabla(tablas["clientes"], "clientes")
    # Assert
    assert any("PII" in e for e in errores)


# --- reglas por columna -------------------------------------------------------------------------

DOMINIOS = [
    ("clientes", "genero", "X"),
    ("clientes", "ocupacion", "astronauta"),
    ("clientes", "ingreso_smmlv", "mucho"),
    ("clientes", "estado_civil", "viudo"),
    ("clientes", "vehiculo", "avion"),
    ("clientes", "vivienda", "hotel"),
    ("clientes", "canal_preferido", "fax"),
    ("polizas", "product_id", "P99"),
    ("polizas", "estado", "suspendida"),
    ("polizas", "canal_venta", "fax"),
    ("siniestros", "estado", "perdido"),
]


@pytest.mark.parametrize(("tabla", "columna", "valor"), DOMINIOS)
def test_detecta_valores_fuera_de_dominio(tablas, tabla, columna, valor):
    # Arrange
    tablas[tabla].loc[tablas[tabla].index[0], columna] = valor
    # Act
    errores = validar_tabla(tablas[tabla], tabla)
    # Assert
    assert f"{tabla}.{columna}: valores fuera de dominio ['{valor}']" in errores


RANGOS = [
    ("clientes", "edad", 17, "<"),
    ("clientes", "edad", 101, ">"),
    ("clientes", "estrato", 0, "<"),
    ("clientes", "estrato", 7, ">"),
    ("clientes", "num_hijos", -1, "<"),
    ("clientes", "num_hijos", 16, ">"),
    ("polizas", "prima_mensual_cop", -5, "<"),
    ("siniestros", "monto_cop", -1, "<"),
    ("productos", "prima_base_cop", -1, "<"),
    ("productos", "edad_max", 101, ">"),
]


@pytest.mark.parametrize(("tabla", "columna", "valor", "signo"), RANGOS)
def test_detecta_valores_fuera_de_rango(tablas, tabla, columna, valor, signo):
    # Arrange
    tablas[tabla].loc[tablas[tabla].index[0], columna] = valor
    # Act
    errores = validar_tabla(tablas[tabla], tabla)
    # Assert
    assert any(e.startswith(f"{tabla}.{columna}: valores {signo}") for e in errores)


@pytest.mark.parametrize(
    ("tabla", "columna"),
    [
        ("clientes", "edad"),
        ("clientes", "ciudad"),
        ("polizas", "fecha_inicio"),
        ("siniestros", "fecha"),
        ("productos", "nombre"),
    ],
)
def test_detecta_nulos_donde_no_se_permiten(tablas, tabla, columna):
    # Arrange
    df = tablas[tabla]
    df[columna] = df[columna].astype(object)
    df.loc[df.index[0], columna] = None
    # Act
    errores = validar_tabla(df, tabla)
    # Assert
    assert f"{tabla}.{columna}: tiene nulos" in errores


def test_fecha_fin_admite_nulos(tablas):
    # Arrange
    tablas["polizas"]["fecha_fin"] = pd.NaT
    # Act
    errores = validar_tabla(tablas["polizas"], "polizas")
    # Assert
    assert errores == []


@pytest.mark.parametrize(
    ("tabla", "columna", "valor"),
    [
        ("clientes", "edad", "treinta"),
        ("clientes", "tiene_mascota", "sí"),
        ("polizas", "fecha_inicio", "ayer"),
        ("siniestros", "monto_cop", "mucho"),
    ],
)
def test_detecta_tipos_incorrectos(tablas, tabla, columna, valor):
    # Arrange
    df = tablas[tabla]
    df[columna] = df[columna].astype(object)
    df.loc[df.index[0], columna] = valor
    # Act
    errores = validar_tabla(df, tabla)
    # Assert
    assert any(e.startswith(f"{tabla}.{columna}: tipo") for e in errores)


@pytest.mark.parametrize("tabla", list(ESQUEMAS))
def test_detecta_columnas_faltantes(tablas, tabla):
    # Arrange
    obligatoria = ESQUEMAS[tabla].columnas[-1].nombre
    df = tablas[tabla].drop(columns=[obligatoria])
    # Act
    errores = validar_tabla(df, tabla)
    # Assert
    assert f"{tabla}: faltan columnas ['{obligatoria}']" in errores


@pytest.mark.parametrize("tabla", list(ESQUEMAS))
def test_detecta_claves_duplicadas(tablas, tabla):
    # Arrange
    df = pd.concat([tablas[tabla], tablas[tabla].head(1)], ignore_index=True)
    # Act
    errores = validar_tabla(df, tabla)
    # Assert
    assert f"{tabla}.{ESQUEMAS[tabla].clave}: clave duplicada" in errores


def test_tabla_desconocida_falla(tablas):
    # Arrange
    # Act / Assert
    with pytest.raises(KeyError, match="desconocida"):
        validar_tabla(tablas["clientes"], "empleados")


# --- integridad ---------------------------------------------------------------------------------


def test_integridad_cliente_inexistente(tablas):
    # Arrange
    tablas["polizas"].loc[tablas["polizas"].index[0], "cliente_id"] = "fantasma"
    # Act
    errores = validar_integridad(tablas)
    # Assert
    assert "polizas.cliente_id: hay clientes inexistentes" in errores


def test_integridad_poliza_inexistente(tablas):
    # Arrange
    if tablas["siniestros"].empty:
        pytest.skip("la semilla no generó siniestros")
    tablas["siniestros"].loc[tablas["siniestros"].index[0], "poliza_id"] = "fantasma"
    # Act
    errores = validar_integridad(tablas)
    # Assert
    assert "siniestros.poliza_id: hay pólizas inexistentes" in errores


def test_integridad_fecha_fin_antes_del_inicio(tablas):
    # Arrange
    polizas = tablas["polizas"]
    polizas.loc[polizas.index[0], "fecha_fin"] = polizas.loc[polizas.index[0], "fecha_inicio"] - pd.Timedelta(
        days=1
    )
    # Act
    errores = validar_integridad(tablas)
    # Assert
    assert "polizas: fecha_fin anterior a fecha_inicio" in errores


def test_integridad_producto_repetido_por_cliente(tablas):
    # Arrange
    fila = tablas["polizas"].head(1).assign(poliza_id="duplicada")
    tablas["polizas"] = pd.concat([tablas["polizas"], fila], ignore_index=True)
    # Act
    errores = validar_integridad(tablas)
    # Assert
    assert "polizas: un cliente tiene dos veces el mismo producto" in errores


def test_validar_dataset_no_revisa_integridad_si_una_tabla_falla(tablas):
    # Arrange: tabla inválida y, además, llave foránea rota
    tablas["clientes"]["email"] = "x"
    tablas["polizas"].loc[tablas["polizas"].index[0], "cliente_id"] = "fantasma"
    # Act
    errores = validar_dataset(tablas)
    # Assert
    assert errores and all("inexistentes" not in e for e in errores)


# --- catálogo -----------------------------------------------------------------------------------


@pytest.mark.parametrize("producto", CATALOGO, ids=lambda p: p.product_id)
def test_cada_producto_es_coherente(producto):
    # Arrange
    # Act
    rango_edad = (producto.edad_min, producto.edad_max)
    # Assert
    assert producto.product_id.startswith("P") and producto.nombre and len(producto.descripcion) >= 60
    assert producto.prima_base_cop > 0 and 0 <= rango_edad[0] < rango_edad[1] <= 100


def test_los_ids_del_catalogo_son_unicos_y_estan_indexados():
    # Arrange
    # Act
    ids = list(PRODUCT_IDS)
    # Assert
    assert len(ids) == len(set(ids)) == len(CATALOGO) and set(POR_ID) == set(ids)


def test_el_catalogo_no_tiene_marca_comercial_en_las_descripciones():
    # Arrange
    # Act
    con_marca = [p.product_id for p in CATALOGO if "bolívar" in p.descripcion.lower()]
    # Assert
    assert con_marca == []

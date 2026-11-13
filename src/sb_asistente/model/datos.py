"""Herramienta determinista sobre los datos estructurados (CSV sintéticos del recomendador).

El LLM **no calcula**: elige una métrica y unos filtros validados con ``ConsultaDatos`` y este
módulo hace la cuenta con pandas. Así una pregunta como «¿cuántas pólizas se vendieron en el
tercer trimestre de 2025?» devuelve el número exacto y los filtros usados, nunca una cifra
estimada. Las métricas son cerradas (``Literal``): no hay SQL ni código generado por el modelo.

Los datos son **sintéticos** (Ley 1581 de 2012): la respuesta siempre lo indica.
"""

import json
import unicodedata
from collections.abc import Callable
from typing import Literal

import pandas as pd
from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field, ValidationError

Metrica = Literal[
    "polizas_vendidas", "primas_mensuales_cop", "siniestros", "monto_siniestros_cop", "clientes"
]
Agrupacion = Literal["anio", "trimestre", "producto", "linea", "canal", "ciudad"]
Canal = Literal["digital", "asesor", "banca_aliada", "telefonico"]

UNIDADES: dict[str, str] = {
    "polizas_vendidas": "pólizas",
    "primas_mensuales_cop": "COP por mes",
    "siniestros": "siniestros",
    "monto_siniestros_cop": "COP",
    "clientes": "clientes",
}
FUENTE = "data/recomendador/*.csv (cartera sintética de práctica, no datos reales)"


class DatosError(ValueError):
    """La consulta no se puede responder con los datos (filtro desconocido)."""


class ConsultaDatos(BaseModel):
    """Parámetros de una consulta numérica sobre la cartera sintética."""

    metrica: Metrica = Field(
        description=(
            "polizas_vendidas (pólizas que iniciaron en el periodo), primas_mensuales_cop (suma de las "
            "primas de esas pólizas), siniestros (reclamaciones), monto_siniestros_cop (suma reclamada) o "
            "clientes (clientes vinculados en el periodo)."
        )
    )
    anio: int | None = Field(default=None, ge=2014, le=2026, description="Año, p. ej. 2025.")
    trimestre: int | None = Field(default=None, ge=1, le=4, description="Trimestre 1 a 4 (3 = jul–sep).")
    producto: str | None = Field(default=None, max_length=80, description="Nombre o id (P01…P19).")
    linea: str | None = Field(default=None, max_length=40, description="movilidad, hogar, vida, salud…")
    canal: Canal | None = Field(default=None, description="Canal de venta.")
    agrupar_por: Agrupacion | None = Field(default=None, description="Desglose por esta columna.")


class ResultadoDatos(BaseModel):
    """Resultado exacto de una consulta, con lo necesario para citarlo."""

    metrica: str
    valor: float
    unidad: str
    filtros: dict[str, object]
    filas: int = Field(description="Filas que entraron en el cálculo.")
    grupos: dict[str, float] | None = None
    fuente: str = FUENTE


def _normal(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sin_tildes.lower().split())


def _producto_id(productos: pd.DataFrame, buscado: str) -> str:
    """Id del producto por id exacto, nombre exacto o coincidencia única (sin tildes)."""
    clave = _normal(buscado)
    ids = {_normal(i): i for i in productos["product_id"]}
    if clave in ids:
        return ids[clave]
    nombres = {_normal(n): i for n, i in zip(productos["nombre"], productos["product_id"], strict=True)}
    if clave in nombres:
        return nombres[clave]
    parecidos = [i for n, i in nombres.items() if clave in n]
    if len(parecidos) == 1:
        return parecidos[0]
    validos = ", ".join(f"{i} {n}" for i, n in zip(productos["product_id"], productos["nombre"], strict=True))
    raise DatosError(f"Producto «{buscado}» no encontrado o ambiguo. Productos válidos: {validos}.")


def _base(tablas: dict[str, pd.DataFrame], metrica: str) -> tuple[pd.DataFrame, str, str | None]:
    """Tabla de hechos, columna de fecha y columna a sumar (``None`` = contar filas)."""
    productos = tablas["productos"][["product_id", "nombre", "linea"]]
    clientes = tablas["clientes"][["cliente_id", "ciudad"]]
    polizas = tablas["polizas"].merge(productos, on="product_id").merge(clientes, on="cliente_id")
    polizas = polizas.rename(columns={"canal_venta": "canal"})
    if metrica in ("polizas_vendidas", "primas_mensuales_cop"):
        return polizas, "fecha_inicio", "prima_mensual_cop" if metrica == "primas_mensuales_cop" else None
    if metrica in ("siniestros", "monto_siniestros_cop"):
        columnas = ["poliza_id", "product_id", "nombre", "linea", "canal", "ciudad"]
        hechos = tablas["siniestros"].merge(polizas[columnas], on="poliza_id")
        return hechos, "fecha", "monto_cop" if metrica == "monto_siniestros_cop" else None
    return tablas["clientes"].rename(columns={"canal_preferido": "canal"}), "fecha_vinculacion", None


def _filtro_producto(
    tablas: dict[str, pd.DataFrame],
    hechos: pd.DataFrame,
    metrica: str,
    producto_id: str | None,
    linea: str | None,
) -> pd.Series:
    """Filtra por producto o línea; para ``clientes``, los que tienen una póliza de ese producto o línea."""
    filtro = pd.Series(True, index=hechos.index)
    if metrica != "clientes":
        if producto_id:
            filtro &= hechos["product_id"] == producto_id
        if linea:
            filtro &= hechos["linea"] == linea
        return filtro
    polizas = tablas["polizas"].merge(tablas["productos"][["product_id", "linea"]], on="product_id")
    if producto_id:
        filtro &= hechos["cliente_id"].isin(polizas.loc[polizas["product_id"] == producto_id, "cliente_id"])
    if linea:
        filtro &= hechos["cliente_id"].isin(polizas.loc[polizas["linea"] == linea, "cliente_id"])
    return filtro


def consultar(tablas: dict[str, pd.DataFrame], consulta: ConsultaDatos) -> ResultadoDatos:
    """Calcula la métrica con los filtros pedidos (función pura; no usa LLM).

    Raises:
        DatosError: si un producto o una línea no existen, o la agrupación no aplica.

    """
    productos = tablas["productos"]
    producto_id = _producto_id(productos, consulta.producto) if consulta.producto else None
    linea = _normal(consulta.linea) if consulta.linea else None
    if linea and linea not in set(productos["linea"]):
        validas = ", ".join(sorted(productos["linea"].unique()))
        raise DatosError(f"Línea «{consulta.linea}» no existe. Líneas válidas: {validas}.")
    hechos, fecha, columna = _base(tablas, consulta.metrica)
    fechas = pd.to_datetime(hechos[fecha])
    filtro = _filtro_producto(tablas, hechos, consulta.metrica, producto_id, linea)
    if consulta.anio is not None:
        filtro &= fechas.dt.year == consulta.anio
    if consulta.trimestre is not None:
        filtro &= fechas.dt.quarter == consulta.trimestre
    if consulta.canal is not None:
        filtro &= hechos["canal"] == consulta.canal
    elegidos = hechos[filtro].assign(
        anio=fechas[filtro].dt.year.astype(str),
        trimestre=fechas[filtro].dt.year.astype(str) + "-T" + fechas[filtro].dt.quarter.astype(str),
    )
    elegidos = elegidos.rename(columns={"nombre": "producto"})

    def total(df: pd.DataFrame) -> float:
        return float(df[columna].sum()) if columna else float(len(df))

    grupos = None
    if consulta.agrupar_por:
        if consulta.agrupar_por not in elegidos:
            raise DatosError(f"La métrica {consulta.metrica} no se puede agrupar por {consulta.agrupar_por}.")
        grupos = {str(k): total(g) for k, g in elegidos.groupby(consulta.agrupar_por, sort=True)}
    filtros = consulta.model_dump(exclude_none=True, exclude={"metrica", "agrupar_por"})
    if producto_id:
        filtros["producto"] = f"{producto_id} {productos.set_index('product_id').at[producto_id, 'nombre']}"
    return ResultadoDatos(
        metrica=consulta.metrica,
        valor=total(elegidos),
        unidad=UNIDADES[consulta.metrica],
        filtros=filtros,
        filas=len(elegidos),
        grupos=grupos,
    )


def crear_tool_datos(cargar: Callable[[], dict[str, pd.DataFrame]]) -> BaseTool:
    """Tool ``consultar_datos`` con la carga de tablas inyectada (las pruebas usan tablas pequeñas)."""

    @tool("consultar_datos", args_schema=ConsultaDatos)
    def consultar_datos(**parametros: object) -> str:
        """Cifras exactas de la cartera sintética: pólizas vendidas, primas, siniestros y clientes.

        Úsala para cualquier pregunta numérica (cuántos, total, suma, por trimestre, por canal). Copia
        el `valor` tal cual: no recalcules ni redondees. Los datos son sintéticos de práctica.
        """
        try:
            resultado = consultar(cargar(), ConsultaDatos(**parametros))
        except FileNotFoundError:
            falta = {"error": "Faltan los datos. Ejecute: uv run sb reco generar"}
            return json.dumps(falta, ensure_ascii=False)
        except (DatosError, ValidationError) as exc:
            return json.dumps({"error": str(exc)}, ensure_ascii=False)
        return resultado.model_dump_json()

    return consultar_datos

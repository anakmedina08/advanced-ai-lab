"""Contrato de datos: columnas, tipos y dominios que deben cumplir las tablas.

Los datos sintéticos de hoy y los datos reales anonimizados de mañana pasan por el mismo
contrato. Si un extracto real no lo cumple, el pipeline se detiene antes de entrenar.
Prohíbe explícitamente columnas de identificación personal (PII).
"""

from dataclasses import dataclass, field

import pandas as pd

from sb_asistente.model.recomendador.catalogo import PRODUCT_IDS

# Columnas que nunca deben llegar al proyecto, ni en datos reales (Ley 1581 de 2012).
COLUMNAS_PII_PROHIBIDAS: frozenset[str] = frozenset(
    {
        "nombre_cliente",
        "nombres",
        "apellidos",
        "documento",
        "numero_documento",
        "cedula",
        "email",
        "correo",
        "telefono",
        "celular",
        "direccion",
        "fecha_nacimiento",
    }
)


@dataclass(frozen=True, slots=True)
class Columna:
    """Regla de una columna."""

    nombre: str
    tipo: str  # "str", "int", "bool", "date", "float"
    nulos: bool = False
    dominio: frozenset | None = None
    minimo: float | None = None
    maximo: float | None = None


@dataclass(frozen=True, slots=True)
class Esquema:
    """Reglas de una tabla."""

    tabla: str
    clave: str
    columnas: tuple[Columna, ...] = field(default_factory=tuple)


ESQUEMAS: dict[str, Esquema] = {
    "clientes": Esquema(
        "clientes",
        "cliente_id",
        (
            Columna("cliente_id", "str"),
            Columna("edad", "int", minimo=18, maximo=100),
            Columna("genero", "str", dominio=frozenset({"F", "M", "O"})),
            Columna("ciudad", "str"),
            Columna("estrato", "int", minimo=1, maximo=6),
            Columna(
                "ocupacion",
                "str",
                dominio=frozenset({"empleado", "independiente", "pensionado", "estudiante"}),
            ),
            Columna("ingreso_smmlv", "str", dominio=frozenset({"<2", "2-4", "4-8", ">8"})),
            Columna("estado_civil", "str", dominio=frozenset({"casado_union", "soltero"})),
            Columna("num_hijos", "int", minimo=0, maximo=15),
            Columna("vehiculo", "str", dominio=frozenset({"ninguno", "carro", "moto", "electrico"})),
            Columna("vivienda", "str", dominio=frozenset({"propia", "arrendada", "familiar"})),
            Columna("arrienda_inmueble", "bool"),
            Columna("tiene_mascota", "bool"),
            Columna("tiene_credito", "bool"),
            Columna("cliente_banco_aliado", "bool"),
            Columna(
                "canal_preferido",
                "str",
                dominio=frozenset({"digital", "asesor", "banca_aliada", "telefonico"}),
            ),
            Columna("fecha_vinculacion", "date"),
        ),
    ),
    "productos": Esquema(
        "productos",
        "product_id",
        (
            Columna("product_id", "str", dominio=frozenset(PRODUCT_IDS)),
            Columna("nombre", "str"),
            Columna("linea", "str"),
            Columna("descripcion", "str"),
            Columna("prima_base_cop", "int", minimo=0),
            Columna("edad_min", "int", minimo=0, maximo=100),
            Columna("edad_max", "int", minimo=0, maximo=100),
        ),
    ),
    "polizas": Esquema(
        "polizas",
        "poliza_id",
        (
            Columna("poliza_id", "str"),
            Columna("cliente_id", "str"),
            Columna("product_id", "str", dominio=frozenset(PRODUCT_IDS)),
            Columna("fecha_inicio", "date"),
            Columna("estado", "str", dominio=frozenset({"vigente", "cancelada"})),
            Columna("fecha_fin", "date", nulos=True),
            Columna(
                "canal_venta", "str", dominio=frozenset({"digital", "asesor", "banca_aliada", "telefonico"})
            ),
            Columna("prima_mensual_cop", "int", minimo=0),
        ),
    ),
    "siniestros": Esquema(
        "siniestros",
        "siniestro_id",
        (
            Columna("siniestro_id", "str"),
            Columna("poliza_id", "str"),
            Columna("fecha", "date"),
            Columna("monto_cop", "int", minimo=0),
            Columna("estado", "str", dominio=frozenset({"pagado", "objetado", "en_tramite"})),
        ),
    ),
}

_CHEQUEO_TIPO = {
    "str": pd.api.types.is_string_dtype,
    "int": pd.api.types.is_integer_dtype,
    "bool": pd.api.types.is_bool_dtype,
    "date": pd.api.types.is_datetime64_any_dtype,
    "float": pd.api.types.is_float_dtype,
}


def validar_tabla(df: pd.DataFrame, nombre: str) -> list[str]:
    """Devuelve la lista de violaciones del contrato (vacía si la tabla es válida)."""
    if nombre not in ESQUEMAS:
        raise KeyError(f"Tabla desconocida: {nombre}")
    esquema = ESQUEMAS[nombre]
    errores: list[str] = []
    pii = COLUMNAS_PII_PROHIBIDAS & {c.lower() for c in df.columns}
    if pii:
        errores.append(f"{nombre}: columnas PII prohibidas {sorted(pii)}")
    esperadas = [c.nombre for c in esquema.columnas]
    faltan = [c for c in esperadas if c not in df.columns]
    if faltan:
        errores.append(f"{nombre}: faltan columnas {faltan}")
    for col in esquema.columnas:
        if col.nombre not in df.columns:
            continue
        serie = df[col.nombre]
        if not col.nulos and serie.isna().any():
            errores.append(f"{nombre}.{col.nombre}: tiene nulos")
        no_nulos = serie.dropna()
        if len(no_nulos) and not _CHEQUEO_TIPO[col.tipo](serie):
            errores.append(f"{nombre}.{col.nombre}: tipo {serie.dtype} ≠ {col.tipo}")
            continue
        if col.dominio is not None and not set(no_nulos.unique()) <= col.dominio:
            extra = sorted(set(no_nulos.unique()) - col.dominio)[:5]
            errores.append(f"{nombre}.{col.nombre}: valores fuera de dominio {extra}")
        if col.minimo is not None and (no_nulos < col.minimo).any():
            errores.append(f"{nombre}.{col.nombre}: valores < {col.minimo}")
        if col.maximo is not None and (no_nulos > col.maximo).any():
            errores.append(f"{nombre}.{col.nombre}: valores > {col.maximo}")
    if esquema.clave in df.columns and df[esquema.clave].duplicated().any():
        errores.append(f"{nombre}.{esquema.clave}: clave duplicada")
    return errores


def validar_integridad(tablas: dict[str, pd.DataFrame]) -> list[str]:
    """Llaves foráneas y coherencia temporal entre tablas."""
    errores: list[str] = []
    clientes, polizas, siniestros = tablas["clientes"], tablas["polizas"], tablas["siniestros"]
    if not polizas["cliente_id"].isin(clientes["cliente_id"]).all():
        errores.append("polizas.cliente_id: hay clientes inexistentes")
    if not siniestros["poliza_id"].isin(polizas["poliza_id"]).all():
        errores.append("siniestros.poliza_id: hay pólizas inexistentes")
    fin = polizas["fecha_fin"].dropna()
    if (fin < polizas.loc[fin.index, "fecha_inicio"]).any():
        errores.append("polizas: fecha_fin anterior a fecha_inicio")
    if polizas.duplicated(["cliente_id", "product_id"]).any():
        errores.append("polizas: un cliente tiene dos veces el mismo producto")
    return errores


def validar_dataset(tablas: dict[str, pd.DataFrame]) -> list[str]:
    """Contrato completo: cada tabla más la integridad entre ellas."""
    errores = [e for nombre, df in tablas.items() for e in validar_tabla(df, nombre)]
    return errores or validar_integridad(tablas)

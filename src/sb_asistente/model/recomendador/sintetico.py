"""Generador reproducible de datos sintéticos de una cartera de seguros para personas.

Produce cuatro tablas con el mismo contrato que tendrán los datos reales anonimizados
(ver :mod:`recomendador.data.contrato`): ``clientes``, ``productos``, ``polizas`` y
``siniestros``. No contiene nombres, documentos ni datos de contacto: los identificadores son
consecutivos y no corresponden a personas reales.

La compra se simula en dos pasos para que exista una señal aprendible:

1. **Propensión base** según el perfil (p. ej. solo quien tiene carro compra Autos).
2. **Venta cruzada**: los productos que ya tiene el cliente aumentan la probabilidad de
   otros (Autos → Accidentes, Hogar → Mascotas, Salud → Renta por hospitalización…).
"""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd

from sb_asistente.model.recomendador.catalogo import CATALOGO, POR_ID, PRODUCT_IDS

FECHA_INICIO_CARTERA = pd.Timestamp("2014-01-01")
FECHA_CORTE = pd.Timestamp("2026-09-30")
MAX_POLIZAS_POR_CLIENTE = 6

CIUDADES = ("Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga", "Cartagena", "Pereira", "Manizales")
PESO_CIUDADES = (0.36, 0.17, 0.13, 0.10, 0.07, 0.06, 0.06, 0.05)
PESO_ESTRATOS = (0.10, 0.25, 0.30, 0.18, 0.10, 0.07)  # estratos 1..6
OCUPACIONES = ("empleado", "independiente", "pensionado", "estudiante")
CANALES = ("digital", "asesor", "banca_aliada", "telefonico")
RANGOS_INGRESO = ("<2", "2-4", "4-8", ">8")  # en salarios mínimos

# Venta cruzada: (producto que ya tiene, producto que se potencia, multiplicador)
AFINIDADES: tuple[tuple[str, str, float], ...] = (
    ("P01", "P10", 1.8),
    ("P02", "P19", 1.5),
    ("P03", "P10", 1.6),
    ("P04", "P07", 1.6),
    ("P04", "P06", 1.4),
    ("P08", "P15", 1.7),
    ("P09", "P18", 2.0),
    ("P12", "P14", 1.6),
    ("P12", "P15", 1.5),
    ("P16", "P08", 1.6),
)

# Frecuencia anual esperada de siniestros por línea
TASA_SINIESTROS: dict[str, float] = {
    "movilidad": 0.18,
    "hogar": 0.08,
    "mascotas": 0.25,
    "salud": 0.40,
    "accidentes": 0.05,
    "vida": 0.005,
    "ahorro": 0.0,
    "proteccion_financiera": 0.06,
}


@dataclass(frozen=True, slots=True)
class DatasetSintetico:
    """Las cuatro tablas de la cartera sintética."""

    clientes: pd.DataFrame
    productos: pd.DataFrame
    polizas: pd.DataFrame
    siniestros: pd.DataFrame

    def tablas(self) -> dict[str, pd.DataFrame]:
        """Diccionario nombre → tabla (para guardar o validar)."""
        return {
            "clientes": self.clientes,
            "productos": self.productos,
            "polizas": self.polizas,
            "siniestros": self.siniestros,
        }


def generar_productos() -> pd.DataFrame:
    """Tabla del catálogo."""
    return pd.DataFrame(
        [
            {
                "product_id": p.product_id,
                "nombre": p.nombre,
                "linea": p.linea,
                "descripcion": p.descripcion,
                "prima_base_cop": p.prima_base_cop,
                "edad_min": p.edad_min,
                "edad_max": p.edad_max,
            }
            for p in CATALOGO
        ]
    )


def generar_clientes(n: int, rng: np.random.Generator) -> pd.DataFrame:
    """Perfiles sintéticos de ``n`` clientes con correlaciones plausibles."""
    if n <= 0:
        raise ValueError("n debe ser positivo.")
    edad = np.clip(rng.normal(41, 13, n).round(), 18, 80).astype(int)
    estrato = rng.choice(np.arange(1, 7), size=n, p=PESO_ESTRATOS)
    ocupacion = np.where(
        edad >= 62,
        rng.choice(OCUPACIONES, n, p=(0.15, 0.10, 0.75, 0.0)),
        np.where(
            edad <= 24,
            rng.choice(OCUPACIONES, n, p=(0.45, 0.15, 0.0, 0.40)),
            rng.choice(OCUPACIONES, n, p=(0.68, 0.30, 0.02, 0.0)),
        ),
    )
    # Ingreso correlacionado con el estrato
    idx_ingreso = np.clip(np.round((estrato - 1) * 0.6 + rng.normal(0, 0.7, n)), 0, 3).astype(int)
    casado = rng.random(n) < np.clip((edad - 22) / 40, 0.05, 0.65)
    num_hijos = np.where(edad < 23, 0, rng.poisson(np.where(casado, 1.6, 0.5)))
    num_hijos = np.minimum(num_hijos, 5)
    prob_carro = np.clip(0.08 + 0.11 * (estrato - 1), 0, 0.85)
    u = rng.random(n)
    vehiculo = np.select(
        [u < prob_carro * 0.06, u < prob_carro, u < prob_carro + 0.12],
        ["electrico", "carro", "moto"],
        default="ninguno",
    )
    prob_propia = np.clip(0.15 + 0.012 * (edad - 18) + 0.05 * (estrato - 1), 0.05, 0.9)
    u = rng.random(n)
    vivienda = np.where(u < prob_propia, "propia", np.where(u < prob_propia + 0.25, "arrendada", "familiar"))
    arrienda_inmueble = (vivienda == "propia") & (rng.random(n) < np.clip(0.04 * (estrato - 1), 0, 0.3))
    canal = np.where(
        edad < 35,
        rng.choice(CANALES, n, p=(0.55, 0.15, 0.20, 0.10)),
        rng.choice(CANALES, n, p=(0.25, 0.35, 0.25, 0.15)),
    )
    dias_cartera = (FECHA_CORTE - FECHA_INICIO_CARTERA).days - 270
    fecha_vinculacion = FECHA_INICIO_CARTERA + pd.to_timedelta(rng.integers(0, dias_cartera, n), unit="D")
    return pd.DataFrame(
        {
            "cliente_id": [f"C{i:06d}" for i in range(1, n + 1)],
            "edad": edad,
            "genero": rng.choice(("F", "M", "O"), n, p=(0.51, 0.48, 0.01)),
            "ciudad": rng.choice(CIUDADES, n, p=PESO_CIUDADES),
            "estrato": estrato,
            "ocupacion": ocupacion,
            "ingreso_smmlv": np.array(RANGOS_INGRESO)[idx_ingreso],
            "estado_civil": np.where(casado, "casado_union", "soltero"),
            "num_hijos": num_hijos,
            "vehiculo": vehiculo,
            "vivienda": vivienda,
            "arrienda_inmueble": arrienda_inmueble,
            "tiene_mascota": rng.random(n) < 0.42,
            "tiene_credito": rng.random(n) < np.clip(0.2 + 0.06 * estrato, 0, 0.7),
            "cliente_banco_aliado": rng.random(n) < 0.45,
            "canal_preferido": canal,
            "fecha_vinculacion": fecha_vinculacion.normalize(),
        }
    )


def _reglas_propension() -> dict[str, Callable[[pd.Series], float]]:
    """Peso base (≥ 0) de cada producto según el perfil; 0 = no elegible."""
    return {
        "P01": lambda c: 3.0 * (1 + c.estrato / 6) if c.vehiculo == "carro" else 0.0,
        "P02": lambda c: 4.0 if c.vehiculo == "electrico" else 0.0,
        "P03": lambda c: (0.45 if c.edad < 45 else 0.12) * (1.5 if c.ciudad in ("Bogotá", "Medellín") else 1),
        "P04": lambda c: 2.0 if c.vivienda == "propia" else 0.0,
        "P05": lambda c: (
            (0.8 if c.vivienda != "familiar" else 0.0)
            * (2.0 if c.canal_preferido == "digital" else 1)
            * (1.5 if c.edad < 40 else 1)
        ),
        "P06": lambda c: 3.0 if c.arrienda_inmueble else 0.0,
        "P07": lambda c: 2.5 if c.tiene_mascota else 0.0,
        "P08": lambda c: (
            0.6 * (2.0 if c.num_hijos > 0 else 1) * (1.3 if c.estado_civil == "casado_union" else 1)
        ),
        "P09": lambda c: 2.5 if c.tiene_credito else 0.0,
        "P10": lambda c: 0.7 * (1.5 if c.ocupacion == "independiente" else 1),
        "P11": lambda c: (1.0 if c.ocupacion == "independiente" else 0.1) * (1.5 if c.edad < 40 else 1),
        "P12": lambda c: 0.4 * c.estrato if c.estrato >= 3 else 0.05,
        "P13": lambda c: 1.5 if c.estrato >= 5 else 0.0,
        "P14": lambda c: 0.5,
        "P15": lambda c: 0.8 if c.edad >= 35 else 0.15,
        "P16": lambda c: 1.8 if c.num_hijos > 0 and 25 <= c.edad <= 55 else 0.0,
        "P17": lambda c: 0.5 * (1.3 if 2 <= c.estrato <= 4 else 1),
        "P18": lambda c: 1.5 if c.cliente_banco_aliado else 0.2,
        "P19": lambda c: 0.8 if c.canal_preferido == "digital" else 0.2,
    }


def pesos_base(cliente: pd.Series) -> np.ndarray:
    """Vector de propensión base del cliente sobre todo el catálogo (respeta edades)."""
    reglas = _reglas_propension()
    pesos = np.array([reglas[pid](cliente) for pid in PRODUCT_IDS], dtype=float)
    edad_ok = np.array([POR_ID[pid].edad_min <= cliente.edad <= POR_ID[pid].edad_max for pid in PRODUCT_IDS])
    return pesos * edad_ok


def aplicar_afinidades(pesos: np.ndarray, poseidos: set[str]) -> np.ndarray:
    """Potencia los productos afines a los que ya tiene el cliente."""
    ajustados = pesos.copy()
    for origen, destino, factor in AFINIDADES:
        if origen in poseidos:
            ajustados[PRODUCT_IDS.index(destino)] *= factor
    return ajustados


def generar_polizas(clientes: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Historia de compra de cada cliente: una fila por póliza, en orden cronológico."""
    filas: list[dict[str, object]] = []
    for c in clientes.itertuples(index=False):
        antiguedad_anios = (FECHA_CORTE - c.fecha_vinculacion).days / 365.25
        lam = 0.5 + 0.12 * c.estrato + 0.08 * min(antiguedad_anios, 10) + 0.4 * c.cliente_banco_aliado
        objetivo = min(1 + rng.poisson(lam), MAX_POLIZAS_POR_CLIENTE)
        base = pesos_base(pd.Series(c._asdict()))
        poseidos: set[str] = set()
        fecha = c.fecha_vinculacion + pd.Timedelta(days=int(rng.integers(0, 60)))
        for _ in range(objetivo):
            pesos = aplicar_afinidades(base, poseidos)
            pesos[[PRODUCT_IDS.index(p) for p in poseidos]] = 0.0
            if fecha > FECHA_CORTE or pesos.sum() == 0:
                break
            pid = PRODUCT_IDS[rng.choice(len(PRODUCT_IDS), p=pesos / pesos.sum())]
            poseidos.add(pid)
            producto = POR_ID[pid]
            cancelada = rng.random() < 0.12
            fecha_fin = fecha + pd.Timedelta(days=int(rng.integers(90, 900))) if cancelada else pd.NaT
            if pd.notna(fecha_fin) and fecha_fin > FECHA_CORTE:
                cancelada, fecha_fin = False, pd.NaT
            canal = c.canal_preferido if rng.random() < 0.7 else rng.choice(CANALES)
            prima = producto.prima_base_cop * (1 + max(c.edad - 40, 0) / 80) * rng.uniform(0.85, 1.25)
            filas.append(
                {
                    "cliente_id": c.cliente_id,
                    "product_id": pid,
                    "fecha_inicio": fecha.normalize(),
                    "estado": "cancelada" if cancelada else "vigente",
                    "fecha_fin": fecha_fin,
                    "canal_venta": canal,
                    "prima_mensual_cop": int(round(prima, -3)),
                }
            )
            fecha = fecha + pd.Timedelta(days=int(rng.exponential(260)) + 30)
    polizas = pd.DataFrame(filas)
    polizas.insert(0, "poliza_id", [f"PZ{i:07d}" for i in range(1, len(polizas) + 1)])
    return polizas


def generar_siniestros(polizas: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Reclamaciones por póliza según la frecuencia anual de su línea."""
    lineas = polizas["product_id"].map(lambda p: POR_ID[p].linea)
    fin = polizas["fecha_fin"].fillna(FECHA_CORTE)
    anios = ((fin - polizas["fecha_inicio"]).dt.days / 365.25).clip(lower=0)
    tasas = lineas.map(TASA_SINIESTROS).to_numpy() * anios.to_numpy()
    cantidades = rng.poisson(tasas)
    filas: list[dict[str, object]] = []
    for idx in np.flatnonzero(cantidades):
        poliza = polizas.iloc[idx]
        dias = max((fin.iloc[idx] - poliza.fecha_inicio).days, 1)
        for _ in range(cantidades[idx]):
            filas.append(
                {
                    "poliza_id": poliza.poliza_id,
                    "fecha": (
                        poliza.fecha_inicio + pd.Timedelta(days=int(rng.integers(0, dias)))
                    ).normalize(),
                    "monto_cop": int(round(rng.lognormal(14.2, 0.9), -3)),
                    "estado": rng.choice(("pagado", "objetado", "en_tramite"), p=(0.78, 0.12, 0.10)),
                }
            )
    siniestros = pd.DataFrame(filas, columns=["poliza_id", "fecha", "monto_cop", "estado"])
    siniestros.insert(0, "siniestro_id", [f"S{i:07d}" for i in range(1, len(siniestros) + 1)])
    return siniestros


def generar_dataset(n_clientes: int = 20_000, semilla: int = 42) -> DatasetSintetico:
    """Genera la cartera completa; misma semilla ⇒ mismas tablas."""
    rng = np.random.default_rng(semilla)
    clientes = generar_clientes(n_clientes, rng)
    polizas = generar_polizas(clientes, rng)
    siniestros = generar_siniestros(polizas, rng)
    return DatasetSintetico(clientes, generar_productos(), polizas, siniestros)

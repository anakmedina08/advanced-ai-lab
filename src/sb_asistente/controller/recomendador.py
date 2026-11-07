"""Controlador del recomendador: generar y validar datos, comparar líneas base y recomendar.

Las vistas (CLI, API y Streamlit) llaman a estas funciones; nunca construyen modelos ni leen
CSV por su cuenta (MVC).
"""

from functools import lru_cache
from pathlib import Path

import pandas as pd

from sb_asistente.config import RECO_DIR, RECO_K, RECO_N_CLIENTES, RECO_SEGMENTO, RECO_SEMILLA
from sb_asistente.model.recomendador.catalogo import POR_ID
from sb_asistente.model.recomendador.contrato import ESQUEMAS, validar_dataset
from sb_asistente.model.recomendador.metricas import evaluar
from sb_asistente.model.recomendador.particion import leave_last_out
from sb_asistente.model.recomendador.popularidad import RecomendadorPopularidad, RecomendadorSegmento
from sb_asistente.model.recomendador.sintetico import generar_dataset

RAZON_SEGMENTO = "Muy contratado por clientes con su mismo perfil (vehículo, vivienda, mascota, crédito)."
FECHAS: dict[str, list[str]] = {
    "clientes": ["fecha_vinculacion"],
    "polizas": ["fecha_inicio", "fecha_fin"],
    "siniestros": ["fecha"],
}


def generar(
    n_clientes: int = RECO_N_CLIENTES, semilla: int = RECO_SEMILLA, salida: Path = RECO_DIR
) -> dict[str, int]:
    """Genera el dataset sintético, lo valida contra el contrato y lo guarda en CSV.

    Returns:
        Filas escritas por tabla.

    Raises:
        ValueError: si el dataset generado no cumple el contrato de datos.

    """
    dataset = generar_dataset(n_clientes, semilla)
    errores = validar_dataset(dataset.tablas())
    if errores:
        raise ValueError("\n".join(errores))
    salida.mkdir(parents=True, exist_ok=True)
    filas: dict[str, int] = {}
    for nombre, df in dataset.tablas().items():
        df.to_csv(salida / f"{nombre}.csv", index=False)
        filas[nombre] = len(df)
    return filas


def leer_tablas(directorio: Path = RECO_DIR) -> dict[str, pd.DataFrame]:
    """Lee las tablas en CSV con sus fechas tipadas."""
    tablas: dict[str, pd.DataFrame] = {}
    for nombre in ESQUEMAS:
        ruta = directorio / f"{nombre}.csv"
        if not ruta.is_file():
            raise FileNotFoundError(f"No existe {ruta}. Ejecute: uv run sb reco generar")
        tablas[nombre] = pd.read_csv(ruta, parse_dates=FECHAS.get(nombre, []))
    return tablas


def validar(directorio: Path = RECO_DIR) -> list[str]:
    """Errores del contrato de datos (lista vacía si todo está bien)."""
    return validar_dataset(leer_tablas(directorio))


def comparar_baselines(tablas: dict[str, pd.DataFrame], k: int = RECO_K) -> dict[str, dict]:
    """Recall@k y NDCG@k de las líneas base con partición leave-last-out."""
    entrenamiento, objetivos = leave_last_out(tablas["polizas"])
    modelos = {
        "popularidad": RecomendadorPopularidad(),
        "segmento": RecomendadorSegmento(tablas["clientes"], RECO_SEGMENTO),
    }
    resultados: dict[str, dict] = {}
    for nombre, modelo in modelos.items():
        modelo.fit(entrenamiento)
        recomendaciones = {c: modelo.recomendar(c, k) for c in objetivos}
        resultados[nombre] = evaluar(recomendaciones, objetivos, k)
    return resultados


@lru_cache(maxsize=4)
def _modelo_segmento(directorio: Path) -> RecomendadorSegmento:
    """Entrena una sola vez la línea base por segmento (caché por carpeta)."""
    tablas = leer_tablas(directorio)
    return RecomendadorSegmento(tablas["clientes"], RECO_SEGMENTO).fit(tablas["polizas"])


def recomendar(cliente_id: str, k: int = RECO_K, directorio: Path = RECO_DIR) -> list[dict[str, str]]:
    """Top-k de productos para un cliente con nombre y razón legible.

    Mientras el ranking e5 + LightGBM (M3) no esté listo, responde la línea base por segmento.
    """
    if not 1 <= k <= 10:
        raise ValueError("k debe estar entre 1 y 10.")
    modelo = _modelo_segmento(directorio)
    if not modelo.conoce(cliente_id):
        raise KeyError(f"Cliente desconocido: {cliente_id}")
    return [
        {
            "product_id": pid,
            "nombre": POR_ID[pid].nombre,
            "linea": POR_ID[pid].linea,
            "razon": RAZON_SEGMENTO,
        }
        for pid in modelo.recomendar(cliente_id, k)
    ]

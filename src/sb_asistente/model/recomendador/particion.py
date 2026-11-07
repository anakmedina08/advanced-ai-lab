"""Partición temporal *leave-last-out*: se retiene la póliza más reciente de cada cliente."""

import pandas as pd


def leave_last_out(polizas: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """Separa entrenamiento y objetivo.

    Para cada cliente con dos o más pólizas, la última por ``fecha_inicio`` se convierte en el
    producto a predecir; las anteriores quedan en entrenamiento. Los clientes con una sola
    póliza aportan solo a entrenamiento. Así el modelo nunca ve el futuro del cliente.
    """
    ordenadas = polizas.sort_values(["cliente_id", "fecha_inicio", "poliza_id"])
    conteo = ordenadas.groupby("cliente_id")["poliza_id"].transform("size")
    es_ultima = ~ordenadas.duplicated("cliente_id", keep="last")
    retener = es_ultima & (conteo >= 2)
    objetivos = dict(
        zip(ordenadas.loc[retener, "cliente_id"], ordenadas.loc[retener, "product_id"], strict=True)
    )
    return ordenadas.loc[~retener].reset_index(drop=True), objetivos

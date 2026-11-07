"""Línea base: recomendar los productos más vendidos que el cliente aún no tiene.

Es el umbral mínimo que el modelo propuesto (e5 + ranking) debe superar en el M3.
"""

import pandas as pd


class RecomendadorPopularidad:
    """Ordena el catálogo por número de pólizas en entrenamiento."""

    def __init__(self) -> None:
        self.ranking: list[str] = []
        self._poseidos: dict[str, set[str]] = {}

    def fit(self, polizas: pd.DataFrame) -> "RecomendadorPopularidad":
        """Aprende la popularidad global y qué tiene cada cliente."""
        if polizas.empty:
            raise ValueError("No hay pólizas para entrenar.")
        conteo = polizas.groupby("product_id")["poliza_id"].count()
        self.ranking = conteo.sort_values(ascending=False, kind="stable").index.tolist()
        self._poseidos = polizas.groupby("cliente_id")["product_id"].agg(set).to_dict()
        return self

    def recomendar(self, cliente_id: str, k: int = 5) -> list[str]:
        """Top-k de productos populares excluyendo los que el cliente ya tiene."""
        if not self.ranking:
            raise RuntimeError("Llame a fit() antes de recomendar.")
        poseidos = self._poseidos.get(cliente_id, set())
        return [p for p in self.ranking if p not in poseidos][:k]


class RecomendadorSegmento(RecomendadorPopularidad):
    """Popularidad dentro del segmento del cliente (p. ej. vehículo × vivienda × mascota).

    Muestra cuánto aporta personalizar con reglas simples; si el segmento no tiene datos,
    recurre a la popularidad global.
    """

    def __init__(self, clientes: pd.DataFrame, columnas: tuple[str, ...]) -> None:
        super().__init__()
        faltan = [c for c in columnas if c not in clientes.columns]
        if faltan:
            raise KeyError(f"Columnas de segmento inexistentes: {faltan}")
        self._segmento = clientes.set_index("cliente_id")[list(columnas)].apply(tuple, axis=1).to_dict()
        self._ranking_segmento: dict[tuple, list[str]] = {}

    def fit(self, polizas: pd.DataFrame) -> "RecomendadorSegmento":
        """Aprende la popularidad global y la de cada segmento."""
        super().fit(polizas)
        seg = polizas["cliente_id"].map(self._segmento)
        conteo = polizas.assign(_seg=seg).groupby(["_seg", "product_id"])["poliza_id"].count()
        for segmento, serie in conteo.groupby(level=0):
            orden = serie.droplevel(0).sort_values(ascending=False, kind="stable").index.tolist()
            self._ranking_segmento[segmento] = orden + [p for p in self.ranking if p not in orden]
        return self

    def conoce(self, cliente_id: str) -> bool:
        """Indica si el cliente existe en la tabla de clientes usada al construir el modelo."""
        return cliente_id in self._segmento

    def recomendar(self, cliente_id: str, k: int = 5) -> list[str]:
        """Top-k del segmento excluyendo lo que el cliente ya tiene."""
        if not self.ranking:
            raise RuntimeError("Llame a fit() antes de recomendar.")
        ranking = self._ranking_segmento.get(self._segmento.get(cliente_id), self.ranking)
        poseidos = self._poseidos.get(cliente_id, set())
        return [p for p in ranking if p not in poseidos][:k]

"""Bitácora de experimentos: cada corrida con sus parámetros, métricas y archivos (MLflow, ADR-022).

Una ``Corrida`` describe un experimento (p. ej., «prompt v3 en modo rag con Claude») sin depender
de MLflow. ``BitacoraMlflow`` la guarda en la base local; ``BitacoraNula`` no hace nada y se usa
cuando el extra ``mlflow`` no está instalado o ``SB_MLFLOW=0`` (CI, pruebas, Docker).
"""

import re
import subprocess
from dataclasses import dataclass, field
from importlib.util import find_spec
from pathlib import Path
from typing import Protocol

from sb_asistente.config import (
    MLFLOW_ACTIVO,
    MLFLOW_ARTIFACTS,
    MLFLOW_TRACKING_URI,
    PROJECT_ROOT,
)

_NO_PERMITIDO = re.compile(r"[^\w\-. /]")


@dataclass(frozen=True, slots=True)
class Corrida:
    """Un experimento: qué se probó (parámetros), cómo salió (métricas) y sus archivos."""

    experimento: str
    nombre: str
    parametros: dict[str, object] = field(default_factory=dict)
    metricas: dict[str, float] = field(default_factory=dict)
    artefactos: tuple[Path, ...] = ()
    etiquetas: dict[str, str] = field(default_factory=dict)


class Bitacora(Protocol):
    """Contrato de la bitácora (MLflow real o un doble en las pruebas)."""

    def registrar(self, corrida: Corrida) -> str | None:  # noqa: D102
        ...

    def existe(self, experimento: str, etiqueta: str, valor: str) -> bool:  # noqa: D102
        ...


def nombre_metrica(nombre: str) -> str:
    """Nombre válido para MLflow: ``recall@5`` → ``recall_at_5`` (MLflow rechaza la «@»)."""
    return _NO_PERMITIDO.sub("_", nombre.replace("@", "_at_"))


def commit_actual(raiz: Path = PROJECT_ROOT) -> str | None:
    """Commit de git del código que produjo la corrida (trazabilidad)."""
    try:
        salida = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=raiz, capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return salida.stdout.strip() or None


class BitacoraNula:
    """No registra nada (MLflow sin instalar o apagado con ``SB_MLFLOW=0``)."""

    def registrar(self, corrida: Corrida) -> str | None:
        """No hace nada."""
        return None

    def existe(self, experimento: str, etiqueta: str, valor: str) -> bool:
        """Nunca hay corridas."""
        return False


class BitacoraMlflow:
    """Guarda las corridas en MLflow (base SQLite local y carpeta de artefactos en ``data/``)."""

    def __init__(self, uri: str = MLFLOW_TRACKING_URI, artefactos: Path = MLFLOW_ARTIFACTS) -> None:
        """Recibe dónde guardar (inyectable para usar una base temporal en las pruebas)."""
        import mlflow

        self.mlflow = mlflow
        self.uri = uri
        self.artefactos = artefactos
        Path(artefactos).mkdir(parents=True, exist_ok=True)

    def _experimento(self, nombre: str) -> str:
        self.mlflow.set_tracking_uri(self.uri)
        experimento = self.mlflow.get_experiment_by_name(nombre)
        if experimento is not None:
            return experimento.experiment_id
        return self.mlflow.create_experiment(
            nombre, artifact_location=(Path(self.artefactos) / nombre).as_uri()
        )

    def registrar(self, corrida: Corrida) -> str | None:
        """Crea la corrida con parámetros, métricas, etiquetas (incluido el commit) y artefactos."""
        etiquetas = {"commit": commit_actual() or "desconocido"} | corrida.etiquetas
        with self.mlflow.start_run(
            experiment_id=self._experimento(corrida.experimento), run_name=corrida.nombre, tags=etiquetas
        ) as run:
            if corrida.parametros:
                self.mlflow.log_params({k: str(v) for k, v in corrida.parametros.items()})
            if corrida.metricas:
                self.mlflow.log_metrics({nombre_metrica(k): float(v) for k, v in corrida.metricas.items()})
            for archivo in corrida.artefactos:
                if Path(archivo).is_file():
                    self.mlflow.log_artifact(str(archivo))
        return run.info.run_id

    def existe(self, experimento: str, etiqueta: str, valor: str) -> bool:
        """Indica si ya hay una corrida con esa etiqueta (evita importar dos veces lo mismo)."""
        self.mlflow.set_tracking_uri(self.uri)
        exp = self.mlflow.get_experiment_by_name(experimento)
        if exp is None:
            return False
        filtro = f"tags.{etiqueta} = '{valor.replace(chr(39), '')}'"
        return not self.mlflow.search_runs([exp.experiment_id], filter_string=filtro, max_results=1).empty


def disponible() -> bool:
    """Indica si el extra ``mlflow`` está instalado."""
    return find_spec("mlflow") is not None


def bitacora_por_defecto() -> Bitacora:
    """MLflow si está instalado y activo; si no, una bitácora que no hace nada."""
    return BitacoraMlflow() if MLFLOW_ACTIVO and disponible() else BitacoraNula()

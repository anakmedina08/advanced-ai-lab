"""Sube el banco de evaluación (evaluacion/preguntas.yaml) como dataset de LangSmith.

Con el dataset en LangSmith se comparan versiones de prompt, modelos o el agente contra las
mismas 24 preguntas desde la interfaz web. Requiere ``LANGSMITH_API_KEY`` en ``.env``.

    uv run python scripts/langsmith_dataset.py              # crea o actualiza «sb-asistente-banco»
    uv run python scripts/langsmith_dataset.py --dry-run    # muestra qué subiría, sin red
"""

import argparse
import sys
from pathlib import Path

from sb_asistente.config import EVAL_QUESTIONS  # carga .env (LANGSMITH_*)
from sb_asistente.model.evaluation import load_questions

NOMBRE = "sb-asistente-banco"


def ejemplos(path: Path = EVAL_QUESTIONS) -> list[dict[str, dict]]:
    """Preguntas del banco en el formato inputs/outputs/metadata de LangSmith."""
    return [
        {
            "inputs": {"pregunta": q.pregunta},
            "outputs": {"palabras_clave": list(q.palabras_clave), "fuera_de_alcance": q.fuera_de_alcance},
            "metadata": {"id": q.id, "categoria": q.categoria},
        }
        for q in load_questions(path)
    ]


def main(argv: list[str] | None = None) -> int:
    """Crea el dataset (si no existe) y agrega los ejemplos que falten."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    datos = ejemplos()
    if args.dry_run:
        print(f"{len(datos)} ejemplos para el dataset «{NOMBRE}»")
        return 0
    from langsmith import Client

    client = Client()
    if client.has_dataset(dataset_name=NOMBRE):
        dataset = client.read_dataset(dataset_name=NOMBRE)
        existentes = {e.metadata.get("id") for e in client.list_examples(dataset_id=dataset.id)}
    else:
        dataset = client.create_dataset(
            NOMBRE, description="Banco de evaluación del Asistente Seguros Bolívar"
        )
        existentes = set()
    nuevos = [d for d in datos if d["metadata"]["id"] not in existentes]
    if nuevos:
        client.create_examples(dataset_id=dataset.id, examples=nuevos)
    print(f"Dataset «{NOMBRE}»: {len(nuevos)} ejemplos nuevos, {len(existentes)} ya existían.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

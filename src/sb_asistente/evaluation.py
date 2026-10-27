"""Evaluación de las preguntas de prueba (mínimo 20, según la actividad).

Métricas automáticas por respuesta:
- ``keyword_hit``: proporción de palabras clave esperadas presentes en la respuesta.
- ``cites_source``: incluye URL de segurosbolivar.com.
- ``fallback_ok``: en preguntas fuera de alcance, el modelo se negó (debe negarse).
- ``latency_s``.
Además deja columnas vacías ``calificacion_manual`` (1-5) y ``observaciones`` para el equipo.
"""

import csv
import re
import unicodedata
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

import yaml

from sb_asistente.llm.service import Answer


@dataclass(slots=True)
class EvalQuestion:
    """Pregunta del banco de pruebas."""

    id: str
    categoria: str
    pregunta: str
    palabras_clave: list[str]
    fuera_de_alcance: bool = False


def load_questions(path: Path) -> list[EvalQuestion]:
    """Carga el banco de preguntas desde YAML y valida que haya al menos 20 únicas."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    questions = [
        EvalQuestion(
            id=str(q["id"]),
            categoria=q["categoria"],
            pregunta=q["pregunta"],
            palabras_clave=list(q.get("palabras_clave") or []),
            fuera_de_alcance=bool(q.get("fuera_de_alcance", False)),
        )
        for q in data["preguntas"]
    ]
    if len({q.id for q in questions}) != len(questions):
        raise ValueError("Hay ids de pregunta repetidos.")
    if len(questions) < 20:
        raise ValueError(f"La actividad exige al menos 20 preguntas; hay {len(questions)}.")
    return questions


def _fold(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))


def keyword_hit(answer: str, keywords: Iterable[str]) -> float | None:
    """Proporción de palabras clave presentes (sin tildes ni mayúsculas); None si no hay."""
    kws = list(keywords)
    if not kws:
        return None
    folded = _fold(answer)
    return sum(1 for k in kws if _fold(k) in folded) / len(kws)


def score(question: EvalQuestion, answer: Answer) -> dict[str, object]:
    """Calcula las métricas automáticas de una respuesta."""
    return {
        "id": question.id,
        "categoria": question.categoria,
        "pregunta": question.pregunta,
        "prompt_version": answer.prompt_version,
        "respuesta": answer.text,
        "keyword_hit": keyword_hit(answer.text, question.palabras_clave),
        "cita_fuente": answer.cites_source,
        "fallback": answer.is_fallback,
        "fallback_ok": (answer.is_fallback == question.fuera_de_alcance),
        "latencia_s": round(answer.latency_s, 2),
        "calificacion_manual": "",
        "observaciones": "",
    }


def run_eval(
    questions: Iterable[EvalQuestion],
    ask: Callable[[str], Answer],
    out_csv: Path,
    on_progress: Callable[[int, int, dict[str, object]], None] | None = None,
) -> dict[str, float]:
    """Ejecuta el banco, escribe el CSV y devuelve métricas agregadas.

    ``on_progress(i, total, fila)`` se llama después de cada pregunta (avance en consola).
    """
    pending = list(questions)
    rows: list[dict[str, object]] = []
    for i, question in enumerate(pending, start=1):
        row = score(question, ask(question.pregunta))
        rows.append(row)
        if on_progress:
            on_progress(i, len(pending), row)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return aggregate(rows)


def aggregate(rows: list[dict[str, object]]) -> dict[str, float]:
    """Métricas agregadas de un conjunto de respuestas calificadas."""
    if not rows:
        raise ValueError("No hay filas para agregar.")
    hits = [r["keyword_hit"] for r in rows if r["keyword_hit"] is not None]
    return {
        "preguntas": len(rows),
        "keyword_hit_promedio": round(sum(hits) / len(hits), 3) if hits else 0.0,
        "tasa_cita_fuente": round(sum(bool(r["cita_fuente"]) for r in rows) / len(rows), 3),
        "tasa_fallback_correcto": round(sum(bool(r["fallback_ok"]) for r in rows) / len(rows), 3),
        "latencia_promedio_s": round(sum(float(r["latencia_s"]) for r in rows) / len(rows), 2),
    }


RESULT_FILE = re.compile(r"^resultados_(?P<modelo>[a-z0-9]+)_(?P<version>v\d+)\.csv$")


def read_results(path: Path) -> list[dict[str, object]]:
    """Lee un CSV de ``sb eval`` devolviendo booleanos y números con su tipo."""
    rows: list[dict[str, object]] = []
    with path.open(encoding="utf-8", newline="") as fh:
        for raw in csv.DictReader(fh):
            row: dict[str, object] = dict(raw)
            row["keyword_hit"] = float(raw["keyword_hit"]) if raw["keyword_hit"] else None
            for key in ("cita_fuente", "fallback", "fallback_ok"):
                row[key] = raw[key] == "True"
            row["latencia_s"] = float(raw["latencia_s"])
            rows.append(row)
    return rows


def summarize_results(results_dir: Path) -> list[dict[str, object]]:
    """Una fila de métricas por archivo ``resultados_<modelo>_<version>.csv`` (para la pestaña Evaluación)."""
    summary: list[dict[str, object]] = []
    for path in sorted(results_dir.glob("resultados_*.csv")):
        match = RESULT_FILE.match(path.name)
        if not match:
            continue
        rows = read_results(path)
        if rows:
            summary.append({"modelo": match["modelo"], "version": match["version"], **aggregate(rows)})
    return summary

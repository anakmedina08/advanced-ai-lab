"""Evaluación de la recuperación con el banco de preguntas (hit@k).

Una pregunta acierta si los ``k`` fragmentos recuperados contienen TODAS sus palabras clave
(criterio estricto: el modelo solo puede responder bien si el dato le llega). Las preguntas
fuera de alcance no cuentan: para ellas no hay fragmento correcto.
"""

import unicodedata
from dataclasses import dataclass

from sb_asistente.model.evaluation import EvalQuestion
from sb_asistente.model.rag.hibrido import RecuperadorHibrido


def _norm(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


@dataclass(frozen=True, slots=True)
class ResultadoHit:
    """hit@k sobre el banco."""

    k: int
    aciertos: int
    total: int
    fallos: tuple[str, ...]

    @property
    def tasa(self) -> float:
        """Proporción de aciertos."""
        return self.aciertos / self.total if self.total else 0.0


def hit_at_k(recuperador: RecuperadorHibrido, preguntas: list[EvalQuestion], k: int) -> ResultadoHit:
    """Cuenta en cuántas preguntas en alcance los fragmentos traen todas las palabras clave."""
    en_alcance = [q for q in preguntas if not q.fuera_de_alcance]
    fallos = []
    for q in en_alcance:
        texto = _norm(" ".join(f"{f.titulo} {f.texto}" for f in recuperador.buscar(q.pregunta, k=k)))
        if not all(_norm(p) in texto for p in q.palabras_clave):
            fallos.append(q.id)
    return ResultadoHit(k, len(en_alcance) - len(fallos), len(en_alcance), tuple(fallos))

"""Compara la recuperación de los cuatro métodos con la misma métrica (hit@k) y el mismo banco.

Uso (requiere los índices: ``uv run sb rag indexar`` para Chroma y ``uv run sb index`` para Qdrant):

    uv run python scripts/comparar_recuperacion.py -k 4 6 10

Métodos:
- **BM25**: solo la parte léxica del recuperador híbrido de Daniel (ADR-016).
- **Híbrido Chroma**: BM25 + vectores (nomic-embed-text) combinados con RRF (ADR-016).
- **Qdrant denso**: solo vectores (embeddinggemma), el modo «rag» (ADR-018).
- **Por palabras**: la búsqueda del modo «reducido» (ADR-006).

hit@k (``model/rag/evaluacion.hit_at_k``): una pregunta acierta si los k fragmentos traen TODAS sus
palabras clave. Las preguntas fuera de alcance no cuentan.
"""

import argparse
from collections.abc import Callable

from langchain_core.documents import Document

from sb_asistente.config import EVAL_QUESTIONS
from sb_asistente.controller import assistant
from sb_asistente.controller.agente import recuperador_por_defecto
from sb_asistente.model.evaluation import load_questions
from sb_asistente.model.llm import keyword_search, knowledge
from sb_asistente.model.rag.evaluacion import ResultadoHit, hit_at_k
from sb_asistente.model.rag.fuentes import fragmentos_rag
from sb_asistente.model.rag.hibrido import Fragmento, RecuperadorHibrido


def _fragmento(titulo: str, url: str, texto: str) -> Fragmento:
    return Fragmento(chunk_id="", titulo=titulo, url=url, seccion="", texto=texto, puntaje=0.0, origen=())


def _canales() -> Fragmento:
    """Los modos «rag» y «reducido» anteponen SIEMPRE el bloque de canales; se incluye para ser justos."""
    return _fragmento("Canales de atención", "https://www.segurosbolivar.com/", knowledge.load_channels())


class RecuperadorQdrant:
    """Adapta la búsqueda densa del modo «rag» a la interfaz ``buscar(consulta, k)``."""

    def __init__(self) -> None:
        """Abre el índice Qdrant de los chunks (lo crea la primera vez)."""
        self._buscar_k: Callable[[str, int], list[Document]] = lambda q, k: assistant.embedding_search(k=k)(q)
        self._buscar_k("prueba", 1)  # abre el índice una vez antes de medir

    def buscar(self, consulta: str, k: int) -> list[Fragmento]:  # noqa: D102
        return [_canales()] + [
            _fragmento(d.metadata.get("title", ""), d.metadata.get("url", ""), d.page_content)
            for d in self._buscar_k(consulta, k)
        ]


class RecuperadorPalabras:
    """Adapta la búsqueda por palabras del modo «reducido» (top-k por coincidencias)."""

    def __init__(self) -> None:
        """Carga los fragmentos de Gold."""
        self.chunks = knowledge.load_chunks()

    def buscar(self, consulta: str, k: int) -> list[Fragmento]:  # noqa: D102
        palabras = keyword_search.normalize_words(consulta)
        puntajes = sorted(
            ((keyword_search.score(palabras, c), i, c) for i, c in enumerate(self.chunks)),
            key=lambda t: (-t[0], t[1]),
        )
        return [_canales()] + [
            _fragmento(str(c["title"]), str(c["url"]), str(c["text"])) for p, _, c in puntajes[:k] if p > 0
        ]


def main() -> None:
    """Imprime una tabla Markdown de hit@k por método y las preguntas que falla cada uno."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-k", type=int, nargs="+", default=[4, 6, 10])
    args = parser.parse_args()
    preguntas = load_questions(EVAL_QUESTIONS)
    hibrido, modo = recuperador_por_defecto()
    metodos = {
        "BM25 (léxico)": RecuperadorHibrido(fragmentos_rag()),
        f"Híbrido Chroma ({modo})": hibrido,
        "Qdrant denso (modo rag)": RecuperadorQdrant(),
        "Por palabras (modo reducido)": RecuperadorPalabras(),
    }
    resultados: dict[str, list[ResultadoHit]] = {
        nombre: [hit_at_k(r, preguntas, k) for k in args.k] for nombre, r in metodos.items()
    }
    total = next(iter(resultados.values()))[0].total
    print(f"Preguntas en alcance: {total}\n")
    print("| Método | " + " | ".join(f"hit@{k}" for k in args.k) + " |")
    print("|---|" + "---|" * len(args.k))
    for nombre, filas in resultados.items():
        print(f"| {nombre} | " + " | ".join(f"{r.tasa:.0%} ({r.aciertos}/{r.total})" for r in filas) + " |")
    print()
    for nombre, filas in resultados.items():
        print(f"- {nombre} · falla en hit@{filas[-1].k}: {', '.join(filas[-1].fallos) or 'ninguna'}")


if __name__ == "__main__":
    main()

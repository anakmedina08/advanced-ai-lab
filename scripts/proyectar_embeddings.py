"""Mapa t-SNE de los embeddings del corpus y del banco de evaluación (SPEC-084, ítem 2.3).

Lee los vectores del índice Qdrant local, embebe las preguntas con el mismo proveedor del índice,
marca cada pregunta como acierto o fallo de la búsqueda densa (top-10 por coseno con un fragmento
relevante según sus palabras clave, la regla de SPEC-036) y proyecta todo junto a 2D.

    uv run python scripts/proyectar_embeddings.py              # t-SNE
    uv run python scripts/proyectar_embeddings.py --metodo pca

Salidas: docs/figuras/tsne-embeddings.png y docs/figuras/tsne-embeddings.json; si MLflow está
disponible, una corrida en el experimento «recuperacion».
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np

from sb_asistente.config import EMBEDDING_MODEL, EVAL_QUESTIONS, PROJECT_ROOT, QDRANT_COLLECTION, QDRANT_DIR
from sb_asistente.model.evaluation import load_questions
from sb_asistente.model.llm.vector_store import build_embeddings  # la misma fábrica que construyó el índice
from sb_asistente.model.rag.evaluacion import es_relevante
from sb_asistente.model.rag.proyeccion import proyectar, separacion, vecinos

SALIDA = PROJECT_ROOT / "docs" / "figuras"
K = 10


def _leer_indice() -> tuple[np.ndarray, list[str], list[str]]:
    """Vectores, sección y texto de cada fragmento del índice Qdrant local."""
    from qdrant_client import QdrantClient

    cliente = QdrantClient(path=str(QDRANT_DIR))
    try:
        nombre = next(
            c.name for c in cliente.get_collections().collections if c.name.startswith(QDRANT_COLLECTION)
        )
        puntos, _ = cliente.scroll(nombre, limit=100_000, with_vectors=True, with_payload=True)
    finally:
        cliente.close()
    vectores = np.array([p.vector for p in puntos], dtype=np.float64)
    secciones = [str(p.payload.get("metadata", {}).get("section", "otros")) for p in puntos]
    textos = [str(p.payload.get("page_content", "")) for p in puntos]
    return vectores, secciones, textos


def _dibujar(plano: np.ndarray, secciones: list[str], preguntas: list[tuple[str, bool]], ruta: Path) -> None:
    """Fragmentos coloreados por sección; preguntas como estrella (acierto) o X (fallo)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n = len(secciones)
    fig, eje = plt.subplots(figsize=(11, 8), dpi=130)
    paleta = plt.get_cmap("tab10")
    for i, (seccion, cuenta) in enumerate(Counter(secciones).most_common()):
        idx = [j for j, s in enumerate(secciones) if s == seccion]
        eje.scatter(
            plano[idx, 0], plano[idx, 1], s=14, alpha=0.6, color=paleta(i % 10), label=f"{seccion} ({cuenta})"
        )
    for j, (pid, acierto) in enumerate(preguntas):
        x, y = plano[n + j]
        eje.scatter(
            x,
            y,
            s=150 if acierto else 110,
            marker="*" if acierto else "X",
            color="#1a7f37" if acierto else "#cf222e",
            edgecolors="black",
            linewidths=0.6,
            zorder=5,
        )
        eje.annotate(pid, (x, y), textcoords="offset points", xytext=(5, 5), fontsize=8, zorder=6)
    eje.scatter(
        [], [], marker="*", s=150, color="#1a7f37", edgecolors="black", label="pregunta: acierto top-10"
    )
    eje.scatter(
        [], [], marker="X", s=110, color="#cf222e", edgecolors="black", label="pregunta: fallo top-10"
    )
    eje.set_title("t-SNE de los embeddings del corpus y del banco de evaluación")
    eje.set_xticks([])
    eje.set_yticks([])
    eje.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def main() -> None:
    """Calcula el mapa, imprime el diagnóstico y lo registra."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--metodo", choices=["tsne", "pca"], default="tsne")
    parser.add_argument("--semilla", type=int, default=42)
    args = parser.parse_args()

    vectores, secciones, textos = _leer_indice()
    preguntas = [q for q in load_questions(EVAL_QUESTIONS) if not q.fuera_de_alcance]
    consultas = np.array(
        build_embeddings().embed_documents([q.pregunta for q in preguntas]), dtype=np.float64
    )

    resultados: list[tuple[str, bool]] = []
    for pregunta, consulta in zip(preguntas, consultas, strict=True):
        top = vecinos(consulta, vectores, K)
        resultados.append((pregunta.id, any(es_relevante(textos[i], pregunta.palabras_clave) for i in top)))

    plano = proyectar(np.vstack([vectores, consultas]), metodo=args.metodo, semilla=args.semilla)
    SALIDA.mkdir(parents=True, exist_ok=True)
    png = SALIDA / f"{args.metodo}-embeddings.png"
    _dibujar(plano, secciones, resultados, png)

    cuentas = Counter(secciones)
    mayor, n_mayor = cuentas.most_common(1)[0]
    sil = separacion(vectores, secciones)
    aciertos = sum(ok for _, ok in resultados)
    resumen = {
        "metodo": args.metodo,
        "modelo_embeddings": EMBEDDING_MODEL,
        "fragmentos": len(secciones),
        "preguntas": len(resultados),
        "secciones": dict(cuentas.most_common()),
        "seccion_mayor": mayor,
        "proporcion_seccion_mayor": round(n_mayor / len(secciones), 3),
        "silhouette_secciones_coseno": None if sil is None else round(sil, 3),
        "hit@10_denso": round(aciertos / len(resultados), 3),
        "fallos_top10": [pid for pid, ok in resultados if not ok],
    }
    json_path = SALIDA / f"{args.metodo}-embeddings.json"
    json_path.write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    print(f"\nMapa: {png.relative_to(PROJECT_ROOT)}")

    try:
        from sb_asistente.model.experimentos import Corrida, bitacora_por_defecto

        run = bitacora_por_defecto().registrar(
            Corrida(
                experimento="recuperacion",
                nombre=f"proyeccion-{args.metodo}",
                parametros={
                    "metodo": args.metodo,
                    "semilla": args.semilla,
                    "k": K,
                    "modelo": EMBEDDING_MODEL,
                },
                metricas={
                    "silhouette_secciones": sil if sil is not None else 0.0,
                    "proporcion_seccion_mayor": n_mayor / len(secciones),
                    "hit@10_denso": aciertos / len(resultados),
                },
                artefactos=(png, json_path),
                etiquetas={"spec": "SPEC-084"},
            )
        )
        print(f"Registrado en MLflow (experimento «recuperacion»): {run}")
    except Exception as exc:  # noqa: BLE001 - MLflow es opcional para el mapa
        print(f"MLflow no disponible ({exc}); el mapa quedó en docs/figuras.")


if __name__ == "__main__":
    main()

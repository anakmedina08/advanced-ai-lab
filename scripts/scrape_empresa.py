"""Pipeline completo de scraping de segurosbolivar.com: descubrir → extraer → limpiar → Gold.

Uso:
    uv run python scripts/scrape_empresa.py              # todo (~4 min por la pausa de cortesía)
    uv run python scripts/scrape_empresa.py --solo-proceso   # Bronze → Silver → Gold, sin red (segundos)
"""

import argparse
import time

from sb_asistente import pipeline


def main() -> None:
    """Ejecuta las etapas e imprime las métricas de cada una."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--solo-proceso", action="store_true", help="No va a la web: reprocesa Bronze")
    args = parser.parse_args()
    inicio = time.perf_counter()
    if not args.solo_proceso:
        session = pipeline.new_session()
        plan = pipeline.discover(session)
        seleccionadas = len(plan["seleccionadas"])
        print(f"[1/3] Descubrir: {plan['total_sitemap']} URLs en el sitemap, {seleccionadas} en alcance")
        print(f"[2/3] Extraer a Bronze: {pipeline.scrape(session)}")
    resumen = pipeline.process()
    print(f"[3/3] Limpiar, deduplicar y enriquecer: {resumen['documentos']} documentos en Gold")
    for etapa in pipeline.stage_report():
        metricas = " · ".join(f"{k.strip(' ·')}: {v}" for k, v in etapa["metricas"].items())
        print(f"  {etapa['etapa']:<14} {metricas}")
    duracion = time.perf_counter() - inicio
    print(f"Listo en {duracion:.1f} s → data/gold/ (corpus.jsonl, pages/*.md, chunks.jsonl)")


if __name__ == "__main__":
    main()

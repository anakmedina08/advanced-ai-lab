"""CLI: ``sb discover | scrape | process | stats | ask | summary | faq | eval | reco | api``."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from sb_asistente.config import (
    GOLD_DIR,
    LLM_PROVIDER,
    PROVIDERS,
    RECO_DIR,
    RECO_K,
    RECO_N_CLIENTES,
    RECO_SEMILLA,
)
from sb_asistente.controller import assistant, pipeline, recomendador

VERSION_ARG = {"default": assistant.DEFAULT_QA_VERSION, "choices": list(assistant.QA_VERSIONS)}


def build_parser() -> argparse.ArgumentParser:
    """Construye el parser de subcomandos."""
    parser = argparse.ArgumentParser(prog="sb", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("discover", help="robots.txt + sitemap → plan de captura")
    scrape = sub.add_parser("scrape", help="Descarga a Bronze (reanudable)")
    scrape.add_argument("--force", action="store_true", help="Volver a descargar todo")
    sub.add_parser("process", help="Bronze → Silver → Gold")
    sub.add_parser("stats", help="Resumen del corpus Gold")
    for name in ("ask", "summary", "faq", "eval"):
        p = sub.add_parser(name)
        p.add_argument("--provider", default=LLM_PROVIDER, choices=list(PROVIDERS))
        if name == "ask":
            p.add_argument("question")
            p.add_argument(
                "--version", default=assistant.DEFAULT_QA_VERSION, choices=list(assistant.QA_VERSIONS)
            )
        if name in ("summary", "faq"):
            p.add_argument("--topic", default=assistant.TOPICS[0])
        if name == "faq":
            p.add_argument("-n", type=int, default=5)
        if name == "eval":
            p.add_argument(
                "--version", default=assistant.DEFAULT_QA_VERSION, choices=list(assistant.QA_VERSIONS)
            )
            p.add_argument(
                "--limit", type=int, default=None, help="Solo las primeras N preguntas (prueba rápida)"
            )
    reco = sub.add_parser("reco", help="Recomendador de seguros (curso de Gestión)")
    reco_sub = reco.add_subparsers(dest="reco_command", required=True)
    gen = reco_sub.add_parser("generar", help="Dataset sintético → data/recomendador/")
    gen.add_argument("--clientes", type=int, default=RECO_N_CLIENTES)
    gen.add_argument("--semilla", type=int, default=RECO_SEMILLA)
    gen.add_argument("--salida", type=Path, default=RECO_DIR)
    for name in ("validar", "baseline", "cliente"):
        p = reco_sub.add_parser(name)
        p.add_argument("--entrada", type=Path, default=RECO_DIR)
        if name in ("baseline", "cliente"):
            p.add_argument("-k", type=int, default=RECO_K)
        if name == "cliente":
            p.add_argument("cliente_id")
    api = sub.add_parser("api", help="Levanta la API FastAPI (documentación en /docs)")
    api.add_argument("--host", default="127.0.0.1")
    api.add_argument("--port", type=int, default=8000)
    return parser


def _reco(args: argparse.Namespace) -> int:
    """Subcomandos del recomendador."""
    if args.reco_command == "generar":
        for nombre, filas in recomendador.generar(args.clientes, args.semilla, args.salida).items():
            print(f"{nombre:<11} {filas:>7,} filas → {args.salida / (nombre + '.csv')}")
        return 0
    if args.reco_command == "validar":
        errores = recomendador.validar(args.entrada)
        print("\n".join(errores) if errores else "Contrato de datos: OK")
        return 1 if errores else 0
    if args.reco_command == "baseline":
        resultado = recomendador.comparar_baselines(recomendador.leer_tablas(args.entrada), args.k)
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        return 0
    recomendaciones = recomendador.recomendar(args.cliente_id, args.k, args.entrada)
    print(json.dumps(recomendaciones, indent=2, ensure_ascii=False))
    return 0


def _assistant(provider: str) -> assistant.KnowledgeAssistant:
    """Asistente con toda la base (punto de inyección para las pruebas)."""
    return assistant.full_assistant(provider)


def main(argv: Sequence[str] | None = None) -> int:
    """Punto de entrada; devuelve el código de salida."""
    args = build_parser().parse_args(argv)
    if args.command == "reco":
        return _reco(args)
    if args.command == "api":
        import uvicorn

        uvicorn.run("sb_asistente.view.api:app", host=args.host, port=args.port)
        return 0
    if args.command == "discover":
        plan = pipeline.discover(pipeline.new_session())
        print(
            f"Sitemap: {plan['total_sitemap']} URLs · seleccionadas: {len(plan['seleccionadas'])}"
            f" · descartadas: {len(plan['descartadas'])}  → data/raw/plan_captura.json"
        )
    elif args.command == "scrape":
        print(pipeline.scrape(pipeline.new_session(), force=args.force))
    elif args.command in ("process", "stats"):
        summary = (
            pipeline.process()
            if args.command == "process"
            else json.loads((GOLD_DIR / "resumen.json").read_text(encoding="utf-8"))
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    elif args.command == "ask":
        ans = _assistant(args.provider).answer(args.question, version=args.version)
        print(ans.text, f"\n\n[{ans.latency_s:.1f}s · contexto ~{ans.context_tokens_est:,} tokens]")
    elif args.command == "summary":
        print(_assistant(args.provider).summarize(args.topic).text)
    elif args.command == "faq":
        print(_assistant(args.provider).faq(args.topic, args.n).text)
    elif args.command == "eval":

        def progress(i: int, total: int, row: dict[str, object]) -> None:
            fuente = "fuente ✓" if row["cita_fuente"] else "sin fuente"
            print(f"  [{i}/{total}] {row['id']} · {row['latencia_s']} s · {fuente}", flush=True)

        print(f"Evaluando · modelo {args.provider} · prompt {args.version}", flush=True)
        metrics, out = assistant.evaluate(
            args.provider, args.version, args.limit, progress, factory=_assistant
        )
        print(json.dumps(metrics, ensure_ascii=False, indent=2), f"\n→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

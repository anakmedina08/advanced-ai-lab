"""CLI: ``sb discover | scrape | process | stats | ask | summary | faq | eval``."""

import argparse
import json
from collections.abc import Sequence

from sb_asistente import pipeline
from sb_asistente.config import EVAL_QUESTIONS, EVAL_RESULTS, GOLD_DIR, LLM_PROVIDER
from sb_asistente.llm import prompts


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
        p.add_argument("--provider", default=LLM_PROVIDER, choices=["anthropic", "ollama"])
        if name == "ask":
            p.add_argument("question")
            p.add_argument("--version", default=prompts.DEFAULT_QA_VERSION, choices=list(prompts.QA_SYSTEM))
        if name in ("summary", "faq"):
            p.add_argument("--topic", default=prompts.TOPICS[0])
        if name == "faq":
            p.add_argument("-n", type=int, default=5)
        if name == "eval":
            p.add_argument("--version", default=prompts.DEFAULT_QA_VERSION, choices=list(prompts.QA_SYSTEM))
            p.add_argument(
                "--limit", type=int, default=None, help="Solo las primeras N preguntas (prueba rápida)"
            )
    return parser


def _assistant(provider: str):  # noqa: ANN202 - importación diferida de LangChain
    from sb_asistente.llm.service import KnowledgeAssistant, build_llm, context_budget, load_knowledge

    return KnowledgeAssistant(build_llm(provider), load_knowledge(max_tokens=context_budget(provider)))


def main(argv: Sequence[str] | None = None) -> int:
    """Punto de entrada; devuelve el código de salida."""
    args = build_parser().parse_args(argv)
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
        from sb_asistente.evaluation import load_questions, run_eval

        questions = load_questions(EVAL_QUESTIONS)[: args.limit]
        # Una muestra parcial no se mezcla con las corridas completas de la pestaña Evaluación.
        suffix = f"_muestra{len(questions)}" if args.limit else ""
        out = EVAL_RESULTS.with_name(f"resultados_{args.provider}_{args.version}{suffix}.csv")
        print(
            f"Evaluando {len(questions)} preguntas · modelo {args.provider} · prompt {args.version}",
            flush=True,
        )
        assistant = _assistant(args.provider)

        def progress(i: int, total: int, row: dict[str, object]) -> None:
            fuente = "fuente ✓" if row["cita_fuente"] else "sin fuente"
            print(f"  [{i}/{total}] {row['id']} · {row['latencia_s']} s · {fuente}", flush=True)

        metrics = run_eval(questions, lambda q: assistant.answer(q, args.version), out, progress)
        print(json.dumps(metrics, ensure_ascii=False, indent=2), f"\n→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""CLI: ``sb discover | scrape | process | stats | index | ask | summary | faq | eval``."""

import argparse
import json
import sys
from collections.abc import Sequence
from typing import TextIO

from sb_asistente.config import GOLD_DIR, LLM_PROVIDER
from sb_asistente.controller import assistant, pipeline


def build_parser() -> argparse.ArgumentParser:
    """Construye el parser de subcomandos."""
    parser = argparse.ArgumentParser(prog="sb", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("discover", help="robots.txt + sitemap → plan de captura")
    scrape = sub.add_parser("scrape", help="Descarga a Bronze (reanudable)")
    scrape.add_argument("--force", action="store_true", help="Volver a descargar todo")
    sub.add_parser("process", help="Bronze → Silver → Gold")
    sub.add_parser("stats", help="Resumen del corpus Gold")
    sub.add_parser("index", help="Fase 2: embeddings de los chunks en Qdrant (Ollama local)")
    for name in ("ask", "summary", "faq", "eval"):
        p = sub.add_parser(name)
        p.add_argument("--provider", default=LLM_PROVIDER, choices=["anthropic", "ollama"])
        if name in ("ask", "eval"):
            p.add_argument(
                "--version", default=assistant.DEFAULT_QA_VERSION, choices=list(assistant.QA_VERSIONS)
            )
            p.add_argument(
                "--modo",
                default=assistant.DEFAULT_MODE,
                choices=list(assistant.MODES),
                help="completo (Fase 1) · reducido · rag · agente (Fase 2)",
            )
        if name == "ask":
            p.add_argument("question")
        if name in ("summary", "faq"):
            p.add_argument("--topic", default=assistant.TOPICS[0])
        if name == "faq":
            p.add_argument("-n", type=int, default=5)
        if name == "eval":
            p.add_argument(
                "--limit", type=int, default=None, help="Solo las primeras N preguntas (prueba rápida)"
            )
    return parser


def _assistant(provider: str, mode: str = assistant.DEFAULT_MODE) -> assistant.QAAssistant:
    """Asistente del modo pedido (punto de inyección para las pruebas)."""
    return assistant.build_assistant(provider, mode)


def use_utf8(*streams: TextIO) -> None:
    """Fuerza UTF-8 en la salida.

    En Windows, cuando la salida se redirige (``sb eval > log.txt``), Python usa cp1252 y los
    símbolos «→» y «✓» lanzan ``UnicodeEncodeError``.
    """
    for stream in streams or (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def _read_summary() -> dict[str, object]:
    path = GOLD_DIR / "resumen.json"
    if not path.is_file():
        raise SystemExit(f"No existe {path}. Ejecute primero: uv run sb process")
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: Sequence[str] | None = None) -> int:
    """Punto de entrada; devuelve el código de salida."""
    use_utf8()
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
        summary = pipeline.process() if args.command == "process" else _read_summary()
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    elif args.command == "index":
        print("Calculando embeddings con Ollama (solo la primera vez o si cambian los chunks)…", flush=True)
        assistant.embedding_search()
        print("Índice listo → data/gold/qdrant/")
    elif args.command == "ask":
        ans = _assistant(args.provider, args.modo).answer(args.question, version=args.version)
        print(ans.text, f"\n\n[{ans.latency_s:.1f}s · modo {args.modo} · prompt {ans.prompt_version}]")
    elif args.command == "summary":
        print(assistant.full_assistant(args.provider).summarize(args.topic).text)
    elif args.command == "faq":
        print(assistant.full_assistant(args.provider).faq(args.topic, args.n).text)
    elif args.command == "eval":

        def progress(i: int, total: int, row: dict[str, object]) -> None:
            fuente = "fuente ✓" if row["cita_fuente"] else "sin fuente"
            print(f"  [{i}/{total}] {row['id']} · {row['latencia_s']} s · {fuente}", flush=True)

        print(f"Evaluando · modelo {args.provider} · modo {args.modo} · prompt {args.version}", flush=True)
        metrics, out = assistant.evaluate(
            args.provider,
            args.version,
            args.limit,
            progress,
            factory=lambda provider: _assistant(provider, args.modo),
            mode=args.modo,
        )
        print(json.dumps(metrics, ensure_ascii=False, indent=2), f"\n→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

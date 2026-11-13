"""CLI: ``sb`` · datos, asistente (modos completo/reducido/rag/agente), recomendador, chat, skills y API.

Cada subcomando delega en el controlador (MVC).
"""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from sb_asistente.config import (
    EMBEDDINGS_PROVIDER,
    EMBEDDINGS_PROVIDERS,
    GOLD_DIR,
    LLM_PROVIDER,
    PROVIDERS,
    RAG_K,
    RECO_DIR,
    RECO_K,
    RECO_N_CLIENTES,
    RECO_SEMILLA,
)
from sb_asistente.controller import assistant, chat, experimentos, pipeline, recomendador, vision
from sb_asistente.model import skills


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
        p.add_argument("--provider", default=LLM_PROVIDER, choices=list(PROVIDERS))
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
    conv = sub.add_parser("chat", help="Un turno del chat (clasifica y llama a la herramienta)")
    conv.add_argument("mensaje")
    conv.add_argument(
        "--modo", default="auto", choices=["auto", "conocimiento", "recomendador", "clasificador"]
    )
    conv.add_argument("--skill", default=None)
    conv.add_argument("--cliente", default=None)
    conv.add_argument("--provider", default=LLM_PROVIDER, choices=list(PROVIDERS))
    sk = sub.add_parser("skills", help="Skills de Claude Code / OpenCode del proyecto")
    sk_sub = sk.add_subparsers(dest="skills_command", required=True)
    sk_sub.add_parser("listar", help="Lista las skills y su uso (asistente o desarrollo)")
    sk_sub.add_parser("validar", help="Valida el frontmatter de todas las skills")
    nueva = sk_sub.add_parser("nueva", help="Crea .claude/skills/<nombre>/SKILL.md")
    nueva.add_argument("nombre")
    nueva.add_argument("--descripcion", required=True)
    nueva.add_argument("--uso", default="desarrollo", choices=["asistente", "desarrollo"])
    rag = sub.add_parser("rag", help="Base vectorial Chroma y búsqueda híbrida")
    rag_sub = rag.add_subparsers(dest="rag_command", required=True)
    idx = rag_sub.add_parser("indexar", help="Indexa data/gold/chunks.jsonl en data/vector/")
    idx.add_argument("--embeddings", default=EMBEDDINGS_PROVIDER, choices=list(EMBEDDINGS_PROVIDERS))
    idx.add_argument("--reset", action="store_true", help="Vacía el índice antes de indexar")
    bus = rag_sub.add_parser("buscar", help="Prueba la recuperación híbrida")
    bus.add_argument("consulta")
    bus.add_argument("-k", type=int, default=RAG_K)
    bus.add_argument("--seccion", default=None)
    ev = rag_sub.add_parser("evaluar", help="hit@k de la recuperación con el banco de preguntas")
    ev.add_argument("-k", type=int, nargs="+", default=[3, 6])
    ag = sub.add_parser("agente", help="Turno del agente (tools + salida estructurada + memoria)")
    ag.add_argument("mensaje")
    ag.add_argument("--conversacion", default="cli-local", help="Id de la conversación (memoria)")
    ag.add_argument("--provider", default=LLM_PROVIDER, choices=list(PROVIDERS))
    ag.add_argument("--olvidar", action="store_true", help="Borra la memoria de la conversación y sale")
    ag.add_argument("--usuario", default=None, help="Id del usuario (memoria de largo plazo en el Store)")
    ml = sub.add_parser("mlflow", help="Bitácora de experimentos (requiere uv sync --extra mlflow)")
    ml_sub = ml.add_subparsers(dest="mlflow_command", required=True)
    ml_sub.add_parser("importar", help="Carga en MLflow las evaluaciones guardadas en evaluacion/")
    ui_ml = ml_sub.add_parser("ui", help="Abre la interfaz de MLflow (http://127.0.0.1:5000)")
    ui_ml.add_argument("--port", type=int, default=5000)
    api = sub.add_parser("api", help="Levanta la API FastAPI (documentación en /docs)")
    api.add_argument("--host", default="127.0.0.1")
    api.add_argument("--port", type=int, default=8000)
    foto = sub.add_parser("foto", help="Foto → seguro sugerido (YOLO; requiere uv sync --extra vision)")
    foto.add_argument("ruta", type=Path, help="Imagen JPG o PNG")
    foto.add_argument("--interpretar", action="store_true", help="Entiende la situación con Claude (visión)")
    foto.add_argument("--responder", action="store_true", help="El asistente explica qué hacer, con fuente")
    foto.add_argument("--provider", default=LLM_PROVIDER, choices=list(PROVIDERS))
    foto.add_argument(
        "--api", default=None, metavar="URL", help="Usa la API por HTTP (p. ej. http://127.0.0.1:8000)"
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
        runs = experimentos.registrar_baselines(resultado, args.k, {"entrada": args.entrada.name})
        _avisar_mlflow(runs)
        return 0
    recomendaciones = recomendador.recomendar(args.cliente_id, args.k, args.entrada)
    print(json.dumps(recomendaciones, indent=2, ensure_ascii=False))
    return 0


def _skills(args: argparse.Namespace) -> int:
    """Subcomandos de skills."""
    if args.skills_command == "nueva":
        ruta = skills.nueva_skill(args.nombre, args.descripcion, args.uso)
        print(f"Creada {ruta.relative_to(skills.PROJECT_ROOT)} · edítela y ábrala en un PR")
        return 0
    encontradas, errores = skills.descubrir()
    if args.skills_command == "listar":
        for s in encontradas:
            print(f"{s.nombre:<24} {s.uso:<11} {s.ruta.parent.parent.relative_to(skills.PROJECT_ROOT)}")
    print("\n".join(errores) if errores else f"{len(encontradas)} skills válidas")
    return 1 if errores else 0


def _rag(args: argparse.Namespace) -> int:
    """Subcomandos de la base vectorial."""
    from sb_asistente.controller.agente import recuperador_por_defecto
    from sb_asistente.model.rag import indice
    from sb_asistente.model.rag.fuentes import fragmentos_rag

    if args.rag_command == "indexar":
        info = indice.indexar(fragmentos_rag(), args.embeddings, reset=args.reset)
        print(f"Índice listo: {info.fragmentos} fragmentos · {info.proveedor}/{info.modelo} → data/vector/")
        return 0
    recuperador, modo = recuperador_por_defecto()
    print(f"Modo: {modo}\n")
    if args.rag_command == "evaluar":
        from sb_asistente.config import EVAL_QUESTIONS
        from sb_asistente.model.evaluation import load_questions
        from sb_asistente.model.rag.evaluacion import hit_at_k

        preguntas = load_questions(EVAL_QUESTIONS)
        for k in args.k:
            r = hit_at_k(recuperador, preguntas, k)
            print(f"hit@{k}: {r.aciertos}/{r.total} ({r.tasa:.0%})  fallos: {', '.join(r.fallos) or '—'}")
        return 0
    for f in recuperador.buscar(args.consulta, k=args.k, seccion=args.seccion):
        print(f"{f.puntaje:.4f}  {'+'.join(f.origen):<11} {f.titulo[:50]:<50} {f.url}")
    return 0


def _foto(args: argparse.Namespace) -> int:
    """Analiza una foto en local (controlador) o a través de la API (cliente httpx)."""
    datos = args.ruta.read_bytes()
    if args.api:
        from sb_asistente.view.api_client import ClienteAPI

        cliente = ClienteAPI(args.api)
        out = cliente.analizar_foto(datos, args.ruta.name, args.responder, args.provider, args.interpretar)
        print(json.dumps(out.model_dump(), indent=2, ensure_ascii=False))
        return 0
    analisis = vision.analizar_foto(
        datos,
        asistente=assistant.LiteAssistant.build(args.provider) if args.responder else None,
        interprete=vision.interprete_por_defecto(args.provider) if args.interpretar else None,
        recomendar=(lambda perfil: recomendador.recomendar_por_perfil(perfil, 3)[0])
        if args.responder
        else None,
    )
    res = analisis.resultado
    print(f"{res.ancho}x{res.alto} px · inferencia {res.tiempo_ms} ms · {len(res.detecciones)} objetos")
    print(f"Privacidad: {analisis.personas_difuminadas} personas difuminadas antes de enviar la foto")
    for d in res.detecciones:
        print(f"  · {vision.etiqueta(d.clase):<12} {d.confianza:.0%}")
    if analisis.escena:
        print(f"\nSituación: {analisis.escena.situacion} · {analisis.escena.descripcion}")
    print(
        f"\nPlan: {analisis.plan.nombre}" + (f" → {analisis.plan.pregunta}" if analisis.plan.pregunta else "")
    )
    if analisis.aviso:
        print(analisis.aviso)
    if analisis.respuesta:
        print("\n" + analisis.respuesta.text)
    for r in analisis.recomendaciones:
        print(f"  ★ {r['nombre']} · {r['razon']}")
    return 0


def _avisar_mlflow(runs: list[str | None]) -> None:
    """Dice si la corrida quedó en la bitácora (o cómo activarla)."""
    if any(runs):
        print(f"Registrado en MLflow ({len([r for r in runs if r])} corrida/s) · ver: uv run sb mlflow ui")
    else:
        print("MLflow no registró: instálelo con uv sync --extra mlflow (o quite SB_MLFLOW=0).")


def _mlflow(args: argparse.Namespace) -> int:
    """Subcomandos de la bitácora de experimentos."""
    from sb_asistente.model.experimentos import disponible

    if not disponible():
        print("MLflow no está instalado: uv sync --extra mlflow")
        return 1
    if args.mlflow_command == "importar":
        for archivo, estado in experimentos.importar_evaluaciones():
            print(f"  {estado:<12} {archivo}")
        return 0
    import subprocess

    from sb_asistente.config import MLFLOW_TRACKING_URI

    print(f"MLflow en http://127.0.0.1:{args.port} (Ctrl+C para salir)")
    comando = [sys.executable, "-m", "mlflow", "ui", "--backend-store-uri", MLFLOW_TRACKING_URI]
    return subprocess.call([*comando, "--port", str(args.port)])


def _agente(args: argparse.Namespace) -> int:
    """Un turno del agente con su salida estructurada y la traza de tools."""
    from sb_asistente.controller.agente import agente_por_defecto

    agente = agente_por_defecto(args.provider)
    if args.olvidar:
        agente.olvidar(args.conversacion)
        print(f"Memoria de «{args.conversacion}» borrada.")
        return 0
    turno = agente.responder(args.mensaje, args.conversacion, args.usuario)
    d = turno.decision
    print(f"Router → {d['ruta']} (confianza {d['confianza']}) · tools: {', '.join(d['tools']) or 'ninguna'}")
    for paso in turno.pasos:
        print(f"  · tool {paso.tool}({json.dumps(paso.argumentos, ensure_ascii=False)})")
    print()
    print(json.dumps(turno.salida.model_dump(), indent=2, ensure_ascii=False))
    if turno.fuentes_descartadas:
        print(f"\nFuentes descartadas (no vistas en las tools): {turno.fuentes_descartadas}")
    return 0


def _chat(args: argparse.Namespace) -> int:
    """Un turno del chat en la terminal, con su traza."""
    lite: list[assistant.LiteAssistant] = []

    def qa(pregunta: str, skill: str | None) -> assistant.Answer:
        if not lite:
            lite.append(assistant.LiteAssistant.build(args.provider))
        return lite[0].answer(pregunta, skill=skill)

    turno = chat.responder(args.mensaje, qa, modo=args.modo, cliente_id=args.cliente, skill=args.skill)
    print(turno.respuesta, "\n")
    for paso in turno.traza:
        print(f"  · {paso.agente:<13} {paso.accion:<18} {paso.detalle} ({paso.ms} ms)")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Punto de entrada; devuelve el código de salida."""
    use_utf8()
    args = build_parser().parse_args(argv)
    if args.command == "reco":
        return _reco(args)
    if args.command == "skills":
        return _skills(args)
    if args.command == "chat":
        return _chat(args)
    if args.command == "rag":
        return _rag(args)
    if args.command == "agente":
        return _agente(args)
    if args.command == "foto":
        return _foto(args)
    if args.command == "mlflow":
        return _mlflow(args)
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
        version = assistant.AGENT_VERSION if args.modo == "agente" else args.version
        _avisar_mlflow([experimentos.registrar_eval(args.provider, args.modo, version, metrics, out)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

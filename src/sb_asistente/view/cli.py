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
    API_PORT,
    EMBEDDINGS_PROVIDER,
    EMBEDDINGS_PROVIDERS,
    GOLD_DIR,
    LLM_PROVIDER,
    MLFLOW_PUERTO,
    PROVIDERS,
    RAG_EVAL_KS,
    RAG_K,
    RECO_DIR,
    RECO_K,
    RECO_K_FOTO,
    RECO_N_CLIENTES,
    RECO_SEMILLA,
    TRAZAS_N,
)
from sb_asistente.controller import (
    assistant,
    chat,
    experimentos,
    herramientas,
    mercado,
    pipeline,
    recomendador,
    vision,
)


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
    ev.add_argument("-k", type=int, nargs="+", default=list(RAG_EVAL_KS))
    ag = sub.add_parser("agente", help="Turno del agente (tools + salida estructurada + memoria)")
    ag.add_argument("mensaje")
    ag.add_argument("--conversacion", default="cli-local", help="Id de la conversación (memoria)")
    ag.add_argument("--provider", default=LLM_PROVIDER, choices=list(PROVIDERS))
    ag.add_argument("--olvidar", action="store_true", help="Borra la memoria de la conversación y sale")
    ag.add_argument("--usuario", default=None, help="Id del usuario (memoria de largo plazo en el Store)")
    mer = sub.add_parser("mercado", help="Corpus de mercado: varias aseguradoras (SPEC-069)")
    mer_sub = mer.add_subparsers(dest="mercado_command", required=True)
    mer_sub.add_parser("listar", help="Aseguradoras del registro y su estado")
    for nombre, ayuda in (
        ("verificar", "robots.txt + sitemap de cada aseguradora → plan (sin descargar páginas)"),
        ("capturar", "Descarga a Bronze el plan de cada aseguradora (reanudable)"),
    ):
        p = mer_sub.add_parser(nombre, help=ayuda)
        p.add_argument("--solo", nargs="+", default=[], metavar="ID", help="Solo estas aseguradoras")
    mer_sub.add_parser("procesar", help="Bronze → Silver → Gold de todas (sin volver a la web)")
    mbus = mer_sub.add_parser("buscar", help="Busca en el corpus de mercado")
    mbus.add_argument("consulta")
    mbus.add_argument("-k", type=int, default=RAG_K)
    mbus.add_argument("--aseguradora", default=None)
    mcmp = mer_sub.add_parser("comparar", help="La misma consulta en varias aseguradoras")
    mcmp.add_argument("consulta")
    mcmp.add_argument("--aseguradoras", nargs="+", required=True, metavar="ID")
    mcan = mer_sub.add_parser(
        "canales", help="WhatsApp y teléfonos oficiales de una aseguradora para un servicio"
    )
    mcan.add_argument("aseguradora")
    mcan.add_argument("--servicio", choices=mercado.SERVICIOS_ATENCION, default=None)
    mcan.add_argument(
        "--resumen", default="", help="Resumen del caso (deduce el servicio y va en el WhatsApp)"
    )
    mid = mer_sub.add_parser(
        "identificar", help="Con qué aseguradora está la persona (pistas o recibo/carátula, OCR local)"
    )
    fuente = mid.add_mutually_exclusive_group(required=True)
    fuente.add_argument("--pistas", help="Dónde paga, de qué dominio le llegan correos, qué app usa…")
    fuente.add_argument("--archivo", type=Path, help="Foto, pantallazo o PDF (se lee en memoria)")
    ml = sub.add_parser("mlflow", help="Bitácora de experimentos (requiere uv sync --extra mlflow)")
    ml_sub = ml.add_subparsers(dest="mlflow_command", required=True)
    ml_sub.add_parser("importar", help="Carga en MLflow las evaluaciones guardadas en evaluacion/")
    ui_ml = ml_sub.add_parser("ui", help="Abre la interfaz de MLflow (http://127.0.0.1:5050)")
    ui_ml.add_argument("--port", type=int, default=MLFLOW_PUERTO)
    srv = ml_sub.add_parser("servidor", help="Servidor de tracking en http://127.0.0.1:5050 (UI + API)")
    srv.add_argument("--port", type=int, default=MLFLOW_PUERTO)
    tr = sub.add_parser("trazas", help="Últimos turnos del agente: ruta, tools y latencia (sin texto)")
    tr.add_argument("-n", type=int, default=TRAZAS_N)
    api = sub.add_parser("api", help="Levanta la API FastAPI (documentación en /docs)")
    api.add_argument("--host", default="127.0.0.1")
    api.add_argument("--port", type=int, default=API_PORT)
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
        ruta = herramientas.nueva_skill(args.nombre, args.descripcion, args.uso)
        print(f"Creada {ruta.relative_to(herramientas.RAIZ_PROYECTO)} · edítela y ábrala en un PR")
        return 0
    encontradas, errores = herramientas.skills_del_proyecto()
    if args.skills_command == "listar":
        for s in encontradas:
            print(
                f"{s.nombre:<24} {s.uso:<11} {s.ruta.parent.parent.relative_to(herramientas.RAIZ_PROYECTO)}"
            )
    print("\n".join(errores) if errores else f"{len(encontradas)} skills válidas")
    return 1 if errores else 0


def _rag(args: argparse.Namespace) -> int:
    """Subcomandos de la base vectorial."""
    from sb_asistente.controller.agente import recuperador_por_defecto

    if args.rag_command == "indexar":
        info = herramientas.indexar_rag(args.embeddings, args.reset)
        print(f"Índice listo: {info.fragmentos} fragmentos · {info.proveedor}/{info.modelo} → data/vector/")
        return 0
    if args.rag_command == "evaluar":
        modo, resultados = herramientas.evaluar_rag(args.k)
        print(f"Modo: {modo}\n")
        for k, r in zip(args.k, resultados, strict=True):
            print(f"hit@{k}: {r.aciertos}/{r.total} ({r.tasa:.0%})  fallos: {', '.join(r.fallos) or '—'}")
        return 0
    recuperador, modo = recuperador_por_defecto()
    print(f"Modo: {modo}\n")
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
        recomendar=(lambda perfil: recomendador.recomendar_por_perfil(perfil, RECO_K_FOTO)[0])
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
    if not herramientas.mlflow_disponible():
        print("MLflow no está instalado: uv sync --extra mlflow")
        return 1
    if args.mlflow_command == "importar":
        for archivo, estado in experimentos.importar_evaluaciones():
            print(f"  {estado:<12} {archivo}")
        return 0
    import subprocess

    print(f"MLflow en http://127.0.0.1:{args.port} (Ctrl+C para salir)")
    return subprocess.call(comando_mlflow(args.mlflow_command, args.port))


def comando_mlflow(subcomando: str, puerto: int) -> list[str]:
    """Comando de ``mlflow ui`` o ``mlflow server`` sobre la base SQLite y los artefactos de ``data/``.

    Con el servidor arriba, el resto del proyecto registra contra él definiendo
    ``MLFLOW_TRACKING_URI=http://127.0.0.1:5050``.
    """
    from sb_asistente.config import MLFLOW_ARTIFACTS, MLFLOW_BACKEND_URI

    base = [sys.executable, "-m", "mlflow", "server" if subcomando == "servidor" else "ui"]
    base += ["--backend-store-uri", MLFLOW_BACKEND_URI, "--host", "127.0.0.1", "--port", str(puerto)]
    if subcomando == "servidor":
        MLFLOW_ARTIFACTS.mkdir(parents=True, exist_ok=True)
        base += ["--default-artifact-root", MLFLOW_ARTIFACTS.as_uri()]
    return base


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


def _trazas(args: argparse.Namespace) -> int:
    """Resumen de las últimas trazas del agente (``data/logs/turnos.jsonl``)."""
    ruta, filas = herramientas.ultimas_trazas(args.n)
    if not filas:
        print(f"Aún no hay trazas en {ruta}. Converse con el agente (sb agente o la API).")
        return 0
    for f in filas:
        tools = ", ".join(f"{t['tool']} {t['ms']:.0f} ms" for t in f["tools"]) or "sin tools"
        error = f" · error {f['error']}" if f.get("error") else ""
        print(f"{f['fecha']}  hilo {f['hilo']}  {f['ruta']:<16} {f['ms_total']:>8.0f} ms  [{tools}]{error}")
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


def _mercado(args: argparse.Namespace) -> int:
    """Subcomandos de ``sb mercado``; los errores (id desconocido, corpus sin generar) salen como mensaje."""
    try:
        return _mercado_comando(args)
    except (KeyError, FileNotFoundError, ValueError, mercado.LectorNoDisponibleError) as exc:
        print(f"No se pudo: {exc.args[0] if exc.args else exc}")
        return 1


def _mercado_comando(args: argparse.Namespace) -> int:
    """Subcomandos de ``sb mercado`` (registro, scraping por aseguradora, búsqueda y comparación)."""
    registro = mercado.cargar_registro()
    if args.mercado_command == "listar":
        for fila in mercado.registro_con_datos():
            estado = "activa" if fila["activo"] else "en registro"
            wa = ", ".join(fila["whatsapp"]) or "—"
            sitio = fila["sitio"] or ""
            print(f"{fila['id']:<20} {estado:<12} docs={fila['documentos']:<4} WhatsApp={wa}  {sitio}")
    elif args.mercado_command == "verificar":
        for fila in mercado.descubrir(pipeline.new_session(), registro, args.solo):
            cuenta = f"{fila['seleccionadas']:>4} de {fila['en_sitemap']:<5}"
            print(f"{fila['aseguradora']:<20} {cuenta} {fila['estado']}")
    elif args.mercado_command == "capturar":
        print(json.dumps(mercado.capturar(pipeline.new_session(), registro, args.solo), indent=2))
    elif args.mercado_command == "procesar":
        print(json.dumps(mercado.procesar(registro), ensure_ascii=False, indent=2))
    elif args.mercado_command == "buscar":
        for f in mercado.recuperador_mercado().buscar(args.consulta, k=args.k, aseguradora=args.aseguradora):
            print(f"[{f.aseguradora}] {f.titulo} · {f.seccion} · {f.url}")
    elif args.mercado_command == "comparar":
        mercado.aseguradoras(args.aseguradoras)  # ids primero: un tipeo no depende de tener el corpus
        for oferta in mercado.comparar_aseguradoras(
            mercado.recuperador_mercado(), args.consulta, args.aseguradoras
        ):
            print(f"\n## {oferta.nombre}")
            if not oferta.tiene_informacion:
                print("  (no publica información sobre esto)")
            for f in oferta.fragmentos:
                print(f"  · {f.titulo} — {f.url}")
    elif args.mercado_command == "canales":
        r = mercado.canales_para(args.aseguradora, args.servicio, args.resumen)
        print(f"{r['nombre']} · servicio: {r['servicio']}")
        wa = r["whatsapp"]
        print(f"  WhatsApp: {wa['enlace']}" if isinstance(wa, dict) else "  WhatsApp: no publicado")
        telefonos = r["telefonos"] if isinstance(r["telefonos"], list) else []
        for t in telefonos:
            alcance = "(este servicio)" if t["especifico"] else "(línea general)"
            print(f"  Tel. {t['valor']:<16} {alcance}  {t['fuente']}")
        if not telefonos:
            print(f"  Sin teléfonos publicados: ver {r['sitio']}")
    elif args.mercado_command == "identificar":
        r = (
            mercado.identificar_documento(args.archivo.read_bytes())
            if args.archivo
            else mercado.identificar_por_pistas(args.pistas)
        )
        print(f"Aseguradora: {r['aseguradora'] or 'sin identificar'} · confianza {r['confianza']}")
        candidatas = r["candidatas"] if isinstance(r["candidatas"], list) else []
        for c in candidatas:
            print(f"  · {c['nombre']} ({c['id']}) por {', '.join(c['senales'])}")
        if r.get("leido") is False:
            print("  No se pudo leer texto: pruebe con una foto más nítida o un pantallazo.")
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
    if args.command == "trazas":
        return _trazas(args)
    if args.command == "foto":
        return _foto(args)
    if args.command == "mlflow":
        return _mlflow(args)
    if args.command == "mercado":
        return _mercado(args)
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

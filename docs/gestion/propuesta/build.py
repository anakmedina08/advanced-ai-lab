"""Construye la propuesta M2 en PDF desde la plantilla, backlog.json y las cifras reales del dataset.

Uso: uv run --with playwright==1.56.0 python docs/propuesta/build.py
(requiere Chromium de Playwright, pdftotext y, para regenerar el Gantt, Mermaid CLI «mmdc»)
"""

import asyncio
import html
import json
import re
import shutil
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

from playwright.async_api import async_playwright

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from sb_asistente.controller.recomendador import leer_tablas  # noqa: E402
from sb_asistente.model.recomendador.catalogo import POR_ID  # noqa: E402
from sb_asistente.model.recomendador.particion import leave_last_out  # noqa: E402
from sb_asistente.model.recomendador.popularidad import RecomendadorPopularidad  # noqa: E402

SALIDA = "M2_Propuesta_Grupo5_Silva_Medina.pdf"
REPO = "github.com/daalrasi/gpia-recomendador-bolivar"
CAPITULOS = [
    ("c1", "1. Contexto, modelo base y restricciones"),
    ("c2", "2. Objetivos y matriz de alcance"),
    ("c3", "3. Cronograma y ruta crítica (CPM)"),
    ("c4", "4. Marco de investigación y CRISP-DM"),
    ("c5", "5. Historias de usuario, criterios de aceptación y Kanban"),
    ("c6", "6. Anexos y enlaces"),
]


def num(x, dec=0):
    s = f"{x:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def cifras():
    eda = json.loads((RAIZ / "docs" / "gestion" / "eda.json").read_text(encoding="utf-8"))
    t = leer_tablas()
    train, obj = leave_last_out(t["polizas"])
    pop = RecomendadorPopularidad().fit(train)
    cubiertos = {p for c in obj for p in pop.recomendar(c, 5)}
    b = eda["baselines"]
    dist = {int(k): v for k, v in eda["dist_polizas_por_cliente"].items()}
    top3 = ", ".join(f"{n} ({num(v, 1)} %)" for n, v in eda["penetracion_top3"].items())
    return {
        "POL_MEDIA": num(eda["polizas_por_cliente_media"], 2),
        "PCT_UNA": num(dist[1] / eda["clientes"] * 100, 1),
        "SEG_R": num(b["segmento"]["recall@5"], 3),
        "SEG_N": num(b["segmento"]["ndcg@5"], 3),
        "POP_R": num(b["popularidad"]["recall@5"], 3),
        "POP_N": num(b["popularidad"]["ndcg@5"], 3),
        "COB_POP": num(len(cubiertos) / len(POR_ID) * 100, 0),
        "N_CLI": num(eda["clientes"]),
        "N_PROD": str(eda["productos"]),
        "N_POL": num(eda["polizas"]),
        "N_SIN": num(eda["siniestros"]),
        "N_EVAL": num(b["segmento"]["clientes"]),
        "FECHA_INI": eda["rango_fechas"][0],
        "FECHA_FIN": eda["rango_fechas"][1],
        "NULOS_FIN": num(eda["nulos_fecha_fin_pct"], 1),
        "TOP3": top3,
        "REPO": REPO,
    }


def cpm(hu):
    """Pase adelante y atrás sobre dependencias lógicas y de recurso (misma persona)."""
    tareas = {h["id"]: h for h in hu if h["estado"] != "Done"}
    previas = {i: [d for d in t["depende"] + t["recurso"] if d in tareas] for i, t in tareas.items()}
    orden, vistos = [], set()

    def visitar(i):
        if i not in vistos:
            vistos.add(i)
            for d in previas[i]:
                visitar(d)
            orden.append(i)

    for i in tareas:
        visitar(i)
    es, ef = {}, {}
    for i in orden:
        es[i] = max((ef[d] for d in previas[i]), default=0)
        ef[i] = es[i] + tareas[i]["sp"]
    fin = max(ef.values())
    lf, ls = {}, {}
    for i in reversed(orden):
        sucesoras = [j for j in tareas if i in previas[j]]
        lf[i] = min((ls[j] for j in sucesoras), default=fin)
        ls[i] = lf[i] - tareas[i]["sp"]
    return {i: (es[i], ef[i], ls[i], lf[i], ls[i] - es[i]) for i in orden}, fin


def gantt(hu, tiempos, inicio, equipo):
    dia0 = date.fromisoformat(inicio)
    lineas = [
        "gantt",
        "    dateFormat YYYY-MM-DD",
        "    axisFormat %d/%m",
        "    tickInterval 1day",
    ]
    secciones = [*equipo, "Equipo"]
    for persona in secciones:
        lineas.append(f"    section {persona.split()[0]}")
        for h in sorted(hu, key=lambda x: tiempos.get(x["id"], (99,))[0]):
            if h["id"] not in tiempos or not h["responsable"].startswith(persona.split()[0]):
                continue
            es, ef, _, _, holgura = tiempos[h["id"]]
            crit = "crit, " if holgura == 0 else ""
            lineas.append(
                f"    {h['id']} · {h['sp']} SP :{crit}{h['id'].lower()}, {dia0 + timedelta(es)}, {ef - es}d"
            )
    return "\n".join(lineas) + "\n"


def historias():
    backlog = json.loads((RAIZ / "docs" / "gestion" / "backlog.json").read_text(encoding="utf-8"))
    s = backlog["sprint"]
    capacidad = s["integrantes"] * s["dias"] * s["foco"]
    hu = backlog["historias"]
    sprint = sum(h["sp"] for h in hu if h["estado"] != "Done")
    tiempos, duracion = cpm(hu)
    (AQUI / "gantt.mmd").write_text(gantt(hu, tiempos, s["inicio"], backlog["equipo"]), encoding="utf-8")
    if shutil.which("mmdc"):
        subprocess.run(
            [
                "mmdc",
                "-i",
                "gantt.mmd",
                "-o",
                "gantt.png",
                "-c",
                "cfg.json",
                "-w",
                "1000",
                "-s",
                "2",
                "-b",
                "white",
            ],
            cwd=AQUI,
            check=True,
            capture_output=True,
        )
    titulos = {h["id"]: h["titulo"] for h in hu}
    filas_cpm = "".join(
        f"<tr{' class=crit' if t[4] == 0 else ''}><td>{i} {html.escape(titulos[i])}</td>"
        f"<td>{', '.join(h['depende'] + [r + '*' for r in h['recurso']]) or '—'}</td>"
        + "".join(f"<td class='c'>{v}</td>" for v in (t[1] - t[0], *t))
        + "</tr>"
        for h in hu
        if (i := h["id"]) in tiempos and (t := tiempos[i])
    )
    por_id = {h["id"]: h for h in hu}
    actual = next(i for i, t in tiempos.items() if t[1] == duracion and t[4] == 0)
    cadena = [actual]
    while True:  # recorre hacia atrás por predecesoras críticas, primero las lógicas
        h = por_id[actual]
        previa = [
            d
            for d in h["depende"] + h["recurso"]
            if d in tiempos and tiempos[d][4] == 0 and tiempos[d][1] == tiempos[actual][0]
        ]
        if not previa:
            break
        actual = previa[0]
        cadena.append(actual)
    ruta = " → ".join(reversed(cadena))
    carga = {m: 0.0 for m in backlog["equipo"]}
    for h in hu:
        if h["estado"] == "Done":
            continue
        for m in carga:
            if h["responsable"].startswith("Equipo"):
                carga[m] += h["sp"] / len(carga)
            elif h["responsable"] == m:
                carga[m] += h["sp"]
    por_persona = s["dias"] * s["foco"]
    filas_carga = "".join(
        f"<tr><td>{m}</td><td>{', '.join(h['id'] for h in hu if h['responsable'] == m and h['estado'] != 'Done')}"
        f", HU-10</td><td class='c'>{num(c, 2)}</td><td class='c'>{num(por_persona, 2)}</td>"
        f"<td class='c'>{num(c / por_persona * 100, 0)} %</td></tr>"
        for m, c in carga.items()
    )
    filas = "".join(
        f"<tr><td>{h['id']}</td><td>{html.escape(h['titulo'])}</td><td class='c'>{h['sp']}</td>"
        f"<td>{h['etiqueta']}</td><td>{h['responsable']}</td><td>{h['estado']}</td></tr>"
        for h in hu
    )
    resumen = (
        "<div class='tabcap'>Tabla 5. Backlog del proyecto</div><table><tr><th>ID</th><th>Historia</th>"
        "<th class='c'>SP</th><th>Etiqueta</th><th>Responsable</th><th>Columna</th></tr>" + filas + "</table>"
    )
    tarjetas = "".join(
        f"<div class='story'><div class='h'><span>{h['id']} · {html.escape(h['titulo'])}</span>"
        f"<span class='tag'>{h['sp']} SP · {h['etiqueta']} · {h['responsable']}</span></div>"
        f"<div class='b'><b>Como</b> {h['como']}, <b>quiero</b> {h['quiero']}, <b>para</b> {h['para']}."
        "<ol class='gwt'>"
        + "".join(
            f"<li><b>Dado:</b> {html.escape(a['dado'])}. <b>Cuando:</b> {html.escape(a['cuando'])}. "
            f"<b>Entonces:</b> {html.escape(a['entonces'])}.</li>"
            for a in h["ac"]
        )
        + f"</ol><div class='just'><b>Estimación {h['sp']} SP:</b> {html.escape(h['justificacion'])}</div></div></div>"
        for h in hu
    )
    return {
        "CAPACIDAD": num(capacidad, 1),
        "SP_SPRINT": str(sprint),
        "CARGA": num(sprint / capacidad * 100, 0),
        "N_HU": str(len(hu)),
        "N_SPRINT": str(sum(h["estado"] != "Done" for h in hu)),
        "SP_PERSONA": num(por_persona, 2),
        "TABLA_CARGA": filas_carga,
        "TABLA_CPM": filas_cpm,
        "RUTA": ruta,
        "DURACION": str(duracion),
        "HOLGURA_SPRINT": str(s["dias"] - duracion),
        "RESUMEN_HU": resumen,
        "HISTORIAS": tarjetas,
    }


def evidencia():
    """Árbol del repositorio y resultado de pytest, para que la evidencia quede dentro del PDF."""
    incluir = ("src", "tests", "scripts", ".github", "docs/gestion/backlog.json", "pyproject.toml", "uv.lock")
    excluir = ("__pycache__", ".pyc", "_render.html")
    rutas = sorted(
        str(p.relative_to(RAIZ))
        for p in RAIZ.rglob("*")
        if p.is_file()
        and str(p.relative_to(RAIZ)).startswith(incluir)
        and not any(x in str(p) for x in excluir)
    )
    pytest = subprocess.run(
        ["uv", "run", "pytest", "--cov=recomendador", "--cov-report=term", "-p", "no:cacheprovider"],
        cwd=RAIZ,
        capture_output=True,
        text=True,
    ).stdout
    pasaron = re.search(r"(\d+) passed", pytest)
    cobertura = re.search(r"^TOTAL.*?(\d+)%", pytest, re.M)
    resumen = (
        f"Resultado de <code>uv run pytest</code> al generar este documento: {pasaron.group(1)} pruebas en verde "
        f"(patrón AAA, datos sintéticos, sin red) y cobertura de {cobertura.group(1)} %. "
        "Herramientas: Python 3.13 con uv (pyproject.toml y uv.lock), ruff y pre-commit, CI en GitHub Actions, "
        "ramas Gitflow (main, develop, feature/*) y PR revisados por la Code Reviewer."
        if pasaron and cobertura
        else "No se pudo ejecutar pytest al generar el documento."
    )
    return {"ARBOL": html.escape("\n".join(rutas)), "PRUEBAS": resumen}


def toc(paginas):
    items = "".join(f"<li><span>{t}</span><span>{paginas.get(i, '')}</span></li>" for i, t in CAPITULOS)
    return f"<ul class='toc'>{items}</ul>"


async def render(html_text, salida):
    # Encabezado de tabla en <thead> para que se repita si la tabla cruza de página
    html_text = re.sub(
        r"<table([^>]*)>\s*<tr>(\s*<th.*?</tr>)", r"<table\1><thead><tr>\2</thead>", html_text, flags=re.S
    )
    (AQUI / "_render.html").write_text(html_text, encoding="utf-8")
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        await pg.goto((AQUI / "_render.html").as_uri())
        await pg.wait_for_timeout(500)
        await pg.pdf(
            path=str(salida),
            prefer_css_page_size=True,
            print_background=True,
            display_header_footer=True,
            header_template="<span></span>",
            footer_template='<div style="font-size:9px;width:100%;text-align:center;font-family:Arial;color:#555">'
            '<span class="pageNumber"></span></div>',
        )
        await b.close()


def paginas_de_capitulos(pdf):
    texto = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
    paginas = texto.split("\f")
    resultado = {}
    for cid, titulo in CAPITULOS:
        for i, pag in enumerate(paginas[2:], start=3):  # saltar portada e índice
            if re.search(r"^\s*" + re.escape(titulo[:28]), pag, re.M):
                resultado[cid] = i
                break
    return resultado, len([p for p in paginas if p.strip()])


def main():
    plantilla = (AQUI / "plantilla.html").read_text(encoding="utf-8")
    valores = cifras() | historias() | evidencia()
    for k, v in valores.items():
        plantilla = plantilla.replace("{{" + k + "}}", v)
    faltan = re.findall(r"{{(\w+)}}", plantilla.replace("{{TOC}}", ""))
    if faltan:
        raise SystemExit(f"Marcadores sin valor: {faltan}")
    salida = AQUI / SALIDA
    asyncio.run(render(plantilla.replace("{{TOC}}", toc({})), salida))
    paginas, total = paginas_de_capitulos(salida)
    asyncio.run(render(plantilla.replace("{{TOC}}", toc(paginas)), salida))
    shutil.copyfile(
        salida, RAIZ / "docs" / "gestion" / "propuesta-m2.pdf"
    )  # copia exigida por el Anuncio 006
    contenido = paginas["c6"] - paginas["c1"]
    print(
        json.dumps({"paginas_total": total, "capitulos": paginas, "paginas_contenido_cap1_a_cap5": contenido})
    )


if __name__ == "__main__":
    main()

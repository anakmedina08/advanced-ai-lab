"""Renderiza ``docs/arquitectura.json`` (formato de Archify, tipo architecture) a un HTML autocontenido.

El HTML no depende de nada externo: SVG inline, tema claro/oscuro, y al pasar el mouse por un
componente se resaltan sus relaciones y se muestra su detalle. Si la skill Archify está instalada,
el mismo JSON se puede entregar con ``archify deliver``.

    uv run python scripts/diagrama_arquitectura.py
"""

import html
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ANCHO_COLUMNA, ALTO_NODO, SEPARACION, MARGEN = 230, 78, 22, 40


def posiciones(datos: dict) -> dict[str, tuple[int, int]]:
    """(x, y) de cada nodo: columna por capa, fila por orden de aparición."""
    capas = [c["id"] for c in datos["capas"]]
    filas: dict[str, int] = {}
    salida = {}
    for nodo in datos["nodos"]:
        columna = capas.index(nodo["capa"])
        fila = filas.get(nodo["capa"], 0)
        filas[nodo["capa"]] = fila + 1
        salida[nodo["id"]] = (MARGEN + columna * (ANCHO_COLUMNA + 40), 90 + fila * (ALTO_NODO + SEPARACION))
    return salida


def svg(datos: dict) -> str:
    """SVG del diagrama con capas, límite de confianza, nodos y relaciones."""
    pos = posiciones(datos)
    ancho = MARGEN * 2 + len(datos["capas"]) * (ANCHO_COLUMNA + 40)
    alto = max(y for _, y in pos.values()) + ALTO_NODO + 70
    partes = [f'<svg viewBox="0 0 {ancho} {alto}" role="img" aria-label="{html.escape(datos["titulo"])}">']
    partes.append(
        '<defs><marker id="flecha" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" class="punta"/></marker></defs>'
    )
    for i, capa in enumerate(datos["capas"]):
        x = MARGEN + i * (ANCHO_COLUMNA + 40)
        partes.append(
            f'<rect x="{x - 10}" y="40" width="{ANCHO_COLUMNA + 20}" height="{alto - 60}" class="capa"/>'
        )
        nombre = html.escape(capa["nombre"])
        partes.append(f'<text x="{x + ANCHO_COLUMNA / 2}" y="64" class="titulo-capa">{nombre}</text>')
    x0 = MARGEN + ANCHO_COLUMNA + 20
    fin = MARGEN + (len(datos["capas"]) - 1) * (ANCHO_COLUMNA + 40) - 20  # sin la columna externa
    partes.append(f'<rect x="{x0}" y="22" width="{fin - x0}" height="{alto - 30}" class="limite"/>')
    partes.append(f'<text x="{x0 + 10}" y="36" class="texto-limite">Equipo local · los datos no salen</text>')
    for r in datos["relaciones"]:
        (x1, y1), (x2, y2) = pos[r["de"]], pos[r["a"]]
        if x2 > x1:
            ax, ay, bx, by = x1 + ANCHO_COLUMNA, y1 + ALTO_NODO / 2, x2, y2 + ALTO_NODO / 2
        else:
            ax, ay, bx, by = x1 + ANCHO_COLUMNA / 2, y1 + ALTO_NODO, x2 + ANCHO_COLUMNA / 2, y2
        medio = (ax + bx) / 2
        camino = f"M {ax} {ay} C {medio} {ay}, {medio} {by}, {bx} {by}"
        partes.append(
            f'<g class="arista" data-de="{r["de"]}" data-a="{r["a"]}">'
            f'<path d="{camino}" marker-end="url(#flecha)"/>'
            f'<text x="{medio}" y="{(ay + by) / 2 - 4}">{html.escape(r["etiqueta"])}</text></g>'
        )
    externos = {n for lim in datos["limites"] for n in lim.get("nodos", [])}
    for n in datos["nodos"]:
        x, y = pos[n["id"]]
        clase = "nodo externo" if n["id"] in externos else "nodo"
        partes.append(
            f'<g class="{clase}" data-id="{n["id"]}" tabindex="0"><title>{html.escape(n["detalle"])}</title>'
            f'<rect x="{x}" y="{y}" width="{ANCHO_COLUMNA}" height="{ALTO_NODO}" rx="10"/>'
            f'<text x="{x + 12}" y="{y + 26}" class="nombre">{html.escape(n["nombre"])}</text>'
            f'<foreignObject x="{x + 10}" y="{y + 32}" width="{ANCHO_COLUMNA - 20}" '
            f'height="{ALTO_NODO - 34}">'
            f'<p xmlns="http://www.w3.org/1999/xhtml">{html.escape(n["detalle"])}</p></foreignObject></g>'
        )
    partes.append("</svg>")
    return "\n".join(partes)


PLANTILLA = Path(__file__).with_name("plantilla_arquitectura.html")


def main() -> None:
    """Lee el JSON y escribe ``docs/arquitectura.html``."""
    datos = json.loads((RAIZ / "docs" / "arquitectura.json").read_text(encoding="utf-8"))
    pagina = (
        PLANTILLA.read_text(encoding="utf-8")
        .replace("__TITULO__", html.escape(datos["titulo"]))
        .replace("__DESCRIPCION__", html.escape(datos["descripcion"]))
        .replace("__SVG__", svg(datos))
    )
    (RAIZ / "docs" / "arquitectura.html").write_text(pagina, encoding="utf-8")
    print("docs/arquitectura.html")


if __name__ == "__main__":
    main()

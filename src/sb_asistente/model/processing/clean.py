"""Etapa 3 · Bronze → Silver: extraer el contenido editorial y quitar el boilerplate.

Estrategia para segurosbolivar.com (Angular SSR):
- El contenido de cada página vive en ``<main>``; el pie (``<footer>``) se repite en todas.
- El pie trae los **canales de atención** (WhatsApp, líneas, sede): se guarda UNA sola vez
  como documento propio y se quita de cada página (evita que el RAG lo devuelva siempre).
- Las líneas que aparecen en ≥ 50 % de las páginas (menús, banners) se eliminan por hash.
"""

import hashlib
import re
from collections import Counter
from dataclasses import dataclass, field

import trafilatura
from bs4 import BeautifulSoup

from sb_asistente.config import BOILERPLATE_MIN_SHARE

NOISE_TAGS = ("script", "style", "noscript", "svg", "iframe", "form", "button", "img")


@dataclass(slots=True)
class CleanPage:
    """Página limpia (capa Silver)."""

    url: str
    title: str
    description: str
    text: str
    headings: list[str] = field(default_factory=list)


def _norm(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text).strip()


def extract_meta(html: str) -> tuple[str, str]:
    """Devuelve ``(title, description)`` de la página."""
    soup = BeautifulSoup(html, "lxml")
    title = _norm(soup.title.get_text()) if soup.title else ""
    title = re.sub(r"\s*\|\s*Seguros Bol[ií]var\s*$", "", title)
    meta = soup.find("meta", attrs={"name": "description"})
    description = _norm(meta.get("content", "")) if meta else ""
    return title, description


def extract_footer(html: str) -> str:
    """Texto del pie de página (canales de atención), en líneas limpias."""
    soup = BeautifulSoup(html, "lxml")
    footer = soup.find("footer")
    if footer is None:
        return ""
    for tag in footer.find_all(NOISE_TAGS):
        tag.decompose()
    lines = [_norm(t) for t in footer.get_text("\n").splitlines()]
    return join_label_values([line for line in lines if line and not line.startswith("©")])


def join_label_values(lines: list[str]) -> str:
    """Une «Etiqueta:» con el valor de la línea siguiente: 'WhatsApp:' + '322…' → 'WhatsApp: 322…'."""
    out: list[str] = []
    for line in lines:
        if out and out[-1].endswith(":") and not line.endswith(":"):
            out[-1] = f"{out[-1]} {line}"
        else:
            out.append(line)
    return "\n".join(out)


def pdf_links(html: str, base_url: str = "https://www.segurosbolivar.com") -> list[str]:
    """Enlaces a PDF (clausulados, condiciones) de la página, absolutos y sin duplicados."""
    from urllib.parse import urljoin

    soup = BeautifulSoup(html, "lxml")
    links = {
        urljoin(base_url, a["href"]) for a in soup.find_all("a", href=True) if ".pdf" in a["href"].lower()
    }
    return sorted(links)


def _main_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(["footer", "nav", "header", *NOISE_TAGS]):
        tag.decompose()
    main = soup.find("main") or soup.body or soup
    return str(main)


def html_to_markdown(html: str) -> str:
    """Convierte el ``<main>`` a Markdown; si trafilatura no extrae nada, usa texto plano."""
    main_html = _main_html(html)
    md = trafilatura.extract(
        f"<html><body>{main_html}</body></html>",
        output_format="markdown",
        include_tables=True,
        include_links=False,
        include_comments=False,
        favor_recall=True,
    )
    if md and len(md.strip()) > 50:
        return md.strip()
    soup = BeautifulSoup(main_html, "lxml")
    lines = [_norm(t) for t in soup.get_text("\n").splitlines()]
    return "\n".join(line for line in lines if line)


def headings_of(html: str) -> list[str]:
    """Títulos h1–h3 del contenido principal (para metadatos y chunking)."""
    soup = BeautifulSoup(_main_html(html), "lxml")
    return [_norm(h.get_text()) for h in soup.find_all(["h1", "h2", "h3"]) if _norm(h.get_text())]


def _line_key(line: str) -> str:
    return hashlib.sha1(re.sub(r"\W+", "", line.lower()).encode()).hexdigest()


# Bloques de venta cruzada al final de cada producto: describen OTROS seguros y harían que el
# modelo citara la página equivocada; se corta desde el marcador hasta el final de la página.
CROSS_SELL_MARKERS: tuple[str, ...] = ("Otros seguros de su interés",)


def trim_noise(markdown: str, markers: tuple[str, ...] = CROSS_SELL_MARKERS) -> str:
    """Quita venta cruzada, etiquetas ``<u>`` residuales y líneas que son solo un punto."""
    lines: list[str] = []
    for line in markdown.splitlines():
        bare = re.sub(r"^[#>*\s]+|[*\s]+$", "", line)  # el marcador suele venir como título: "## …"
        if bare in markers:
            break
        if bare == ".":
            continue
        lines.append(re.sub(r"</?u>", "", line))
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def title_from_path(path: str) -> str:
    """Título legible cuando la página no trae ``<title>``.

    Ejemplo: '/medios-de-pago/reembolsos' → 'Medios de pago · Reembolsos'.
    """
    parts = [p.replace("-", " ").strip() for p in path.strip("/").split("/") if p]
    return " · ".join(p[:1].upper() + p[1:] for p in parts) or "Inicio"


def find_boilerplate(texts: list[str], min_share: float = BOILERPLATE_MIN_SHARE) -> set[str]:
    """Hashes de las líneas que aparecen en al menos ``min_share`` de los documentos."""
    if len(texts) < 3:
        return set()
    counts: Counter[str] = Counter()
    for text in texts:
        counts.update({_line_key(line) for line in text.splitlines() if line.strip()})
    threshold = max(3, int(len(texts) * min_share))
    return {key for key, n in counts.items() if n >= threshold}


def remove_lines(text: str, boilerplate: set[str]) -> str:
    """Quita las líneas de boilerplate y colapsa líneas en blanco repetidas."""
    kept = [line for line in text.splitlines() if not line.strip() or _line_key(line) not in boilerplate]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()

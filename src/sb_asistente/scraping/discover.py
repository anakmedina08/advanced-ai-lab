"""Etapa 1 · Descubrir: robots.txt + sitemap.xml → lista de URLs dentro del alcance."""

from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

from lxml import etree

from sb_asistente.config import EXCLUDE_PATTERNS, compile_patterns

SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


@dataclass(frozen=True, slots=True)
class SitemapEntry:
    """Una URL del sitemap con su fecha de modificación (si existe)."""

    url: str
    lastmod: str | None = None


def parse_sitemap(xml: bytes | str) -> tuple[list[SitemapEntry], list[str]]:
    """Lee un sitemap o un índice de sitemaps.

    Returns:
        Tupla ``(urls, sub_sitemaps)``: entradas de página y sitemaps hijos a recorrer.

    """
    data = xml.encode() if isinstance(xml, str) else xml
    root = etree.fromstring(data, parser=etree.XMLParser(resolve_entities=False, no_network=True))
    tag = etree.QName(root).localname
    if tag == "sitemapindex":
        subs = [loc.text.strip() for loc in root.findall("sm:sitemap/sm:loc", SITEMAP_NS) if loc.text]
        return [], subs
    entries = []
    for node in root.findall("sm:url", SITEMAP_NS):
        loc = node.find("sm:loc", SITEMAP_NS)
        if loc is None or not loc.text:
            continue
        lastmod = node.find("sm:lastmod", SITEMAP_NS)
        entries.append(SitemapEntry(loc.text.strip(), lastmod.text.strip() if lastmod is not None else None))
    return entries, []


def build_robots(robots_txt: str, robots_url: str) -> RobotFileParser:
    """Construye el parser de robots.txt a partir de su contenido."""
    parser = RobotFileParser(robots_url)
    parser.parse(robots_txt.splitlines())
    return parser


def path_of(url: str) -> str:
    """Ruta normalizada de una URL (sin barra final, '/' para la home)."""
    path = urlsplit(url).path.rstrip("/")
    return path or "/"


def in_scope(url: str, exclude: Iterable[str] = EXCLUDE_PATTERNS) -> bool:
    """Indica si la URL entra en el alcance PERSONAS + CANALES de la Fase 1."""
    path = path_of(url)
    return not any(p.search(path) for p in compile_patterns(tuple(exclude)))


def select_urls(
    entries: Iterable[SitemapEntry],
    robots: RobotFileParser,
    user_agent: str,
    exclude: Iterable[str] = EXCLUDE_PATTERNS,
) -> tuple[list[SitemapEntry], list[tuple[str, str]]]:
    """Filtra por robots.txt y por alcance, sin duplicados y en orden estable.

    Returns:
        ``(seleccionadas, descartadas)`` donde cada descartada lleva su motivo.

    """
    selected: list[SitemapEntry] = []
    rejected: list[tuple[str, str]] = []
    seen: set[str] = set()
    for entry in entries:
        key = path_of(entry.url)
        if key in seen:
            rejected.append((entry.url, "duplicada"))
            continue
        seen.add(key)
        if not robots.can_fetch(user_agent, entry.url):
            rejected.append((entry.url, "robots.txt"))
        elif not in_scope(entry.url, exclude):
            rejected.append((entry.url, "fuera de alcance"))
        else:
            selected.append(entry)
    return selected, rejected

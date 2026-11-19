"""Canales de atención de cada aseguradora por servicio, leídos de sus páginas oficiales (SPEC-070).

De cada página se toman los WhatsApp (``wa.me`` / ``api.whatsapp.com``), los teléfonos de enlaces
``tel:`` y los números que aparecen en el texto: líneas cortas (``#322``), ``01 8000`` y fijos
nacionales (``60x``). El texto que rodea a cada número dice para qué servicio es (siniestro de
autos, asistencia de hogar, salud, PQR…). Ningún número se escribe a mano.

Privacidad (Ley 1581): un celular solo se guarda si aparece en la mayoría de las páginas del sitio
(canal oficial del encabezado o del pie); los que salen en una sola página pueden ser de un asesor.
Líneas cortas, ``01 8000`` y fijos son institucionales.
"""

import math
import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Literal, cast
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup, Tag

from sb_asistente.config import MERCADO_CONTEXTO_CANAL, MERCADO_WHATSAPP_MIN_FRACCION
from sb_asistente.model.mercado.contactos import normalizar_numero

TipoCanal = Literal["whatsapp", "linea_corta", "linea_nacional", "fijo", "celular"]
Servicio = Literal["autos", "hogar", "salud", "vida", "arl", "soat", "pqr", "ventas", "general"]
TIPOS: frozenset[str] = frozenset({"whatsapp", "linea_corta", "linea_nacional", "fijo", "celular"})
SERVICIOS: tuple[Servicio, ...] = (
    "autos",
    "soat",
    "hogar",
    "salud",
    "vida",
    "arl",
    "pqr",
    "ventas",
    "general",
)

# Palabras del contexto → servicio (la primera que coincide gana; «general» si ninguna).
_REGLAS_SERVICIO: tuple[tuple[str, Servicio], ...] = (
    (r"soat", "soat"),
    (r"arl|riesgos laborales|accidente de trabajo|riesgos profesionales", "arl"),
    (r"vehicul|autos?\b|carro|moto|grua|transito|movilidad|conductor", "autos"),
    (r"hogar|vivienda|casa|cerrajer|plomer|electricist|inmueble", "hogar"),
    (r"salud|medic|ambulancia|hospital|clinic|odontolog|urgencia", "salud"),
    (r"vida|exequial|fallecimiento|funerari", "vida"),
    (r"pqr|queja|reclamo|defensor|peticion", "pqr"),
    (r"venta|cotiz|asesor comercial|compra", "ventas"),
)

_LINEA_CORTA = re.compile(r"(?<![\w#])#\s?(\d{3,4})\b")
_LINEA_NACIONAL = re.compile(r"\b01\s*-?\s*8000\s*-?\s*(\d{3})\s*-?\s*(\d{3,4})\b")
_FIJO = re.compile(r"\(?\b(60\d)\)?\s*-?\s*(\d{3})\s*-?\s*(\d{4})\b")


@dataclass(frozen=True, slots=True)
class Canal:
    """Un canal de atención visto en una página."""

    tipo: TipoCanal
    valor: str  # normalizado: 57XXXXXXXXXX, #322 o 018000XXXXXX
    servicio: Servicio
    fuente: str  # URL de la página donde aparece


@dataclass(slots=True)
class CanalAgregado:
    """Un canal de una aseguradora con todas las páginas y servicios donde aparece."""

    tipo: TipoCanal
    valor: str
    servicios: set[str] = field(default_factory=set)
    fuentes: list[str] = field(default_factory=list)
    paginas: int = 0  # en cuántas páginas del sitio aparece


def _plano(texto: str) -> str:
    """Minúsculas sin tildes."""
    return unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()


def servicio_de(contexto: str) -> Servicio:
    """Servicio del canal según las palabras que lo rodean."""
    plano = _plano(contexto)
    return next((s for patron, s in _REGLAS_SERVICIO if re.search(patron, plano)), "general")


def _desde_tel(href: str) -> tuple[TipoCanal, str] | None:
    """Tipo y valor normalizado de un enlace ``tel:``."""
    crudo = unquote(href.split(":", 1)[1]).strip()
    if crudo.startswith("#"):
        digitos = re.sub(r"\D", "", crudo)
        return ("linea_corta", f"#{digitos}") if 3 <= len(digitos) <= 4 else None
    digitos = re.sub(r"\D", "", crudo)
    if re.fullmatch(r"(57)?018000\d{6,7}", digitos):
        return "linea_nacional", digitos.removeprefix("57")
    numero = normalizar_numero(digitos)
    if numero is None:
        return None
    return ("celular" if numero[2] == "3" else "fijo"), numero


def _desde_whatsapp(href: str) -> str | None:
    """Número de un enlace de WhatsApp oficial."""
    partes = urlsplit(href)
    host = partes.netloc.lower().removeprefix("www.")
    if host == "wa.me":
        return normalizar_numero(partes.path.strip("/").split("/")[0])
    if host in {"api.whatsapp.com", "web.whatsapp.com", "whatsapp.com"}:
        telefono = re.search(r"phone=([^&]+)", partes.query)
        return normalizar_numero(telefono.group(1)) if telefono else None
    return None


def _contexto(nodo: Tag) -> str:
    """Título de la sección, texto del enlace y de su bloque padre (para saber el servicio)."""
    titulo = nodo.find_previous(["h1", "h2", "h3", "h4"])
    partes = [
        titulo.get_text(" ", strip=True) if titulo is not None else "",
        nodo.get_text(" ", strip=True),
        nodo.parent.get_text(" ", strip=True) if nodo.parent is not None else "",
    ]
    return " ".join(partes)[:MERCADO_CONTEXTO_CANAL]


def canales_de_html(html: str, url: str) -> list[Canal]:
    """Canales de una página: enlaces ``wa.me`` y ``tel:`` y números escritos en el texto."""
    soup = BeautifulSoup(html, "lxml")
    vistos: dict[tuple[str, str], Canal] = {}

    def agregar(tipo: TipoCanal, valor: str, contexto: str) -> None:
        vistos.setdefault((tipo, valor), Canal(tipo, valor, servicio_de(contexto), url))

    for a in soup.find_all("a", href=True):
        href = str(a["href"]).strip()
        if href.lower().startswith("tel:"):
            tel = _desde_tel(href)
            if tel:
                agregar(tel[0], tel[1], _contexto(a))
        elif (numero := _desde_whatsapp(href)) is not None:
            agregar("whatsapp", numero, _contexto(a))
    for nodo in soup.find_all(string=True):
        texto = str(nodo)
        if not re.search(r"\d", texto) or getattr(nodo.parent, "name", "") in {"script", "style"}:
            continue
        contexto = _contexto(nodo.parent) if isinstance(nodo.parent, Tag) else texto
        for m in _LINEA_CORTA.finditer(texto):
            agregar("linea_corta", f"#{m.group(1)}", contexto)
        for m in _LINEA_NACIONAL.finditer(texto):
            agregar("linea_nacional", f"018000{m.group(1)}{m.group(2)}", contexto)
        for m in _FIJO.finditer(texto):
            numero = normalizar_numero("".join(m.groups()))
            if numero:
                agregar("fijo", numero, contexto)
    return list(vistos.values())


def agregar_canales(
    paginas: Iterable[list[Canal]], min_fraccion: float = MERCADO_WHATSAPP_MIN_FRACCION
) -> list[CanalAgregado]:
    """Une los canales de todas las páginas de una aseguradora y aplica la regla de privacidad.

    Celulares y WhatsApp solo quedan si aparecen en al menos ``min_fraccion`` de las páginas
    (canal oficial del sitio); líneas cortas, ``01 8000`` y fijos quedan siempre. El orden es por
    número de páginas (el canal más visible primero).
    """
    lista = list(paginas)
    agregados: dict[tuple[str, str], CanalAgregado] = {}
    for canales in lista:
        for c in canales:
            a = agregados.setdefault((c.tipo, c.valor), CanalAgregado(c.tipo, c.valor))
            a.servicios.add(c.servicio)
            a.fuentes.append(c.fuente)
            a.paginas += 1  # canales_de_html ya deja un canal por página
    minimo = math.ceil(min_fraccion * len(lista))
    personales = {"whatsapp", "celular"}
    utiles = [a for a in agregados.values() if a.tipo not in personales or a.paginas >= minimo]
    return sorted(utiles, key=lambda a: (-a.paginas, a.tipo, a.valor))


# Preferencia entre teléfonos para atender (marcar desde el celular): corta > 01 8000 > fijo > celular.
_ORDEN_TELEFONO: dict[str, int] = {"linea_corta": 0, "linea_nacional": 1, "fijo": 2, "celular": 3}


def elegir(
    canales: Iterable[CanalAgregado], servicio: Servicio, maximo: int
) -> tuple[CanalAgregado | None, list[CanalAgregado]]:
    """El WhatsApp y los teléfonos más adecuados para un servicio.

    Primero los que el sitio asocia a ese servicio; si no hay, los generales (línea general).
    Los de ventas nunca se usan para atender un siniestro o una solicitud.
    """
    lista = [c for c in canales if c.servicios != {"ventas"}]

    def puntaje(c: CanalAgregado) -> tuple[int, int, int]:
        especifico = 0 if servicio in c.servicios else 1 if "general" in c.servicios else 2
        return (especifico, _ORDEN_TELEFONO.get(c.tipo, 0), -c.paginas)

    whatsapps = sorted((c for c in lista if c.tipo == "whatsapp"), key=puntaje)
    telefonos = sorted((c for c in lista if c.tipo != "whatsapp"), key=puntaje)
    return (whatsapps[0] if whatsapps else None), telefonos[:maximo]


def como_dict(c: CanalAgregado) -> dict[str, object]:
    """Canal agregado en JSON (para ``canales.json``)."""
    return {
        "tipo": c.tipo,
        "valor": c.valor,
        "servicios": sorted(c.servicios),
        "fuentes": sorted(set(c.fuentes)),
        "paginas": c.paginas,
    }


def desde_dict(d: dict[str, object]) -> CanalAgregado:
    """Canal agregado leído de ``canales.json``."""
    fuentes = d.get("fuentes", [])
    servicios = d.get("servicios", [])
    tipo = str(d["tipo"])
    if tipo not in TIPOS:
        raise ValueError(f"Tipo de canal desconocido: «{tipo}»")
    return CanalAgregado(
        tipo=cast(TipoCanal, tipo),
        valor=str(d["valor"]),
        servicios={str(s) for s in servicios} if isinstance(servicios, list) else set(),
        fuentes=[str(f) for f in fuentes] if isinstance(fuentes, list) else [],
        paginas=int(str(d.get("paginas", 1))),
    )


def enlace_telefono(c: CanalAgregado) -> str:
    """URI ``tel:`` para marcar desde el celular (``#`` codificado como ``%23``)."""
    if c.tipo == "linea_corta":
        return f"tel:%23{c.valor.lstrip('#')}"
    return f"tel:+{c.valor}" if c.valor.startswith("57") else f"tel:{c.valor}"

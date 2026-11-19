"""WhatsApp oficial de cada aseguradora, leído de sus propias páginas públicas.

Ningún número se escribe a mano: sale de los enlaces ``wa.me`` / ``api.whatsapp.com`` que la
aseguradora publica en su sitio (capa Bronze). Con él, la interfaz arma un enlace de traspaso
(``wa.me/<número>?text=<resumen>``) que la persona abre y envía desde su propia cuenta.
"""

import math
import re
from collections import Counter
from collections.abc import Iterable
from urllib.parse import parse_qs, quote, unquote, urlsplit

from bs4 import BeautifulSoup

from sb_asistente.config import MERCADO_WHATSAPP_MIN_FRACCION, WHATSAPP_MAX_TEXTO

INDICATIVO_CO = "57"
# Celular colombiano (3xx xxx xxxx) o fijo nacional (60x xxx xxxx), con o sin el 57.
NUMERO_CO = re.compile(r"^(57)?(3\d{9}|60\d{8})$")


def normalizar_numero(crudo: str) -> str | None:
    """Número en formato internacional sin «+» (``573001234567``) o None si no es de Colombia."""
    digitos = re.sub(r"\D", "", unquote(crudo))
    coincidencia = NUMERO_CO.match(digitos)
    if not coincidencia:
        return None
    return f"{INDICATIVO_CO}{coincidencia.group(2)}"


def _numero_de_enlace(href: str) -> str | None:
    """Número de un enlace de WhatsApp (``wa.me/57…``, ``api.whatsapp.com/send?phone=…``)."""
    partes = urlsplit(href.strip())
    host = partes.netloc.lower().removeprefix("www.")
    if host == "wa.me":
        return normalizar_numero(partes.path.strip("/").split("/")[0])
    if host in {"api.whatsapp.com", "web.whatsapp.com", "whatsapp.com"}:
        telefono = parse_qs(partes.query).get("phone", [""])[0]
        return normalizar_numero(telefono)
    return None


def whatsapp_de_html(html: str) -> list[str]:
    """Números de WhatsApp enlazados en una página, sin repetir y en orden de aparición."""
    soup = BeautifulSoup(html, "lxml")
    numeros = (_numero_de_enlace(a["href"]) for a in soup.find_all("a", href=True))
    return list(dict.fromkeys(n for n in numeros if n))


def whatsapp_principal(
    paginas: Iterable[list[str]], min_fraccion: float = MERCADO_WHATSAPP_MIN_FRACCION
) -> list[str]:
    """WhatsApp oficial de una aseguradora: los números que enlaza la mayoría de sus páginas.

    Un número del encabezado o del pie aparece en casi todas las páginas; el de un asesor, en una
    o dos. Solo se guardan los que aparecen en al menos ``min_fraccion`` de las páginas, para no
    recoger números personales (Ley 1581). Orden: el más enlazado primero.
    """
    lista = list(paginas)
    conteo: Counter[str] = Counter()
    for numeros in lista:
        conteo.update(set(numeros))
    minimo = math.ceil(min_fraccion * len(lista))
    return [n for n, veces in conteo.most_common() if veces >= minimo]


def enlace_whatsapp(numero: str, texto: str) -> str:
    """Enlace de traspaso ``https://wa.me/<número>?text=<texto>`` (el texto se recorta y se codifica)."""
    limpio = normalizar_numero(numero)
    if limpio is None:
        raise ValueError(f"Número de WhatsApp no válido para Colombia: «{numero}»")
    recortado = texto.strip()[:WHATSAPP_MAX_TEXTO]
    return f"https://wa.me/{limpio}?text={quote(recortado)}"

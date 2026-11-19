"""Alcance, prioridad y sección de las páginas de cualquier aseguradora (sin reglas por sitio).

El pipeline principal usa reglas escritas para segurosbolivar.com. Aquí las reglas son
genéricas: palabras de la ruta y del título que significan lo mismo en cualquier sitio de
seguros en Colombia. Las secciones son las mismas del corpus principal, para que el buscador,
el clasificador y la interfaz las traten igual.
"""

import re
import unicodedata
from collections.abc import Iterable

from sb_asistente.model.scraping.discover import path_of

# Fuera del alcance PERSONAS + CANALES (igual criterio que la Fase 1): empresas, inversionistas,
# legales extensos, noticias y portales transaccionales.
EXCLUIR_GENERICO: tuple[str, ...] = (
    r"(^|/)(empresas?|pymes?|corporativ\w*|negocios|grandes-empresas)(/|$)",
    r"(^|/)(inversionistas|relacion-con-inversionistas|gobierno-corporativo|informes?-financier\w*)(/|$)",
    r"(^|/)(proveedores|reaseguro\w*|intermediarios|corredores|agentes|asesores-comerciales)(/|$)",
    r"(^|/)(blog|noticias|prensa|sala-de-prensa|articulos|eventos)(/|$)",
    r"(^|/)(trabaj[ae]-con-nosotros|empleo|vacantes|talento)(/|$)",
    r"(^|/)(login|ingreso|iniciar-sesion|mi-cuenta|portal|oficina-virtual|sucursal-virtual)(/|$)",
    # Portales transaccionales (AGENTS.md): cotizar, comprar, pagar, radicar o llenar formularios.
    r"(^|/)(cotiza\w*|cotizacion\w*|compra\w*|checkout|carrito|simulador\w*|formularios?)(/|$|-)",
    r"(^|/)(pagos?|pago-en-linea|pagos-en-linea|pse|paga-\w+|pague-\w+)(/|$|-)",
    r"(^|/)(radica\w*|reportar?-siniestro\w*|aviso-de-siniestro\w*|tramites?-en-linea)(/|$|-)",
    r"(politica|terminos|aviso)-de-(privacidad|uso|tratamiento)|tratamiento-de-datos|habeas-data",
    r"\.(pdf|jpg|jpeg|png|zip|xml|docx?|xlsx?)$",
    r"(^|/)(en|english|pt)(/|$)",
)

# Sección temática por palabras de la ruta y del título; la primera regla que coincide gana.
REGLAS_SECCION: tuple[tuple[str, str], ...] = (
    (
        r"canal(es)?-de-atencion|contact|pqr|defensor|linea-de-atencion|oficinas|reclam|siniestr|"
        r"medios-de-pago|atencion-al-cliente|servicio-al-cliente",
        "canales_y_servicio",
    ),
    (r"\barl\b|riesgos-laborales|riesgos-profesionales", "arl"),
    (r"soat|vehicul|autos?\b|carro|moto|movilidad|bicicleta|patineta", "movilidad"),
    (r"hogar|vivienda|casa|arrendamiento|arriendo|mascota|hurto-residencial", "hogar_y_mascotas"),
    (
        r"\bvida\b|vida-|exequial|accidentes-personales|educativ|ahorro|pension|renta|desempleo|deudor",
        "vida_y_ahorro",
    ),
    (r"salud|medic|hospital|cancer|enfermedad|odontolog|plan-complementario", "salud"),
    (r"quienes-somos|nosotros|historia|acerca-de|sobre-nosotros", "institucional"),
)
SECCION_POR_DEFECTO = "otros"

# Palabras que delatan una página de producto para personas (se capturan primero).
PALABRAS_PRODUCTO: tuple[str, ...] = (
    "seguro",
    "soat",
    "auto",
    "vehiculo",
    "moto",
    "hogar",
    "vida",
    "salud",
    "mascota",
    "arriendo",
    "arrendamiento",
    "accidente",
    "exequial",
    "cancer",
    "viaje",
    "personas",
    "canales",
    "atencion",
    "siniestro",
    "reclamacion",
    "asistencia",
    "arl",
    "plan",
)


def _plano(texto: str) -> str:
    """Minúsculas sin tildes, con espacios y guiones bajos como guiones (para las reglas)."""
    sin_tildes = unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[\s_]+", "-", sin_tildes)


def en_alcance(url: str, prefijo: str = "", excluir: Iterable[str] = EXCLUIR_GENERICO) -> bool:
    """True si la URL es de personas o canales y está bajo el prefijo (si la aseguradora lo usa)."""
    ruta = path_of(url)
    if prefijo and not (ruta == prefijo or ruta.startswith(f"{prefijo}/")):
        return False
    plana = _plano(ruta)
    return not any(re.search(p, plana) for p in excluir)


def prioridad(url: str) -> int:
    """Cuántas palabras de producto tiene la ruta (más alto = se captura antes)."""
    plana = _plano(path_of(url))
    return sum(1 for p in PALABRAS_PRODUCTO if p in plana)


def ordenar_por_prioridad(urls: Iterable[str], maximo: int) -> list[str]:
    """Las ``maximo`` URLs más relevantes; a igual prioridad, las de ruta más corta (más generales)."""
    unicas = list(dict.fromkeys(urls))
    return sorted(unicas, key=lambda u: (-prioridad(u), len(path_of(u)), u))[:maximo]


def clasificar_seccion(url: str, titulo: str = "") -> str:
    """Sección temática de una página según su ruta y, si la ruta no basta, su título."""
    for texto in (path_of(url), titulo):
        plano = _plano(texto)
        for patron, seccion in REGLAS_SECCION:
            if re.search(patron, plano):
                return seccion
    if path_of(url) == "/":
        return "institucional"
    return SECCION_POR_DEFECTO

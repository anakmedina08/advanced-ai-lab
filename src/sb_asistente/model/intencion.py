"""Clasificador de intención y extractor de perfil para el chat (línea base por reglas).

Decide a qué herramienta va cada mensaje del chat antes de gastar tokens:

- ``conocimiento``: dudas sobre seguros, coberturas o canales → Q&A con fuentes.
- ``recomendacion``: el usuario pide qué seguro le conviene → recomendador.
- ``saludo``: saludos o agradecimientos cortos → respuesta fija.
- ``fuera_de_alcance``: temas ajenos a seguros → respuesta fija, sin LLM.

También detecta la sección temática (para orientar la búsqueda) y el perfil que el usuario
describe («tengo carro y un perro») para recomendar sin pedir datos personales. Es la línea
base interpretable de la tarea T-27; el modelo entrenado deberá superarla en el mismo banco.
"""

import re
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Final, Literal

Etiqueta = Literal["conocimiento", "recomendacion", "saludo", "fuera_de_alcance"]

_RECOMENDACION: Final[tuple[str, ...]] = (
    r"\brecomiend",
    r"\brecomendaci",
    r"\bsugier",
    r"\bme conviene",
    r"\bque seguros? (me|nos) (sirve|conviene|recomienda|sugiere)",
    r"\bque seguros? (deberia|debo|puedo) (tener|tomar|comprar|adquirir)",
    r"\bcual(es)? seguros? (me|nos|deberia|debo)",
    r"\bque me ofrecen\b",
    r"\bque seguros? necesito",
)
_SALUDO: Final[tuple[str, ...]] = (
    r"^(hola|buen[oa]s? (dias|tardes|noches)|hey|saludos)\b",
    r"^(muchas )?gracias\b",
    r"^(ok|listo|perfecto|chao|adios)\b",
)
_DOMINIO: Final[tuple[str, ...]] = (
    r"segur",
    r"poliza",
    r"\bsoat\b",
    r"cobertur",
    r"cubr",
    r"siniestr",
    r"reclam",
    r"\barl\b",
    r"asegur",
    r"bolivar",
    r"whatsapp",
    r"\blinea\b",
    r"telefon",
    r"\bcanal",
    r"atencion",
    r"\bpqr",
    r"oficina",
    r"\bsede",
    r"horario",
    r"\bpag[oa]r?\b",
    r"\bprima\b",
    r"asistencia",
    r"\bgrua\b",
    r"hogar",
    r"mascota",
    r"\bvida\b",
    r"\bsalud\b",
    r"vehicul",
    r"\bcarro",
    r"\bmoto",
    r"\bauto",
    r"accidente",
    r"\bcredito",
    r"\bdefensor",
    r"\bcontact",
)
_FUERA: Final[tuple[str, ...]] = (
    r"\bmundial\b",
    r"\bfutbol\b",
    r"\breceta",
    r"\bclima\b",
    r"\bpelicula",
    r"\bcancion",
    r"\bchiste",
    r"\bprogram(a|ar|acion) en\b",
    r"\bcodigo (en|python|java)",
    r"\bpresidente\b",
    r"\belecciones\b",
    r"\bbitcoin\b",
    r"\bacciones de\b",
    r"\bhoroscopo\b",
)
_SECCIONES: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    (
        "canales_y_servicio",
        (
            r"whatsapp",
            r"\blinea\b",
            r"telefon",
            r"\bcanal",
            r"atencion",
            r"\bpqr",
            r"oficina",
            r"\bsede",
            r"horario",
            r"\bpag[oa]r?\b",
            r"defensor",
            r"contact",
        ),
    ),
    ("movilidad", (r"\bsoat\b", r"vehicul", r"\bcarro", r"\bmoto", r"\bauto", r"bicicleta", r"\bgrua\b")),
    (
        "hogar_y_mascotas",
        (r"hogar", r"\bcasa\b", r"apartamento", r"arriend", r"mascota", r"\bperro", r"\bgato"),
    ),
    ("vida_y_ahorro", (r"\bvida\b", r"\brenta\b", r"ahorro", r"accidente", r"credito", r"educacion")),
    ("salud", (r"\bsalud\b", r"medic", r"cancer", r"hospital", r"clinica")),
    ("arl", (r"\barl\b", r"riesgos laborales", r"empleador", r"independiente")),
)


def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes ni signos, espacios simples (para comparar con las reglas)."""
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", sin_tildes)).strip()


def _legible(patron: str) -> str:
    """Convierte un patrón en una palabra legible para la traza del chat."""
    sin_grupos = re.sub(r"\(.*?\)|\[.*?\]", "", patron)
    return re.sub(r"\\b|[\^$?|\\]", "", sin_grupos).strip()


def _coincidencias(texto: str, patrones: tuple[str, ...]) -> list[str]:
    return [p for p in patrones if re.search(p, texto)]


@dataclass(slots=True)
class Perfil:
    """Perfil que el usuario describe en el mensaje (``None`` = no lo dijo)."""

    vehiculo: str | None = None  # ninguno | carro | moto | electrico
    vivienda: str | None = None  # propia | arrendada | familiar
    tiene_mascota: bool | None = None
    tiene_credito: bool | None = None

    def conocido(self) -> dict[str, object]:
        """Solo los campos que el usuario mencionó."""
        return {k: v for k, v in asdict(self).items() if v is not None}


def extraer_perfil(texto: str) -> Perfil:
    """Detecta vehículo, vivienda, mascota y crédito en un texto libre."""
    t = normalizar(texto)
    perfil = Perfil()
    if re.search(r"\b(no tengo|sin) (carro|vehiculo|moto|auto)", t):
        perfil.vehiculo = "ninguno"
    elif re.search(r"electric|hibrid", t):
        perfil.vehiculo = "electrico"
    elif re.search(r"\bmoto", t):
        perfil.vehiculo = "moto"
    elif re.search(r"\b(carro|auto|automovil|vehiculo|camioneta)", t):
        perfil.vehiculo = "carro"
    if re.search(r"arriend|arrendad|alquil|pago renta", t):
        perfil.vivienda = "arrendada"
    elif re.search(r"(casa|apartamento|vivienda) propi|\bpropia\b|\bpropio\b", t):
        perfil.vivienda = "propia"
    elif re.search(r"con (mis|mi) (papas|padres|familia|mama|papa)|vivienda familiar", t):
        perfil.vivienda = "familiar"
    if re.search(r"\b(no tengo|sin) (mascota|perro|gato)", t):
        perfil.tiene_mascota = False
    elif re.search(r"\b(perr[oa]s?|gat[oa]s?|mascotas?)\b", t):
        perfil.tiene_mascota = True
    if re.search(r"\b(no tengo|sin) (credito|prestamo|deuda)", t):
        perfil.tiene_credito = False
    elif re.search(r"\b(credito|prestamo|hipoteca|leasing)", t):
        perfil.tiene_credito = True
    return perfil


@dataclass(slots=True)
class Intencion:
    """Resultado del clasificador, con las señales que lo explican."""

    etiqueta: Etiqueta
    confianza: float
    seccion: str | None
    perfil: Perfil
    senales: list[str] = field(default_factory=list)


def clasificar(mensaje: str) -> Intencion:
    """Clasifica un mensaje del chat.

    Prioridad: recomendación explícita > saludo corto > fuera de alcance sin vocabulario de
    seguros > conocimiento (por defecto: el Q&A ya tiene la respuesta de no-información).
    """
    if not mensaje.strip():
        raise ValueError("El mensaje está vacío.")
    t = normalizar(mensaje)
    perfil = extraer_perfil(mensaje)
    dominio = _coincidencias(t, _DOMINIO)
    secciones = [(nombre, len(_coincidencias(t, pats))) for nombre, pats in _SECCIONES]
    nombre, puntos = max(secciones, key=lambda s: s[1])
    seccion = nombre if puntos else None

    reco = _coincidencias(t, _RECOMENDACION)
    if reco:
        confianza = 0.9 if perfil.conocido() else 0.75
        senal = f"pide recomendación («{_legible(reco[0])}…»)"
        return Intencion("recomendacion", confianza, seccion, perfil, [senal])
    saludo = _coincidencias(t, _SALUDO)
    if saludo and len(t.split()) <= 6 and not dominio:
        return Intencion("saludo", 0.95, None, perfil, ["saludo corto"])
    fuera = _coincidencias(t, _FUERA)
    if fuera and not dominio:
        return Intencion("fuera_de_alcance", 0.9, None, perfil, [f"tema ajeno («{_legible(fuera[0])}»)"])
    if not dominio:
        return Intencion("conocimiento", 0.4, seccion, perfil, ["sin vocabulario de seguros: el Q&A decide"])
    confianza = min(0.95, 0.6 + 0.1 * len(dominio))
    senales = [f"vocabulario de seguros ({len(dominio)})"] + ([f"sección: {seccion}"] if seccion else [])
    return Intencion("conocimiento", round(confianza, 2), seccion, perfil, senales)

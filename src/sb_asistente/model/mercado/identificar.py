"""¿Con qué aseguradora está la persona? Pistas de un texto o de un documento (SPEC-071).

No hay una fuente pública que diga con qué aseguradora está alguien (no hay API de pólizas y el
asistente no pide cédula). Lo que sí hay son pistas que la persona tiene a mano: el recibo de
pago, el débito en el extracto, la carátula de la póliza, el correo o la app de la aseguradora.
Este módulo cruza ese texto con el registro (``aseguradoras.toml``) y devuelve solo lo que es del
registro: id, nombre y qué tipo de pista coincidió. El texto leído nunca sale de aquí: ni se
devuelve, ni se guarda, ni se registra en logs (Ley 1581).
"""

import re
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Literal

from sb_asistente.model.llm.retrieval import normalize_words
from sb_asistente.model.mercado.canales import Servicio, servicio_de
from sb_asistente.model.mercado.registro import Aseguradora

Senal = Literal["nombre", "dominio", "coincidencia"]
Confianza = Literal["alta", "media", "baja", "ninguna"]

# Alias de una palabra que en un documento suelen ser otra cosa: «Bolívar» es un departamento, una
# avenida y una localidad. En un documento cuentan solo dentro de una frase más larga del registro
# («seguros bolívar»); en lo que escribe la persona sí cuentan (ahí sí habla de la aseguradora).
AMBIGUAS_EN_DOCUMENTO: frozenset[str] = frozenset({"bolivar"})

_DOMINIO = re.compile(r"(?:[a-z0-9-]+\.)+[a-z]{2,}", re.IGNORECASE)
PESO: dict[Senal, float] = {"nombre": 1.0, "dominio": 1.5, "coincidencia": 0.75}

# --- Coincidencia por palabras (no depende de la razón social exacta) ---------------------------
# Una razón social cambia («Seguros Comerciales Bolívar S.A.», «Bolívar Seguros Generales»), pero
# conserva la palabra que distingue a la compañía. Esa palabra cuenta si aparece cerca de una
# palabra de seguros: «Seguros Comerciales Bolívar» sí; «Av. Simón Bolívar» no. También tolera
# errores del OCR («MAPFKE», «B0LIVAR») con una similitud mínima.
GENERICAS: frozenset[str] = frozenset(
    {"seguros", "seguro", "compania", "cia", "aseguradora", "colombia", "generales", "vida", "arl",
     "international", "internacional", "comerciales", "grupo", "colombiana", "nacional", "proteccion"}
)  # fmt: skip
CONTEXTO: frozenset[str] = frozenset(
    {
        "seguros",
        "seguro",
        "aseguradora",
        "compania",
        "cia",
        "poliza",
        "polizas",
        "generales",
        "nit",
        "asegurado",
    }
)
VENTANA_CONTEXTO = 4  # palabras antes o después
SIMILITUD_MINIMA = 0.8  # parecido entre palabras para tolerar errores del OCR
LARGO_MINIMO_DIFUSO = 5  # palabras más cortas solo cuentan si son idénticas
MENCIONES_ALTA = 2  # el nombre repetido en el documento (encabezado y pie) también es confianza alta


@dataclass(frozen=True, slots=True)
class Candidata:
    """Una aseguradora del registro que aparece en las pistas."""

    id: str
    nombre: str
    sitio: str
    senales: tuple[Senal, ...]
    menciones: int

    @property
    def puntaje(self) -> float:
        """Más señales distintas y más menciones = más probable (el dominio pesa más que el nombre)."""
        return sum(PESO[s] for s in self.senales) + 0.25 * (self.menciones - 1)


@dataclass(frozen=True, slots=True)
class Identificacion:
    """Resultado: candidatas ordenadas, el servicio que sugiere el texto y qué tan claro quedó."""

    candidatas: tuple[Candidata, ...]
    servicio: Servicio | None
    confianza: Confianza

    @property
    def aseguradora(self) -> Candidata | None:
        """La candidata cuando no hay duda razonable (confianza alta o media)."""
        return self.candidatas[0] if self.confianza in ("alta", "media") else None


def _host(url: str) -> str:
    return url.split("//", 1)[-1].split("/", 1)[0].lower().removeprefix("www.")


def _frases(a: Aseguradora, documento: bool) -> list[tuple[str, ...]]:
    formas = {tuple(normalize_words(x)) for x in (a.nombre, *a.alias)}
    if documento:
        formas = {f for f in formas if not (len(f) == 1 and f[0] in AMBIGUAS_EN_DOCUMENTO)}
    return sorted((f for f in formas if f), key=len, reverse=True)


def distintivas(registro: Sequence[Aseguradora]) -> dict[str, frozenset[str]]:
    """Palabras que distinguen a cada aseguradora, calculadas desde el registro.

    Son las de su nombre y alias que no son genéricas ni se repiten en otra compañía: al agregar una
    aseguradora al TOML, sus palabras distintivas salen solas.
    """
    por_id = {
        a.id: {w for x in (a.nombre, *a.alias) for w in normalize_words(x) if w not in GENERICAS}
        for a in registro
    }
    veces = Counter(w for palabras in por_id.values() for w in palabras)
    return {ident: frozenset(w for w in palabras if veces[w] == 1) for ident, palabras in por_id.items()}


def _parecida(palabra: str, objetivos: frozenset[str]) -> bool:
    if palabra in objetivos:
        return True
    if len(palabra) < LARGO_MINIMO_DIFUSO:
        return False
    return any(
        abs(len(palabra) - len(o)) <= 2 and SequenceMatcher(None, palabra, o).ratio() >= SIMILITUD_MINIMA
        for o in objetivos
    )


def _coincidencias(palabras: Sequence[str], objetivos: frozenset[str]) -> int:
    """Veces que una palabra distintiva (o una muy parecida) aparece cerca de una palabra de seguros."""
    total = 0
    for i, palabra in enumerate(palabras):
        if not _parecida(palabra, objetivos):
            continue
        vecinas = palabras[max(0, i - VENTANA_CONTEXTO) : i] + palabras[i + 1 : i + 1 + VENTANA_CONTEXTO]
        total += any(v in CONTEXTO for v in vecinas)
    return total


def _menciones(palabras: Sequence[str], frase: tuple[str, ...]) -> int:
    n = len(frase)
    return sum(1 for i in range(len(palabras) - n + 1) if tuple(palabras[i : i + n]) == frase)


def _dominios(texto: str) -> set[str]:
    """Dominios que aparecen en el texto (correos y enlaces), sin «www.»."""
    return {d.lower().removeprefix("www.") for d in _DOMINIO.findall(texto)}


def _confianza(candidatas: Sequence[Candidata]) -> Confianza:
    if not candidatas:
        return "ninguna"
    primera = candidatas[0]
    if len(candidatas) > 1 and candidatas[1].puntaje >= primera.puntaje:
        return "baja"  # empate: el recibo nombra a dos (p. ej. el banco y la aseguradora con el mismo peso)
    if primera.senales == ("coincidencia",):
        # Solo por palabras parecidas: un documento real repite la razón social (encabezado y pie);
        # una sola coincidencia («seguros… estado civil») se le muestra a la persona para que confirme.
        return "media" if primera.menciones >= MENCIONES_ALTA else "baja"
    if "dominio" in primera.senales or primera.menciones >= MENCIONES_ALTA:
        return "alta"
    return "media"


def identificar(texto: str, registro: Iterable[Aseguradora], documento: bool = False) -> Identificacion:
    """Aseguradoras del registro que aparecen en el texto, de la más a la menos probable.

    Args:
        texto: Lo que escribió la persona o el texto leído de su documento.
        registro: Aseguradoras registradas.
        documento: True si el texto viene de un documento (descarta alias ambiguos como «Bolívar»).

    """
    registro = list(registro)
    palabras = normalize_words(texto)
    dominios = _dominios(texto)
    propias = distintivas(registro)
    candidatas: list[Candidata] = []
    for a in registro:
        senales: list[Senal] = []
        menciones = 0
        for frase in _frases(a, documento):
            veces = _menciones(palabras, frase)
            if veces:
                menciones = max(menciones, veces)
                if "nombre" not in senales:
                    senales.append("nombre")
        if not senales and propias[a.id]:
            veces = _coincidencias(palabras, propias[a.id])
            if veces:
                senales.append("coincidencia")
                menciones = veces
        propio = _host(a.sitio) if a.sitio else ""
        if propio and any(d == propio or d.endswith("." + propio) for d in dominios):
            senales.append("dominio")
            menciones = max(menciones, 1)
        if senales:
            candidatas.append(Candidata(a.id, a.nombre, a.sitio, tuple(senales), menciones))
    candidatas.sort(key=lambda c: c.puntaje, reverse=True)
    servicio = servicio_de(texto)
    return Identificacion(
        candidatas=tuple(candidatas),
        servicio=None if servicio in ("general", "ventas") else servicio,
        confianza=_confianza(candidatas),
    )

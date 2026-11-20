"""¿Con qué aseguradora está la persona? Pistas de un texto o de un documento (SPEC-071).

No hay una fuente pública que diga con qué aseguradora está alguien (no hay API de pólizas y el
asistente no pide cédula). Lo que sí hay son pistas que la persona tiene a mano: el recibo de
pago, el débito en el extracto, la carátula de la póliza, el correo o la app de la aseguradora.
Este módulo cruza ese texto con el registro (``aseguradoras.toml``) y devuelve solo lo que es del
registro: id, nombre y qué tipo de pista coincidió. El texto leído nunca sale de aquí: ni se
devuelve, ni se guarda, ni se registra en logs (Ley 1581).
"""

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Literal

from sb_asistente.model.llm.retrieval import normalize_words
from sb_asistente.model.mercado.canales import Servicio, servicio_de
from sb_asistente.model.mercado.registro import Aseguradora

Senal = Literal["nombre", "dominio"]
Confianza = Literal["alta", "media", "baja", "ninguna"]

# Alias de una palabra que en un documento suelen ser otra cosa: «Bolívar» es un departamento, una
# avenida y una localidad. En un documento cuentan solo dentro de una frase más larga del registro
# («seguros bolívar»); en lo que escribe la persona sí cuentan (ahí sí habla de la aseguradora).
AMBIGUAS_EN_DOCUMENTO: frozenset[str] = frozenset({"bolivar"})

_DOMINIO = re.compile(r"(?:[a-z0-9-]+\.)+[a-z]{2,}", re.IGNORECASE)
PESO: dict[Senal, float] = {"nombre": 1.0, "dominio": 1.5}


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
    if "dominio" in primera.senales or primera.menciones >= 2:  # noqa: PLR2004 - dos menciones
        return "alta"
    return "media"


def identificar(texto: str, registro: Iterable[Aseguradora], documento: bool = False) -> Identificacion:
    """Aseguradoras del registro que aparecen en el texto, de la más a la menos probable.

    Args:
        texto: Lo que escribió la persona o el texto leído de su documento.
        registro: Aseguradoras registradas.
        documento: True si el texto viene de un documento (descarta alias ambiguos como «Bolívar»).

    """
    palabras = normalize_words(texto)
    dominios = _dominios(texto)
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

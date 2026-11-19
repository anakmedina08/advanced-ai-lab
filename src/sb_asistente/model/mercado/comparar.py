"""Comparación entre aseguradoras con el buscador híbrido (sin LLM: solo recuperación).

Para cada aseguradora se buscan sus mejores pasajes sobre la misma consulta; el resultado es la
materia prima de una tabla comparativa (la skill ``comparar-seguros`` o la interfaz la redactan).
Solo compara lo que cada compañía publica: coberturas, requisitos y canales, no precios.
"""

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Protocol

from sb_asistente.config import (
    MERCADO_CANDIDATOS_POR_PAGINA,
    MERCADO_MAX_COMPARAR,
    MERCADO_MAX_POR_ASEGURADORA,
    MERCADO_POR_ASEGURADORA,
    RAG_K,
)
from sb_asistente.model.mercado.registro import Aseguradora
from sb_asistente.model.rag.hibrido import Fragmento


class Buscador(Protocol):
    """Lo que se usa del recuperador (``RecuperadorHibrido`` o un doble en las pruebas)."""

    def buscar(
        self, consulta: str, k: int = RAG_K, seccion: str | None = None, aseguradora: str | None = None
    ) -> list[Fragmento]:
        """Top-k pasajes de la consulta, opcionalmente de una sección y una aseguradora."""
        ...


@dataclass(frozen=True, slots=True)
class Oferta:
    """Lo que una aseguradora publica sobre la consulta."""

    aseguradora: str
    nombre: str
    fragmentos: tuple[Fragmento, ...]

    @property
    def tiene_informacion(self) -> bool:
        """True si el buscador encontró al menos un pasaje de esta aseguradora."""
        return bool(self.fragmentos)


def comparar(
    buscador: Buscador,
    consulta: str,
    aseguradoras: Sequence[Aseguradora],
    por_aseguradora: int = MERCADO_POR_ASEGURADORA,
    seccion: str | None = None,
) -> list[Oferta]:
    """Mejores pasajes de cada aseguradora para la misma consulta; primero las que tienen información."""
    if not consulta.strip():
        raise ValueError("La consulta está vacía.")
    if not aseguradoras:
        raise ValueError("Indique al menos una aseguradora.")
    if len(aseguradoras) > MERCADO_MAX_COMPARAR:
        raise ValueError(f"Compare como máximo {MERCADO_MAX_COMPARAR} aseguradoras a la vez.")
    if not 1 <= por_aseguradora <= MERCADO_MAX_POR_ASEGURADORA:
        raise ValueError(f"por_aseguradora debe estar entre 1 y {MERCADO_MAX_POR_ASEGURADORA}.")
    ofertas = []
    for a in aseguradoras:
        # Se piden más pasajes y se deja uno por página: dos trozos de la misma página no comparan nada.
        candidatos = buscador.buscar(
            consulta, k=por_aseguradora * MERCADO_CANDIDATOS_POR_PAGINA, seccion=seccion, aseguradora=a.id
        )
        ofertas.append(Oferta(a.id, a.nombre, tuple(_una_por_pagina(candidatos)[:por_aseguradora])))
    return sorted(ofertas, key=lambda o: not o.tiene_informacion)


def _una_por_pagina(fragmentos: Iterable[Fragmento]) -> list[Fragmento]:
    """El mejor fragmento de cada URL, en el orden del buscador."""
    vistas: set[str] = set()
    unicos = []
    for f in fragmentos:
        if f.url not in vistas:
            vistas.add(f.url)
            unicos.append(f)
    return unicos


def cobertura_por_seccion(chunks: Iterable[dict[str, object]]) -> dict[str, dict[str, int]]:
    """Documentos por aseguradora y sección: qué compañías publican cada tipo de seguro."""
    conteo: dict[str, Counter[str]] = {}
    vistos: set[tuple[str, str]] = set()
    for c in chunks:
        aseguradora, doc = str(c.get("aseguradora", "")), str(c.get("doc_id", ""))
        if not aseguradora or (aseguradora, doc) in vistos:
            continue
        vistos.add((aseguradora, doc))
        conteo.setdefault(str(c.get("section", "otros")), Counter())[aseguradora] += 1
    return {seccion: dict(c.most_common()) for seccion, c in conteo.items()}

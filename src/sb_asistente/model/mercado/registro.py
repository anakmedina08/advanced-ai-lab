"""Registro de aseguradoras (``aseguradoras.toml``) y detección de cuáles nombra un mensaje.

El registro es la única lista de compañías del corpus de mercado: sumar una aseguradora es
agregar un bloque al TOML. Se valida al cargar (ids únicos, sitio https) para que un error de
tipeo falle en la carga y no a mitad del scraping.
"""

import re
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from sb_asistente.model.llm.retrieval import normalize_words

REGISTRO_TOML = Path(__file__).with_name("aseguradoras.toml")
ID_VALIDO = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class RegistroInvalidoError(ValueError):
    """El TOML del registro tiene un error (id repetido, sitio sin https, campo faltante)."""


@dataclass(frozen=True, slots=True)
class Aseguradora:
    """Una aseguradora del registro."""

    id: str
    nombre: str
    sitio: str = ""
    prefijo: str = ""
    alias: tuple[str, ...] = field(default_factory=tuple)
    verificado: bool = False
    activo: bool = True
    corpus_propio: bool = False
    nota: str = ""

    @property
    def dominio(self) -> str:
        """Host del sitio (``www.ejemplo.com``) o cadena vacía si no hay sitio."""
        return urlsplit(self.sitio).netloc

    @property
    def hace_scraping(self) -> bool:
        """True si el pipeline de mercado debe visitar su sitio."""
        return self.activo and bool(self.sitio) and not self.corpus_propio


def _aseguradora(datos: dict[str, object]) -> Aseguradora:
    """Convierte un bloque del TOML en ``Aseguradora`` y valida sus campos."""
    ident = str(datos.get("id", ""))
    if not ID_VALIDO.match(ident):
        raise RegistroInvalidoError(f"id inválido: «{ident}» (minúsculas, números y guiones)")
    nombre = str(datos.get("nombre", "")).strip()
    if not nombre:
        raise RegistroInvalidoError(f"«{ident}» no tiene nombre")
    sitio = str(datos.get("sitio", "")).rstrip("/")
    if sitio and not (sitio.startswith("https://") and urlsplit(sitio).netloc):
        raise RegistroInvalidoError(f"«{ident}»: el sitio debe ser una URL https (recibido «{sitio}»)")
    prefijo = str(datos.get("prefijo", "")).rstrip("/")
    if prefijo and not prefijo.startswith("/"):
        raise RegistroInvalidoError(f"«{ident}»: el prefijo debe empezar con «/»")
    crudos = datos.get("alias", [])
    if not isinstance(crudos, list):
        raise RegistroInvalidoError(f"«{ident}»: alias debe ser una lista de textos")
    alias = tuple(str(a).strip().lower() for a in crudos if str(a).strip())
    return Aseguradora(
        id=ident,
        nombre=nombre,
        sitio=sitio,
        prefijo=prefijo,
        alias=alias,
        verificado=bool(datos.get("verificado", False)),
        activo=bool(datos.get("activo", True)),
        corpus_propio=bool(datos.get("corpus_propio", False)),
        nota=str(datos.get("nota", "")),
    )


def leer_registro(texto: str) -> list[Aseguradora]:
    """Lee el TOML del registro (texto) y devuelve las aseguradoras en su orden."""
    datos = tomllib.loads(texto)
    bloques = datos.get("aseguradora", [])
    if not isinstance(bloques, list) or not bloques:
        raise RegistroInvalidoError("El registro no tiene bloques [[aseguradora]]")
    aseguradoras = [_aseguradora(b) for b in bloques]
    vistos: set[str] = set()
    for a in aseguradoras:
        if a.id in vistos:
            raise RegistroInvalidoError(f"id repetido: «{a.id}»")
        vistos.add(a.id)
    return aseguradoras


def cargar_registro(ruta: Path = REGISTRO_TOML) -> list[Aseguradora]:
    """Carga el registro desde disco (por defecto, el TOML junto a este módulo)."""
    return leer_registro(ruta.read_text(encoding="utf-8"))


def por_id(registro: Iterable[Aseguradora]) -> dict[str, Aseguradora]:
    """Índice ``id → Aseguradora``."""
    return {a.id: a for a in registro}


def _frases(a: Aseguradora) -> list[tuple[str, ...]]:
    """Formas normalizadas en que se nombra una aseguradora (nombre y alias), como tuplas de palabras."""
    formas = {tuple(normalize_words(x)) for x in (a.nombre, *a.alias)}
    return sorted((f for f in formas if f), key=len, reverse=True)


def detectar(mensaje: str, registro: Iterable[Aseguradora]) -> list[str]:
    """Ids de las aseguradoras que nombra el mensaje, en el orden en que aparecen.

    Compara palabras completas (sin tildes ni mayúsculas): «sura» no coincide con «asegurarme»,
    y «seguros del estado» exige la frase entera, no solo «estado».
    """
    palabras = normalize_words(mensaje)
    encontradas: list[tuple[int, str]] = []
    for a in registro:
        for frase in _frases(a):
            n = len(frase)
            inicios = range(len(palabras) - n + 1)
            posicion = next((i for i in inicios if tuple(palabras[i : i + n]) == frase), None)
            if posicion is not None:
                encontradas.append((posicion, a.id))
                break
    return [ident for _, ident in sorted(encontradas)]

"""Memoria de largo plazo del agente: hechos del usuario en un Store con namespace.

- **Corto plazo** (otro módulo): el *checkpointer* guarda cada hilo por ``thread_id``.
- **Largo plazo** (este módulo): lo que el usuario dice de sí mismo («me llamo Ana», «trabajo
  en Carvajal», «tengo carro y un perro») se guarda en el namespace
  ``("usuarios", usuario_id, "perfil")`` y se recupera con ``store.search`` en **cualquier**
  hilo nuevo del mismo usuario.

Los hechos se extraen con reglas, sin LLM, y solo si el usuario los dice explícitamente.
Correos, teléfonos y números de documento nunca se guardan (Ley 1581 de 2012); el perfil se
puede consultar y borrar.
"""

import re
import sqlite3
from pathlib import Path
from typing import Final

from langgraph.store.base import BaseStore
from langgraph.store.sqlite import SqliteStore

from sb_asistente.model.intencion import extraer_perfil

USUARIO_VALIDO: Final = re.compile(r"^[A-Za-z0-9_-]{6,64}$")
_PALABRA = r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+"
_HASTA_FIN = r"(?=\s+y\s|[,.;!?]|$)"
_PATRONES: Final[dict[str, re.Pattern[str]]] = {
    "nombre": re.compile(
        rf"\b(?:me llamo|mi nombre es)\s+({_PALABRA}(?:\s+(?!y\b){_PALABRA})?)", re.IGNORECASE
    ),
    "empresa": re.compile(rf"\btrabajo (?:en|para)\s+(.{{2,40}}?){_HASTA_FIN}", re.IGNORECASE),
    "ciudad": re.compile(rf"\bvivo en\s+(.{{2,30}}?){_HASTA_FIN}", re.IGNORECASE),
}
_DATO_SENSIBLE: Final = re.compile(r"@|\d{5,}")


def namespace(usuario_id: str) -> tuple[str, str, str]:
    """Namespace del perfil de un usuario.

    Raises:
        ValueError: si el id no es seguro (6 a 64 letras, números, ``-`` o ``_``).

    """
    if not USUARIO_VALIDO.match(usuario_id):
        raise ValueError("usuario_id inválido (6 a 64 letras, números, - o _).")
    return ("usuarios", usuario_id, "perfil")


def extraer_hechos(mensaje: str) -> dict[str, str]:
    """Hechos explícitos del mensaje (nombre, empresa, ciudad y perfil de seguros)."""
    hechos: dict[str, str] = {}
    for clave, patron in _PATRONES.items():
        encontrado = patron.search(mensaje)
        if encontrado:
            valor = encontrado.group(1).strip(" .")
            if valor and not _DATO_SENSIBLE.search(valor):
                hechos[clave] = valor[:1].upper() + valor[1:]
    for clave, valor in extraer_perfil(mensaje).conocido().items():
        hechos[clave] = "sí" if valor is True else "no" if valor is False else str(valor)
    return hechos


class PerfilStore:
    """Lectura y escritura del perfil sobre cualquier ``BaseStore`` (SQLite o en memoria)."""

    def __init__(self, store: BaseStore) -> None:
        """Recibe el Store (inyectado para probar con ``InMemoryStore``)."""
        self.store = store

    def guardar(self, usuario_id: str, hechos: dict[str, str]) -> None:
        """Guarda (o actualiza) cada hecho como un ítem del namespace."""
        ns = namespace(usuario_id)
        for clave, valor in hechos.items():
            self.store.put(ns, clave, {"valor": valor})

    def leer(self, usuario_id: str) -> dict[str, str]:
        """Todos los hechos del usuario (``store.search`` sobre su namespace)."""
        return {
            i.key: str(i.value.get("valor", "")) for i in self.store.search(namespace(usuario_id), limit=50)
        }

    def borrar(self, usuario_id: str) -> int:
        """Borra el perfil completo y devuelve cuántos hechos había."""
        ns = namespace(usuario_id)
        claves = [i.key for i in self.store.search(ns, limit=50)]
        for clave in claves:
            self.store.delete(ns, clave)
        return len(claves)


def bloque_perfil(hechos: dict[str, str]) -> str:
    """Hechos como bloque delimitado para el prompt del sistema."""
    lineas = "\n".join(f"- {clave}: {valor}" for clave, valor in sorted(hechos.items()))
    return (
        '<perfil_usuario nota="lo que el usuario dijo de sí mismo en conversaciones anteriores">\n'
        f"{lineas}\n</perfil_usuario>"
    )


def abrir_store(ruta: Path) -> SqliteStore:
    """Store SQLite persistente (sobrevive al reinicio del proceso)."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    store = SqliteStore(sqlite3.connect(str(ruta), check_same_thread=False, isolation_level=None))
    store.setup()
    return store

"""Códigos de acceso con vencimiento y cupo para lo que gasta tokens (SPEC-072).

El sitio público (yellowdata) deja usar gratis todo lo que corre en local (YOLO, Tesseract,
canales, comparación, recomendador). Lo que llama a un LLM (el chat y el agente) exige un código
que un administrador genera con ``sb acceso crear``: dura unas horas y trae un cupo de mensajes.

- El código es aleatorio (``secrets``) y legible: ``YELO-7K3M-Q9TD`` (sin 0/O ni 1/I/L).
- Se guarda solo su hash SHA-256: quien lea la base no puede usar los códigos.
- Consumir es atómico (un ``UPDATE`` con la condición): dos pestañas no gastan más del cupo.
"""

import hashlib
import secrets
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

ALFABETO = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"  # sin 0/O, 1/I/L: se dictan sin confusión
PREFIJO = "YELO"
GRUPOS, LARGO_GRUPO = 2, 4

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS codigos (
    hash TEXT PRIMARY KEY,
    pista TEXT NOT NULL,
    creado TEXT NOT NULL,
    expira TEXT NOT NULL,
    cupo INTEGER NOT NULL,
    usados INTEGER NOT NULL DEFAULT 0,
    nota TEXT NOT NULL DEFAULT '',
    revocado INTEGER NOT NULL DEFAULT 0
)
"""


class AccesoDenegadoError(PermissionError):
    """El código falta, no existe, venció, se revocó o ya no tiene cupo."""


@dataclass(frozen=True, slots=True)
class Codigo:
    """Estado de un código (nunca el código en claro)."""

    pista: str  # últimos 4 caracteres, para reconocerlo en la lista
    creado: datetime
    expira: datetime
    cupo: int
    usados: int
    nota: str
    revocado: bool

    @property
    def restantes(self) -> int:
        """Mensajes que quedan."""
        return max(0, self.cupo - self.usados)

    def vigente(self, ahora: datetime) -> bool:
        """True si se puede usar ahora."""
        return not self.revocado and ahora < self.expira and self.restantes > 0


def normalizar(codigo: str) -> str:
    """Mayúsculas y sin espacios ni guiones: «yelo 7k3m-q9td» y «YELO-7K3M-Q9TD» son el mismo."""
    return "".join(c for c in codigo.upper() if c.isalnum())


def huella(codigo: str) -> str:
    """Hash SHA-256 del código normalizado (lo único que se guarda)."""
    return hashlib.sha256(normalizar(codigo).encode()).hexdigest()


def generar() -> str:
    """Código aleatorio criptográficamente seguro: ``YELO-XXXX-XXXX``."""
    grupos = ["".join(secrets.choice(ALFABETO) for _ in range(LARGO_GRUPO)) for _ in range(GRUPOS)]
    return "-".join([PREFIJO, *grupos])


def _fecha(texto: str) -> datetime:
    return datetime.fromisoformat(texto)


def _codigo(fila: sqlite3.Row) -> Codigo:
    return Codigo(
        pista=fila["pista"],
        creado=_fecha(fila["creado"]),
        expira=_fecha(fila["expira"]),
        cupo=fila["cupo"],
        usados=fila["usados"],
        nota=fila["nota"],
        revocado=bool(fila["revocado"]),
    )


class CodigosAcceso:
    """Códigos de acceso en SQLite (un archivo; las pruebas usan uno temporal)."""

    def __init__(self, ruta: Path) -> None:
        """Crea la tabla si no existe."""
        self.ruta = ruta
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with self._conexion() as con:
            con.execute(_ESQUEMA)

    @contextmanager
    def _conexion(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.ruta, timeout=10)
        con.row_factory = sqlite3.Row
        try:
            with con:
                yield con
        finally:
            con.close()

    def crear(
        self, horas: float, cupo: int, nota: str = "", ahora: datetime | None = None
    ) -> tuple[str, Codigo]:
        """Genera un código; devuelve el código en claro (se muestra una sola vez) y su estado."""
        if horas <= 0 or cupo <= 0:
            raise ValueError("Las horas y el cupo deben ser mayores que cero.")
        ahora = ahora or datetime.now(UTC)
        codigo = generar()
        expira = ahora + timedelta(hours=horas)
        with self._conexion() as con:
            con.execute(
                "INSERT INTO codigos (hash, pista, creado, expira, cupo, nota) VALUES (?, ?, ?, ?, ?, ?)",
                (huella(codigo), codigo[-LARGO_GRUPO:], ahora.isoformat(), expira.isoformat(), cupo, nota),
            )
        return codigo, Codigo(codigo[-LARGO_GRUPO:], ahora, expira, cupo, 0, nota, False)

    def estado(self, codigo: str) -> Codigo | None:
        """Estado del código sin gastar cupo (``None`` si no existe)."""
        with self._conexion() as con:
            fila = con.execute("SELECT * FROM codigos WHERE hash = ?", (huella(codigo),)).fetchone()
        return _codigo(fila) if fila else None

    def consumir(self, codigo: str, ahora: datetime | None = None) -> Codigo:
        """Gasta un mensaje del cupo, o ``AccesoDenegadoError`` con el motivo."""
        ahora = ahora or datetime.now(UTC)
        with self._conexion() as con:
            cambio = con.execute(
                "UPDATE codigos SET usados = usados + 1 "
                "WHERE hash = ? AND revocado = 0 AND expira > ? AND usados < cupo",
                (huella(codigo), ahora.isoformat()),
            )
            if cambio.rowcount == 1:
                fila = con.execute("SELECT * FROM codigos WHERE hash = ?", (huella(codigo),)).fetchone()
                return _codigo(fila)
        actual = self.estado(codigo)
        if actual is None:
            raise AccesoDenegadoError("El código de acceso no existe. Revisa que esté bien escrito.")
        if actual.revocado:
            raise AccesoDenegadoError("Este código de acceso fue desactivado.")
        if ahora >= actual.expira:
            raise AccesoDenegadoError("Tu código de acceso venció. Pide uno nuevo.")
        raise AccesoDenegadoError("Tu código de acceso ya usó todos sus mensajes. Pide uno nuevo.")

    def listar(self) -> list[Codigo]:
        """Todos los códigos, del más reciente al más antiguo (sin el código en claro)."""
        with self._conexion() as con:
            filas = con.execute("SELECT * FROM codigos ORDER BY creado DESC").fetchall()
        return [_codigo(f) for f in filas]

    def revocar(self, codigo: str) -> bool:
        """Desactiva un código; ``False`` si no existía."""
        with self._conexion() as con:
            cambio = con.execute("UPDATE codigos SET revocado = 1 WHERE hash = ?", (huella(codigo),))
        return cambio.rowcount == 1

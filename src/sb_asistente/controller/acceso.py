"""Controlador de los códigos de acceso (SPEC-072): exigir, consultar y administrar.

La vista llama a ``exigir`` antes de cualquier llamada al LLM. Con
``ACCESO_CODIGO_OBLIGATORIO=1`` (el sitio público) sin un código vigente no hay LLM; apagado (el
curso, las pruebas) todo funciona como antes.
"""

from datetime import UTC, datetime

from sb_asistente import config
from sb_asistente.model.acceso import AccesoDenegadoError, Codigo, CodigosAcceso

__all__ = ["AccesoDenegadoError", "crear", "estado", "exigir", "listar", "revocar"]


def _codigos() -> CodigosAcceso:
    """Base de códigos (la ruta se lee al llamar: las pruebas la cambian)."""
    return CodigosAcceso(config.ACCESO_DB)


def _obligatorio() -> bool:
    return config.ACCESO_CODIGO_OBLIGATORIO


def exigir(codigo: str | None) -> Codigo | None:
    """Gasta un mensaje del código si el acceso es obligatorio; ``AccesoDenegadoError`` si no se puede."""
    if not _obligatorio():
        return None
    if not codigo or not codigo.strip():
        raise AccesoDenegadoError(
            "El chat con IA necesita un código de acceso. Lo demás (fotos, canales, comparar) es libre."
        )
    return _codigos().consumir(codigo)


def _json(c: Codigo) -> dict[str, object]:
    return {
        "pista": c.pista,
        "expira": c.expira.isoformat(),
        "cupo": c.cupo,
        "usados": c.usados,
        "restantes": c.restantes,
        "nota": c.nota,
        "revocado": c.revocado,
    }


def estado(codigo: str | None) -> dict[str, object]:
    """¿Sirve este código? Sin gastar cupo (para validarlo al escribirlo en la página)."""
    if not _obligatorio():
        return {"obligatorio": False, "valido": True}
    actual = _codigos().estado(codigo) if codigo and codigo.strip() else None
    if actual is None:
        return {"obligatorio": True, "valido": False, "motivo": "El código no existe."}
    valido = actual.vigente(datetime.now(UTC))
    return {
        "obligatorio": True,
        "valido": valido,
        "expira": actual.expira.isoformat(),
        "restantes": actual.restantes,
    }


def crear(
    horas: float | None = None, cupo: int | None = None, nota: str = ""
) -> tuple[str, dict[str, object]]:
    """Nuevo código (el texto en claro solo se ve aquí)."""
    codigo, info = _codigos().crear(horas or config.ACCESO_HORAS, cupo or config.ACCESO_CUPO, nota)
    return codigo, _json(info)


def listar() -> list[dict[str, object]]:
    """Códigos creados, del más reciente al más antiguo (sin el código en claro)."""
    return [_json(c) for c in _codigos().listar()]


def revocar(codigo: str) -> bool:
    """Desactiva un código."""
    return _codigos().revocar(codigo)

"""Router del agente: decide, sin LLM, si un mensaje necesita buscar, consultar datos o nada.

Rutas y herramientas que habilita cada una:

- ``directo``: saludos, agradecimientos y datos personales para la memoria («me llamo Ana»,
  «¿dónde trabajo?») → el LLM responde **sin tools** (no se gasta una búsqueda).
- ``datos``: preguntas numéricas sobre la cartera («¿cuántas pólizas se vendieron en el T3?»)
  → solo ``consultar_datos`` (cifra exacta, el LLM no calcula).
- ``rag``: dudas sobre seguros, coberturas, trámites o canales → ``buscar_conocimiento`` (y
  ``recomendar_seguros`` si pide una sugerencia).
- ``mixto``: una parte de la pregunta va a los documentos y otra a los datos → ambas tools.
- ``fuera_de_alcance``: temas ajenos → respuesta fija, sin LLM.

Con confianza baja la ruta es ``rag`` con **todas** las tools y ``cautela=True``: el agente
decide, pero el prompt le pide responder con prudencia. Las reglas son interpretables y se
miden con el banco ``evaluacion/router.yaml``.
"""

import re
from dataclasses import dataclass, field
from typing import Final, Literal

from sb_asistente.model.intencion import _DOMINIO, _FUERA, clasificar, normalizar

Ruta = Literal["directo", "datos", "rag", "mixto", "fuera_de_alcance"]

TOOLS_POR_RUTA: Final[dict[str, tuple[str, ...]]] = {
    "directo": (),
    "datos": ("consultar_datos",),
    "rag": ("buscar_conocimiento", "recomendar_seguros"),
    "mixto": ("buscar_conocimiento", "consultar_datos"),
    "fuera_de_alcance": (),
}
TODAS: Final[tuple[str, ...]] = ("buscar_conocimiento", "recomendar_seguros", "consultar_datos")
UMBRAL_CAUTELA: Final[float] = 0.5

_CANTIDAD = r"(cuant[oa]s?|total|suma|promedio|numero de|cifra|monto|cantidad)"
_ENTIDAD = r"(polizas?|clientes?|siniestros?|reclamaciones|ventas?|primas?)"
_DATOS: Final[tuple[str, ...]] = (
    rf"\b{_CANTIDAD}\b(\s+\w+){{0,3}}\s+{_ENTIDAD}\b",
    r"\bvend(io|ieron|idas?|imos)\b",
    r"\bventas?\b",
    r"\btrimestre\b",
    r"\bcartera\b",
    r"\bcsv\b",
    r"\bpor canal\b",
)
_DOCUMENTO: Final[tuple[str, ...]] = (
    r"\bdocumento",
    r"\bpagina",
    r"\bcorpus\b",
    r"\bsegun\b",
    r"\bque dice\b",
    r"\bpolitica\b",
    r"\bmeta\b",
)
_PERSONAL: Final[tuple[str, ...]] = (
    r"\bme llamo\b",
    r"\bmi nombre\b",
    r"\btrabajo en\b",
    r"\bvivo en\b",
    r"\bcomo me llamo\b",
    r"\bdonde trabajo\b",
    r"\bdonde vivo\b",
    r"\bquien soy\b",
    r"\bque (sabes|recuerdas) de mi\b",
    r"^(muchas )?gracias\b",
)
_SEPARADORES = re.compile(r"\b(y|con|frente a|versus|vs|ademas|tambien)\b|[,;]")


@dataclass(slots=True)
class Decision:
    """Ruta elegida, con la confianza y las señales que la explican."""

    ruta: Ruta
    confianza: float
    senales: list[str] = field(default_factory=list)
    tools: tuple[str, ...] = ()
    cautela: bool = False


def _hay(texto: str, patrones: tuple[str, ...]) -> list[str]:
    return [p for p in patrones if re.search(p, texto)]


def _es_datos(clausula: str) -> bool:
    return bool(_hay(clausula, _DATOS))


def _es_documento(clausula: str) -> bool:
    """La cláusula pide información de los documentos (vocabulario de seguros o referencia explícita)."""
    if _es_datos(clausula):
        return False
    if _hay(clausula, _DOCUMENTO):
        return True
    return (
        clasificar(clausula).etiqueta in {"conocimiento", "recomendacion"}
        and clasificar(clausula).confianza >= 0.6
    )


def _decision(ruta: Ruta, confianza: float, senales: list[str], cautela: bool = False) -> Decision:
    tools = TODAS if cautela else TOOLS_POR_RUTA[ruta]
    return Decision(ruta, round(confianza, 2), senales, tools, cautela)


def enrutar(mensaje: str) -> Decision:
    """Elige la ruta del mensaje.

    Prioridad: fuera de alcance > datos y documentos (mixto) > datos > personal/saludo (directo)
    > recomendación o conocimiento (rag). Sin vocabulario de seguros, rag con cautela.

    Raises:
        ValueError: si el mensaje está vacío.

    """
    intencion = clasificar(mensaje)
    texto = normalizar(mensaje)
    if intencion.etiqueta == "fuera_de_alcance":
        return _decision("fuera_de_alcance", intencion.confianza, intencion.senales)
    if _hay(texto, _FUERA) and not _hay(texto, _DOMINIO):  # «recomiéndame una película»
        return _decision("fuera_de_alcance", 0.85, ["tema ajeno sin vocabulario de seguros"])
    clausulas = [
        c.strip() for c in _SEPARADORES.split(texto) if c and c.strip() and not _SEPARADORES.fullmatch(c)
    ]
    datos = [c for c in clausulas if _es_datos(c)]
    if datos:
        documentos = [c for c in clausulas if _es_documento(c)]
        if documentos:
            senales = [f"datos: «{datos[0]}»", f"documentos: «{documentos[0]}»"]
            return _decision("mixto", 0.85, senales)
        return _decision("datos", 0.9, [f"pregunta numérica: «{datos[0]}»"])
    personal = _hay(texto, _PERSONAL)
    if intencion.etiqueta == "saludo" or (personal and intencion.etiqueta != "recomendacion"):
        if personal and intencion.confianza >= 0.6 and intencion.etiqueta == "conocimiento":
            return _decision(
                "rag", intencion.confianza, ["dato personal + pregunta de seguros", *intencion.senales]
            )
        senal = "saludo" if intencion.etiqueta == "saludo" else "dato personal o memoria"
        return _decision("directo", 0.9, [senal])
    if intencion.confianza < UMBRAL_CAUTELA:
        return _decision(
            "rag", intencion.confianza, ["confianza baja: todas las tools, con cautela"], cautela=True
        )
    return _decision("rag", intencion.confianza, intencion.senales)

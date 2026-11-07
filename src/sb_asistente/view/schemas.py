"""Contratos de la API (Pydantic v2): validan cada petición y documentan cada respuesta.

Las preguntas se rechazan si traen datos personales (correo, teléfono o número de documento):
el asistente solo trabaja con información pública (Ley 1581 de 2012).
"""

import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sb_asistente.config import PROVIDERS, RECO_K

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_DOC_O_TELEFONO = re.compile(r"(?<!\d)\d{7,12}(?!\d)")  # cédula, NIT o celular colombianos
_SEPARADOR_DIGITOS = re.compile(r"(?<=\d)[\s.-](?=\d)")
_URL = re.compile(r"https?://[^\s)\]>\"']+")

Modo = Literal["completo", "reducido"]


def rechazar_datos_personales(texto: str) -> str:
    """Valida que el texto no traiga correo, teléfono ni número de documento."""
    if _EMAIL.search(texto) or _DOC_O_TELEFONO.search(_SEPARADOR_DIGITOS.sub("", texto)):
        raise ValueError(
            "La pregunta parece incluir datos personales (correo, teléfono o documento). "
            "Escríbala sin ellos: el asistente solo usa información pública."
        )
    return texto.strip()


def extraer_fuentes(texto: str) -> list[str]:
    """URLs de segurosbolivar.com citadas en la respuesta, sin duplicados y en orden."""
    vistas: dict[str, None] = {}
    for url in _URL.findall(texto):
        limpia = url.rstrip(".,;:")
        if "segurosbolivar.com" in limpia:
            vistas.setdefault(limpia, None)
    return list(vistas)


class _Entrada(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PreguntaIn(_Entrada):
    """Pregunta de un cliente."""

    pregunta: Annotated[
        str, Field(min_length=3, max_length=500, examples=["¿Cuál es el WhatsApp de atención?"])
    ]
    version: Literal["v1", "v2", "v3"] = "v3"
    modo: Modo = "reducido"
    proveedor: str | None = Field(default=None, description=f"Uno de {', '.join(PROVIDERS)}")

    @field_validator("pregunta")
    @classmethod
    def _sin_datos_personales(cls, valor: str) -> str:
        return rechazar_datos_personales(valor)

    @field_validator("proveedor")
    @classmethod
    def _proveedor_valido(cls, valor: str | None) -> str | None:
        if valor is not None and valor not in PROVIDERS:
            raise ValueError(f"Proveedor no soportado: {valor}")
        return valor


class TemaIn(_Entrada):
    """Tema para un resumen o para generar preguntas frecuentes."""

    tema: Annotated[str, Field(min_length=3, max_length=200)]
    n: Annotated[int, Field(ge=1, le=15)] = 5
    proveedor: str | None = None

    @field_validator("proveedor")
    @classmethod
    def _proveedor_valido(cls, valor: str | None) -> str | None:
        return PreguntaIn._proveedor_valido(valor)


class RespuestaOut(BaseModel):
    """Respuesta del asistente con trazabilidad."""

    texto: str
    tarea: str
    version_prompt: str
    latencia_s: float
    tokens_contexto: int
    cita_fuente: bool
    fuentes: list[str]


class EtapaOut(BaseModel):
    """Métricas de una etapa del pipeline Medallion."""

    etapa: str
    capa: str
    hecha: bool
    metricas: dict[str, int | float | str]


class RecomendacionOut(BaseModel):
    """Un producto recomendado con su razón legible."""

    product_id: str
    nombre: str
    linea: str
    razon: str


class RecomendacionesOut(BaseModel):
    """Top-k de un cliente."""

    cliente_id: str
    k: Annotated[int, Field(ge=1, le=10)] = RECO_K
    modelo: str = "linea_base_segmento"
    recomendaciones: list[RecomendacionOut]


class SaludOut(BaseModel):
    """Estado del servicio y de sus datos."""

    estado: Literal["ok"] = "ok"
    version: str
    proveedor: str
    corpus_listo: bool
    recomendador_listo: bool

"""Interpretación de la escena de una foto con un modelo multimodal (Claude) y salida estructurada.

YOLO solo conoce 80 objetos genéricos; un modelo multimodal entiende la **situación** (un choque, una
gotera, un robo o un bien que se quiere asegurar). La foto debe llegar ya sin personas
(``privacidad.difuminar``) y la salida se valida con Pydantic (``Escena``).
"""

import base64
from io import BytesIO
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from PIL import Image
from pydantic import BaseModel, Field

from sb_asistente.model.llm import prompts

Situacion = Literal["accidente_transito", "dano_hogar", "robo", "asegurar_bien", "otro"]
LADO_MAXIMO_PX = 1568  # más grande no mejora la interpretación y cuesta más tokens


class Escena(BaseModel):
    """Lo que el modelo entendió de la foto (solo descripción; nada de coberturas ni valores)."""

    situacion: Situacion
    descripcion: str = Field(max_length=400, description="Una o dos frases neutrales en español")
    objetos: list[str] = Field(default_factory=list, max_length=8, description="Objetos relevantes")
    vehiculo: Literal["carro", "moto", "electrico"] | None = None
    tiene_mascota: bool | None = None
    contiene_documento: bool = False
    confianza: Literal["alta", "media", "baja"] = "media"


def contenido_imagen(imagen: Image.Image, lado_maximo: int = LADO_MAXIMO_PX) -> dict[str, str]:
    """Bloque de imagen para LangChain (JPEG en base64, reducida si es muy grande)."""
    copia = imagen.convert("RGB")
    copia.thumbnail((lado_maximo, lado_maximo))
    buffer = BytesIO()
    copia.save(buffer, format="JPEG", quality=90)
    return {
        "type": "image",
        "base64": base64.b64encode(buffer.getvalue()).decode(),
        "mime_type": "image/jpeg",
    }


class InterpreteEscena:
    """Clasifica la situación de una foto con un modelo de chat que acepta imágenes."""

    def __init__(self, llm: BaseChatModel) -> None:
        """Recibe el modelo por inyección (``build_llm("anthropic")`` o un doble en las pruebas)."""
        self.llm = llm

    def interpretar(self, imagen: Image.Image) -> Escena:
        """Devuelve la escena validada con Pydantic (salida estructurada nativa de la API)."""
        mensajes = [
            SystemMessage(prompts.ESCENA_SYSTEM),
            HumanMessage(content=[contenido_imagen(imagen), {"type": "text", "text": prompts.ESCENA_HUMAN}]),
        ]
        return self.llm.with_structured_output(Escena, method="json_schema").invoke(mensajes)

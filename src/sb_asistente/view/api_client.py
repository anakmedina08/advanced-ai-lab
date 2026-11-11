"""Vista · cliente HTTP de la API con ``httpx`` (patrón de ``client.py`` en ``ejercicio_gestion_fastapi``).

Sirve para que otro programa (u otra vista) use el asistente por HTTP sin cargar modelos:

    cliente = ClienteAPI()                        # SB_API_URL o http://127.0.0.1:8000
    cliente.salud()
    cliente.preguntar("¿Cuál es el WhatsApp de atención?")
    cliente.analizar_foto(Path("moto.jpg").read_bytes(), "moto.jpg", responder=True)
"""

import mimetypes

import httpx

from sb_asistente.config import API_URL
from sb_asistente.view.schemas import FotoOut, RespuestaOut, SaludOut

TIMEOUT_S = 120.0  # la primera foto puede cargar YOLO y una respuesta con LLM tarda segundos


class ClienteAPI:
    """Cliente de la API REST; valida cada respuesta con los mismos contratos Pydantic."""

    def __init__(self, base_url: str = API_URL, http: httpx.Client | None = None) -> None:
        """``http`` permite inyectar un cliente (p. ej. con ``httpx.MockTransport`` en las pruebas)."""
        self.base_url = base_url.rstrip("/")
        self.http = http or httpx.Client(timeout=TIMEOUT_S)

    def _url(self, ruta: str) -> str:
        return f"{self.base_url}{ruta}"

    def salud(self) -> SaludOut:
        """``GET /salud``."""
        respuesta = self.http.get(self._url("/salud"))
        respuesta.raise_for_status()
        return SaludOut.model_validate(respuesta.json())

    def preguntar(self, pregunta: str, modo: str = "reducido", proveedor: str | None = None) -> RespuestaOut:
        """``POST /preguntas``."""
        cuerpo = {"pregunta": pregunta, "modo": modo} | ({"proveedor": proveedor} if proveedor else {})
        respuesta = self.http.post(self._url("/preguntas"), json=cuerpo)
        respuesta.raise_for_status()
        return RespuestaOut.model_validate(respuesta.json())

    def analizar_foto(
        self,
        imagen: bytes,
        nombre: str,
        responder: bool = False,
        proveedor: str | None = None,
        interpretar: bool = False,
    ) -> FotoOut:
        """``POST /fotos`` con la imagen como multipart."""
        tipo = mimetypes.guess_type(nombre)[0] or "image/jpeg"
        params = {"responder": str(responder).lower(), "interpretar": str(interpretar).lower()}
        params |= {"proveedor": proveedor} if proveedor else {}
        respuesta = self.http.post(
            self._url("/fotos"), files={"archivo": (nombre, imagen, tipo)}, params=params
        )
        respuesta.raise_for_status()
        return FotoOut.model_validate(respuesta.json())

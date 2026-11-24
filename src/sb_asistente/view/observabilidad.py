"""Observabilidad mínima: una línea JSON por petición y cabeceras de trazabilidad.

Cada respuesta lleva ``X-Request-ID`` (el recibido o uno nuevo) y ``X-Process-Time-ms``. El log
registra método, ruta, status y milisegundos, **nunca el cuerpo** (puede traer texto del usuario).
"""

import json
import logging
import re
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

logger = logging.getLogger("sb.api")

# Parámetros de la URL que nunca deben quedar en un log: Meta manda el token de verificación del
# webhook de WhatsApp en la query (SPEC-073), y el log de acceso de uvicorn imprime la URL completa.
_SECRETOS_EN_URL = re.compile(r"((?:hub[._]verify_token|access_token|token|codigo)=)[^&\s\"]+", re.IGNORECASE)


def ocultar_secretos(texto: str) -> str:
    """Reemplaza el valor de los parámetros sensibles de una URL por ``***``."""
    return _SECRETOS_EN_URL.sub(r"\1***", texto)


class SinSecretos(logging.Filter):
    """Filtro para ``uvicorn.access``: la ruta con query se registra sin tokens."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D102
        if isinstance(record.args, tuple):
            record.args = tuple(ocultar_secretos(a) if isinstance(a, str) else a for a in record.args)
        return True


class FormatoJSON(logging.Formatter):
    """Formatea cada registro como una línea JSON (campos extra en ``registro.datos``)."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D102
        base = {"nivel": record.levelname, "logger": record.name, "mensaje": record.getMessage()}
        return json.dumps(base | getattr(record, "datos", {}), ensure_ascii=False)


def configurar_logs() -> None:
    """Instala el formateador JSON en el logger de la API (una sola vez)."""
    if not any(isinstance(h.formatter, FormatoJSON) for h in logger.handlers):
        manejador = logging.StreamHandler()
        manejador.setFormatter(FormatoJSON())
        logger.addHandler(manejador)
        logger.setLevel(logging.INFO)


async def medir(request: Request, siguiente: Callable[[Request], Awaitable[Response]]) -> Response:
    """Middleware: asigna el request id, mide la latencia y registra la petición."""
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    request.state.request_id = rid
    inicio = time.perf_counter()
    respuesta = await siguiente(request)
    ms = round((time.perf_counter() - inicio) * 1000, 1)
    respuesta.headers["X-Request-ID"] = rid
    respuesta.headers["X-Process-Time-ms"] = str(ms)
    datos = {"request_id": rid, "metodo": request.method, "ruta": request.url.path}
    logger.info("peticion", extra={"datos": datos | {"status": respuesta.status_code, "ms": ms}})
    return respuesta


def registrar(app: FastAPI) -> None:
    """Instala el middleware, el formato JSON y el filtro que oculta tokens del log de acceso."""
    configurar_logs()
    acceso = logging.getLogger("uvicorn.access")
    if not any(isinstance(f, SinSecretos) for f in acceso.filters):
        acceso.addFilter(SinSecretos())
    app.middleware("http")(medir)

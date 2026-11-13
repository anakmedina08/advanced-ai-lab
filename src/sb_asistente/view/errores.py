"""Errores HTTP uniformes: todo error sale como ``ErrorOut`` con el mismo esquema JSON.

- ``HTTPException`` conserva su status y su mensaje.
- ``RequestValidationError`` (422) lista los campos inválidos.
- Cualquier otra excepción responde 500 **sin la traza**; la traza queda en el log con el
  ``request_id`` para encontrarla.
"""

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from sb_asistente.view.schemas import ErrorOut

logger = logging.getLogger("sb.api")

CODIGOS = {400: "solicitud_invalida", 404: "no_encontrado", 405: "metodo_no_permitido", 413: "muy_grande"}
CODIGOS |= {422: "validacion", 500: "interno", 503: "no_disponible"}


def request_id(request: Request) -> str:
    """Id de la petición: el del middleware, el de la cabecera ``X-Request-ID`` o uno nuevo."""
    rid = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")
    if not rid:
        rid = uuid.uuid4().hex[:12]
        request.state.request_id = rid
    return rid


def _respuesta(request: Request, status: int, detalle: object) -> JSONResponse:
    rid = request_id(request)
    cuerpo = ErrorOut(
        error=CODIGOS.get(status, "error"), detalle=detalle, ruta=request.url.path, request_id=rid
    )
    return JSONResponse(cuerpo.model_dump(), status_code=status, headers={"X-Request-ID": rid})


async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _respuesta(request, exc.status_code, exc.detail)


async def _validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
    campos = [
        {"campo": ".".join(str(p) for p in e.get("loc", ()) if p != "body"), "mensaje": e.get("msg", "")}
        for e in exc.errors()
    ]
    return _respuesta(request, 422, campos)


async def _interno(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Error no controlado [%s] en %s", request_id(request), request.url.path, exc_info=exc)
    return _respuesta(request, 500, "Error interno. Use el request_id para buscarlo en el log del servidor.")


def registrar(app: FastAPI) -> None:
    """Instala los manejadores en la aplicación."""
    app.add_exception_handler(StarletteHTTPException, _http)
    app.add_exception_handler(RequestValidationError, _validacion)
    app.add_exception_handler(Exception, _interno)

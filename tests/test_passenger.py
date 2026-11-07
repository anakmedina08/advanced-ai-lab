"""El arranque de cPanel expone la API como aplicación WSGI."""

import importlib.util
from io import BytesIO
from pathlib import Path

ARCHIVO = Path(__file__).resolve().parents[1] / "passenger_wsgi.py"


def test_passenger_responde_salud():
    spec = importlib.util.spec_from_file_location("passenger_wsgi", ARCHIVO)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    estado = {}

    def start_response(status, headers, exc_info=None):
        estado["status"] = status

    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/salud",
        "QUERY_STRING": "",
        "SERVER_NAME": "test",
        "SERVER_PORT": "80",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.url_scheme": "http",
        "wsgi.input": BytesIO(b""),
        "wsgi.errors": BytesIO(),
    }
    cuerpo = b"".join(modulo.application(environ, start_response))
    assert estado["status"].startswith("200") and b'"estado":"ok"' in cuerpo

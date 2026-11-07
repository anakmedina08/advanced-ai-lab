"""Arranque de la API en cPanel («Setup Python App», Phusion Passenger).

Passenger habla WSGI y FastAPI es ASGI: ``a2wsgi`` hace el puente. En cPanel:

- Application root: la carpeta de este repositorio · Application startup file: ``passenger_wsgi.py``
- Application Entry point: ``application``
- Variables: ``LLM_PROVIDER``, ``ANTHROPIC_API_KEY`` (o ``DEEPSEEK_API_KEY``), ``ANTHROPIC_MODEL``.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from a2wsgi import ASGIMiddleware  # noqa: E402

from sb_asistente.view.api import app  # noqa: E402

application = ASGIMiddleware(app)

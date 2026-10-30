"""Punto de entrada de la interfaz: ``uv run streamlit run app.py``.

Streamlit vuelve a ejecutar este archivo en cada interacción, así que se ejecuta la vista con
``runpy`` (no con ``import``, que solo correría la primera vez).
"""

import runpy
from pathlib import Path

runpy.run_path(
    str(Path(__file__).parent / "src" / "sb_asistente" / "view" / "streamlit_app.py"), run_name="__main__"
)

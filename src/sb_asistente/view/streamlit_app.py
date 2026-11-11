"""Interfaz web (Streamlit) en dos áreas: atención al cliente y panel del equipo.

- **Atención al cliente:** asistente en formato chat con fuentes, foto «¿qué hago?» y guías.
- **Panel del equipo:** configuración técnica (proveedor, modo de contexto, prompt), pipeline de
  scraping y evaluación. El cliente nunca ve estos detalles.

Ejecutar: ``uv run streamlit run app.py``. El tema está en ``.streamlit/config.toml``.
"""

from pathlib import Path

import streamlit as st

from sb_asistente.view import ui

VISTA = Path(__file__).parent
PAGINAS = VISTA / "app_pages"

st.set_page_config(page_title=ui.NOMBRE_APP, page_icon=":material/shield:", layout="wide")
ui.iniciar_estado()
st.logo(VISTA / "assets" / "logo.svg", size="large", icon_image=VISTA / "assets" / "icono.svg")

pagina = st.navigation(
    {
        "Atención al cliente": [
            st.Page(
                PAGINAS / "asistente.py", title="Asistente", icon=":material/support_agent:", default=True
            ),
            st.Page(PAGINAS / "foto.py", title="Foto: ¿qué hago?", icon=":material/photo_camera:"),
            st.Page(PAGINAS / "guias.py", title="Guías de seguros", icon=":material/menu_book:"),
        ],
        "Panel del equipo": [
            st.Page(PAGINAS / "configuracion.py", title="Configuración", icon=":material/tune:"),
            st.Page(PAGINAS / "pipeline.py", title="Pipeline de datos", icon=":material/account_tree:"),
            st.Page(PAGINAS / "evaluacion.py", title="Evaluación", icon=":material/analytics:"),
        ],
    },
    position="sidebar",
)

with st.sidebar:
    st.caption(f":material/school: {ui.AVISO_ACADEMICO}")

st.title(pagina.title, icon=pagina.icon)
pagina.run()

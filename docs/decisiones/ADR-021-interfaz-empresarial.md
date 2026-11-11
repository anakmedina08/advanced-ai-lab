# ADR-021 · Interfaz Streamlit en dos áreas con un estilo corporativo neutro

- **Fecha:** 2026-11-11
- **What:** la interfaz pasa de 6 pestañas a una aplicación de varias páginas (`st.navigation`) con
  dos secciones:
  - **Atención al cliente:**
    - **Asistente:** chat con historial, preguntas sugeridas y fuentes como enlaces bajo cada
      respuesta.
    - **Foto: ¿qué hago?**
    - **Guías de seguros:** resumen o preguntas frecuentes por tema.
  - **Panel del equipo:**
    - **Configuración:** proveedor, modo de contexto, versión del prompt y estado del sistema.
    - **Pipeline de datos.**
    - **Evaluación.**

  El tema propio en `.streamlit/config.toml` usa azul marino y grises, tipografía Inter y una barra
  lateral oscura. Usa íconos Material Symbols en lugar de emojis y un logo SVG neutro. Se ocultan
  las opciones de desarrollador (`client.toolbarMode = "viewer"`) y el límite de carga queda en 8 MB.
- **Why:**
  - La interfaz anterior mezclaba lo del cliente (preguntar, foto) con lo técnico (versión del
    prompt, *chunks*, tokens, pipeline). Un producto empresarial separa esas audiencias.
  - El jurado sigue viendo lo técnico en el panel del equipo.
  - El chat es el formato que un cliente espera.
  - Las guías ya no muestran el error «elija el modo Toda la base», porque usan siempre la base
    completa.
- **Marca:** a propósito **no** se usan el logo, los colores (verde y amarillo) ni el aspecto de
  Seguros Bolívar.
  - Es un proyecto académico y una página que parezca oficial podría confundirse con un canal de la
    compañía (sección de ética de la constitución).
  - El nombre es neutro («Asistente de seguros») y la barra lateral siempre muestra el aviso «No es
    un canal oficial».
- **Where:**
  - `view/streamlit_app.py`: navegación, logo y aviso.
  - `view/app_pages/`: una página por archivo, como scripts directos.
  - `view/ui.py`: recursos cacheados, ajustes de la sesión y fuentes.
  - `view/assets/`: `logo.svg` e `icono.svg`.
  - `.streamlit/config.toml`.
  - `tests/test_streamlit_ui.py`: pruebas con `AppTest` y un asistente falso.
  - `docs/capturas/`.
- **Learned:**
  - Los ajustes técnicos se guardan en claves de `st.session_state` que no pertenecen a un widget.
    Las claves de los widgets se borran al cambiar de página, porque el widget deja de dibujarse.
  - **Botón «Nueva conversación».** Se dibuja en un espacio reservado *después* de la respuesta.
    Si se dibuja arriba, no aparece tras la primera pregunta.
  - **Preguntas sugeridas.** El callback del botón también debe limpiar la sugerencia elegida; si
    no, la pregunta se repite sola. Lo detectó una prueba de regresión.
  - El valor de las «pills» debe ser el texto plano y el ícono se agrega con `format_func`. Así el
    valor es estable y se puede probar.
  - `[client]` y `[server]` en `config.toml` solo se leen al arrancar; el tema se recarga solo.
  - La primera carga tras reiniciar importa LangChain y tarda; las capturas sin navegador (Edge)
    necesitan un segundo intento.

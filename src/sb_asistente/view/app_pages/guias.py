"""Página «Guías de seguros»: resumen o preguntas frecuentes de un tema, con toda la base pública."""

import streamlit as st

from sb_asistente.controller import assistant as ctrl
from sb_asistente.view import ui

a = ui.ajustes()
st.caption("Guías generadas a partir de la información pública, con la página de donde sale cada dato.")

with st.container(border=True):
    tipo = st.segmented_control(
        "Tipo de guía",
        ["Resumen", "Preguntas frecuentes"],
        default="Resumen",
        required=True,
    )
    fila = st.container(horizontal=True, vertical_alignment="bottom")
    tema = fila.selectbox("Tema", ctrl.TOPICS, index=1 if tipo == "Preguntas frecuentes" else 0)
    n = fila.slider("Número de preguntas", 3, 10, 5) if tipo == "Preguntas frecuentes" else None
    generar = fila.button("Generar guía", type="primary", icon=":material/auto_awesome:")

if generar:
    try:
        with st.spinner("Preparando la guía con toda la base pública…"):
            asistente = ui.asistente_completo(a.proveedor)
            respuesta = asistente.faq(tema, n) if n else asistente.summarize(tema)
        st.session_state["guia"] = (tipo, tema, respuesta.text, respuesta.sources)
    except Exception as exc:  # noqa: BLE001 - p. ej., sin clave del proveedor
        st.error(f"No se pudo generar la guía: {exc}", icon=":material/error:")

if "guia" in st.session_state:
    tipo_guia, tema_guia, texto, fuentes = st.session_state["guia"]
    with st.container(border=True):
        st.subheader(f"{tipo_guia}: {tema_guia}", icon=":material/description:")
        st.markdown(texto)
        ui.mostrar_fuentes(fuentes)

"""Página «Asistente»: chat con historial; cada respuesta cita la página oficial de donde salió."""

import streamlit as st

from sb_asistente.view import ui

SUGERENCIAS = {  # pregunta → ícono
    "¿Cuál es el WhatsApp de atención?": ":material/chat:",
    "¿Qué cubre el SOAT?": ":material/directions_car:",
    "¿El seguro de mascotas cubre vacunas?": ":material/pets:",
    "¿Qué cubre el seguro de hogar?": ":material/home:",
}

a = ui.ajustes()
historial: list[dict] = st.session_state["chat"]


def nueva_conversacion() -> None:
    """Borra el historial y la sugerencia elegida (si no, se volvería a preguntar sola)."""
    historial.clear()
    st.session_state["sugerencia"] = None


encabezado = st.container(horizontal=True, vertical_alignment="center")
encabezado.caption(
    "Pregunte sobre seguros para personas y canales de atención. Cada pregunta se responde por "
    "separado, solo con información pública, y con la página de donde sale el dato."
)
espacio_boton = encabezado.empty()  # se llena al final, cuando ya existe la respuesta

for mensaje in historial:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])
        if mensaje["role"] == "assistant":
            ui.mostrar_fuentes(mensaje.get("fuentes", []))

pregunta = st.chat_input("Escriba su pregunta…", max_chars=500, submit_mode="disable")

if not historial:
    chips = st.empty()
    elegida = chips.pills(
        "Preguntas frecuentes",
        list(SUGERENCIAS),
        format_func=lambda p: f"{SUGERENCIAS[p]} {p}",
        label_visibility="collapsed",
        key="sugerencia",
    )
    pregunta = pregunta or elegida
    if pregunta:
        chips.empty()

if pregunta:
    historial.append({"role": "user", "content": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)
    with st.chat_message("assistant"):
        try:
            with st.spinner("Buscando en la información pública…"):
                respuesta = ui.asistente(a).answer(pregunta, version=a.version)
            texto, fuentes = respuesta.text, respuesta.sources
        except Exception as exc:  # noqa: BLE001 - p. ej., sin clave del proveedor u Ollama apagado
            texto = (
                "No pude responder en este momento. Intente de nuevo o use los canales oficiales "
                f"de atención.\n\n:gray[Detalle técnico: {exc}]"
            )
            fuentes = []
        st.markdown(texto)
        ui.mostrar_fuentes(fuentes)
    historial.append({"role": "assistant", "content": texto, "fuentes": fuentes})

if historial:
    espacio_boton.button(
        "Nueva conversación", icon=":material/restart_alt:", on_click=nueva_conversacion, width="content"
    )

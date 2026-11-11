"""Página «Foto: ¿qué hago?»: las personas se difuminan en este equipo antes de enviar la foto."""

import pandas as pd
import streamlit as st

from sb_asistente.config import BASE_URL
from sb_asistente.controller import vision
from sb_asistente.view import ui
from sb_asistente.view.anotaciones import dibujar_detecciones

SITUACIONES = {
    "accidente_transito": (":material/car_crash:", "Accidente de tránsito"),
    "dano_hogar": (":material/water_damage:", "Daño en la vivienda"),
    "robo": (":material/lock_open:", "Posible robo"),
    "asegurar_bien": (":material/verified_user:", "Algo para asegurar"),
    "otro": (":material/info:", "Otra situación"),
}

a = ui.ajustes()
st.caption(
    "Suba una foto de un choque, de un daño en su vivienda o de algo que quiera asegurar (carro, "
    "moto, bicicleta, mascota, hogar o equipos) y le indicamos qué hacer, con la fuente oficial."
)
with st.container(border=True):
    st.markdown(
        ":material/privacy_tip: **Su privacidad:** las personas se difuminan en este equipo antes de "
        "enviar la foto y nada se guarda. No suba documentos ni fotos con placas o datos personales."
    )

archivo = st.file_uploader("Foto (JPG o PNG, máx. 8 MB)", type=["jpg", "jpeg", "png"])
if archivo is None:
    st.stop()

datos = archivo.getvalue()
try:
    imagen = vision.abrir_imagen(datos)
except vision.ImagenInvalidaError as exc:
    st.error(str(exc), icon=":material/error:")
    st.stop()

opciones = st.container(horizontal=True, vertical_alignment="center")
con_vision = a.proveedor in ("anthropic",)
interpretar = opciones.toggle(
    "Entender la situación",
    value=con_vision,
    disabled=not con_vision,
    help="Usa un modelo con visión (Claude). Configúrelo en Panel del equipo › Configuración.",
)
responder = opciones.toggle("Explicar qué hacer", value=True)
analizar = opciones.button("Analizar foto", type="primary", icon=":material/search:")

if not analizar:
    st.image(imagen, width=480, caption="Vista previa")
    st.stop()

try:
    with st.spinner("Protegiendo su privacidad y analizando la foto…"):
        analisis = vision.analizar_foto(
            datos,
            ui.detector(),
            ui.asistente(a) if responder else None,
            vision.interprete_por_defecto(a.proveedor) if interpretar else None,
            ui.recomendar_por_perfil if responder else None,
        )
except vision.VisionNoDisponibleError as exc:
    st.warning(str(exc), icon=":material/warning:")
    st.stop()
except Exception as exc:  # noqa: BLE001 - p. ej., sin clave del proveedor
    st.error(f"No se pudo analizar la foto: {exc}", icon=":material/error:")
    st.stop()

res = analisis.resultado
privada, anotada = st.columns(2)
privada.image(
    analisis.imagen_privada,
    caption=f"Lo que se analizó · {analisis.personas_difuminadas} personas difuminadas",
    width="stretch",
)
anotada.image(
    dibujar_detecciones(imagen, res.detecciones),
    caption=f"Objetos detectados · {len(res.detecciones)} · {res.tiempo_ms:.0f} ms",
    width="stretch",
)

if analisis.aviso:
    st.warning(analisis.aviso, icon=":material/badge:")
    st.stop()

plan = analisis.plan
with st.container(border=True):
    if analisis.escena:
        icono, nombre = SITUACIONES[analisis.escena.situacion]
        st.subheader(nombre, icon=icono)
        st.caption(analisis.escena.descripcion)
    if plan.tipo == "ninguno":
        st.info(
            "No identificamos una situación de seguros en la foto. Puede preguntar directamente en "
            "«Asistente».",
            icon=":material/info:",
        )
        st.stop()
    st.markdown(f"**{plan.nombre}**")
    ui.mostrar_fuentes([BASE_URL + ruta for ruta in plan.rutas])

if analisis.respuesta:
    with st.chat_message("assistant"):
        st.caption(plan.pregunta)
        st.markdown(analisis.respuesta.text)
        ui.mostrar_fuentes(analisis.respuesta.sources)

if analisis.recomendaciones:
    st.subheader(
        "Otros seguros que contratan clientes con un perfil como el suyo", icon=":material/recommend:"
    )
    st.dataframe(
        pd.DataFrame(analisis.recomendaciones)[["nombre", "linea", "razon"]],
        hide_index=True,
        column_config={"nombre": "Seguro", "linea": "Línea", "razon": "Por qué"},
    )

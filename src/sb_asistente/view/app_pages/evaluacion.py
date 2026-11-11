"""Página «Evaluación» (panel del equipo): compara corridas de ``sb eval`` por versión y modo."""

import pandas as pd
import streamlit as st

from sb_asistente.controller import assistant as ctrl

ETIQUETAS = {
    "keyword_hit_promedio": "Palabras clave",
    "tasa_cita_fuente": "Cita la fuente",
    "tasa_fallback_correcto": "Rechazo correcto",
}

resumen = ctrl.evaluation_summary()
if not resumen:
    st.info(
        "Aún no hay resultados. Ejecute, por ejemplo: `uv run sb eval --version v3`",
        icon=":material/info:",
    )
    st.stop()

df = pd.DataFrame(resumen)
df["corrida"] = df["modelo"] + " · " + df["version"]
mejor = df.loc[df["tasa_cita_fuente"].idxmax()]

tarjetas = st.container(horizontal=True)
tarjetas.metric("Corridas", len(df), border=True, icon=":material/playlist_add_check:")
tarjetas.metric(
    "Mejor cita de fuente", f"{mejor['tasa_cita_fuente']:.0%}", border=True, icon=":material/link:"
)
tarjetas.metric("Corrida con mejor cita", mejor["corrida"], border=True, icon=":material/emoji_events:")

with st.container(border=True):
    st.subheader("Comparación de corridas", icon=":material/bar_chart:")
    st.caption(
        "Proporción de 0 a 1 sobre el banco de preguntas (evaluacion/preguntas.yaml); más alto es mejor."
    )
    grafica = df.set_index("corrida")[list(ETIQUETAS)].rename(columns=ETIQUETAS)
    st.bar_chart(grafica, stack=False, height=320)

tabla = df.drop(columns="corrida").rename(
    columns=ETIQUETAS | {"latencia_promedio_s": "Latencia (s)", "preguntas": "Preguntas"}
)
st.dataframe(tabla, hide_index=True)

st.subheader("Detalle por pregunta", icon=":material/list_alt:")
corrida = st.selectbox("Corrida", df["corrida"].tolist())
modelo, version = corrida.split(" · ")
detalle = pd.DataFrame(ctrl.evaluation_detail(modelo, version))
st.dataframe(
    detalle[
        [
            "id",
            "categoria",
            "pregunta",
            "respuesta",
            "keyword_hit",
            "cita_fuente",
            "fallback_ok",
            "latencia_s",
        ]
    ],
    hide_index=True,
    column_config={
        "keyword_hit": st.column_config.ProgressColumn("Palabras clave", min_value=0.0, max_value=1.0),
        "cita_fuente": st.column_config.CheckboxColumn("Cita fuente"),
        "fallback_ok": st.column_config.CheckboxColumn("Rechazo correcto"),
        "latencia_s": st.column_config.NumberColumn("Latencia (s)", format="%.1f"),
    },
)

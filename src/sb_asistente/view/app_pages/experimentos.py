"""Página «Experimentos» (panel del equipo): la bitácora de MLflow comparada de forma visual (ADR-022)."""

from datetime import datetime

import pandas as pd
import streamlit as st

from sb_asistente.controller import experimentos

# Métricas que se grafican por experimento (nombre en MLflow → etiqueta legible).
GRAFICAS = {
    "asistente-qa": {
        "tasa_cita_fuente": "Cita la fuente",
        "tasa_fallback_correcto": "Rechazo correcto",
        "keyword_hit_promedio": "Palabras clave",
    },
    "recuperacion": {"hit_at_4": "hit@4", "hit_at_6": "hit@6", "hit_at_10": "hit@10"},
    "recomendador": {"recall_at_5": "Recall@5", "ndcg_at_5": "NDCG@5"},
}
PARAMETROS = {
    "asistente-qa": ["proveedor", "modelo", "modo", "version_prompt"],
    "recuperacion": ["metodo", "preguntas_en_alcance"],
    "recomendador": ["modelo", "k", "clientes_evaluados"],
}


@st.cache_data(ttl=30, show_spinner="Leyendo la bitácora de MLflow…")
def cargar() -> dict[str, list[dict[str, object]]]:
    """Corridas de todos los experimentos (se refresca cada 30 s)."""
    return experimentos.resumen()


st.caption(
    "Cada experimento queda registrado con lo que se probó (parámetros), cómo salió (métricas) y el "
    "commit del código que lo produjo. Fuente: MLflow (`data/mlflow.db`)."
)

if not experimentos.activa():
    st.info(
        "La bitácora de MLflow no está activa. Instálela con `uv sync --extra mlflow` y cargue las "
        "evaluaciones guardadas con `uv run sb mlflow importar`.",
        icon=":material/info:",
    )
    st.stop()

datos = cargar()
total = sum(len(c) for c in datos.values())
fechas = [c["fecha"] for corridas in datos.values() for c in corridas]
tarjetas = st.container(horizontal=True)
tarjetas.metric("Corridas registradas", total, border=True, icon=":material/science:")
tarjetas.metric("Experimentos", len([d for d in datos.values() if d]), border=True, icon=":material/folder:")
tarjetas.metric(
    "Última corrida",
    datetime.fromtimestamp(max(fechas) / 1000).strftime("%d/%m %H:%M") if fechas else "—",
    border=True,
    icon=":material/schedule:",
)
acciones = st.container(horizontal=True, vertical_alignment="center")
acciones.link_button("Abrir MLflow", "http://127.0.0.1:5000", icon=":material/open_in_new:")
acciones.caption("Antes, en una terminal: `uv run sb mlflow ui` · elija la vista «Model training».")
if acciones.button("Actualizar", icon=":material/refresh:"):
    cargar.clear()
    st.rerun()

experimento = st.segmented_control(
    "Experimento",
    list(experimentos.EXPERIMENTOS),
    default="asistente-qa",
    required=True,
    format_func=experimentos.EXPERIMENTOS.get,
)
corridas = datos.get(experimento, [])
if not corridas:
    st.info("Este experimento aún no tiene corridas.", icon=":material/info:")
    st.stop()

nombres = [str(c["nombre"]) for c in corridas]
prefijo = nombres[0].split(" · ")[0] + " · " if " · " in nombres[0] else ""
if len(nombres) > 1 and prefijo and all(n.startswith(prefijo) for n in nombres):
    nombres = [n.removeprefix(prefijo) for n in nombres]  # «anthropic · rag · v3» → «rag · v3»
filas = [
    {"corrida": etiqueta_corrida}
    | {p: c["parametros"].get(p, "") for p in PARAMETROS[experimento]}
    | {etiqueta: c["metricas"].get(metrica) for metrica, etiqueta in GRAFICAS[experimento].items()}
    | {"commit": c["commit"], "fecha": datetime.fromtimestamp(c["fecha"] / 1000)}
    for etiqueta_corrida, c in zip(nombres, corridas, strict=True)
]
tabla = pd.DataFrame(filas)

with st.container(border=True):
    st.subheader("Comparación de corridas", icon=":material/bar_chart:")
    st.bar_chart(
        tabla.set_index("corrida")[list(GRAFICAS[experimento].values())],
        stack=False,
        height=340,
        horizontal=True,
    )

st.dataframe(
    tabla,
    hide_index=True,
    column_config={
        etiqueta: st.column_config.ProgressColumn(etiqueta, min_value=0.0, max_value=1.0, format="%.2f")
        for etiqueta in GRAFICAS[experimento].values()
    }
    | {"fecha": st.column_config.DatetimeColumn("Fecha", format="DD/MM HH:mm")},
)

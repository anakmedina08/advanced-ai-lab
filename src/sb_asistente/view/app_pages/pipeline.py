"""Página «Pipeline de datos» (panel del equipo): etapas Medallion, métricas y re-ejecución."""

import pandas as pd
import streamlit as st

from sb_asistente.config import BASE_URL
from sb_asistente.controller import pipeline

st.caption(
    f"Fuente: {BASE_URL} · respeta robots.txt y sitemap.xml · User-Agent identificado · "
    "1,5 s entre peticiones · Bronze → Silver → Gold"
)

acciones = st.container(horizontal=True)
if acciones.button("Reprocesar sin volver a la web", type="primary", icon=":material/sync:"):
    with st.status("Ejecutando el pipeline…", expanded=True) as status:
        st.write("Limpiando HTML a Markdown y quitando boilerplate…")
        resumen = pipeline.process()
        st.write(f"Deduplicando: {len(resumen['descartadas_duplicadas'])} páginas repetidas descartadas")
        st.write(f"Enriqueciendo: {resumen['documentos']} documentos y {resumen['chunks']} fragmentos")
        status.update(label="Pipeline terminado", state="complete")
if acciones.button("Descubrir en vivo (robots.txt + sitemap)", icon=":material/travel_explore:"):
    with st.spinner("Consultando robots.txt y sitemap.xml…"):
        try:
            plan = pipeline.discover(pipeline.new_session())
            st.success(
                f"Sitemap: {plan['total_sitemap']} URLs · seleccionadas {len(plan['seleccionadas'])} "
                f"· descartadas {len(plan['descartadas'])}",
                icon=":material/check_circle:",
            )
        except Exception as exc:  # noqa: BLE001 - sin red en la sala: se informa y se sigue
            st.warning(f"No se pudo consultar el sitio ({exc}); se muestran los datos ya capturados.")

for etapa in pipeline.stage_report():
    icono = ":material/check_circle:" if etapa["hecha"] else ":material/pending:"
    with st.container(border=True):
        st.markdown(f"{icono} **{etapa['etapa']}** · :gray[{etapa['capa']}]")
        metricas = etapa["metricas"]
        principales = {k: v for k, v in metricas.items() if not k.startswith("  ·")}
        fila = st.container(horizontal=True)
        for nombre, valor in principales.items():
            fila.metric(nombre, f"{valor:,}" if isinstance(valor, int) else valor)
        detalle = {k.strip(" ·"): v for k, v in metricas.items() if k.startswith("  ·")}
        if detalle:
            st.caption("Motivos de descarte: " + " · ".join(f"{k}: {v}" for k, v in detalle.items()))

filas = pipeline.corpus_table()
if filas:
    st.subheader(f"Corpus Gold · {len(filas)} documentos", icon=":material/table_chart:")
    st.dataframe(
        pd.DataFrame(filas),
        hide_index=True,
        column_config={
            "url": st.column_config.LinkColumn("URL"),
            "tokens": st.column_config.NumberColumn("Tokens"),
        },
    )
else:
    st.info("Aún no hay corpus. Ejecute: uv run python scripts/scrape_empresa.py", icon=":material/info:")

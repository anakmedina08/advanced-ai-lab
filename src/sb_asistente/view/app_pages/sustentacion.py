"""Página «Entregables por curso» (sustentación): requisitos con su evidencia y cifras en vivo.

Lee ``docs/requisitos.md`` (fuente única) y calcula los contadores del repositorio al abrirse.
"""

import streamlit as st

from sb_asistente.controller import proyecto

PRUEBAS_MINIMAS = 120
ESTILO = {  # estado → (color del badge, ícono)
    "cumplido": ("green", ":material/check_circle:"),
    "en curso": ("orange", ":material/pending:"),
    "pendiente": ("gray", ":material/schedule:"),
}
PESTANAS = {  # título de la sección en requisitos.md → etiqueta corta e ícono
    "Gestión de Proyectos en IA y CD": ("Gestión de Proyectos", ":material/account_tree:"),
    "Técnicas Avanzadas de IA en Modelos de Lenguaje": ("Técnicas Avanzadas", ":material/psychology:"),
    "Comunes a los dos cursos (gobernanza y herramientas)": ("Comunes", ":material/handshake:"),
}


@st.cache_data(ttl=60, show_spinner=False)
def cargar() -> tuple[dict, object, int | None]:
    """Requisitos, contadores y corridas de MLflow (se refresca cada minuto)."""
    return proyecto.requisitos_por_seccion(), proyecto.contadores(), proyecto.corridas_mlflow()


secciones, cifras, corridas = cargar()

st.caption(
    "Lo que contiene el proyecto, organizado por curso. Cada requisito muestra su estado y dónde está "
    "la evidencia en el repositorio; las cifras se calculan en vivo."
)

tarjetas = st.container(horizontal=True)
tarjetas.metric(
    "Pruebas automatizadas",
    cifras.funciones_de_prueba,
    delta=f"mínimo {PRUEBAS_MINIMAS}",
    delta_color="off",
    border=True,
    icon=":material/verified:",
    help=f"Funciones de prueba en {cifras.archivos_de_prueba} archivos; con parametrizaciones son más casos.",
)
tarjetas.metric("Specs (SDD)", cifras.specs, border=True, icon=":material/description:")
tarjetas.metric("Decisiones (ADR)", cifras.adr, border=True, icon=":material/gavel:")
tarjetas.metric(
    "Tareas hechas",
    f"{cifras.tareas_hechas} / {cifras.tareas_hechas + cifras.tareas_pendientes}",
    border=True,
    icon=":material/task_alt:",
)
tarjetas.metric(
    "Corridas en MLflow", corridas if corridas is not None else "—", border=True, icon=":material/science:"
)

enlaces = st.container(horizontal=True)
for nombre, url in proyecto.ENLACES.items():
    enlaces.link_button(nombre, url, icon=":material/open_in_new:")

pestanas = st.tabs(
    [f"{icono} {etiqueta}" for etiqueta, icono in (PESTANAS.get(s, (s, "")) for s in secciones)]
)
for pestana, (seccion, requisitos) in zip(pestanas, secciones.items(), strict=True):
    with pestana:
        cumplidos = sum(r.estado == "cumplido" for r in requisitos)
        fila = st.container(horizontal=True, vertical_alignment="center")
        fila.progress(cumplidos / len(requisitos), text=f"{cumplidos} de {len(requisitos)} cumplidos")
        estados = fila.pills(
            "Estado",
            list(ESTILO),
            selection_mode="multi",
            default=list(ESTILO),
            label_visibility="collapsed",
            key=f"filtro_{seccion}",
        )
        visibles = [r for r in requisitos if r.estado in (estados or [])]
        columnas = st.columns(2)
        for i, r in enumerate(visibles):
            color, icono = ESTILO[r.estado]
            with columnas[i % 2].container(border=True):
                st.badge(r.estado.capitalize(), icon=icono, color=color)
                st.markdown(f"**{r.requisito}**")
                st.caption(r.evidencia)

"""Página «Configuración» (panel del equipo): proveedor, modo de contexto, prompt y estado del sistema."""

import json
import os
from importlib.util import find_spec

import streamlit as st

from sb_asistente.config import CHUNKS_JSONL, GOLD_DIR
from sb_asistente.controller import assistant as ctrl
from sb_asistente.view import ui

AYUDA_MODOS = (
    "Toda la base: todo el conocimiento en el prompt (Fase 1). Reducido: fragmentos por palabras, "
    "rápido en CPU. RAG: fragmentos por embeddings locales (Ollama + Qdrant). Agente: busca y delega "
    "el análisis de cada fragmento a un subagente."
)

a = ui.ajustes()
st.caption("Ajustes técnicos de esta sesión. El área de atención al cliente los usa sin mostrarlos.")

with st.container(border=True):
    st.subheader("Modelo y contexto", icon=":material/psychology:")
    proveedor = st.segmented_control(
        "Proveedor del modelo",
        list(ui.PROVEEDORES),
        default=a.proveedor,
        required=True,
        format_func=lambda p: ui.NOMBRES_PROVEEDOR.get(p, p),
        key="_cfg_proveedor",
    )
    modos = list(ctrl.MODES)
    modo = st.selectbox(
        "Modo de contexto",
        modos,
        index=modos.index(a.modo),
        format_func=ctrl.MODES.get,
        help=AYUDA_MODOS,
        key="_cfg_modo",
    )
    version = st.segmented_control(
        "Versión del prompt",
        list(ctrl.QA_VERSIONS),
        default=a.version,
        required=True,
        disabled=modo == "agente",
        help="v1: ingenuo · v2: grounding simple · v3: zero-shot estructurado · v4: few-shot",
        key="_cfg_version",
    )
    if proveedor == "ollama" and modo == ctrl.DEFAULT_MODE:
        st.caption(
            ":material/warning: Con Ollama en CPU, «Toda la base» puede tardar minutos; "
            "use «Reducido» o «RAG»."
        )

st.session_state.update(proveedor=proveedor, modo=modo, version_prompt=version)

st.subheader("Estado del sistema", icon=":material/monitor_heart:")
estado = st.container(horizontal=True)
estado.badge(
    "Base de conocimiento lista" if CHUNKS_JSONL.is_file() else "Falta la base: make data",
    icon=":material/database:",
    color="green" if CHUNKS_JSONL.is_file() else "red",
)
estado.badge(
    "Visión (YOLO) instalada" if find_spec("ultralytics") else "Visión sin instalar: make vision",
    icon=":material/photo_camera:",
    color="green" if find_spec("ultralytics") else "orange",
)
clave = bool(os.getenv("ANTHROPIC_API_KEY"))
estado.badge(
    "Clave de Anthropic configurada" if clave else "Sin clave de Anthropic en .env",
    icon=":material/key:",
    color="green" if clave else "orange",
)

resumen = GOLD_DIR / "resumen.json"
if resumen.is_file():
    datos = json.loads(resumen.read_text(encoding="utf-8"))
    tarjetas = st.container(horizontal=True)
    tarjetas.metric("Páginas en la base", f"{datos['documentos']:,}", border=True, icon=":material/article:")
    tarjetas.metric("Fragmentos", f"{datos['chunks']:,}", border=True, icon=":material/segment:")
    tarjetas.metric(
        "Tokens de contexto (aprox.)",
        f"{datos['tokens_conocimiento_est']:,}",
        border=True,
        icon=":material/token:",
    )

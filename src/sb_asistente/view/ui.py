"""Vista · piezas compartidas por las páginas de Streamlit (recursos cacheados, ajustes y avisos).

Las páginas de ``app_pages/`` solo hablan con este módulo y con el controlador (MVC). Los ajustes
técnicos (proveedor, modo de contexto, versión del prompt) se eligen en «Panel del equipo ›
Configuración» y se guardan en ``st.session_state`` para que el área del cliente no los muestre.
"""

from dataclasses import dataclass

import streamlit as st

from sb_asistente.config import LLM_PROVIDER, PROVIDERS
from sb_asistente.controller import assistant as ctrl
from sb_asistente.controller import recomendador, vision

NOMBRE_APP = "Asistente de seguros"
AVISO_ACADEMICO = (
    "Proyecto académico (UAO) con información pública de segurosbolivar.com. "
    "No es un canal oficial de la compañía: para trámites use sus canales oficiales."
)
PROVEEDORES: tuple[str, ...] = tuple(PROVIDERS)
NOMBRES_PROVEEDOR = {"anthropic": "Claude (Anthropic)", "deepseek": "DeepSeek", "ollama": "Ollama (local)"}


@dataclass(frozen=True, slots=True)
class Ajustes:
    """Ajustes técnicos vigentes para la sesión del usuario."""

    proveedor: str
    modo: str
    version: str


def modo_por_defecto(proveedor: str) -> str:
    """Toda la base con proveedores en la nube; contexto reducido con Ollama en CPU."""
    return "reducido" if proveedor == "ollama" else ctrl.DEFAULT_MODE


def iniciar_estado() -> None:
    """Valores iniciales de la sesión (una sola vez, en el script principal)."""
    proveedor = LLM_PROVIDER if LLM_PROVIDER in PROVEEDORES else PROVEEDORES[0]
    st.session_state.setdefault("proveedor", proveedor)
    st.session_state.setdefault("modo", modo_por_defecto(proveedor))
    st.session_state.setdefault("version_prompt", ctrl.DEFAULT_QA_VERSION)
    st.session_state.setdefault("chat", [])


def ajustes() -> Ajustes:
    """Ajustes elegidos en el panel del equipo (o los valores por defecto)."""
    iniciar_estado()
    return Ajustes(
        st.session_state["proveedor"], st.session_state["modo"], st.session_state["version_prompt"]
    )


@st.cache_resource(show_spinner="Cargando la base de conocimiento…", max_entries=4)
def asistente_completo(proveedor: str) -> ctrl.KnowledgeAssistant:
    """Asistente con toda la base (también para resúmenes y preguntas frecuentes)."""
    return ctrl.full_assistant(proveedor)


@st.cache_resource(show_spinner="Preparando el asistente…", max_entries=8)
def _asistente_modo(proveedor: str, modo: str) -> ctrl.QAAssistant:
    return ctrl.build_assistant(proveedor, modo)


def asistente(a: Ajustes) -> ctrl.QAAssistant:
    """Asistente de preguntas del modo configurado."""
    return (
        asistente_completo(a.proveedor)
        if a.modo == ctrl.DEFAULT_MODE
        else _asistente_modo(a.proveedor, a.modo)
    )


@st.cache_resource(show_spinner="Cargando el modelo de visión…")
def detector() -> vision.Detector:
    """Detector YOLO cargado y calentado una sola vez por servidor."""
    det = vision.detector_por_defecto()
    det.cargar()
    return det


def recomendar_por_perfil(perfil: dict[str, object]) -> list[dict[str, str]]:
    """Top-3 del recomendador de Gestión para un perfil."""
    return recomendador.recomendar_por_perfil(perfil, 3)[0]


def etiqueta_fuente(url: str) -> str:
    """Texto corto para un enlace de fuente: la ruta de la página (o «inicio»)."""
    ruta = url.split("segurosbolivar.com", 1)[-1].strip("/")
    return ruta.rsplit("/", 1)[-1].replace("-", " ") or "inicio"


def mostrar_fuentes(urls: list[str]) -> None:
    """Fuentes citadas como enlaces discretos bajo una respuesta."""
    if urls:
        enlaces = " · ".join(f"[{etiqueta_fuente(u)}]({u})" for u in urls)
        st.caption(f":material/link: Fuentes: {enlaces}")

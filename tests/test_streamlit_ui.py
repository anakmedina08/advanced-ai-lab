"""Pruebas de la interfaz Streamlit con AppTest (asistente falso: sin red ni API)."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from sb_asistente.model.llm.service import Answer
from sb_asistente.view import ui

APP = Path(__file__).resolve().parents[1] / "app.py"
PAGINAS = "src/sb_asistente/view/app_pages/{}.py"
FUENTE = "https://www.segurosbolivar.com/canales-de-atencion"


class FakeAsistente:
    """Responde siempre con una fuente y registra las preguntas y versiones recibidas."""

    def __init__(self) -> None:
        self.preguntas: list[tuple[str, str]] = []

    def answer(self, question, version="v3", skill=None):
        self.preguntas.append((question, version))
        return Answer(f"Escriba al WhatsApp 322 332 2322.\nFuente: {FUENTE}", "qa", version, 0.1, 10)

    def summarize(self, topic):
        return Answer(f"Resumen de {topic}.\nFuente: {FUENTE}", "resumen", "v3", 0.1, 10)

    def faq(self, topic, n):
        return Answer(f"{n} preguntas de {topic}.\nFuente: {FUENTE}", "faq", "v3", 0.1, 10)


@pytest.fixture
def asistente(monkeypatch) -> FakeAsistente:
    fake = FakeAsistente()
    monkeypatch.setattr(ui, "asistente", lambda ajustes: fake)
    monkeypatch.setattr(ui, "asistente_completo", lambda proveedor: fake)
    return fake


def app() -> AppTest:
    return AppTest.from_file(str(APP), default_timeout=120).run()


@pytest.mark.parametrize(
    "pagina",
    ["asistente", "foto", "guias", "configuracion", "pipeline", "evaluacion", "experimentos", "sustentacion"],
)
def test_cada_pagina_carga_sin_errores(pagina):
    at = app().switch_page(PAGINAS.format(pagina)).run()
    assert not at.exception and at.title


def test_navegacion_separa_cliente_y_equipo():
    at = app()
    assert at.title[0].value == "Asistente"  # la página por defecto es la del cliente
    assert any("Proyecto académico" in c.value for c in at.sidebar.caption)


def test_area_del_cliente_no_muestra_ajustes_tecnicos():
    at = app()
    etiquetas = [w.label for w in at.selectbox] + [w.label for w in at.get("segmented_control")]
    assert not any("prompt" in e.lower() or "proveedor" in e.lower() for e in etiquetas)


def test_chat_responde_con_fuente_y_guarda_historial(asistente):
    at = app()
    at.chat_input[0].set_value("¿Cuál es el WhatsApp?").run()
    assert [m.name for m in at.chat_message] == ["user", "assistant"]
    assert any("canales de atencion" in c.value for c in at.caption)
    assert at.session_state["chat"][-1]["fuentes"] == [FUENTE]


def test_pregunta_sugerida_inicia_la_conversacion(asistente):
    at = app()
    at.get("pills")[0].set_value("¿Qué cubre el SOAT?").run()
    assert asistente.preguntas == [("¿Qué cubre el SOAT?", "v3")] and len(at.chat_message) == 2
    assert not at.get("pills")  # las sugerencias desaparecen al empezar


def test_nueva_conversacion_borra_el_historial(asistente):
    at = app()
    at.chat_input[0].set_value("Hola").run()
    next(b for b in at.button if b.label == "Nueva conversación").click().run()
    assert at.session_state["chat"] == []


def test_error_del_modelo_se_muestra_sin_romper_la_pagina(monkeypatch):
    def falla(ajustes):
        raise RuntimeError("sin clave")

    monkeypatch.setattr(ui, "asistente", falla)
    at = app()
    at.chat_input[0].set_value("Hola").run()
    assert not at.exception and "No pude responder" in at.chat_message[1].markdown[0].value


def test_configuracion_cambia_la_version_que_usa_el_chat(asistente):
    at = app().switch_page(PAGINAS.format("configuracion")).run()
    next(s for s in at.get("segmented_control") if s.label == "Versión del prompt").set_value("v4").run()
    assert at.session_state["version_prompt"] == "v4"
    at.switch_page(PAGINAS.format("asistente")).run()
    at.chat_input[0].set_value("¿Qué cubre el SOAT?").run()
    assert asistente.preguntas[-1] == ("¿Qué cubre el SOAT?", "v4")


def test_guias_genera_resumen_con_fuente(asistente):
    at = app().switch_page(PAGINAS.format("guias")).run()
    next(b for b in at.button if b.label == "Generar guía").click().run()
    assert any("Resumen de" in m.value for m in at.markdown)


def test_etiqueta_fuente_es_corta_y_legible():
    assert ui.etiqueta_fuente("https://www.segurosbolivar.com/seguro-para-mascotas") == "seguro para mascotas"
    assert ui.etiqueta_fuente("https://www.segurosbolivar.com/") == "inicio"


def test_modo_por_defecto_segun_proveedor():
    assert ui.modo_por_defecto("ollama") == "reducido" and ui.modo_por_defecto("anthropic") == "completo"


def test_nueva_conversacion_tras_sugerencia_no_repite_la_pregunta(asistente):
    at = app()
    at.get("pills")[0].set_value("¿Qué cubre el SOAT?").run()
    next(b for b in at.button if b.label == "Nueva conversación").click().run()
    assert len(asistente.preguntas) == 1 and at.session_state["chat"] == []
    assert at.get("pills")[0].value is None

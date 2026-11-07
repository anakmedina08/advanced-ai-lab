"""Pruebas del orquestador del chat (sin red ni API: Q&A falso y datos sintéticos)."""

import pytest

from sb_asistente.controller import chat, recomendador
from sb_asistente.model.llm import prompts
from sb_asistente.model.llm.service import Answer, KnowledgeAssistant

URL = "https://www.segurosbolivar.com/canales-de-atencion"


class QAFalso:
    def __init__(self):
        self.llamadas = []

    def __call__(self, pregunta, skill):
        self.llamadas.append((pregunta, skill))
        return Answer(f"Respuesta. Fuente: {URL}", "qa", "v3", 0.2, 900)


@pytest.fixture
def datos(tmp_path, monkeypatch):
    recomendador.generar(400, 5, tmp_path)
    por_perfil, por_cliente = recomendador.recomendar_por_perfil, recomendador.recomendar
    monkeypatch.setattr(chat.recomendador, "recomendar_por_perfil", lambda p, k: por_perfil(p, k, tmp_path))
    monkeypatch.setattr(chat.recomendador, "recomendar", lambda c, k: por_cliente(c, k, tmp_path))
    return tmp_path


def test_pregunta_va_al_qa_con_traza():
    qa = QAFalso()
    turno = chat.responder("¿Cuál es el WhatsApp?", qa, extraer_fuentes=lambda t: [URL])
    assert turno.herramienta == "conocimiento" and turno.fuentes == [URL]
    assert [p.agente for p in turno.traza] == ["clasificador", "conocimiento"]


def test_saludo_no_gasta_tokens():
    qa = QAFalso()
    assert chat.responder("Hola", qa).herramienta == "respuesta_fija" and qa.llamadas == []


def test_fuera_de_alcance_no_gasta_tokens():
    qa = QAFalso()
    turno = chat.responder("¿Quién ganó el mundial?", qa)
    assert turno.respuesta == chat.FUERA and qa.llamadas == []


def test_recomendacion_por_perfil(datos):
    turno = chat.responder("¿Qué seguro me recomiendas? Tengo carro y un perro", QAFalso(), k=3)
    assert turno.herramienta == "recomendador" and len(turno.recomendaciones) == 3
    assert turno.perfil == {"vehiculo": "carro", "tiene_mascota": True}
    assert "sintéticos" in turno.respuesta


def test_recomendacion_sin_perfil_pide_datos(datos):
    turno = chat.responder("Recomiéndame un seguro", QAFalso())
    assert turno.respuesta == chat.PIDE_PERFIL and turno.recomendaciones == []


def test_recomendacion_por_cliente(datos):
    turno = chat.responder("dame recomendaciones", QAFalso(), modo="recomendador", cliente_id="C000001", k=2)
    assert len(turno.recomendaciones) == 2 and "C000001" in turno.traza[-1].detalle


def test_modo_clasificador_no_llama_herramientas():
    qa = QAFalso()
    turno = chat.responder("¿Cubre el SOAT a la moto?", qa, modo="clasificador")
    assert turno.herramienta == "clasificador" and qa.llamadas == [] and "conocimiento" in turno.respuesta


def test_modo_conocimiento_forzado():
    qa = QAFalso()
    chat.responder("Recomiéndame un seguro", qa, modo="conocimiento")
    assert len(qa.llamadas) == 1


def test_skill_se_entrega_al_qa():
    qa = QAFalso()
    turno = chat.responder(
        "¿Diferencia entre seguro de hogar y de arrendamiento?", qa, skill="comparar-seguros"
    )
    assert "Producto | Para quién es" in qa.llamadas[0][1] and turno.skill == "comparar-seguros"
    assert any(p.agente == "skill" for p in turno.traza)


def test_skill_desconocida_falla():
    with pytest.raises(KeyError):
        chat.responder("¿Qué cubre el seguro de vida?", QAFalso(), skill="no-existe")


def test_bloque_de_skill_escapa_llaves_y_mantiene_reglas():
    bloque = prompts.skill_block("Use {formato} propio")
    assert "{{formato}}" in bloque and "ganan las <reglas>" in bloque


def test_skill_llega_al_system_prompt():
    from langchain_core.language_models.fake_chat_models import FakeListChatModel

    asistente = KnowledgeAssistant(
        FakeListChatModel(responses=["ok"]), "conocimiento de prueba", cache_prompt=False
    )
    capturado = {}
    original = asistente._run

    def espia(system, human, task, version, **kwargs):
        capturado["system"] = system
        return original(system, human, task, version, **kwargs)

    asistente._run = espia
    asistente.answer("¿Qué es el SOAT?", skill="Responde en tabla {x}")
    assert "<skill>" in capturado["system"] and "{{x}}" in capturado["system"]

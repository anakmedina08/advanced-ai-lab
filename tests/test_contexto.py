"""Pruebas de la gestión del contexto multi-turno: resumen del historial y recorte por tokens."""

from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage, trim_messages
from langchain_core.messages.utils import count_tokens_approximately

from sb_asistente.config import MEMORY_KEEP_MESSAGES, MEMORY_MAX_TOKENS, MEMORY_SUMMARY_TOKENS
from sb_asistente.model.agente import middleware


def historial_largo(turnos: int = 30) -> list:
    mensajes = []
    for i in range(turnos):
        mensajes.append(HumanMessage(f"Pregunta {i}: " + "detalle del seguro " * 120))
        mensajes.append(AIMessage(f"Respuesta {i}: " + "texto de la póliza " * 120))
    return mensajes


def test_recorte_por_tokens_respeta_el_tope_y_empieza_en_humano():
    # Arrange
    mensajes = historial_largo()
    # Act
    recortados = trim_messages(
        mensajes,
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=MEMORY_MAX_TOKENS,
        start_on="human",
        allow_partial=False,
    )
    # Assert
    assert count_tokens_approximately(mensajes) > MEMORY_MAX_TOKENS
    assert count_tokens_approximately(recortados) <= MEMORY_MAX_TOKENS
    assert isinstance(recortados[0], HumanMessage)
    assert recortados[-1] is mensajes[-1]


def test_el_agente_resume_antes_de_recortar():
    # Act
    capas = middleware(GenericFakeChatModel(messages=iter([])))
    # Assert
    assert isinstance(capas[0], SummarizationMiddleware)


def test_umbrales_coherentes_resumen_antes_que_el_tope():
    # Assert
    assert MEMORY_SUMMARY_TOKENS < MEMORY_MAX_TOKENS
    assert MEMORY_KEEP_MESSAGES >= 4


def test_el_resumen_se_dispara_al_superar_el_umbral():
    # Arrange
    capa = middleware(GenericFakeChatModel(messages=iter([])))[0]
    # Act
    corto = capa._should_summarize(historial_largo(1), count_tokens_approximately(historial_largo(1)))
    largo = capa._should_summarize(historial_largo(), count_tokens_approximately(historial_largo()))
    # Assert
    assert corto is False
    assert largo is True

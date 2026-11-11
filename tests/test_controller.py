"""Pruebas del controlador del asistente (AAA, modelo falso, sin red ni API)."""

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from sb_asistente.controller import assistant as ctrl
from sb_asistente.model.llm.assistants import RetrievalAssistant
from sb_asistente.model.llm.keyword_search import select_context
from sb_asistente.model.llm.service import KnowledgeAssistant

URL = "https://www.segurosbolivar.com/canales"
CHUNKS = [
    {"title": "Canales", "breadcrumb": "", "url": URL, "text": "WhatsApp 322 332 2322", "tokens_est": 10},
    {"title": "SOAT", "breadcrumb": "", "url": "https://x/soat", "text": "SOAT gastos", "tokens_est": 10},
]
CANALES = "## Canales de atención\nWhatsApp: 322 332 2322\n"


def fake_llm(reply: str = f"Escriba al 322 332 2322. Fuente: {URL}") -> FakeListChatModel:
    return FakeListChatModel(responses=[reply] * 30)


@pytest.fixture
def lite() -> RetrievalAssistant:
    return RetrievalAssistant(fake_llm(), lambda q: select_context(q, CHUNKS), CANALES)


def test_versions_include_default():
    assert ctrl.DEFAULT_QA_VERSION in ctrl.QA_VERSIONS


def test_topics_are_not_empty():
    assert len(ctrl.TOPICS) > 0


def test_lite_context_always_starts_with_channels(lite):
    assert lite.context_for("¿cómo compro el SOAT?").startswith(CANALES)


def test_lite_context_includes_relevant_chunk_url(lite):
    assert URL in lite.context_for("whatsapp")


def test_lite_context_skips_unrelated_chunks(lite):
    assert "https://x/soat" not in lite.context_for("whatsapp")


def test_lite_answer_returns_model_text(lite):
    assert "322 332 2322" in lite.answer("¿Cuál es el WhatsApp?").text


def test_lite_answer_cites_source(lite):
    assert lite.answer("¿Cuál es el WhatsApp?").cites_source


def test_evaluate_writes_sample_csv(tmp_path):
    factory = lambda provider: KnowledgeAssistant(fake_llm(), "### Base\nFuente: " + URL)  # noqa: E731
    metrics, out = ctrl.evaluate("ollama", "v3", 2, factory=factory, results_path=tmp_path / "r.csv")
    assert out.name == "resultados_ollama_v3_muestra2.csv" and out.is_file()


def test_evaluate_reports_progress_per_question(tmp_path):
    seen: list[int] = []
    factory = lambda provider: KnowledgeAssistant(fake_llm(), "### Base\nFuente: " + URL)  # noqa: E731
    ctrl.evaluate("ollama", "v3", 3, lambda i, t, row: seen.append(i), factory, tmp_path / "r.csv")
    assert seen == [1, 2, 3]


def test_evaluation_summary_empty_without_results(monkeypatch, tmp_path):
    monkeypatch.setattr(ctrl, "EVAL_RESULTS", tmp_path / "resultados.csv")
    assert ctrl.evaluation_summary() == []


# --- Construcción de cada modo (archivos de Gold, índice y modelo reemplazados por dobles) ----------
@pytest.fixture
def offline(monkeypatch):
    from langchain_core.documents import Document

    monkeypatch.setattr(ctrl, "build_llm", lambda provider, num_ctx=None: fake_llm())
    monkeypatch.setattr(ctrl.knowledge, "load_knowledge", lambda max_tokens: "### Base\nFuente: " + URL)
    monkeypatch.setattr(ctrl.knowledge, "load_chunks", lambda: CHUNKS)
    monkeypatch.setattr(ctrl.knowledge, "load_channels", lambda: CANALES)
    doc = Document(page_content="WhatsApp 322 332 2322", metadata={"title": "Canales", "url": URL})
    monkeypatch.setattr(ctrl, "embedding_search", lambda: lambda question: [doc])


@pytest.mark.parametrize("mode", ["completo", "reducido", "rag"])
def test_build_assistant_every_mode_answers_with_source(offline, mode):
    assert ctrl.build_assistant("ollama", mode).answer("¿Cuál es el WhatsApp?").cites_source


def test_build_assistant_agent_mode_builds_graph(offline, monkeypatch):
    monkeypatch.setattr(ctrl.agent, "build_agent", lambda llm, search, channels: "grafo")
    assert ctrl.build_assistant("ollama", "agente").graph == "grafo"


def test_rag_mode_formats_retrieved_documents_with_source(offline):
    assistant = ctrl.build_assistant("ollama", "rag")
    assert f"Fuente: {URL}" in assistant.context_for("whatsapp")

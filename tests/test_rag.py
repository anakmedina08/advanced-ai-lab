"""Pruebas de la Fase 2 (RAG y agente) con embeddings deterministas y Qdrant en memoria (sin red ni API)."""

from dataclasses import dataclass

import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage

from sb_asistente.controller import assistant as ctrl
from sb_asistente.model.evaluation import RESULT_FILE
from sb_asistente.model.llm import agent, prompts, vector_store
from sb_asistente.model.llm.assistants import AgentAssistant, RetrievalAssistant
from sb_asistente.view import cli

URL_CANALES = "https://www.segurosbolivar.com/canales"
URL_SOAT = "https://www.segurosbolivar.com/soat"
CHUNKS = [
    {"chunk_id": "canales#000", "title": "Canales", "url": URL_CANALES, "section": "canales_y_servicio",
     "breadcrumb": "", "text": "Escríbanos por WhatsApp al 322 332 2322."},
    {"chunk_id": "soat#000", "title": "SOAT", "url": URL_SOAT, "section": "movilidad",
     "breadcrumb": "", "text": "El SOAT cubre gastos médicos por accidentes de tránsito."},
]  # fmt: skip
CANALES = "## Canales de atención\nWhatsApp: 322 332 2322\n"


class CountingEmbedding(DeterministicFakeEmbedding):
    """Embeddings deterministas que cuentan cuántos textos se vectorizaron.

    ``QdrantVectorStore`` vectoriza UN texto de prueba al abrirse para validar la dimensión; eso no
    es recalcular el índice, así que las pruebas comparan contra ese costo fijo.
    """

    calls: int = 0

    def embed_documents(self, texts):
        self.calls += len(texts)
        return super().embed_documents(texts)


VALIDATION_CALLS = 1  # texto de prueba de QdrantVectorStore al abrir una colección


class BrokenEmbedding(DeterministicFakeEmbedding):
    """Simula Ollama apagado."""

    def embed_query(self, text):
        raise ConnectionError("Ollama no responde")


@pytest.fixture(autouse=True)
def _close_qdrant_clients():
    yield
    vector_store.close_clients()


@pytest.fixture
def client():
    return vector_store.open_client(None)


@pytest.fixture
def store(client):
    return vector_store.build_index(CHUNKS, DeterministicFakeEmbedding(size=16), client)


# --- Índice vectorial ------------------------------------------------------------------------
def test_chunks_to_documents_keeps_citation_metadata():
    doc = vector_store.chunks_to_documents(CHUNKS)[0]
    assert doc.metadata["url"] == URL_CANALES and doc.metadata["chunk_id"] == "canales#000"


def test_fingerprint_changes_when_text_changes():
    changed = [CHUNKS[0] | {"text": "otro texto"}, CHUNKS[1]]
    assert vector_store.fingerprint(CHUNKS) != vector_store.fingerprint(changed)


def test_build_index_stores_every_chunk(store, client):
    assert client.count(store.collection_name).count == len(CHUNKS)


def test_build_index_reuses_existing_collection_without_reembedding(client):
    emb = CountingEmbedding(size=16)
    vector_store.build_index(CHUNKS, emb, client)
    before = emb.calls
    vector_store.build_index(CHUNKS, emb, client)
    assert emb.calls - before == VALIDATION_CALLS


def test_build_index_replaces_old_collection_when_chunks_change(client):
    vector_store.build_index(CHUNKS, DeterministicFakeEmbedding(size=16), client)
    vector_store.build_index(CHUNKS[:1], DeterministicFakeEmbedding(size=16), client)
    assert len(client.get_collections().collections) == 1


def test_build_index_rejects_empty_chunks(client):
    with pytest.raises(ValueError, match="sb process"):
        vector_store.build_index([], DeterministicFakeEmbedding(size=16), client)


def test_build_index_explains_missing_ollama_and_leaves_no_partial_index(client):
    with pytest.raises(vector_store.EmbeddingSetupError, match="ollama pull"):
        vector_store.build_index(CHUNKS, BrokenEmbedding(size=16), client)
    assert client.get_collections().collections == []


def test_search_returns_k_documents(store):
    assert len(vector_store.search(store, "whatsapp", k=1)) == 1


def test_search_rejects_non_positive_k(store):
    with pytest.raises(ValueError):
        vector_store.search(store, "whatsapp", k=0)


def test_search_finds_identical_text_first(store):
    # Con embeddings deterministas, el texto idéntico produce el mismo vector (similitud 1).
    assert vector_store.search(store, CHUNKS[1]["text"], k=1)[0].metadata["url"] == URL_SOAT


def test_format_docs_has_title_and_source():
    text = vector_store.format_docs(vector_store.chunks_to_documents(CHUNKS[:1]))
    assert text.startswith("### Canales\nFuente: " + URL_CANALES)


def test_open_client_on_disk_persists_index(tmp_path):
    first = vector_store.open_client(tmp_path / "qdrant")
    vector_store.build_index(CHUNKS, DeterministicFakeEmbedding(size=16), first)
    vector_store.close_clients()  # simula un proceso nuevo
    emb = CountingEmbedding(size=16)
    vector_store.build_index(CHUNKS, emb, vector_store.open_client(tmp_path / "qdrant"))
    assert emb.calls == VALIDATION_CALLS


def test_open_client_reuses_client_in_same_process(tmp_path):
    # Streamlit: los modos «rag» y «agente» abren el mismo índice; Qdrant local no admite dos clientes.
    assert vector_store.open_client(tmp_path / "q") is vector_store.open_client(tmp_path / "q")


def test_open_client_uses_copy_when_another_process_holds_the_folder(tmp_path):
    from qdrant_client import QdrantClient

    path = tmp_path / "qdrant"
    other = QdrantClient(path=str(path))  # «la app de Streamlit abierta»
    vector_store.build_index(CHUNKS, DeterministicFakeEmbedding(size=16), other)
    try:
        emb = CountingEmbedding(size=16)
        store = vector_store.build_index(CHUNKS, emb, vector_store.open_client(path))
        assert emb.calls == VALIDATION_CALLS  # la copia trae el índice: no recalcula
        assert len(vector_store.search(store, "SOAT", k=2)) == 2
    finally:
        other.close()


# --- Modo RAG (RetrievalAssistant + vector_store) ------------------------------------------
def fake_llm(reply: str = f"Escriba al 322 332 2322.\nFuente: {URL_CANALES}") -> FakeListChatModel:
    return FakeListChatModel(responses=[reply] * 10)


def fixed_search(question: str) -> list[Document]:
    return vector_store.chunks_to_documents(CHUNKS[:1])


def make_rag(llm, search=fixed_search) -> RetrievalAssistant:
    """El modo RAG tal como lo arma el controlador, con búsqueda y modelo falsos."""
    return RetrievalAssistant(llm, lambda q: vector_store.format_docs(search(q)), CANALES)


def test_rag_context_starts_with_channels_and_includes_source():
    rag = make_rag(fake_llm())
    context = rag.context_for("¿Tienen WhatsApp?")
    assert context.startswith(CANALES) and f"Fuente: {URL_CANALES}" in context


def test_rag_answer_uses_requested_prompt_version():
    ans = make_rag(fake_llm()).answer("¿WhatsApp?", version="v4")
    assert ans.prompt_version == "v4" and ans.cites_source


def test_rag_with_real_index(store):
    rag = make_rag(fake_llm(), lambda q: vector_store.search(store, q, k=2))
    assert URL_SOAT in rag.context_for("SOAT")


# --- Agente --------------------------------------------------------------------------------
@dataclass
class Upload:
    error: str | None = None


class FakeBackend:
    """Doble del StateBackend de Deep Agents: guarda los archivos en un diccionario."""

    def __init__(self, error: str | None = None):
        self.files: dict[str, bytes] = {}
        self.error = error

    def upload_files(self, files):
        self.files.update(files)
        return [Upload(self.error) for _ in files]


def test_search_tool_saves_each_fragment_with_its_source():
    backend = FakeBackend()
    tool = agent.make_search_tool(fixed_search, backend, new_batch_id=lambda: "b1")
    out = tool.invoke({"query": "whatsapp"})
    assert "/retrieved/b1/chunk_1.md" in out
    assert f"Fuente: {URL_CANALES}" in backend.files["/retrieved/b1/chunk_1.md"].decode()


def test_search_tool_reports_no_results():
    tool = agent.make_search_tool(lambda q: [], FakeBackend())
    assert tool.invoke({"query": "x"}) == agent.NO_RESULTS


def test_search_tool_fails_when_backend_cannot_save():
    tool = agent.make_search_tool(fixed_search, FakeBackend(error="permiso"))
    with pytest.raises(RuntimeError):
        tool.invoke({"query": "whatsapp"})


def test_agent_prompt_keeps_phase1_rules_and_channels():
    system = prompts.AGENT_SYSTEM.format(channels=CANALES)
    assert prompts.FALLBACK in system and "322 332 2322" in system and "search_knowledge" in system


def test_final_text_takes_last_message():
    assert agent.final_text({"messages": [AIMessage("a"), AIMessage(" b ")]}) == "b"


def test_final_text_fails_without_messages():
    with pytest.raises(RuntimeError):
        agent.final_text({"messages": []})


class FakeGraph:
    def __init__(self, reply: str):
        self.reply = reply
        self.inputs: list[object] = []

    def invoke(self, state):
        self.inputs.append(state)
        return {"messages": [*state["messages"], AIMessage(self.reply)]}


def test_agent_assistant_answers_with_agent_version():
    graph = FakeGraph(f"Escriba al 322 332 2322.\nFuente: {URL_CANALES}")
    ans = AgentAssistant(graph, CANALES).answer("¿WhatsApp?", version="v1")
    assert ans.prompt_version == "agente" and ans.cites_source
    assert graph.inputs[0]["messages"][0].content == "¿WhatsApp?"


def test_agent_assistant_rejects_empty_question():
    with pytest.raises(ValueError):
        AgentAssistant(FakeGraph("x"), CANALES).answer("  ")


def test_build_agent_compiles_with_fake_model():
    graph = agent.build_agent(fake_llm(), fixed_search, CANALES, backend=FakeBackend())
    assert hasattr(graph, "invoke")


# --- Controlador y CLI -------------------------------------------------------------------
def test_build_assistant_rejects_unknown_mode():
    with pytest.raises(ValueError, match="Modo desconocido"):
        ctrl.build_assistant("anthropic", "magia")


@pytest.mark.parametrize(
    ("mode", "label"), [("completo", "anthropic"), ("rag", "anthropic-rag"), ("agente", "anthropic-agente")]
)
def test_run_label(mode, label):
    assert ctrl.run_label("anthropic", mode) == label


@pytest.mark.parametrize("name", ["resultados_ollama_v3.csv", "resultados_anthropic-rag_v4.csv",
                                  "resultados_anthropic-agente_agente.csv"])  # fmt: skip
def test_result_file_pattern_accepts_phase2_runs(name):
    assert RESULT_FILE.match(name)


def test_evaluate_rag_names_file_with_mode(tmp_path):
    factory = lambda provider: make_rag(fake_llm())  # noqa: E731
    _, out = ctrl.evaluate("ollama", "v3", 2, factory=factory, results_path=tmp_path / "r.csv", mode="rag")
    assert out.name == "resultados_ollama-rag_v3_muestra2.csv" and out.is_file()


def test_evaluate_agent_ignores_prompt_version(tmp_path):
    factory = lambda provider: AgentAssistant(FakeGraph(f"Fuente: {URL_CANALES}"), CANALES)  # noqa: E731
    _, out = ctrl.evaluate("ollama", "v1", 1, factory=factory, results_path=tmp_path / "r.csv", mode="agente")
    assert out.name == "resultados_ollama-agente_agente_muestra1.csv"


def test_evaluate_rejects_zero_limit(tmp_path):
    with pytest.raises(ValueError, match="limit"):
        ctrl.evaluate("ollama", "v3", 0, factory=lambda p: None, results_path=tmp_path / "r.csv")


def test_cli_ask_passes_mode(monkeypatch, capsys):
    seen: list[str] = []

    def fake(provider, mode="completo"):
        seen.append(mode)
        return make_rag(fake_llm("Hola\nFuente: " + URL_CANALES))

    monkeypatch.setattr(cli, "_assistant", fake)
    assert cli.main(["ask", "¿WhatsApp?", "--modo", "rag"]) == 0
    assert seen == ["rag"] and "modo rag" in capsys.readouterr().out


def test_cli_index_builds_index(monkeypatch, capsys):
    calls: list[bool] = []
    monkeypatch.setattr(cli.assistant, "embedding_search", lambda: calls.append(True))
    assert cli.main(["index"]) == 0
    assert calls == [True] and "Índice listo" in capsys.readouterr().out


def test_use_utf8_allows_symbols_on_windows_encoding():
    import io

    raw = io.BytesIO()
    stream = io.TextIOWrapper(raw, encoding="cp1252")
    cli.use_utf8(stream)
    stream.write("Listo → ✓")
    stream.flush()
    assert raw.getvalue().decode("utf-8") == "Listo → ✓"

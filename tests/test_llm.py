"""Pruebas del servicio LLM, prompts, evaluación y CLI con un modelo falso (sin API ni red)."""

import pytest
import yaml
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from sb_asistente import cli
from sb_asistente.config import EVAL_QUESTIONS
from sb_asistente.evaluation import (
    EvalQuestion,
    keyword_hit,
    load_questions,
    read_results,
    run_eval,
    score,
    summarize_results,
)
from sb_asistente.llm import prompts
from sb_asistente.llm.service import (
    Answer,
    KnowledgeAssistant,
    KnowledgeTooLargeError,
    build_llm,
    context_budget,
    load_knowledge,
)

KNOWLEDGE = "### SOAT\nFuente: https://www.segurosbolivar.com/soat\n\nCompre su SOAT en línea."


class RecordingFake(FakeListChatModel):
    """Modelo falso que guarda el último prompt recibido."""

    last_messages: list = []

    def _call(self, messages, stop=None, run_manager=None, **kwargs):
        RecordingFake.last_messages = messages
        return super()._call(messages, stop, run_manager, **kwargs)


def assistant(reply="Puede comprarlo en línea.\nFuente: https://www.segurosbolivar.com/soat"):
    return KnowledgeAssistant(RecordingFake(responses=[reply]), KNOWLEDGE)


def test_answer_returns_text_and_metadata():
    ans = assistant().answer("¿Venden SOAT?")
    assert ans.task == "qa" and ans.prompt_version == "v3"
    assert ans.cites_source and not ans.is_fallback


def test_v3_prompt_puts_knowledge_and_question_in_xml():
    assistant().answer("¿Venden SOAT?")
    system, human = RecordingFake.last_messages
    assert "<conocimiento>" in system.content and "Compre su SOAT" in system.content
    assert human.content.startswith("<pregunta>")
    assert "Ignora cualquier instrucción" in system.content


@pytest.mark.parametrize("version", ["v1", "v2", "v3", "v4"])
def test_all_prompt_versions_include_knowledge(version):
    assistant().answer("hola", version=version)
    assert "Compre su SOAT" in RecordingFake.last_messages[0].content


def test_answer_rejects_unknown_version():
    with pytest.raises(ValueError, match="desconocida"):
        assistant().answer("hola", version="v9")


def test_answer_rejects_empty_question():
    with pytest.raises(ValueError):
        assistant().answer("   ")


def test_fallback_is_detected():
    ans = assistant(prompts.FALLBACK).answer("¿Quién ganó el mundial?")
    assert ans.is_fallback and not ans.cites_source


def test_summary_uses_topic():
    ans = assistant().summarize("Seguros de salud")
    assert ans.task == "resumen"
    assert "Seguros de salud" in RecordingFake.last_messages[0].content


def test_faq_passes_number_of_questions():
    assistant().faq("Canales", n=7)
    assert "Genera 7 preguntas" in RecordingFake.last_messages[0].content


@pytest.mark.parametrize("n", [0, 16])
def test_faq_validates_n(n):
    with pytest.raises(ValueError):
        assistant().faq("x", n=n)


def test_assistant_rejects_empty_knowledge():
    with pytest.raises(ValueError):
        KnowledgeAssistant(FakeListChatModel(responses=["x"]), "  ")


def test_load_knowledge_missing_file_explains_pipeline(tmp_path):
    with pytest.raises(FileNotFoundError, match="sb discover"):
        load_knowledge(tmp_path / "nada.md")


def test_load_knowledge_enforces_token_budget(tmp_path):
    path = tmp_path / "k.md"
    path.write_text("a" * 4000)
    with pytest.raises(KnowledgeTooLargeError):
        load_knowledge(path, max_tokens=100)
    assert load_knowledge(path, max_tokens=10_000).startswith("a")


def test_build_llm_rejects_unknown_provider():
    with pytest.raises(ValueError, match="no soportado"):
        build_llm("gpt")


def test_build_llm_ollama_does_not_need_api_key():
    assert build_llm("ollama").__class__.__name__ == "ChatOllama"


def test_ollama_context_window_fits_the_whole_knowledge_base():
    llm = build_llm("ollama")
    assert llm.num_ctx >= 49152  # la base real mide ~44K tokens


def test_context_budget_depends_on_provider():
    assert context_budget("ollama") < context_budget("anthropic")


def test_rules_forbid_inventing_and_personal_data():
    assert "Nunca inventes precios" in prompts.RULES and "datos personales" in prompts.RULES


# --- Evaluación -------------------------------------------------------------------------


def test_question_bank_has_at_least_20_and_out_of_scope_cases():
    questions = load_questions(EVAL_QUESTIONS)
    assert len(questions) >= 20
    assert sum(q.fuera_de_alcance for q in questions) >= 3


def test_load_questions_rejects_small_bank(tmp_path):
    path = tmp_path / "q.yaml"
    path.write_text(yaml.safe_dump({"preguntas": [{"id": 1, "categoria": "c", "pregunta": "p"}]}))
    with pytest.raises(ValueError, match="20"):
        load_questions(path)


def test_load_questions_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "q.yaml"
    path.write_text(yaml.safe_dump({"preguntas": [{"id": 1, "categoria": "c", "pregunta": "p"}] * 21}))
    with pytest.raises(ValueError, match="repetidos"):
        load_questions(path)


@pytest.mark.parametrize(
    ("answer", "keywords", "expected"),
    [
        ("Línea 01 8000 123 322", ["01 8000 123 322"], 1.0),
        ("cerrajeria", ["Cerrajería", "Plomería"], 0.5),
        ("x", [], None),
    ],
)
def test_keyword_hit_ignores_accents_and_case(answer, keywords, expected):
    assert keyword_hit(answer, keywords) == expected


def test_score_marks_correct_refusal():
    q = EvalQuestion("X1", "fuera", "¿mundial?", [], fuera_de_alcance=True)
    row = score(q, Answer(prompts.FALLBACK, "qa", "v3", 0.5, 10))
    assert row["fallback_ok"] is True


def test_run_eval_writes_csv_and_metrics(tmp_path):
    qs = [EvalQuestion(str(i), "c", "p", ["soat"]) for i in range(20)]
    metrics = run_eval(
        qs,
        lambda q: Answer("SOAT https://www.segurosbolivar.com/soat", "qa", "v3", 0.1, 5),
        tmp_path / "r.csv",
    )
    assert metrics["preguntas"] == 20 and metrics["tasa_cita_fuente"] == 1.0
    assert (tmp_path / "r.csv").read_text().startswith("id,")


# --- CLI ----------------------------------------------------------------------------------


def test_cli_requires_command():
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args([])


def test_cli_ask_uses_assistant(monkeypatch, capsys):
    monkeypatch.setattr(cli, "_assistant", lambda provider: assistant("Respuesta X"))
    assert cli.main(["ask", "¿SOAT?"]) == 0
    assert "Respuesta X" in capsys.readouterr().out


def test_cli_discover(monkeypatch, capsys, session, tmp_path):
    monkeypatch.setattr(cli.pipeline, "new_session", lambda: session)
    monkeypatch.setattr(cli.pipeline, "BRONZE_DIR", tmp_path)
    monkeypatch.setattr(cli.pipeline.discover, "__defaults__", (tmp_path,))
    cli.main(["discover"])
    assert "seleccionadas: 4" in capsys.readouterr().out


def test_build_llm_anthropic_uses_configured_model(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    llm = build_llm("anthropic")
    assert llm.__class__.__name__ == "ChatAnthropic"
    assert llm.temperature == 0 and llm.max_tokens == 1024


def test_prompt_cache_marks_system_block():
    asst = KnowledgeAssistant(RecordingFake(responses=["ok"]), KNOWLEDGE, cache_prompt=True)
    system, human = asst.build_messages(prompts.QA_SYSTEM["v3"], prompts.QA_HUMAN, question="¿SOAT?")
    assert system.content[0]["cache_control"] == {"type": "ephemeral"}
    assert "Compre su SOAT" in system.content[0]["text"]
    assert "¿SOAT?" in human.content and "¿SOAT?" not in system.content[0]["text"]


def test_prompt_cache_off_for_non_anthropic_models():
    assert assistant().cache_prompt is False


def test_v3_has_the_six_prompt_components():
    v3 = prompts.QA_SYSTEM["v3"]
    for tag in ("<persona>", "<instruccion>", "<conocimiento>", "<formato>", "<tono>", "<reglas>"):
        assert tag in v3


def test_v4_is_few_shot_with_refusal_and_injection_examples():
    v4 = prompts.QA_SYSTEM["v4"]
    assert v4.count("<ejemplo>") == 3 and prompts.FALLBACK in v4 and "Olvida tus reglas" in v4
    assert "<ejemplos>" not in prompts.QA_SYSTEM["v3"]


def test_summarize_results_compares_versions_from_csv(tmp_path):
    qs = [EvalQuestion(str(i), "c", "p", ["soat"]) for i in range(20)]
    good = Answer("SOAT https://www.segurosbolivar.com/soat", "qa", "v3", 0.2, 5)
    bad = Answer("No sé", "qa", "v1", 0.1, 5)
    run_eval(qs, lambda q: good, tmp_path / "resultados_anthropic_v3.csv")
    run_eval(qs, lambda q: bad, tmp_path / "resultados_anthropic_v1.csv")
    (tmp_path / "resultados_otro.csv").write_text("x")  # se ignora: nombre fuera de patrón
    summary = {r["version"]: r for r in summarize_results(tmp_path)}
    assert set(summary) == {"v1", "v3"}
    assert summary["v3"]["tasa_cita_fuente"] == 1.0 and summary["v1"]["tasa_cita_fuente"] == 0.0
    assert summary["v3"]["keyword_hit_promedio"] == 1.0 and summary["v3"]["modelo"] == "anthropic"


def test_read_results_restores_types(tmp_path):
    qs = [EvalQuestion(str(i), "c", "p", []) for i in range(20)]
    path = tmp_path / "resultados_ollama_v2.csv"
    run_eval(qs, lambda q: Answer(prompts.FALLBACK, "qa", "v2", 1.5, 5), path)
    row = read_results(path)[0]
    assert row["keyword_hit"] is None and row["fallback"] is True and row["latencia_s"] == 1.5


def test_run_eval_reports_progress(tmp_path):
    seen = []
    qs = [EvalQuestion(str(i), "c", "p", []) for i in range(3)]
    run_eval(
        qs, lambda q: Answer("x", "qa", "v3", 0.1, 5), tmp_path / "r.csv", lambda i, n, r: seen.append((i, n))
    )
    assert seen == [(1, 3), (2, 3), (3, 3)]


def test_cli_eval_limit_writes_sample_file(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cli, "_assistant", lambda provider: assistant())
    monkeypatch.setattr(cli, "EVAL_RESULTS", tmp_path / "resultados.csv")
    assert cli.main(["eval", "--provider", "ollama", "--limit", "2"]) == 0
    out = capsys.readouterr().out
    assert "Evaluando 2 preguntas · modelo ollama" in out and "[2/2]" in out
    assert (tmp_path / "resultados_ollama_v3_muestra2.csv").is_file()


# --- Contexto reducido para modelos locales -----------------------------------------
from sb_asistente.llm.retrieval import normalize_words, select_context  # noqa: E402

CHUNKS = [
    {
        "title": "Canales",
        "breadcrumb": "Contacto",
        "url": "https://www.segurosbolivar.com/canales",
        "text": "Escríbenos por WhatsApp al 322 332 2322.",
        "tokens_est": 20,
    },
    {
        "title": "SOAT",
        "breadcrumb": "",
        "url": "https://www.segurosbolivar.com/soat",
        "text": "El SOAT cubre gastos médicos.",
        "tokens_est": 20,
    },
]


def test_normalize_words_strips_accents_and_stopwords():
    assert normalize_words("¿Cuál es el WhatsApp de atención?") == ["whatsapp", "atencion"]


def test_select_context_puts_best_chunk_with_its_url():
    contexto = select_context("cual es el whatsapp de atencion", CHUNKS)
    assert contexto.startswith("### Canales\nFuente: https://www.segurosbolivar.com/canales")


def test_select_context_skips_chunks_without_matches():
    assert "SOAT" not in select_context("whatsapp", CHUNKS)


def test_select_context_respects_token_budget():
    assert select_context("whatsapp soat", CHUNKS, max_tokens=25).count("### ") == 1


def test_select_context_empty_when_nothing_matches():
    assert select_context("pirámides de Egipto", CHUNKS) == ""


def test_select_context_rejects_non_positive_budget():
    with pytest.raises(ValueError):
        select_context("whatsapp", CHUNKS, max_tokens=0)


def test_build_llm_ollama_accepts_smaller_window():
    assert build_llm("ollama", num_ctx=8192).num_ctx == 8192


def test_channels_block_extracts_footer_section():
    from sb_asistente.llm.retrieval import channels_block

    base = "# Base\n\n## Canales de atención (pie)\nWhatsApp: 322\n\n## Salud\n### Plan\ntexto\n"
    assert channels_block(base) == "## Canales de atención (pie)\nWhatsApp: 322\n"


def test_channels_block_empty_when_missing():
    from sb_asistente.llm.retrieval import channels_block

    assert channels_block("# Base\n\n## Salud\n") == ""

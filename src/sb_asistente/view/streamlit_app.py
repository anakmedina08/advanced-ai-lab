"""Interfaz de prueba (Streamlit) con las tres funcionalidades: Q&A, Resumen y FAQ.

Ejecutar: ``uv run streamlit run src/sb_asistente/view/streamlit_app.py``
"""

import json

import pandas as pd
import streamlit as st

from sb_asistente.config import EVAL_RESULTS, GOLD_DIR, LLM_PROVIDER
from sb_asistente.evaluation import read_results, summarize_results
from sb_asistente.llm import prompts
from sb_asistente.llm.service import KnowledgeAssistant, build_llm, context_budget, load_knowledge

st.set_page_config(page_title="Asistente Seguros Bolívar", page_icon="🛡️", layout="wide")


@st.cache_resource(show_spinner="Cargando la base de conocimiento…")
def get_assistant(provider: str) -> KnowledgeAssistant:
    """Crea el asistente una vez por proveedor."""
    return KnowledgeAssistant(build_llm(provider), load_knowledge(max_tokens=context_budget(provider)))


def sidebar() -> tuple[str, str]:
    """Panel lateral: proveedor, versión de prompt y estadísticas del corpus."""
    st.sidebar.header("Configuración")
    provider = st.sidebar.selectbox(
        "Modelo", ["anthropic", "ollama"], index=0 if LLM_PROVIDER == "anthropic" else 1
    )
    version = st.sidebar.selectbox(
        "Versión del prompt (Q&A)",
        list(prompts.QA_SYSTEM),
        index=list(prompts.QA_SYSTEM).index("v3"),
        help="v1: ingenuo · v2: grounding simple · v3: zero-shot estructurado · v4: few-shot",
    )
    summary_path = GOLD_DIR / "resumen.json"
    if summary_path.is_file():
        s = json.loads(summary_path.read_text(encoding="utf-8"))
        st.sidebar.metric("Páginas en la base", s["documentos"])
        st.sidebar.metric("Chunks (Fase 2)", s["chunks"])
        st.sidebar.metric("Tokens de contexto (aprox.)", f"{s['tokens_conocimiento_est']:,}")
    st.sidebar.caption("Fuente: información pública de segurosbolivar.com · Proyecto académico UAO")
    return provider, version


METRIC_LABELS = {
    "keyword_hit_promedio": "Palabras clave",
    "tasa_cita_fuente": "Cita la fuente",
    "tasa_fallback_correcto": "Rechazo correcto",
}


def evaluation_tab() -> None:
    """Pestaña 📊: compara las versiones del prompt con los resultados de ``sb eval``."""
    results_dir = EVAL_RESULTS.parent
    summary = summarize_results(results_dir)
    if not summary:
        st.info("Aún no hay resultados. Ejecute, por ejemplo: `uv run sb eval --version v3`")
        return
    df = pd.DataFrame(summary)
    df["corrida"] = df["modelo"] + " · " + df["version"]
    st.subheader("Comparación de versiones del prompt")
    st.caption(
        "Proporción de 0 a 1 sobre el banco de preguntas (evaluacion/preguntas.yaml); más alto es mejor."
    )
    chart = df.set_index("corrida")[list(METRIC_LABELS)].rename(columns=METRIC_LABELS)
    st.bar_chart(chart, stack=False, height=320, color=["#2563eb", "#0d9488", "#9333ea"])
    table = df.drop(columns="corrida").rename(
        columns=METRIC_LABELS | {"latencia_promedio_s": "Latencia (s)", "preguntas": "Preguntas"}
    )
    st.dataframe(table, hide_index=True, width="stretch")

    st.subheader("Detalle por pregunta")
    choice = st.selectbox("Corrida", df["corrida"].tolist())
    modelo, version = choice.split(" · ")
    rows = read_results(results_dir / f"resultados_{modelo}_{version}.csv")
    detail = pd.DataFrame(rows)[
        [
            "id",
            "categoria",
            "pregunta",
            "respuesta",
            "keyword_hit",
            "cita_fuente",
            "fallback_ok",
            "latencia_s",
        ]
    ]
    st.dataframe(detail, hide_index=True, width="stretch")


def main() -> None:
    """Compone la página. La pestaña de Evaluación funciona aunque el modelo no esté disponible."""
    st.title("🛡️ Asistente de Seguros Bolívar · Personas y canales")
    provider, version = sidebar()
    try:
        assistant, error = get_assistant(provider), None
    except Exception as exc:  # noqa: BLE001 - se muestra al usuario
        assistant, error = None, f"No se pudo iniciar el asistente ({provider}): {exc}"

    qa, summary, faq, evaluation = st.tabs(
        ["💬 Preguntas y respuestas", "📝 Resumen", "❓ FAQ", "📊 Evaluación"]
    )
    with qa:
        if assistant is None:
            st.error(error)
        else:
            question = st.text_input("Escriba su pregunta", placeholder="¿Cuál es el WhatsApp de atención?")
            if st.button("Responder", type="primary", disabled=not question.strip()):
                with st.spinner("Consultando…"):
                    ans = assistant.answer(question, version=version)
                st.markdown(ans.text)
                st.caption(
                    f"{ans.latency_s:.1f} s · prompt {ans.prompt_version} · "
                    f"{'✅ cita fuente' if ans.cites_source else '⚠️ sin fuente'}"
                )
    with summary:
        if assistant is None:
            st.error(error)
        else:
            topic = st.selectbox("Tema", prompts.TOPICS, key="topic_summary")
            if st.button("Generar resumen"):
                with st.spinner("Resumiendo…"):
                    st.markdown(assistant.summarize(topic).text)
    with faq:
        if assistant is None:
            st.error(error)
        else:
            topic = st.selectbox("Tema", prompts.TOPICS, index=1, key="topic_faq")
            n = st.slider("Número de preguntas", 3, 10, 5)
            if st.button("Generar FAQ"):
                with st.spinner("Generando preguntas frecuentes…"):
                    st.markdown(assistant.faq(topic, n).text)
    with evaluation:
        evaluation_tab()


main()

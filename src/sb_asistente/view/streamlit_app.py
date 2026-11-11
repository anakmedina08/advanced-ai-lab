"""Interfaz (Streamlit): pipeline de scraping por etapas, Q&A con fuente, Resumen, FAQ y Evaluación.

Ejecutar: ``uv run streamlit run src/sb_asistente/view/streamlit_app.py``
"""

import json

import pandas as pd
import streamlit as st

from sb_asistente.config import BASE_URL, GOLD_DIR, LLM_PROVIDER
from sb_asistente.controller import assistant as ctrl
from sb_asistente.controller import pipeline

st.set_page_config(page_title="Asistente Seguros Bolívar", page_icon="🛡️", layout="wide")


@st.cache_resource(show_spinner="Cargando la base de conocimiento…")
def get_assistant(provider: str) -> ctrl.KnowledgeAssistant:
    """Crea el asistente con toda la base una vez por proveedor."""
    return ctrl.full_assistant(provider)


@st.cache_resource(show_spinner="Preparando el modo elegido (el índice RAG se crea la primera vez)…")
def get_mode_assistant(provider: str, mode: str) -> ctrl.QAAssistant:
    """Crea el asistente de Q&A de un modo una vez por proveedor."""
    return ctrl.build_assistant(provider, mode)


def answer_question(provider: str, question: str, version: str, mode: str) -> ctrl.Answer:
    """Responde con el modo de contexto elegido (toda la base, reducido, RAG o agente)."""
    chosen = get_assistant(provider) if mode == ctrl.DEFAULT_MODE else get_mode_assistant(provider, mode)
    return chosen.answer(question, version=version)


def sidebar() -> tuple[str, str, str]:
    """Panel lateral: proveedor, modo de contexto, versión de prompt y estadísticas del corpus."""
    st.sidebar.header("Configuración")
    provider = st.sidebar.selectbox(
        "Modelo", ["anthropic", "ollama"], index=0 if LLM_PROVIDER == "anthropic" else 1
    )
    modes = list(ctrl.MODES)
    mode = st.sidebar.selectbox(
        "Modo de contexto (Q&A)",
        modes,
        index=modes.index("reducido" if provider == "ollama" else ctrl.DEFAULT_MODE),
        format_func=ctrl.MODES.get,
        help="Toda la base: diseño de la Fase 1 (Claude). Reducido: fragmentos por palabras, rápido "
        "en CPU. RAG: fragmentos por embeddings locales (Ollama + Qdrant). Agente: Deep Agent que "
        "busca y delega el análisis de cada fragmento a un subagente.",
    )
    version = st.sidebar.selectbox(
        "Versión del prompt (Q&A)",
        list(ctrl.QA_VERSIONS),
        index=list(ctrl.QA_VERSIONS).index(ctrl.DEFAULT_QA_VERSION),
        help="v1: ingenuo · v2: grounding simple · v3: zero-shot estructurado · v4: few-shot",
        disabled=mode == "agente",
    )
    summary_path = GOLD_DIR / "resumen.json"
    if summary_path.is_file():
        s = json.loads(summary_path.read_text(encoding="utf-8"))
        st.sidebar.metric("Páginas en la base", s["documentos"])
        st.sidebar.metric("Chunks (Fase 2)", s["chunks"])
        st.sidebar.metric("Tokens de contexto (aprox.)", f"{s['tokens_conocimiento_est']:,}")
    st.sidebar.caption("Fuente: información pública de segurosbolivar.com · Proyecto académico UAO")
    return provider, version, mode


METRIC_LABELS = {
    "keyword_hit_promedio": "Palabras clave",
    "tasa_cita_fuente": "Cita la fuente",
    "tasa_fallback_correcto": "Rechazo correcto",
}


def evaluation_tab() -> None:
    """Pestaña 📊: compara las versiones del prompt con los resultados de ``sb eval``."""
    summary = ctrl.evaluation_summary()
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
    rows = ctrl.evaluation_detail(modelo, version)
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


def render_stages() -> None:
    """Tarjetas por etapa: descubrir → extraer → limpiar → deduplicar → enriquecer."""
    for stage in pipeline.stage_report():
        icon = "✅" if stage["hecha"] else "⏳"
        with st.expander(f"{icon} {stage['etapa']} · {stage['capa']}", expanded=True):
            metrics = stage["metricas"]
            principales = {k: v for k, v in metrics.items() if not k.startswith("  ·")}
            cols = st.columns(len(principales))
            for col, (name, value) in zip(cols, principales.items(), strict=True):
                col.metric(name, f"{value:,}" if isinstance(value, int) else value)
            detalle = {k.strip(" ·"): v for k, v in metrics.items() if k.startswith("  ·")}
            if detalle:
                st.caption("Motivos de descarte: " + " · ".join(f"{k}: {v}" for k, v in detalle.items()))


def pipeline_tab() -> None:
    """El proceso de scraping visible: etapas, métricas del corpus y re-ejecución en vivo."""
    st.subheader("Pipeline de scraping · Medallion (Bronze → Silver → Gold)")
    st.caption(
        f"Fuente: {BASE_URL} · respeta robots.txt y sitemap.xml · User-Agent identificado · "
        "1,5 s entre peticiones · timeout 15 s"
    )
    left, right = st.columns(2)
    if left.button("▶ Reprocesar Bronze → Silver → Gold (sin volver a la web)", type="primary"):
        with st.status("Ejecutando el pipeline…", expanded=True) as status:
            st.write("Limpiando HTML a Markdown y quitando boilerplate…")
            resumen = pipeline.process()
            st.write(f"Deduplicando: {len(resumen['descartadas_duplicadas'])} páginas repetidas descartadas")
            st.write(f"Enriqueciendo: {resumen['documentos']} documentos y {resumen['chunks']} chunks")
            status.update(label="Pipeline terminado", state="complete")
    if right.button("🔎 Descubrir en vivo (robots.txt + sitemap.xml)"):
        with st.spinner("Consultando robots.txt y sitemap.xml…"):
            try:
                plan = pipeline.discover(pipeline.new_session())
                st.success(
                    f"Sitemap: {plan['total_sitemap']} URLs · seleccionadas {len(plan['seleccionadas'])}"
                    f" · descartadas {len(plan['descartadas'])}"
                )
            except Exception as exc:  # noqa: BLE001 - sin red en la sala: se informa y se sigue
                st.warning(f"No se pudo consultar el sitio ({exc}); se muestran los datos ya capturados.")
    render_stages()
    rows = pipeline.corpus_table()
    if rows:
        st.subheader(f"Corpus Gold · {len(rows)} documentos con metadatos")
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    else:
        st.info("Aún no hay corpus. Ejecute: uv run python scripts/scrape_empresa.py")


def main() -> None:
    """Compone la página. La pestaña de Evaluación funciona aunque el modelo no esté disponible."""
    st.title("🛡️ Asistente de Seguros Bolívar · Personas y canales")
    provider, version, mode = sidebar()
    try:
        full = mode == ctrl.DEFAULT_MODE
        assistant, error = (get_assistant(provider) if full else None), None
    except Exception as exc:  # noqa: BLE001 - se muestra al usuario
        assistant, error = None, f"No se pudo iniciar el asistente ({provider}): {exc}"

    scraping, qa, summary, faq, evaluation = st.tabs(
        ["🕸️ Pipeline de scraping", "💬 Preguntas y respuestas", "📝 Resumen", "❓ FAQ", "📊 Evaluación"]
    )
    with scraping:
        pipeline_tab()
    with qa:
        if error:
            st.error(error)
        else:
            question = st.text_input("Escriba su pregunta", placeholder="¿Cuál es el WhatsApp de atención?")
            if st.button("Responder", type="primary", disabled=not question.strip()):
                with st.spinner(f"Consultando con {provider} ({ctrl.MODES[mode].lower()})…"):
                    try:
                        st.session_state["qa"] = answer_question(provider, question, version, mode)
                    except Exception as exc:  # noqa: BLE001 - p. ej., Ollama apagado o sin clave
                        st.session_state.pop("qa", None)
                        st.error(f"No se pudo responder con {provider}: {exc}")
            if "qa" in st.session_state:  # se conserva aunque la página se recargue
                ans = st.session_state["qa"]
                st.markdown(ans.text)
                st.caption(
                    f"{ans.latency_s:.1f} s · {ctrl.MODES[mode]} · prompt {ans.prompt_version} · "
                    f"{'✅ cita fuente' if ans.cites_source else '⚠️ sin fuente'}"
                )
                fuentes = ans.sources
                if fuentes:
                    st.markdown("**Fuentes citadas:**\n" + "\n".join(f"- [{u}]({u})" for u in fuentes))
    with summary:
        if assistant is None:
            st.error(error or "Resumen y FAQ usan toda la base: elija el modo «Toda la base».")
        else:
            topic = st.selectbox("Tema", ctrl.TOPICS, key="topic_summary")
            if st.button("Generar resumen"):
                with st.spinner("Resumiendo…"):
                    st.markdown(assistant.summarize(topic).text)
    with faq:
        if assistant is None:
            st.error(error or "Resumen y FAQ usan toda la base: elija el modo «Toda la base».")
        else:
            topic = st.selectbox("Tema", ctrl.TOPICS, index=1, key="topic_faq")
            n = st.slider("Número de preguntas", 3, 10, 5)
            if st.button("Generar FAQ"):
                with st.spinner("Generando preguntas frecuentes…"):
                    st.markdown(assistant.faq(topic, n).text)
    with evaluation:
        evaluation_tab()


main()

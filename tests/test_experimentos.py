"""Pruebas de la bitácora de experimentos (MLflow): dobles sin MLflow y una prueba real con base temporal."""

import csv

import pytest

from sb_asistente.config import EXPERIMENTO_QA, EXPERIMENTO_RECOMENDADOR, EXPERIMENTO_RECUPERACION
from sb_asistente.controller import experimentos as ctrl
from sb_asistente.model import experimentos
from sb_asistente.model.experimentos import BitacoraNula, Corrida
from sb_asistente.model.llm.service import Answer
from sb_asistente.view import cli

COLUMNAS = ["id", "categoria", "pregunta", "prompt_version", "respuesta", "keyword_hit", "cita_fuente",
            "fallback", "fallback_ok", "latencia_s", "calificacion_manual", "observaciones"]  # fmt: skip


class FakeBitacora:
    """Guarda las corridas en memoria y recuerda las etiquetas «origen» ya vistas."""

    def __init__(self) -> None:
        self.corridas: list[Corrida] = []

    def registrar(self, corrida):
        self.corridas.append(corrida)
        return f"run-{len(self.corridas)}"

    def existe(self, experimento, etiqueta, valor):
        return any(c.experimento == experimento and c.etiquetas.get(etiqueta) == valor for c in self.corridas)


@pytest.fixture
def bitacora(monkeypatch) -> FakeBitacora:
    fake = FakeBitacora()
    monkeypatch.setattr(ctrl, "bitacora", lambda: fake)
    return fake


def escribir_resultados(ruta, filas):
    with ruta.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNAS)
        w.writeheader()
        for i, (hit, cita, ok) in enumerate(filas):
            w.writerow({"id": f"P{i}", "categoria": "c", "pregunta": "¿?", "prompt_version": "v3", "respuesta": "r",  # noqa: E501
                        "keyword_hit": hit, "cita_fuente": cita, "fallback": False, "fallback_ok": ok,
                        "latencia_s": 1.5, "calificacion_manual": "", "observaciones": ""})  # fmt: skip


# --- Modelo ---------------------------------------------------------------------------------------
@pytest.mark.parametrize(("crudo", "limpio"), [("recall@5", "recall_at_5"), ("hit@10", "hit_at_10"), ("cita fuente", "cita fuente")])  # fmt: skip  # noqa: E501
def test_nombre_metrica_valido_para_mlflow(crudo, limpio):
    assert experimentos.nombre_metrica(crudo) == limpio


def test_bitacora_nula_no_registra_nada():
    nula = BitacoraNula()
    assert nula.registrar(Corrida("x", "y")) is None and not nula.existe("x", "origen", "z")


def test_sin_mlflow_o_apagado_se_usa_la_bitacora_nula(monkeypatch):
    monkeypatch.setattr(experimentos, "disponible", lambda: False)
    assert isinstance(experimentos.bitacora_por_defecto(), BitacoraNula)


def test_commit_actual_es_un_hash_corto():
    commit = experimentos.commit_actual()
    assert commit is None or (4 <= len(commit) <= 12 and commit.isalnum())


# --- Controlador ----------------------------------------------------------------------------------
@pytest.mark.parametrize(("etiqueta", "esperado"), [("anthropic", ("anthropic", "completo")), ("anthropic-rag", ("anthropic", "rag")), ("ollama-agente", ("ollama", "agente"))])  # fmt: skip  # noqa: E501
def test_proveedor_y_modo_desde_el_nombre_de_la_corrida(etiqueta, esperado):
    assert ctrl.proveedor_y_modo(etiqueta) == esperado


def test_corrida_eval_separa_parametros_y_metricas(tmp_path):
    archivo = tmp_path / "r.csv"
    archivo.write_text("x")
    metricas = {"preguntas": 25, "tasa_cita_fuente": 1.0, "latencia_promedio_s": 1.6}
    corrida = ctrl.corrida_eval("anthropic", "rag", "v3", metricas, archivo)
    assert corrida.experimento == EXPERIMENTO_QA and corrida.nombre == "anthropic · rag · v3"
    assert corrida.parametros["modo"] == "rag" and corrida.parametros["preguntas"] == 25
    assert corrida.metricas == {"tasa_cita_fuente": 1.0, "latencia_promedio_s": 1.6}
    assert corrida.artefactos == (archivo,)


def test_registrar_baselines_una_corrida_por_modelo(bitacora):
    resultado = {"popularidad": {"clientes": 900, "recall@5": 0.5, "ndcg@5": 0.3}, "segmento": {"clientes": 900, "recall@5": 0.64, "ndcg@5": 0.4}}  # fmt: skip  # noqa: E501
    ctrl.registrar_baselines(resultado, 5, {"entrada": "recomendador"})
    assert [c.experimento for c in bitacora.corridas] == [EXPERIMENTO_RECOMENDADOR] * 2
    assert bitacora.corridas[1].metricas == {"recall@5": 0.64, "ndcg@5": 0.4}
    assert bitacora.corridas[1].parametros["clientes_evaluados"] == 900


def test_registrar_recuperacion_guarda_hit_por_k(bitacora):
    ctrl.registrar_recuperacion("BM25", {4: 0.67, 10: 0.86}, 21)
    corrida = bitacora.corridas[0]
    assert corrida.experimento == EXPERIMENTO_RECUPERACION and corrida.metricas == {
        "hit@4": 0.67,
        "hit@10": 0.86,
    }


def test_importar_evaluaciones_carga_cada_csv_y_omite_las_muestras(bitacora, tmp_path):
    escribir_resultados(tmp_path / "resultados_anthropic_v3.csv", [(1.0, True, True), (0.5, True, False)])
    escribir_resultados(tmp_path / "resultados_anthropic-rag_v3.csv", [(0.5, True, True)])
    escribir_resultados(tmp_path / "resultados_ollama_v3_muestra2.csv", [(1.0, False, True)])
    estados = dict(ctrl.importar_evaluaciones(tmp_path))
    assert estados == {
        "resultados_anthropic-rag_v3.csv": "importado",
        "resultados_anthropic_v3.csv": "importado",
    }
    completo = next(c for c in bitacora.corridas if c.parametros["modo"] == "completo")
    assert (
        completo.metricas["keyword_hit_promedio"] == 0.75
        and completo.metricas["tasa_fallback_correcto"] == 0.5
    )


def test_importar_dos_veces_no_duplica(bitacora, tmp_path):
    escribir_resultados(tmp_path / "resultados_anthropic_v1.csv", [(1.0, False, True)])
    ctrl.importar_evaluaciones(tmp_path)
    assert dict(ctrl.importar_evaluaciones(tmp_path)) == {"resultados_anthropic_v1.csv": "ya estaba"}
    assert len(bitacora.corridas) == 1


# --- Vista (CLI) ----------------------------------------------------------------------------------
class FakeAsistente:
    def answer(self, question, version="v3", skill=None):
        return Answer("Respuesta.\nFuente: https://www.segurosbolivar.com/soat", "qa", version, 0.2, 10)


def test_cli_eval_registra_la_corrida(bitacora, monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cli, "_assistant", lambda provider, mode="completo": FakeAsistente())
    monkeypatch.setattr("sb_asistente.controller.assistant.EVAL_RESULTS", tmp_path / "resultados.csv")
    assert cli.main(["eval", "--provider", "ollama", "--modo", "rag", "--limit", "2"]) == 0
    corrida = bitacora.corridas[0]
    assert corrida.parametros["modo"] == "rag" and corrida.parametros["proveedor"] == "ollama"
    assert corrida.artefactos[0].name == "resultados_ollama-rag_v3_muestra2.csv"
    assert "Registrado en MLflow" in capsys.readouterr().out


def test_cli_mlflow_sin_extra_explica_como_instalarlo(monkeypatch, capsys):
    monkeypatch.setattr(experimentos, "disponible", lambda: False)
    assert cli.main(["mlflow", "importar"]) == 1
    assert "uv sync --extra mlflow" in capsys.readouterr().out


# --- Integración real con MLflow (se salta si el extra no está instalado) -------------------------
def test_mlflow_real_registra_y_encuentra_la_corrida(tmp_path):
    pytest.importorskip("mlflow")
    real = experimentos.BitacoraMlflow(f"sqlite:///{(tmp_path / 'm.db').as_posix()}", tmp_path / "art")
    archivo = tmp_path / "respuestas.csv"
    archivo.write_text("id,ok\nP1,1\n")
    corrida = Corrida(
        EXPERIMENTO_QA, "prueba", {"modo": "rag"}, {"recall@5": 0.7}, (archivo,), {"origen": "csv:x"}
    )
    run_id = real.registrar(corrida)
    import mlflow

    run = mlflow.get_run(run_id)
    assert run.data.metrics == {"recall_at_5": 0.7} and run.data.params == {"modo": "rag"}
    assert real.existe(EXPERIMENTO_QA, "origen", "csv:x") and not real.existe(
        EXPERIMENTO_QA, "origen", "otro"
    )
    assert "commit" in run.data.tags


def test_mlflow_real_lee_las_corridas_para_el_panel(tmp_path):
    pytest.importorskip("mlflow")
    real = experimentos.BitacoraMlflow(f"sqlite:///{(tmp_path / 'm.db').as_posix()}", tmp_path / "art")
    real.registrar(Corrida(EXPERIMENTO_RECUPERACION, "BM25", {"metodo": "BM25"}, {"hit@10": 0.86}))
    [corrida] = real.corridas(EXPERIMENTO_RECUPERACION)
    assert corrida["nombre"] == "BM25" and corrida["metricas"] == {"hit_at_10": 0.86}
    assert real.corridas("no-existe") == [] and BitacoraNula().corridas("x") == []

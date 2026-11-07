"""Pruebas de la API FastAPI: contratos Pydantic y códigos HTTP (sin red ni API de pago)."""

import pytest
from fastapi.testclient import TestClient

from sb_asistente.controller import recomendador
from sb_asistente.model.llm.service import Answer
from sb_asistente.view import api
from sb_asistente.view.schemas import extraer_fuentes, rechazar_datos_personales

URL = "https://www.segurosbolivar.com/canales-de-atencion"


def respuesta_falsa(pregunta, version, modo, proveedor):
    return Answer(f"Escríbanos por WhatsApp. Fuente: {URL}.", "qa", version, 0.01, 100)


class AsistenteFalso:
    def summarize(self, tema):
        return Answer(f"Resumen de {tema}. Fuente: {URL}", "resumen", "v3", 0.01, 100)

    def faq(self, tema, n):
        return Answer("\n".join(f"P{i}" for i in range(n)), "faq", "v3", 0.01, 100)


@pytest.fixture
def client():
    api.app.dependency_overrides[api.get_responder] = lambda: respuesta_falsa
    api.app.dependency_overrides[api.get_asistente] = lambda: lambda proveedor: AsistenteFalso()
    yield TestClient(api.app)
    api.app.dependency_overrides.clear()


def test_salud_responde_ok(client):
    cuerpo = client.get("/salud").json()
    assert cuerpo["estado"] == "ok" and "corpus_listo" in cuerpo


def test_pregunta_devuelve_fuentes(client):
    r = client.post("/preguntas", json={"pregunta": "¿Cuál es el WhatsApp?"})
    assert r.status_code == 200
    assert r.json()["fuentes"] == [URL] and r.json()["cita_fuente"] is True


def test_pregunta_vacia_es_422(client):
    assert client.post("/preguntas", json={"pregunta": ""}).status_code == 422


def test_pregunta_con_cedula_es_rechazada(client):
    r = client.post("/preguntas", json={"pregunta": "Mi cédula es 1012345678, ¿tengo póliza?"})
    assert r.status_code == 422 and "datos personales" in r.text


def test_pregunta_con_correo_es_rechazada(client):
    assert client.post("/preguntas", json={"pregunta": "escríbanme a ana@correo.com"}).status_code == 422


def test_campo_desconocido_es_rechazado(client):
    assert client.post("/preguntas", json={"pregunta": "hola hola", "extra": 1}).status_code == 422


def test_proveedor_invalido_es_rechazado(client):
    assert client.post("/preguntas", json={"pregunta": "hola hola", "proveedor": "gpt"}).status_code == 422


def test_version_invalida_es_rechazada(client):
    assert client.post("/preguntas", json={"pregunta": "hola hola", "version": "v9"}).status_code == 422


def test_base_no_lista_es_503(client):
    def sin_base(*args):
        raise FileNotFoundError("chunks.jsonl")

    api.app.dependency_overrides[api.get_responder] = lambda: sin_base
    assert client.post("/preguntas", json={"pregunta": "hola hola"}).status_code == 503


def test_resumen(client):
    r = client.post("/resumen", json={"tema": "Seguros de hogar"})
    assert r.status_code == 200 and r.json()["tarea"] == "resumen"


def test_faq_respeta_n(client):
    assert client.post("/faq", json={"tema": "Canales", "n": 3}).json()["texto"].count("P") == 3


def test_faq_n_fuera_de_rango(client):
    assert client.post("/faq", json={"tema": "Canales", "n": 50}).status_code == 422


def test_pipeline_sin_datos_devuelve_etapas_pendientes(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        api.pipeline,
        "stage_report",
        lambda: [{"etapa": "1. Descubrir", "capa": "robots", "hecha": False, "metricas": {"URLs": 0}}],
    )
    assert client.get("/pipeline").json()[0]["hecha"] is False


def test_recomendaciones(client, monkeypatch, tmp_path):
    recomendador.generar(300, 7, tmp_path)
    cliente = recomendador.leer_tablas(tmp_path)["clientes"]["cliente_id"].iloc[0]
    original = recomendador.recomendar
    monkeypatch.setattr(api.recomendador, "recomendar", lambda c, k: original(c, k, tmp_path))
    r = client.get(f"/recomendaciones/{cliente}", params={"k": 3})
    assert r.status_code == 200 and len(r.json()["recomendaciones"]) == 3


def test_recomendaciones_cliente_desconocido_es_404(client, monkeypatch, tmp_path):
    recomendador.generar(300, 7, tmp_path)
    original = recomendador.recomendar
    monkeypatch.setattr(api.recomendador, "recomendar", lambda c, k: original(c, k, tmp_path))
    assert client.get("/recomendaciones/NO-EXISTE").status_code == 404


def test_recomendaciones_k_invalido_es_422(client):
    assert client.get("/recomendaciones/X", params={"k": 0}).status_code == 422


def test_extraer_fuentes_sin_duplicados():
    texto = f"Ver {URL}. Y otra vez {URL}, y https://otro.com"
    assert extraer_fuentes(texto) == [URL]


def test_rechazar_datos_personales_acepta_texto_normal():
    assert rechazar_datos_personales("  ¿Cubre el SOAT 2026?  ") == "¿Cubre el SOAT 2026?"

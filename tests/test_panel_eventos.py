"""Panel en vivo de Yellowdata (SPEC-082): eventos sin texto del usuario, opcionales y que nunca rompen.

Cada prueba sigue Arrange / Act / Assert. No hay red: ``urlopen`` y los hilos se reemplazan por dobles.
"""

import json
from pathlib import Path

import pytest
import yaml

from sb_asistente.model import panel
from sb_asistente.view import mcp

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture
def capturas(monkeypatch: pytest.MonkeyPatch) -> list:
    """Configura el panel y guarda cada petición en vez de enviarla."""
    monkeypatch.setenv("AGENT_EVENTS_URL", "http://yellowdata:3000/api/agent-events")
    monkeypatch.setenv("AGENT_EVENTS_TOKEN", "token-de-prueba")
    enviadas: list = []

    class _Respuesta:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def _urlopen(peticion, timeout):
        enviadas.append((peticion, timeout))
        return _Respuesta()

    monkeypatch.setattr(panel.urllib.request, "urlopen", _urlopen)
    return enviadas


def test_sin_variables_no_publica_nada(monkeypatch):
    # Arrange
    monkeypatch.delenv("AGENT_EVENTS_URL", raising=False)
    monkeypatch.delenv("AGENT_EVENTS_TOKEN", raising=False)
    monkeypatch.setattr(panel.urllib.request, "urlopen", lambda *a, **k: pytest.fail("no debía enviar"))
    # Act / Assert
    assert panel.publicar("yolo26l", "detección", esperar=True) is False


def test_publica_solo_los_campos_del_panel_con_el_token_en_la_cabecera(capturas):
    # Act
    assert panel.publicar("whatsapp", "buscar_conocimiento", "OpenClaw → MCP", esperar=True)
    # Assert
    peticion, timeout = capturas[0]
    cuerpo = json.loads(peticion.data)
    assert peticion.full_url == "http://yellowdata:3000/api/agent-events"
    assert peticion.get_header("Authorization") == "Bearer token-de-prueba"
    assert set(cuerpo) == {"ts", "evento", "agente", "herramienta", "comando", "ok"}
    assert cuerpo["evento"] == "Tecnologia" and cuerpo["herramienta"] == "buscar_conocimiento"
    assert timeout == panel.TIMEOUT_S


def test_recorta_los_campos_largos(capturas):
    # Act
    panel.publicar("a" * 300, "b" * 300, "c" * 300, esperar=True)
    # Assert
    cuerpo = json.loads(capturas[0][0].data)
    assert all(len(cuerpo[k]) == 120 for k in ("agente", "herramienta", "comando"))


def test_un_fallo_de_red_no_rompe_la_respuesta(monkeypatch, capturas):
    # Arrange
    def _caida(*a, **k):
        raise OSError("sin red")

    monkeypatch.setattr(panel.urllib.request, "urlopen", _caida)
    # Act / Assert: no lanza
    assert panel.publicar("yolo26l", "detección", esperar=True) is True


def test_por_defecto_envia_en_un_hilo_daemon(monkeypatch, capturas):
    # Arrange
    hilos: list = []

    class _Hilo:
        def __init__(self, target, args, daemon):
            hilos.append(daemon)
            self.target, self.args = target, args

        def start(self):
            self.target(*self.args)

    monkeypatch.setattr(panel.threading, "Thread", _Hilo)
    # Act
    panel.publicar("memoria", "checkpoint")
    # Assert
    assert hilos == [True] and len(capturas) == 1


def test_langsmith_solo_se_avisa_con_el_tracing_activo(monkeypatch):
    # Arrange
    avisos: list = []
    monkeypatch.setattr(panel, "publicar", lambda *a, **k: avisos.append((a, k)) or True)
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    # Act / Assert
    assert panel.turno_trazado(812.4) is False and avisos == []
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    assert panel.turno_trazado(812.4, "ValueError") is True
    assert avisos == [(("langsmith", "traza del turno", "812 ms"), {"ok": False})]


def test_la_tool_del_mcp_avisa_el_canal_whatsapp_sin_argumentos(monkeypatch):
    # Arrange
    avisos: list = []
    monkeypatch.setattr(mcp, "tool_por_mcp", avisos.append)

    class _Tool:
        def invoke(self, entrada):
            return f"ok {entrada['consulta']}"

    envuelta = mcp._ConAviso("buscar_conocimiento", _Tool())
    # Act
    resultado = envuelta.invoke({"consulta": "texto privado del usuario"})
    # Assert
    assert resultado == "ok texto privado del usuario"
    assert avisos == ["buscar_conocimiento"]


def test_cada_job_del_pipeline_avisa_al_panel_sin_valores_en_el_repo():
    # Arrange
    ci = yaml.safe_load((RAIZ / ".gitlab-ci.yml").read_text(encoding="utf-8"))
    aviso = ci[".aviso_panel"]["after_script"][0]
    # Act
    jobs = {
        "lint": ci[".uv"]["after_script"],
        "test": ci[".uv"]["after_script"],
        "build_api": ci[".docker"]["after_script"],
        "build_frontend": ci[".docker"]["after_script"],
        "deploy": ci["deploy"]["after_script"],
    }
    # Assert
    assert all(aviso in pasos for pasos in jobs.values())
    assert ci["deploy"]["after_script"][0] == "rm -f ~/.ssh/id_ed25519"  # la llave se borra primero
    assert "$AGENT_EVENTS_TOKEN" in aviso and "|| true" in aviso


def test_el_panel_conserva_sus_eventos_entre_deploys():
    # Arrange
    compose = yaml.safe_load((RAIZ / "deploy/docker-compose.prod.yml").read_text(encoding="utf-8"))
    yellowdata = compose["services"]["yellowdata"]
    # Act / Assert
    assert yellowdata["environment"]["AGENT_EVENTS_DIR"] == "/app/.data"
    assert "yellowdata_eventos:/app/.data" in yellowdata["volumes"]
    assert "yellowdata_eventos" in compose["volumes"]

"""Pruebas del hook de telemetría: nada privado sale del equipo (AAA, sin red)."""

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "agent_events.py"
spec = importlib.util.spec_from_file_location("agent_events", SCRIPT)
events = importlib.util.module_from_spec(spec)
spec.loader.exec_module(events)


@pytest.fixture(autouse=True)
def proyecto(tmp_path, monkeypatch):
    monkeypatch.setattr(events, "ROOT", tmp_path)
    monkeypatch.setattr(events, "LOG", tmp_path / "logs" / "agent-events.jsonl")
    monkeypatch.delenv("AGENT_EVENTS_URL", raising=False)
    return tmp_path


def test_comando_se_reduce_a_etiqueta():
    assert events.command_label("ANTHROPIC_API_KEY=sk-123 uv run pytest -q") == "pytest"


def test_comando_desconocido_no_se_expone():
    assert events.command_label("curl -H 'token: abc' https://x") == "bash"


def test_ruta_de_datos_es_privada(proyecto):
    assert events.safe_path(str(proyecto / "data" / "gold" / "corpus.jsonl")) is None


def test_env_es_privado(proyecto):
    assert events.safe_path(str(proyecto / ".env")) is None


def test_ruta_fuera_del_repo_es_privada():
    assert events.safe_path("/etc/passwd") is None


def test_ruta_de_codigo_queda_relativa(proyecto):
    assert events.safe_path(str(proyecto / "src" / "app.py")) == "src/app.py"


def test_sanitize_descarta_contenido_y_respuesta(proyecto):
    payload = {
        "hook_event_name": "PostToolUse",
        "session_id": "abcdef123456",
        "tool_name": "Write",
        "tool_input": {"file_path": str(proyecto / "src" / "x.py"), "content": "SECRETO"},
        "tool_response": {"success": True, "output": "SECRETO"},
    }
    evento = events.sanitize(payload)
    assert "SECRETO" not in json.dumps(evento)
    assert evento["archivo"] == "src/x.py" and evento["ok"] is True and evento["sesion"] == "abcdef12"


def test_sanitize_identifica_subagente():
    evento = events.sanitize({"hook_event_name": "SubagentStart", "agent_type": "probador"})
    assert evento["agente"] == "probador"


def test_main_escribe_registro_local(proyecto, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO('{"hook_event_name": "Stop"}'))
    assert events.main() == 0
    linea = (proyecto / "logs" / "agent-events.jsonl").read_text(encoding="utf-8")
    assert json.loads(linea)["evento"] == "Stop"


def test_main_nunca_falla_con_json_invalido(monkeypatch):
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO("{no es json"))
    assert events.main() == 0


def test_publica_con_token(monkeypatch):
    enviados = []

    class Resp:
        def close(self):
            pass

    def falso(request, timeout):
        enviados.append((request.full_url, request.headers["Authorization"], timeout))
        return Resp()

    monkeypatch.setenv("AGENT_EVENTS_URL", "https://yellowdata.com.co/api/agent-events")
    monkeypatch.setenv("AGENT_EVENTS_TOKEN", "t0k")
    monkeypatch.setattr(events.urllib.request, "urlopen", falso)
    events.publish({"evento": "Stop"})
    assert enviados == [("https://yellowdata.com.co/api/agent-events", "Bearer t0k", 2)]

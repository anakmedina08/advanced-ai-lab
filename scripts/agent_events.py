"""Hook de Claude Code: convierte cada evento de agentes en un registro saneado y lo publica.

Lo llaman los hooks de ``.claude/settings.json`` (SessionStart, SubagentStart, SubagentStop,
PostToolUse y Stop) con el JSON del evento por la entrada estándar. Hace dos cosas:

1. Agrega una línea a ``logs/agent-events.jsonl`` (no versionado).
2. Si ``AGENT_EVENTS_URL`` está definida, envía el evento al panel en vivo de
   yellowdata.com.co/casos con ``Authorization: Bearer $AGENT_EVENTS_TOKEN``.

Privacidad: el evento es público, así que NUNCA lleva prompts, contenido de archivos, salidas
de herramientas ni comandos completos; solo el tipo de evento, el agente, la herramienta, una
etiqueta del comando (``pytest``, ``ruff``…) y rutas relativas fuera de ``data/`` y ``.env``.
Nunca rompe la sesión: ante cualquier error termina con código 0.
Solo usa la biblioteca estándar para que el hook sea rápido.
"""

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parents[1]))
LOG = ROOT / "logs" / "agent-events.jsonl"
PRIVATE_PREFIXES = ("data/", ".env", "logs/", ".git/")
COMMAND_LABELS = (
    ("pytest", "pytest"),
    ("ruff", "ruff"),
    ("uv lock", "uv lock"),
    ("git commit", "git commit"),
    ("git push", "git push"),
    ("gh pr", "pull request"),
    ("pre-commit", "pre-commit"),
    ("gga", "gga"),
    ("docker", "docker"),
    ("make", "make"),
    ("sb ", "sb cli"),
)


def _load_env() -> None:
    """Lee AGENT_EVENTS_* del .env sin dependencias (no pisa variables ya definidas)."""
    env = ROOT / ".env"
    if not env.is_file():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip().startswith("AGENT_EVENTS_"):
            os.environ.setdefault(key.strip(), value.strip())


def command_label(command: str) -> str:
    """Etiqueta segura de un comando de Bash (nunca el comando completo)."""
    text = f" {command.strip()} "
    for needle, label in COMMAND_LABELS:
        if f" {needle}" in text or f"/{needle}" in text:
            return label
    return "bash"


def safe_path(path: str) -> str | None:
    """Ruta relativa al proyecto, o ``None`` si es privada o está fuera del repositorio."""
    if not path:
        return None
    try:
        rel = Path(path).resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return None
    return None if rel.startswith(PRIVATE_PREFIXES) else rel


def sanitize(payload: dict[str, object]) -> dict[str, object]:
    """Reduce el JSON del hook a los campos públicos del panel."""
    kind = str(payload.get("hook_event_name", "desconocido"))
    tool_input = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
    agent = payload.get("agent_type") or payload.get("subagent_type") or tool_input.get("subagent_type")
    event: dict[str, object] = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "evento": kind,
        "sesion": str(payload.get("session_id", ""))[:8],
        "agente": str(agent) if agent else "lider",
    }
    tool = payload.get("tool_name")
    if tool:
        event["herramienta"] = str(tool)
    if tool == "Bash":
        event["comando"] = command_label(str(tool_input.get("command", "")))
    path = safe_path(str(tool_input.get("file_path", "")))
    if path:
        event["archivo"] = path
    response = payload.get("tool_response")
    if isinstance(response, dict) and "success" in response:
        event["ok"] = bool(response["success"])
    return event


def publish(event: dict[str, object]) -> None:
    """Escribe el registro local y, si hay URL, lo envía al panel (timeout corto)."""
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    url = os.environ.get("AGENT_EVENTS_URL", "").strip()
    if not url:
        return
    request = urllib.request.Request(
        url,
        data=json.dumps(event).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ.get('AGENT_EVENTS_TOKEN', '')}",
            "User-Agent": "sb-asistente-agent-events/1.0",
        },
        method="POST",
    )
    urllib.request.urlopen(request, timeout=2).close()  # noqa: S310 - URL configurada por el equipo


def main() -> int:
    """Punto de entrada del hook: lee stdin, sanea y publica sin interrumpir la sesión."""
    try:
        _load_env()
        publish(sanitize(json.loads(sys.stdin.read() or "{}")))
    except Exception as exc:  # noqa: BLE001 - un hook de telemetría jamás debe bloquear al agente
        print(f"agent_events: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

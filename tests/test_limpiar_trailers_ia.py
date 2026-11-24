"""Pruebas del hook commit-msg que quita trailers de IA (scripts/limpiar_trailers_ia.py)."""

import importlib.util
import sys
from pathlib import Path

RUTA = Path(__file__).resolve().parents[1] / "scripts" / "limpiar_trailers_ia.py"
spec = importlib.util.spec_from_file_location("limpiar_trailers_ia", RUTA)
limpiar_trailers_ia = importlib.util.module_from_spec(spec)
sys.modules["limpiar_trailers_ia"] = limpiar_trailers_ia
spec.loader.exec_module(limpiar_trailers_ia)


def test_quita_coautor_y_sesion() -> None:
    msg = "feat: x\n\nCuerpo\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_1\n"
    assert limpiar_trailers_ia.limpiar(msg) == "feat: x\n\nCuerpo\n"


def test_respeta_coautores_humanos() -> None:
    msg = "fix: y\n\nCo-Authored-By: Katherine Medina <k@example.com>\n"
    assert limpiar_trailers_ia.limpiar(msg) == msg


def test_es_idempotente(tmp_path: Path) -> None:
    archivo = tmp_path / "COMMIT_EDITMSG"
    archivo.write_text(
        "docs: z\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n", encoding="utf-8"
    )
    limpiar_trailers_ia.main(["hook", str(archivo)])
    primero = archivo.read_text(encoding="utf-8")
    limpiar_trailers_ia.main(["hook", str(archivo)])
    assert archivo.read_text(encoding="utf-8") == primero == "docs: z\n"

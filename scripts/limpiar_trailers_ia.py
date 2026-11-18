"""Hook commit-msg: quita del mensaje los trailers que agregan los agentes de IA.

Elimina líneas como ``Co-Authored-By: Claude …``, ``Claude-Session: …`` y
``🤖 Generated with …``. Así, los commits quedan a nombre de la persona y el uso de IA se
declara en ``docs/politica-uso-ia.md``. Es idempotente y no falla si no hay nada que quitar.
"""

import re
import sys
from pathlib import Path

TRAILERS_IA = re.compile(
    r"^(co-authored-by:.*(claude|anthropic|copilot|openai|cursor|devin).*"
    r"|claude-session:.*"
    r"|.*generated with \[?claude code.*"
    r"|https://claude\.ai/code/session_\S+)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def limpiar(texto: str) -> str:
    """Devuelve el mensaje sin trailers de IA y sin líneas en blanco sobrantes al final."""
    return re.sub(r"\n{3,}", "\n\n", TRAILERS_IA.sub("", texto)).rstrip() + "\n"


def main(argv: list[str]) -> int:
    """Reescribe en sitio el archivo del mensaje que git pasa como argumento."""
    ruta = Path(argv[1])
    original = ruta.read_text(encoding="utf-8")
    limpio = limpiar(original)
    if limpio != original:
        ruta.write_text(limpio, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

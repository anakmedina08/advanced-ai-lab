"""Hook commit-msg: exige Conventional Commits (feat, fix, docs, …) en la primera línea."""

import re
import sys
from pathlib import Path

TYPES = "feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert"
PATTERN = re.compile(rf"^({TYPES})(\([\w\-./]+\))?!?: \S.{{0,99}}$")


def is_valid(first_line: str) -> bool:
    """True si la línea cumple el formato o es un merge/revert generado por git."""
    return bool(PATTERN.match(first_line)) or first_line.startswith(("Merge ", 'Revert "'))


def main(argv: list[str]) -> int:
    """Lee el archivo del mensaje (argumento de git) y valida su primera línea."""
    first = Path(argv[1]).read_text(encoding="utf-8").splitlines()[0].strip()
    if is_valid(first):
        return 0
    print(
        f"ERROR: mensaje no semántico: {first!r}\n  Use: <tipo>(<alcance>): <descripción>  · tipos: {TYPES}"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

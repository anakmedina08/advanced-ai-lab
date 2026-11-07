"""Crea o actualiza el tablero Kanban de GitHub desde ``openspec/.../tasks.md``.

Uso (GitHub CLI autenticado con permiso ``project``: ``gh auth refresh -s project``):

    uv run python scripts/crear_kanban.py --repo anakmedina08/advanced-ai-lab --dry-run
    uv run python scripts/crear_kanban.py --repo anakmedina08/advanced-ai-lab --project 1

Idempotente: si ya existe un issue con el mismo ``[T-NN]`` se reutiliza; las tareas marcadas con
``[x]`` se cierran. Así el tablero y la spec nunca se contradicen.
"""

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

SPECS = Path(__file__).resolve().parents[1] / "openspec" / "specs"
# Todas las fases: fase1-base-conocimiento, fase2-producto-unico, … (IDs T-NN únicos entre fases)
TASKS_FILES = sorted(SPECS.glob("*/tasks.md"))
LINE = re.compile(
    r"^- \[(?P<done>[ x])\] (?P<id>T-\d+) \[(?P<label>[\w-]+)\] (?P<title>.+?) \((?P<owner>[^)]+)\)$"
)


@dataclass(frozen=True, slots=True)
class Task:
    """Una tarea de la spec."""

    id: str
    label: str
    title: str
    owner: str
    done: bool


def parse_tasks(text: str) -> list[Task]:
    """Lee las líneas con formato ``- [x] T-NN [etiqueta] Título (responsable)``."""
    tasks = []
    for line in text.splitlines():
        match = LINE.match(line.strip())
        if match:
            tasks.append(
                Task(match["id"], match["label"], match["title"], match["owner"], match["done"] == "x")
            )
    return tasks


def body(task: Task) -> str:
    """Cuerpo del issue."""
    return (
        f"**Responsable:** {task.owner}\n\n"
        "_Generado desde `openspec/specs/*/tasks.md`. "
        "Para cambiarlo, edite la spec y vuelva a ejecutar `scripts/crear_kanban.py`._"
    )


def gh(*args: str, dry: bool) -> str:
    """Ejecuta ``gh`` (o solo lo imprime en modo ensayo)."""
    print("gh", " ".join(a if len(a) < 70 else a[:67] + "..." for a in args))
    if dry:
        return "https://github.com/OWNER/REPO/issues/0"
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout.strip()


def main() -> None:
    """Sincroniza issues y tablero con la spec."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--repo", required=True, help="OWNER/REPO")
    parser.add_argument("--project", type=int, help="Número del GitHub Project (opcional)")
    parser.add_argument("--dry-run", action="store_true", help="Solo muestra los comandos")
    args = parser.parse_args()
    tasks = parse_tasks("\n".join(f.read_text(encoding="utf-8") for f in TASKS_FILES))
    owner = args.repo.split("/")[0]
    existing: dict[str, dict] = {}
    if not args.dry_run:
        listed = subprocess.run(
            [
                "gh",
                "issue",
                "list",
                "--repo",
                args.repo,
                "--state",
                "all",
                "--limit",
                "200",
                "--json",
                "title,url,state",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        existing = {i["title"].split("]")[0] + "]": i for i in json.loads(listed or "[]")}
    for task in tasks:
        title = f"[{task.id}] {task.title}"
        previous = existing.get(f"[{task.id}]")
        if previous:
            url = previous["url"]
            gh(
                "issue",
                "edit",
                url,
                "--title",
                title,
                "--body",
                body(task),
                "--add-label",
                task.label,
                dry=args.dry_run,
            )
        else:
            url = gh(
                "issue",
                "create",
                "--repo",
                args.repo,
                "--title",
                title,
                "--body",
                body(task),
                "--label",
                task.label,
                dry=args.dry_run,
            )
        if args.project:
            gh("project", "item-add", str(args.project), "--owner", owner, "--url", url, dry=args.dry_run)
        if task.done and (not previous or previous["state"] == "OPEN"):
            gh("issue", "close", url, "--reason", "completed", dry=args.dry_run)
    pending = sum(not t.done for t in tasks)
    print(f"\n{len(tasks)} tareas · {pending} pendientes.")


if __name__ == "__main__":
    main()

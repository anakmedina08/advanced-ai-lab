"""Pruebas del generador del tablero (AAA, sin red ni gh)."""

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "crear_kanban.py"
spec = importlib.util.spec_from_file_location("crear_kanban", SCRIPT)
kanban = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kanban)


def test_parse_reads_done_task():
    tasks = kanban.parse_tasks("- [x] T-01 [data] Descubrir sitemap (Daniel)")
    assert tasks[0].done and tasks[0].id == "T-01"


def test_parse_reads_pending_task_label_and_owner():
    task = kanban.parse_tasks("- [ ] T-14 [ml] Evaluar prompts (Daniel y Katherine)")[0]
    assert (task.label, task.owner, task.done) == ("ml", "Daniel y Katherine", False)


def test_parse_ignores_other_lines():
    assert kanban.parse_tasks("# Tareas\n\ntexto libre\n- [ ] sin id") == []


def _todas():
    return "\n".join(f.read_text(encoding="utf-8") for f in kanban.TASKS_FILES)


def test_hay_tasks_de_ambas_fases():
    assert len(kanban.TASKS_FILES) >= 2


def test_ids_unicos_entre_fases():
    ids = [t.id for t in kanban.parse_tasks(_todas())]
    assert len(ids) == len(set(ids))


def test_spec_tasks_file_has_tasks():
    assert len(kanban.parse_tasks(_todas())) >= 10


def test_spec_labels_exist_in_labels_yml():
    labels = (SCRIPT.parents[1] / ".github" / "labels.yml").read_text(encoding="utf-8")
    used = {t.label for t in kanban.parse_tasks(_todas())}
    assert all(f"- name: {label}" in labels for label in used)

"""El banco de evaluación se convierte en ejemplos de LangSmith sin red."""

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "langsmith_dataset.py"
spec = importlib.util.spec_from_file_location("langsmith_dataset", SCRIPT)
modulo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modulo)


def test_ejemplos_tienen_inputs_outputs_y_metadata():
    ejemplos = modulo.ejemplos()
    assert len(ejemplos) >= 20
    primero = ejemplos[0]
    assert set(primero) == {"inputs", "outputs", "metadata"} and "pregunta" in primero["inputs"]


def test_dry_run_no_usa_red(capsys):
    assert modulo.main(["--dry-run"]) == 0
    assert "ejemplos" in capsys.readouterr().out

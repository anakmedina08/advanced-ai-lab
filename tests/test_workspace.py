"""El workspace del agente existe y es coherente (SPEC-079, ítem 3.3)."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
WORKSPACE = RAIZ / "workspace"

ARCHIVOS = ("SOUL.md", "USER.md", "MEMORY.md", "AGENTS.md", "bitacora.md")


def test_workspace_tiene_los_archivos_clave():
    # Arrange / Act
    presentes = {nombre: (WORKSPACE / nombre).is_file() for nombre in ARCHIVOS}
    # Assert
    assert all(presentes.values()), presentes
    assert (RAIZ / "AGENTS.md").is_file(), "el AGENTS.md de la raíz debe existir"


def test_workspace_define_identidad_y_fuentes():
    # Arrange
    soul = (WORKSPACE / "SOUL.md").read_text(encoding="utf-8")
    memoria = (WORKSPACE / "MEMORY.md").read_text(encoding="utf-8")
    # Act / Assert
    assert "Seguros Bolívar" in soul
    assert "CONSTITUTION.md" in memoria

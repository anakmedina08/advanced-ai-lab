"""El pipeline de GitLab y el espejo desde GitHub (SPEC-074) son válidos y no exponen secretos.

Cada prueba sigue Arrange / Act / Assert y solo lee los YAML del repositorio.
"""

from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]


def _yaml(ruta: str) -> dict:
    return yaml.safe_load((RAIZ / ruta).read_text(encoding="utf-8"))


def test_el_pipeline_de_gitlab_tiene_lint_test_y_deteccion_de_secretos():
    # Arrange / Act
    ci = _yaml(".gitlab-ci.yml")
    # Assert
    assert ci["stages"][:2] == ["lint", "test"]
    assert {"lint", "test"} <= set(ci)
    assert {"template": "Jobs/Secret-Detection.gitlab-ci.yml"} in ci["include"]


def test_el_pipeline_usa_uv_ruff_y_pytest_con_el_mismo_minimo_de_cobertura_que_github():
    # Arrange
    ci = _yaml(".gitlab-ci.yml")
    github = (RAIZ / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    # Act
    pruebas = " ".join(ci["test"]["script"])
    # Assert
    assert ci[".uv"]["before_script"] == ["uv sync --frozen"]
    assert ci["lint"]["extends"] == ci["test"]["extends"] == ".uv"
    assert "uv run ruff check ." in ci["lint"]["script"]
    assert "--cov-fail-under=85" in pruebas and "--cov-fail-under=85" in github
    assert ci[".uv"]["image"].startswith("ghcr.io/astral-sh/uv:python3.13")


def test_el_espejo_solo_copia_develop_y_main_y_verifica_la_huella_de_gitlab():
    # Arrange / Act
    espejo = _yaml(".github/workflows/espejo-gitlab.yml")
    paso = espejo["jobs"]["espejo"]["steps"][1]
    # Assert: PyYAML lee «on» como True
    assert espejo[True]["push"]["branches"] == ["main", "develop"]
    assert espejo["permissions"] == {"contents": "read"}
    assert paso["env"]["LLAVE"] == "${{ secrets.GITLAB_ESPEJO_KEY }}"
    assert paso["env"]["HUELLA"].startswith("SHA256:") and "ssh-keygen -lf" in paso["run"]


def test_la_deteccion_de_secretos_no_hereda_uv_ni_su_cache():
    # Arrange / Act
    base = _yaml(".gitlab-ci.yml")["default"]
    # Assert: el job de la plantilla usa su propia imagen, donde uv no existe
    assert not {"before_script", "image", "cache"} & set(base)


def test_ningun_yaml_de_ci_trae_una_llave_privada():
    # Arrange
    archivos = [RAIZ / ".gitlab-ci.yml", *(RAIZ / ".github/workflows").glob("*.yml")]
    # Act / Assert
    for archivo in archivos:
        assert "PRIVATE KEY" not in archivo.read_text(encoding="utf-8"), archivo.name

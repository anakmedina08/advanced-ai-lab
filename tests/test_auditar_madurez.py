"""Pruebas del auditor de madurez (scripts/auditar_madurez.py), con el patrón AAA."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

RUTA = Path(__file__).resolve().parents[1] / "scripts" / "auditar_madurez.py"
spec = importlib.util.spec_from_file_location("auditar_madurez", RUTA)
auditar_madurez = importlib.util.module_from_spec(spec)
sys.modules["auditar_madurez"] = auditar_madurez  # las dataclasses resuelven su módulo
spec.loader.exec_module(auditar_madurez)


def _ids_ok(raiz: Path) -> set[str]:
    dims, _ = auditar_madurez.auditar(raiz)
    return {r.id for d in dims for r in d.resultados if r.ok}


def _escribir(raiz: Path, ruta: str, texto: str) -> None:
    archivo = raiz / ruta
    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_text(texto, encoding="utf-8")


def test_repo_vacio_queda_en_n1(tmp_path: Path) -> None:
    # Arrange: carpeta vacía
    # Act
    dims, global_ = auditar_madurez.auditar(tmp_path)
    # Assert
    assert global_ < 40
    assert all(d.nivel == "N1 Inicial" for d in dims)


def test_catalogo_tiene_70_verificaciones_con_ids_unicos() -> None:
    # Act
    ids = [c.id for checks in auditar_madurez.catalogo().values() for c in checks]
    # Assert
    assert len(ids) == len(set(ids)) == 70


@pytest.mark.parametrize(
    ("pct", "nivel"), [(95, "N4 Optimizado"), (75, "N3 Definido"), (50, "N2 Gestionado"), (10, "N1 Inicial")]
)
def test_niveles_por_umbral(pct: float, nivel: str) -> None:
    # Act
    obtenido = auditar_madurez.nivel(pct)
    # Assert
    assert obtenido == nivel


def test_detecta_secretos_ignorados_y_env_example(tmp_path: Path) -> None:
    # Arrange
    _escribir(tmp_path, ".gitignore", ".env\n")
    _escribir(tmp_path, ".env.example", "API_KEY=\n")
    # Act
    ok = _ids_ok(tmp_path)
    # Assert
    assert "S2" in ok


def test_cobertura_en_workflow_cuenta(tmp_path: Path) -> None:
    # Arrange
    _escribir(
        tmp_path, ".github/workflows/ci.yml", "steps:\n  - run: uv run pytest --cov --cov-fail-under=85\n"
    )
    # Act
    ok = _ids_ok(tmp_path)
    # Assert
    assert "C4" in ok


def test_ignora_carpetas_de_datos(tmp_path: Path) -> None:
    # Arrange: una model card dentro de data/ no es documentación del proyecto
    _escribir(tmp_path, "data/model-card.md", "x")
    # Act
    ok = _ids_ok(tmp_path)
    # Assert
    assert "M1" not in ok


def test_plantillas_dentro_de_skills_no_cuentan(tmp_path: Path) -> None:
    # Arrange
    _escribir(tmp_path, ".claude/skills/x/assets/data-card.md", "# Data card\n")
    _escribir(tmp_path, ".claude/skills/x/SKILL.md", "---\nname: x\n---\n")
    # Act
    ok = _ids_ok(tmp_path)
    # Assert
    assert "M2" not in ok


def test_privacidad_no_cuenta_por_instrucciones_de_agentes(tmp_path: Path) -> None:
    # Arrange: AGENTS.md menciona datos personales, pero no es una política del proyecto
    _escribir(tmp_path, "AGENTS.md", "No subir datos personales ni PII.\n")
    # Act
    sin_politica = _ids_ok(tmp_path)
    _escribir(tmp_path, "docs/alcance.md", "Cumplimos la Ley 1581 de 2012.\n")
    con_politica = _ids_ok(tmp_path)
    # Assert
    assert "M8" not in sin_politica
    assert "M8" in con_politica


def test_estrategia_de_ramas_exige_nombrarla(tmp_path: Path) -> None:
    # Arrange: mencionar «develop» no basta
    _escribir(tmp_path, "CONTRIBUTING.md", "Trabaja sobre develop.\n")
    # Act
    vaga = _ids_ok(tmp_path)
    _escribir(tmp_path, "CONTRIBUTING.md", "Usamos Gitflow: main, develop y feature/*.\n")
    explicita = _ids_ok(tmp_path)
    # Assert
    assert "P6" not in vaga
    assert "P6" in explicita


def test_revision_humana_exige_codeowners(tmp_path: Path) -> None:
    # Arrange
    _escribir(tmp_path, "CONTRIBUTING.md", "Todo PR requiere aprobación.\n")
    # Act
    solo_texto = _ids_ok(tmp_path)
    _escribir(tmp_path, ".github/CODEOWNERS", "* @a @b\n")
    con_dueños = _ids_ok(tmp_path)
    # Assert
    assert "G8" not in solo_texto
    assert "G8" in con_dueños


def test_minimo_devuelve_codigo_de_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Act
    codigo = auditar_madurez.main(["--path", str(tmp_path), "--json", "--minimo", "50"])
    salida = json.loads(capsys.readouterr().out)
    # Assert
    assert codigo == 1
    assert salida["global"] < 50


def test_anuncios_registrados_con_resumen(tmp_path: Path) -> None:
    # Arrange
    _escribir(tmp_path, "docs/anuncios/README.md", "| 551462 | 006 | [resumen](551462-anuncio-006.md) |\n")
    # Act
    sin_resumen = _ids_ok(tmp_path)
    _escribir(tmp_path, "docs/anuncios/551462-anuncio-006.md", "# Anuncio 006\n")
    con_resumen = _ids_ok(tmp_path)
    # Assert
    assert "K1" in sin_resumen and "K2" not in sin_resumen
    assert {"K1", "K2"} <= con_resumen


def test_requisito_pendiente_bloquea_k3(tmp_path: Path) -> None:
    # Arrange
    _escribir(tmp_path, "docs/requisitos.md", "| BitNet b1.58 | ❌ | — |\n")
    # Act
    pendiente = _ids_ok(tmp_path)
    _escribir(tmp_path, "docs/requisitos.md", "| BitNet b1.58 | ⛔ | fuera de alcance |\n")
    decidido = _ids_ok(tmp_path)
    # Assert
    assert "K3" not in pendiente
    assert "K3" in decidido


def test_herramienta_no_permitida_en_dependencias_falla_k4(tmp_path: Path) -> None:
    # Arrange
    _escribir(
        tmp_path,
        "docs/anuncios/herramientas.md",
        "| Herramienta | Paquete | Estado |\n|---|---|---|\n"
        "| Streamlit / Gradio | `streamlit`, `gradio` | ⛔ no permitida → React |\n"
        "| pip / requirements.txt | — | ⛔ no permitida |\n"
        "| FastAPI | `fastapi` | ✅ exigida |\n",
    )
    # Act
    prohibidas = auditar_madurez.herramientas_no_permitidas(auditar_madurez.Repo(tmp_path))
    _escribir(tmp_path, "pyproject.toml", 'dependencies = [\n  "fastapi",\n  "streamlit>=1.40",\n]\n')
    con_streamlit = _ids_ok(tmp_path)
    _escribir(tmp_path, "pyproject.toml", '# sin streamlit ni pip\ndependencies = ["fastapi", "pip-audit"]\n')
    sin_streamlit = _ids_ok(tmp_path)
    # Assert
    assert prohibidas == ["gradio", "streamlit"]
    assert "K4" not in con_streamlit
    assert "K4" in sin_streamlit


def test_importar_paquete_prohibido_en_src_falla_k4(tmp_path: Path) -> None:
    # Arrange
    _escribir(
        tmp_path,
        "docs/anuncios/herramientas.md",
        "| Herramienta | Paquete | Estado |\n|---|---|---|\n| Gradio | `gradio` | ⛔ |\n",
    )
    _escribir(tmp_path, "src/app/ui.py", "import gradio as gr\n")
    # Act
    ok = _ids_ok(tmp_path)
    # Assert
    assert "K4" not in ok


def test_higiene_de_ramas_y_entornos(tmp_path: Path) -> None:
    # Arrange
    _escribir(
        tmp_path, ".github/workflows/ramas.yml", 'run: gh api -X DELETE "repos/$R/git/refs/heads/$RAMA"\n'
    )
    _escribir(tmp_path, ".github/workflows/deploy.yml", "jobs:\n  desplegar:\n    environment: produccion\n")
    # Act
    ok = _ids_ok(tmp_path)
    # Assert
    assert {"P9", "R8"} <= ok


@pytest.mark.parametrize(
    ("verificacion", "patron"), [("G4", "Co-Authored-By: Claude"), ("M10", "register_model")]
)
def test_el_auditor_no_es_evidencia_de_si_mismo(tmp_path: Path, verificacion: str, patron: str) -> None:
    # Arrange: una copia del auditor contiene los patrones que busca, pero no es evidencia
    _escribir(tmp_path, "scripts/auditar_madurez.py", f"# {patron}\n")
    # Act
    ok = _ids_ok(tmp_path)
    # Assert
    assert verificacion not in ok


def test_sin_catalogo_de_herramientas_k4_falla(tmp_path: Path) -> None:
    # Arrange: ni catálogo ni dependencias
    # Act
    ok = _ids_ok(tmp_path)
    # Assert
    assert "K4" not in ok


def test_json_se_puede_guardar_en_archivo(tmp_path: Path) -> None:
    # Arrange
    salida = tmp_path / "madurez.json"
    # Act
    auditar_madurez.main(["--path", str(tmp_path), "--json", "--salida", str(salida)])
    # Assert
    assert json.loads(salida.read_text(encoding="utf-8"))["nivel"] == "N1 Inicial"


def test_una_verificacion_rota_se_reporta_como_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange: una verificación que lanza una excepción
    rota = auditar_madurez.Verificacion("X1", "rota", 1, lambda r: 1 / 0)
    monkeypatch.setattr(auditar_madurez, "catalogo", lambda: {"0. Prueba": [rota]})
    # Act
    dims, _ = auditar_madurez.auditar(tmp_path)
    informe = auditar_madurez.informe_md(tmp_path, dims, 0)
    # Assert
    resultado = dims[0].resultados[0]
    assert not resultado.ok and resultado.error.startswith("ZeroDivisionError")
    assert "Verificaciones con error" in informe and "⚠️ **X1**" in informe

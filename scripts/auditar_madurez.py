"""Auditoría de madurez del repositorio (solo lectura, sin dependencias externas).

Implementa como código propio del proyecto la rúbrica de la skill ``estandar-ia-profesional``
(8 dimensiones, 66 verificaciones) y las verificaciones K1-K4 de ``seguimiento-anuncios-curso``
(dimensión 9). La CI la usa con ``make madurez MINIMO=<umbral de ci.yml>`` sin depender de ninguna skill.

Evalúa 9 dimensiones con verificaciones ponderadas y asigna un nivel por dimensión y global:

    N1 Inicial (<40 %) · N2 Gestionado (40-69 %) · N3 Definido (70-89 %) · N4 Optimizado (>=90 %)

Uso:
    make madurez                                     # informe en consola
    make madurez MINIMO=60                           # falla si el global baja de 60 (la CI fija el umbral)
    uv run python scripts/auditar_madurez.py --salida docs/madurez.md
    uv run python scripts/auditar_madurez.py --json

No ejecuta código del proyecto ni toca la red: solo lee archivos. Por eso P9 (ramas) solo verifica el
workflow de limpieza; que en el remoto queden solo ``main`` y ``develop`` lo confirma una persona o el
agente con ``git ls-remote --heads origin``.

Es un script independiente por diseño: no importa ``sb_asistente``, para poder auditar cualquier
repositorio y para que un error del paquete no rompa la auditoría. Por eso sus umbrales (``NIVELES``,
``TAMANO_MAXIMO_BYTES``, ``ANCHO_BARRA``) y las rutas que revisa (``docs/…``, ``.github/…``,
``.claude/…``) son parte de la rúbrica y viven aquí, no en ``src/sb_asistente/config.py``.
El auditor se excluye a sí mismo de las búsquedas: sus patrones no cuentan como evidencia.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path

AGENTES = (".claude", ".agents", ".opencode")
IGNORAR = {".git", ".venv", "node_modules", "__pycache__", "data", "dist", "build", ".mypy_cache"}
# Umbrales de nivel (% mínimo) de la rúbrica: references/niveles-madurez.md de la skill.
NIVELES = ((90, "N4 Optimizado"), (70, "N3 Definido"), (40, "N2 Gestionado"), (0, "N1 Inicial"))
ARCHIVO_PROPIO = "scripts/auditar_madurez.py"  # sus patrones no son evidencia
ANCHO_BARRA = 20  # caracteres de la barra de progreso del informe
TAMANO_MAXIMO_BYTES = 2_000_000  # no se leen archivos más grandes (datos o artefactos)


# ---------------------------------------------------------------- utilidades de lectura
class Repo:
    """Acceso de solo lectura al repositorio con caché de textos."""

    def __init__(self, raiz: Path) -> None:
        """Prepara la lectura de ``raiz`` sin tocar el disco todavía."""
        self.raiz = raiz
        self._cache: dict[Path, str] = {}

    def existe(self, *rutas: str) -> bool:
        """True si existe alguna de las rutas."""
        return any((self.raiz / r).exists() for r in rutas)

    def texto(self, ruta: str) -> str:
        """Contenido de un archivo de texto, o cadena vacía si no existe."""
        p = self.raiz / ruta
        if p not in self._cache:
            try:
                self._cache[p] = p.read_text(encoding="utf-8", errors="ignore") if p.is_file() else ""
            except OSError:
                self._cache[p] = ""
        return self._cache[p]

    def contiene(self, rutas: tuple[str, ...], patron: str) -> bool:
        """True si alguno de los archivos coincide con el patrón (regex, sin mayúsculas)."""
        rx = re.compile(patron, re.I | re.M)
        return any(rx.search(self.texto(r)) for r in rutas)

    def glob(self, patron: str) -> list[Path]:
        """Rutas que cumplen el patrón, sin carpetas ignoradas."""
        # Las carpetas de agentes traen plantillas (model-card, data-card…) que no son del proyecto:
        # solo cuentan cuando el patrón las nombra explícitamente.
        ocultas = set() if patron.startswith(AGENTES) else set(AGENTES)
        return [
            p
            for p in self.raiz.glob(patron)
            if not (set(p.relative_to(self.raiz).parts) & (IGNORAR | ocultas))
            and p.relative_to(self.raiz).as_posix() != ARCHIVO_PROPIO
        ]

    def en_workflows(self, patron: str) -> bool:
        """True si algún workflow de GitHub Actions coincide con el patrón."""
        return self.en_alguno(".github/workflows/*.y*ml", patron)

    def en_alguno(self, patron_glob: str, patron: str) -> bool:
        """True si algún archivo (menor de 2 MB) del glob coincide con el patrón."""
        rx = re.compile(patron, re.I | re.M)
        return any(
            p.is_file()
            and p.stat().st_size < TAMANO_MAXIMO_BYTES
            and rx.search(p.read_text(encoding="utf-8", errors="ignore"))
            for p in self.glob(patron_glob)
        )


CONFIG = ("pyproject.toml", "Makefile", ".pre-commit-config.yaml", "setup.cfg", "tox.ini", "noxfile.py")


@dataclass
class Verificacion:
    """Una fila de la rúbrica: id, peso y prueba de solo lectura."""

    id: str
    descripcion: str
    peso: int
    prueba: Callable[[Repo], bool] = field(repr=False)
    arreglo: str = ""
    referencia: str = ""


@dataclass
class Resultado:
    """Resultado de una verificación sobre el repositorio."""

    id: str
    descripcion: str
    peso: int
    ok: bool
    arreglo: str
    referencia: str
    error: str = ""  # si la verificación misma falló (bug), no se confunde con un requisito incumplido


@dataclass
class Dimension:
    """Puntaje y nivel de una de las 9 dimensiones."""

    nombre: str
    porcentaje: float
    nivel: str
    resultados: list[Resultado]


# ---------------------------------------------------------------- catálogo de verificaciones
def herramientas_no_permitidas(r: Repo) -> list[str]:
    """Paquetes de las filas ⛔ de docs/anuncios/herramientas.md (columna «Paquete»)."""
    paquetes: list[str] = []
    columnas: list[str] = []
    for linea in r.texto("docs/anuncios/herramientas.md").splitlines():
        if not linea.startswith("|"):
            columnas = []
            continue
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if "Paquete" in celdas and "Estado" in celdas:
            columnas = celdas
            continue
        if not columnas or set(linea) <= set("|-: "):
            continue
        fila = dict(zip(columnas, celdas, strict=False))
        if "⛔" in fila.get("Estado", ""):
            paquetes += re.findall(r"`([\w.@/-]+)`", fila.get("Paquete", ""))
    return sorted(set(paquetes))


def _sin_herramientas_prohibidas(r: Repo) -> bool:
    """True si hay catálogo y ningún paquete ⛔ es dependencia (pyproject, package.json) ni import en src/.

    Sin catálogo (``docs/anuncios/herramientas.md``) no hay evidencia: la verificación falla.
    """
    if not r.contiene(("docs/anuncios/herramientas.md",), r"^\|.*\bPaquete\b.*\bEstado\b"):
        return False
    for paquete in herramientas_no_permitidas(r):
        nombre = re.escape(paquete)
        dependencia = rf"[\"']{nombre}(\[[^\]]*\])?\s*([<>=!~;,\"']|$)"
        importacion = rf"^\s*(import|from)\s+{nombre}\b"
        if r.contiene(("pyproject.toml", "frontend/package.json"), dependencia) or r.en_alguno(
            "src/**/*.py", importacion
        ):
            return False
    return True


def _anuncios_completos(r: Repo) -> bool:
    """True si cada anuncio enlazado en el índice tiene su archivo de resumen."""
    enlazados = set(re.findall(r"\(([\w.-]+-anuncio-\d{3}\.md)\)", r.texto("docs/anuncios/README.md")))
    return bool(enlazados) and all(r.existe(f"docs/anuncios/{n}") for n in enlazados)


# ---------------------------------------------------------------- catálogo de verificaciones
def catalogo() -> dict[str, list[Verificacion]]:
    """Las 66 verificaciones de la rúbrica más las 4 del seguimiento de anuncios (dimensión 9)."""
    v = Verificacion
    return {
        "1. Fundamentos": [
            v(
                "F1",
                "pyproject.toml con metadatos y requires-python",
                3,
                lambda r: r.contiene(("pyproject.toml",), r"requires-python"),
                "Declarar requires-python en pyproject.toml",
                "fundamentos.md",
            ),
            v(
                "F2",
                "Lockfile versionado (uv.lock / poetry.lock)",
                3,
                lambda r: r.existe("uv.lock", "poetry.lock", "pdm.lock"),
                "uv lock && git add uv.lock",
                "fundamentos.md",
            ),
            v(
                "F3",
                "Versión de Python fijada (.python-version)",
                1,
                lambda r: r.existe(".python-version"),
                "echo 3.13 > .python-version",
                "fundamentos.md",
            ),
            v(
                "F4",
                "src-layout (src/<paquete>/)",
                2,
                lambda r: bool(r.glob("src/*/__init__.py")),
                "Mover el código a src/<paquete>/",
                "fundamentos.md",
            ),
            v(
                "F5",
                "Makefile con help y check",
                3,
                lambda r: r.contiene(("Makefile",), r"^help:") and r.contiene(("Makefile",), r"^check:"),
                "Agregar targets help y check",
                "fundamentos.md",
            ),
            v(
                "F6",
                "pre-commit configurado",
                2,
                lambda r: r.existe(".pre-commit-config.yaml"),
                "Crear .pre-commit-config.yaml",
                "fundamentos.md",
            ),
            v(
                "F7",
                "README, LICENSE y CONSTITUTION.md",
                3,
                lambda r: (
                    r.existe("README.md")
                    and r.existe("LICENSE", "LICENSE.md")
                    and r.existe("CONSTITUTION.md")
                ),
                "Completar README/LICENSE/CONSTITUTION",
                "fundamentos.md",
            ),
            v(
                "F8",
                ".editorconfig",
                1,
                lambda r: r.existe(".editorconfig"),
                "Agregar .editorconfig",
                "fundamentos.md",
            ),
        ],
        "2. Calidad de código y pruebas": [
            v(
                "C1",
                "Linter y formateador (Ruff)",
                3,
                lambda r: r.contiene(CONFIG, r"\bruff\b"),
                "Configurar [tool.ruff]",
                "calidad.md",
            ),
            v(
                "C2",
                "Verificación de tipos (ty / mypy / pyright) en el flujo",
                3,
                lambda r: r.contiene(CONFIG, r"\b(ty check|mypy|pyright|basedpyright)\b"),
                "Agregar `ty check` a make check y CI",
                "calidad.md",
            ),
            v(
                "C3",
                "Pruebas con pytest",
                3,
                lambda r: r.existe("tests") and r.contiene(CONFIG, r"pytest"),
                "Crear tests/ y [tool.pytest.ini_options]",
                "calidad.md",
            ),
            v(
                "C4",
                "Umbral de cobertura obligatorio",
                3,
                lambda r: (
                    r.contiene(CONFIG + (".coveragerc",), r"(fail[_-]under|cov-fail-under)")
                    or r.en_workflows(r"cov-fail-under")
                ),
                "pytest --cov --cov-fail-under=80",
                "calidad.md",
            ),
            v(
                "C5",
                "Pirámide de pruebas con marcadores (unit/integration/e2e)",
                2,
                lambda r: r.contiene(("pyproject.toml", "pytest.ini"), r"markers\s*="),
                "Declarar markers en pytest",
                "calidad.md",
            ),
            v(
                "C6",
                "Pruebas de contrato o de API (TestClient / schemathesis)",
                2,
                lambda r: r.en_alguno("tests/**/*.py", r"(TestClient|schemathesis|httpx\.AsyncClient)"),
                "Probar endpoints con TestClient",
                "calidad.md",
            ),
            v(
                "C7",
                "Docstrings exigidos por el linter (pydocstyle D)",
                1,
                lambda r: r.contiene(("pyproject.toml", "ruff.toml"), r'select\s*=\s*\[[^\]]*"D"'),
                'Agregar "D" a ruff select',
                "calidad.md",
            ),
        ],
        "3. Seguridad y cadena de suministro": [
            v(
                "S1",
                "SECURITY.md (política de reporte)",
                2,
                lambda r: r.existe("SECURITY.md", ".github/SECURITY.md"),
                "Copiar plantilla SECURITY.md",
                "seguridad.md",
            ),
            v(
                "S2",
                "Secretos fuera del repo (.env ignorado + .env.example)",
                3,
                lambda r: r.contiene((".gitignore",), r"^\.env\b") and r.existe(".env.example"),
                "Ignorar .env y versionar .env.example",
                "seguridad.md",
            ),
            v(
                "S3",
                "Escaneo de secretos (gitleaks / detect-secrets / trufflehog)",
                3,
                lambda r: (
                    r.contiene((".pre-commit-config.yaml",), r"(gitleaks|detect-secrets|trufflehog)")
                    or r.en_workflows(r"(gitleaks|trufflehog)")
                ),
                "Agregar hook gitleaks",
                "seguridad.md",
            ),
            v(
                "S4",
                "Actualización automática de dependencias (Dependabot / Renovate)",
                2,
                lambda r: r.existe(".github/dependabot.yml", "renovate.json", ".github/renovate.json"),
                "Agregar dependabot.yml",
                "seguridad.md",
            ),
            v(
                "S5",
                "Auditoría de vulnerabilidades (pip-audit / osv-scanner) en CI",
                3,
                lambda r: (
                    r.en_workflows(r"(pip-audit|osv-scanner|safety check|uv audit)")
                    or r.contiene(CONFIG, r"pip-audit")
                ),
                "Workflow seguridad.yml con pip-audit",
                "seguridad.md",
            ),
            v(
                "S6",
                "Análisis estático de seguridad (CodeQL / Bandit / Ruff S)",
                2,
                lambda r: r.en_workflows(r"codeql") or r.contiene(CONFIG, r'(bandit|"S")'),
                "Activar CodeQL o reglas S de Ruff",
                "seguridad.md",
            ),
            v(
                "S7",
                "CODEOWNERS (revisores obligatorios)",
                2,
                lambda r: r.existe(".github/CODEOWNERS", "CODEOWNERS"),
                "Crear .github/CODEOWNERS",
                "seguridad.md",
            ),
            v(
                "S8",
                "Permisos mínimos en workflows (permissions:)",
                1,
                lambda r: r.en_workflows(r"^permissions:"),
                "Declarar permissions: contents: read",
                "seguridad.md",
            ),
            v(
                "S9",
                "SBOM generado (CycloneDX / syft)",
                1,
                lambda r: r.en_workflows(r"(cyclonedx|syft|sbom)"),
                "Generar SBOM en el release",
                "seguridad.md",
            ),
        ],
        "4. CI/CD y releases": [
            v(
                "R1",
                "Workflow de CI",
                3,
                lambda r: bool(r.glob(".github/workflows/*.y*ml")),
                "Crear .github/workflows/ci.yml",
                "entrega.md",
            ),
            v(
                "R2",
                "Paridad local ↔ CI (la CI corre make check / pre-commit)",
                3,
                lambda r: (
                    r.en_workflows(r"(make check|pre-commit run)")
                    or (r.en_workflows(r"ruff (check|format)") and r.en_workflows(r"pytest"))
                ),
                "Que la CI ejecute make check",
                "entrega.md",
            ),
            v(
                "R3",
                "CHANGELOG.md",
                2,
                lambda r: r.existe("CHANGELOG.md"),
                "Generar con git-cliff o release-please",
                "entrega.md",
            ),
            v(
                "R4",
                "Releases automatizados con SemVer (release-please / semantic-release / git-cliff)",
                2,
                lambda r: r.en_workflows(
                    r"(release-please|semantic-release|git-cliff|softprops/action-gh-release)"
                ),
                "Workflow release.yml",
                "entrega.md",
            ),
            v(
                "R5",
                "Contenedor reproducible (Dockerfile multi-stage)",
                2,
                lambda r: r.contiene(("Dockerfile",), r"^FROM .+ AS "),
                "Dockerfile multi-stage",
                "entrega.md",
            ),
            v(
                "R6",
                "Healthcheck del servicio",
                1,
                lambda r: (
                    r.contiene(("Dockerfile", "docker-compose.yml", "compose.yaml"), r"healthcheck")
                    or r.en_alguno("src/**/*.py", r"[\"']/health")
                ),
                "Endpoint /health y HEALTHCHECK",
                "entrega.md",
            ),
            v(
                "R7",
                "Caché de dependencias en CI",
                1,
                lambda r: r.en_workflows(r"(cache|setup-uv)"),
                "Usar astral-sh/setup-uv con cache",
                "entrega.md",
            ),
            v(
                "R8",
                "Entrega continua con entornos de GitHub (environment:)",
                2,
                lambda r: r.en_workflows(r"^\s+environment:"),
                "Workflow deploy.yml con environment staging/produccion",
                "github-cicd.md",
            ),
        ],
        "5. Documentación y decisiones": [
            v(
                "D1",
                "Carpeta docs/ con índice",
                2,
                lambda r: r.existe("docs/README.md", "docs/index.md"),
                "Crear docs/README.md",
                "documentacion.md",
            ),
            v(
                "D2",
                "ADRs (al menos 3)",
                3,
                lambda r: len(r.glob("docs/**/ADR-*.md")) + len(r.glob("docs/adr/*.md")) >= 3,
                "docs/decisiones/ADR-NNN-*.md",
                "documentacion.md",
            ),
            v(
                "D3",
                "Plantilla e índice de ADRs",
                1,
                lambda r: r.existe(
                    "docs/decisiones/README.md", "docs/adr/README.md", "docs/decisiones/plantilla.md"
                ),
                "Índice de ADRs",
                "documentacion.md",
            ),
            v(
                "D4",
                "Diagrama de arquitectura versionado",
                2,
                lambda r: bool(r.glob("docs/arquitectura*")) or bool(r.glob("docs/**/*.mmd")),
                "Archify o Mermaid en docs/",
                "documentacion.md",
            ),
            v(
                "D5",
                "CONTRIBUTING.md y CODE_OF_CONDUCT.md",
                2,
                lambda r: r.existe("CONTRIBUTING.md") and r.existe("CODE_OF_CONDUCT.md"),
                "Agregar guías",
                "documentacion.md",
            ),
            v(
                "D6",
                "Runbook de operación (levantar, diagnosticar, recuperar)",
                2,
                lambda r: r.existe("docs/runbook.md", "docs/operacion.md", "RUNBOOK.md"),
                "docs/runbook.md",
                "documentacion.md",
            ),
            v(
                "D7",
                "AGENTS.md / CLAUDE.md para agentes",
                2,
                lambda r: r.existe("AGENTS.md", "CLAUDE.md"),
                "Crear AGENTS.md",
                "gobernanza-ia.md",
            ),
        ],
        "6. Proceso y trazabilidad": [
            v(
                "P1",
                "Plantilla de PR con checklist",
                2,
                lambda r: r.existe(".github/pull_request_template.md"),
                "Agregar plantilla de PR",
                "proceso.md",
            ),
            v(
                "P2",
                "Plantillas de issue (bug / historia / spike)",
                2,
                lambda r: len(r.glob(".github/ISSUE_TEMPLATE/*.y*ml")) >= 2,
                "Agregar ISSUE_TEMPLATE",
                "proceso.md",
            ),
            v(
                "P3",
                "Desarrollo guiado por specs (openspec/ o specs/)",
                3,
                lambda r: r.existe("openspec", "specs", ".specify"),
                "openspec/specs/NNN-*/",
                "proceso.md",
            ),
            v(
                "P4",
                "Conventional Commits validado por hook",
                2,
                lambda r: r.contiene(
                    (".pre-commit-config.yaml",), r"(commit-msg|conventional|commitizen|commitlint)"
                ),
                "Hook commit-msg",
                "proceso.md",
            ),
            v(
                "P5",
                "Definition of Done explícita",
                2,
                lambda r: r.contiene(
                    ("CONTRIBUTING.md", ".github/pull_request_template.md", "CONSTITUTION.md"),
                    r"(definition of done|definici[oó]n de (hecho|terminado)|\bDoD\b)",
                ),
                "Sección DoD en CONTRIBUTING",
                "proceso.md",
            ),
            v(
                "P6",
                "Estrategia de ramas documentada (Gitflow / trunk)",
                1,
                lambda r: r.contiene(("CONTRIBUTING.md", "CONSTITUTION.md"), r"(gitflow|trunk[- ]based)"),
                "Documentar ramas",
                "proceso.md",
            ),
            v(
                "P7",
                "Labels declarativas",
                1,
                lambda r: r.existe(".github/labels.yml"),
                "Crear .github/labels.yml",
                "proceso.md",
            ),
            v(
                "P8",
                "Matriz de requisitos ↔ evidencia",
                1,
                lambda r: r.existe("docs/requisitos.md", "docs/trazabilidad.md"),
                "docs/requisitos.md",
                "proceso.md",
            ),
            v(
                "P9",
                "Solo main y develop permanentes (borrado automático de ramas fusionadas)",
                2,
                lambda r: r.en_workflows(r"(git/refs/heads|push origin --delete|delete_branch_on_merge)"),
                "Workflow ramas.yml + 'Automatically delete head branches'",
                "github-cicd.md",
            ),
        ],
        "7. IA/ML responsable": [
            v(
                "M1",
                "Model card",
                3,
                lambda r: bool(r.glob("**/model-card*.md")) or bool(r.glob("**/MODEL_CARD*.md")),
                "docs/model-card.md",
                "ia-ml.md",
            ),
            v(
                "M2",
                "Data card / datasheet del conjunto de datos",
                2,
                lambda r: bool(r.glob("**/data-card*.md")) or bool(r.glob("**/datasheet*.md")),
                "docs/data-card.md",
                "ia-ml.md",
            ),
            v(
                "M3",
                "Banco de evaluación versionado (golden set)",
                3,
                lambda r: r.existe("evaluacion", "evals", "eval", "tests/evals"),
                "evaluacion/banco.csv",
                "ia-ml.md",
            ),
            v(
                "M4",
                "Seguimiento de experimentos (MLflow / W&B)",
                2,
                lambda r: r.contiene(CONFIG, r"(mlflow|wandb)"),
                "Registrar corridas en MLflow",
                "ia-ml.md",
            ),
            v(
                "M5",
                "Puerta de regresión de evaluación en CI",
                3,
                lambda r: r.en_workflows(r"(\bevals?\b|evaluacion|promptfoo|deepeval|ragas)"),
                "Workflow evals.yml con umbral",
                "ia-ml.md",
            ),
            v(
                "M6",
                "Prompts versionados como código",
                2,
                lambda r: bool(r.glob("**/prompts*.py")) or bool(r.glob("prompts/**")),
                "Mover prompts a src/<pkg>/prompts.py",
                "ia-ml.md",
            ),
            v(
                "M7",
                "Observabilidad de LLM (LangSmith / OpenTelemetry / Langfuse)",
                2,
                lambda r: r.contiene(CONFIG + (".env.example",), r"(langsmith|opentelemetry|langfuse)"),
                "Trazas con LangSmith",
                "ia-ml.md",
            ),
            v(
                "M8",
                "Privacidad y datos personales documentados (Ley 1581 / GDPR / PII)",
                2,
                # Solo documentos de política o del proyecto; AGENTS.md (instrucciones) no cuenta.
                lambda r: (
                    r.contiene(
                        ("CONSTITUTION.md", "README.md", "SECURITY.md"),
                        r"(ley 1581|habeas data|gdpr|\bPII\b)",
                    )
                    or r.en_alguno("docs/**/*.md", r"(ley 1581|habeas data|gdpr|\bPII\b)")
                ),
                "Sección de privacidad en CONSTITUTION",
                "ia-ml.md",
            ),
            v(
                "M9",
                "Evaluación de sesgo / equidad",
                1,
                lambda r: r.en_alguno("docs/**/*.md", r"(sesgo|bias|equidad|fairness)"),
                "Auditoría de sesgo en model card",
                "ia-ml.md",
            ),
            v(
                "M10",
                "Registro de modelos con alias/versiones",
                1,
                lambda r: (
                    r.en_alguno("src/**/*.py", r"(register_model|registered_model|registered_model_alias)")
                    or r.en_alguno("scripts/*.py", r"(register_model|registered_model_alias|Model Registry)")
                ),
                "MLflow Model Registry",
                "ia-ml.md",
            ),
        ],
        "8. Gobernanza de agentes de IA": [
            v(
                "G1",
                "Política de uso de IA documentada",
                3,
                lambda r: r.existe("docs/politica-uso-ia.md", "AI_POLICY.md", "docs/ai-policy.md"),
                "Copiar plantilla politica-uso-ia.md",
                "gobernanza-ia.md",
            ),
            v(
                "G2",
                "Agente sin acceso a secretos ni datos (permissions.deny)",
                3,
                lambda r: r.contiene((".claude/settings.json", "opencode.json"), r"Read\(\./\.env"),
                "deny Read(./.env) en .claude/settings.json",
                "gobernanza-ia.md",
            ),
            v(
                "G3",
                "Atribución de IA definida explícitamente (attribution)",
                2,
                lambda r: r.contiene((".claude/settings.json",), r'"(attribution|includeCoAuthoredBy)"'),
                "attribution en .claude/settings.json",
                "gobernanza-ia.md",
            ),
            v(
                "G4",
                "Filtro de trailers de IA en commit-msg",
                2,
                lambda r: r.en_alguno("scripts/*.py", r"Co-Authored-By.*(Claude|anthropic)"),
                "scripts/limpiar_trailers_ia.py",
                "gobernanza-ia.md",
            ),
            v(
                "G5",
                "Skills propias con metadatos validados",
                2,
                lambda r: (
                    len(r.glob(".claude/skills/*/SKILL.md")) + len(r.glob(".agents/skills/*/SKILL.md")) >= 2
                ),
                "make skill-new",
                "gobernanza-ia.md",
            ),
            v(
                "G6",
                "Subagentes especializados definidos",
                1,
                lambda r: bool(r.glob(".claude/agents/*.md")),
                ".claude/agents/*.md",
                "gobernanza-ia.md",
            ),
            v(
                "G7",
                "Skills de terceros fijadas por hash (lockfile)",
                1,
                lambda r: r.existe("skills-lock.json"),
                "npx skills add (genera skills-lock.json)",
                "gobernanza-ia.md",
            ),
            v(
                "G8",
                "Revisión humana obligatoria (CODEOWNERS o regla de aprobación)",
                2,
                lambda r: r.existe(".github/CODEOWNERS", "CODEOWNERS"),
                "CODEOWNERS + protección de rama",
                "gobernanza-ia.md",
            ),
        ],
        "9. Requisitos del curso o cliente": [
            v(
                "K1",
                "Índice de anuncios del curso",
                3,
                lambda r: r.contiene(("docs/anuncios/README.md",), r"anuncio-\d{3}"),
                "Paso 0: registrar el último anuncio en docs/anuncios/README.md",
                "anuncios.md",
            ),
            v(
                "K2",
                "Resumen por cada anuncio registrado",
                3,
                _anuncios_completos,
                "Crear los resúmenes que faltan",
                "anuncios.md",
            ),
            v(
                "K3",
                "Sin requisitos pendientes sin plan (❌ / ❓) en docs/requisitos.md",
                3,
                lambda r: (
                    r.existe("docs/requisitos.md")
                    and not r.contiene(("docs/requisitos.md",), r"^\|.*\|\s*(❌|❓)\s*\|")
                ),
                "Convertir cada ❌/❓ en historia o ⛔ con motivo",
                "anuncios.md",
            ),
            v(
                "K4",
                "Sin herramientas no permitidas por el curso (⛔ en docs/anuncios/herramientas.md)",
                3,
                _sin_herramientas_prohibidas,
                "Migrar a la herramienta que la reemplaza y registrar un ADR",
                "anuncios.md",
            ),
        ],
    }


# ---------------------------------------------------------------- motor
def nivel(pct: float) -> str:
    """Nivel N1-N4 según el porcentaje."""
    return next(n for umbral, n in NIVELES if pct >= umbral)


def auditar(raiz: Path) -> tuple[list[Dimension], float]:
    """Evalúa todas las dimensiones; devuelve sus resultados y el puntaje global."""
    repo = Repo(raiz)
    dims: list[Dimension] = []
    total_ok = total = 0
    for nombre, checks in catalogo().items():
        res = []
        for c in checks:
            error = ""
            try:
                ok = bool(c.prueba(repo))
            except Exception as exc:  # noqa: BLE001 - una verificación rota no tumba la auditoría: se reporta
                ok, error = False, f"{type(exc).__name__}: {exc}"
            res.append(Resultado(c.id, c.descripcion, c.peso, ok, c.arreglo, c.referencia, error))
        ganados = sum(r.peso for r in res if r.ok)
        posibles = sum(r.peso for r in res)
        total_ok += ganados
        total += posibles
        pct = round(100 * ganados / posibles, 1)
        dims.append(Dimension(nombre, pct, nivel(pct), res))
    return dims, round(100 * total_ok / total, 1)


def barra(pct: float, ancho: int = ANCHO_BARRA) -> str:
    """Barra de progreso en texto."""
    llenos = round(pct / 100 * ancho)
    return "█" * llenos + "░" * (ancho - llenos)


def informe_md(raiz: Path, dims: list[Dimension], global_: float) -> str:
    """Informe en Markdown con tabla, brechas priorizadas y detalle."""
    out = [
        f"# Informe de madurez — `{raiz.resolve().name}`",
        "",
        f"**Puntaje global: {global_} % · {nivel(global_)}**",
        "",
        "| Dimensión | Puntaje | Nivel | |",
        "|---|---:|---|---|",
    ]
    out += [f"| {d.nombre} | {d.porcentaje} % | {d.nivel} | `{barra(d.porcentaje)}` |" for d in dims]
    brechas = [(d.nombre, r) for d in dims for r in d.resultados if not r.ok]
    brechas.sort(key=lambda x: -x[1].peso)
    out += [
        "",
        "## Brechas priorizadas (mayor peso primero)",
        "",
        "| ID | Peso | Brecha | Cómo cerrarla | Guía |",
        "|---|---:|---|---|---|",
    ]
    out += [
        f"| {r.id} | {r.peso} | {r.descripcion} | {r.arreglo} | `references/{r.referencia}` |"
        for _, r in brechas
    ]
    errores = [r for d in dims for r in d.resultados if r.error]
    if errores:
        out += ["", "## ⚠️ Verificaciones con error (revisar el auditor, no el proyecto)", ""]
        out += [f"- **{r.id}**: {r.error}" for r in errores]
    out += ["", "## Detalle", ""]
    for d in dims:
        out.append(f"### {d.nombre} — {d.porcentaje} % ({d.nivel})")
        out += [
            f"- {'✅' if r.ok else ('⚠️' if r.error else '❌')} **{r.id}** {r.descripcion} *(peso {r.peso})*"
            for r in d.resultados
        ]
        out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada de la línea de comandos."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--path", default=".", type=Path)
    ap.add_argument(
        "--salida", type=Path, help="Escribe el informe (Markdown, o JSON con --json) en esta ruta"
    )
    ap.add_argument("--json", action="store_true", help="Imprime el resultado en JSON")
    ap.add_argument("--minimo", type=float, default=0, help="Falla (exit 1) si el global queda por debajo")
    a = ap.parse_args(argv)

    dims, global_ = auditar(a.path)
    if a.json:
        texto = json.dumps(
            {"global": global_, "nivel": nivel(global_), "dimensiones": [asdict(d) for d in dims]},
            ensure_ascii=False,
            indent=2,
        )
    else:
        texto = informe_md(a.path, dims, global_)
    if a.salida:
        a.salida.parent.mkdir(parents=True, exist_ok=True)
        a.salida.write_text(texto.rstrip("\n") + "\n", encoding="utf-8")
        print(f"Informe escrito en {a.salida}", file=sys.stderr)
    print(texto)
    return 1 if global_ < a.minimo else 0


if __name__ == "__main__":
    sys.exit(main())

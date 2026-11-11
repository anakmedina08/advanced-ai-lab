"""Skills: carpetas con un ``SKILL.md`` (formato abierto de Agent Skills).

El mismo formato lo leen Claude Code, OpenCode y los demás agentes compatibles con
``npx skills``. Este módulo las descubre en las tres rutas de proyecto que usa OpenCode
(``.claude/skills``, ``.agents/skills`` y ``.opencode/skills``), valida el frontmatter con sus
reglas y entrega al chat solo las skills marcadas para el asistente.

Dos usos, separados por ``metadata.uso`` en el frontmatter:

- ``asistente``: el chat puede aplicarlas a una respuesta (formato, tono, comparación…).
- ``desarrollo`` (o sin marca): solo para los agentes que construyen el repositorio.

Así, una skill de terceros instalada con ``npx skills add`` nunca llega al chat público hasta
que el equipo la revise y la marque con ``uso: asistente`` en un Pull Request.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml

from sb_asistente.config import PROJECT_ROOT

SKILL_DIRS: Final[tuple[str, ...]] = (".claude/skills", ".agents/skills", ".opencode/skills")
NOMBRE_VALIDO: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_INSTRUCCIONES: Final[int] = 4000  # caracteres: tope de tokens que una skill suma al prompt
USO_ASISTENTE: Final[str] = "asistente"
_FRONTMATTER: Final[re.Pattern[str]] = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.S)


class SkillError(ValueError):
    """Una skill no cumple el formato."""


@dataclass(frozen=True, slots=True)
class Skill:
    """Metadatos de una skill (las instrucciones se cargan bajo demanda)."""

    nombre: str
    descripcion: str
    uso: str
    ruta: Path
    licencia: str | None = None

    @property
    def para_asistente(self) -> bool:
        """Indica si el chat puede usarla."""
        return self.uso == USO_ASISTENTE


def leer_skill(archivo: Path) -> tuple[Skill, str]:
    """Lee y valida un ``SKILL.md``; devuelve la skill y su cuerpo.

    Reglas (OpenCode): ``name`` de 1 a 64 caracteres en minúsculas, números y guiones simples,
    igual al nombre de la carpeta; ``description`` de 1 a 1024 caracteres.
    """
    match = _FRONTMATTER.match(archivo.read_text(encoding="utf-8"))
    if not match:
        raise SkillError(f"{archivo}: falta el frontmatter YAML entre líneas '---'.")
    meta = yaml.safe_load(match.group(1)) or {}
    nombre = str(meta.get("name", ""))
    descripcion = str(meta.get("description", "")).strip()
    if not (1 <= len(nombre) <= 64 and NOMBRE_VALIDO.match(nombre)):
        raise SkillError(f"{archivo}: name inválido {nombre!r} (minúsculas, números y guiones simples).")
    if nombre != archivo.parent.name:
        raise SkillError(f"{archivo}: name {nombre!r} debe ser igual a la carpeta {archivo.parent.name!r}.")
    if not 1 <= len(descripcion) <= 1024:
        raise SkillError(f"{archivo}: description debe tener entre 1 y 1024 caracteres.")
    metadata = meta.get("metadata") if isinstance(meta.get("metadata"), dict) else {}
    uso = str(metadata.get("uso", "desarrollo"))
    licencia = meta.get("license")
    skill = Skill(nombre, descripcion, uso, archivo, str(licencia) if licencia else None)
    return skill, match.group(2).strip()


def descubrir(raiz: Path = PROJECT_ROOT) -> tuple[list[Skill], list[str]]:
    """Todas las skills válidas del proyecto y los errores encontrados (nombres repetidos incluidos)."""
    skills: dict[str, Skill] = {}
    errores: list[str] = []
    vistos: set[Path] = set()
    for carpeta in SKILL_DIRS:
        for archivo in sorted((raiz / carpeta).glob("*/SKILL.md")):
            real = archivo.resolve()
            if real in vistos:  # `npx skills add` enlaza .claude/skills → .agents/skills
                continue
            vistos.add(real)
            try:
                skill, _ = leer_skill(archivo)
            except (SkillError, yaml.YAMLError) as exc:
                errores.append(str(exc))
                continue
            if skill.nombre in skills:
                errores.append(
                    f"{archivo}: el nombre {skill.nombre!r} ya existe en {skills[skill.nombre].ruta}."
                )
                continue
            skills[skill.nombre] = skill
    return sorted(skills.values(), key=lambda s: s.nombre), errores


def skills_asistente(raiz: Path = PROJECT_ROOT) -> list[Skill]:
    """Skills que el chat puede aplicar."""
    return [s for s in descubrir(raiz)[0] if s.para_asistente]


def instrucciones(nombre: str, raiz: Path = PROJECT_ROOT) -> str:
    """Cuerpo de una skill del asistente, recortado al tope de caracteres.

    Raises:
        KeyError: si no existe o no está marcada con ``uso: asistente``.

    """
    for skill in skills_asistente(raiz):
        if skill.nombre == nombre:
            return leer_skill(skill.ruta)[1][:MAX_INSTRUCCIONES]
    raise KeyError(f"Skill del asistente desconocida: {nombre}")


PLANTILLA: Final[str] = """---
name: {nombre}
description: {descripcion}
license: MIT
metadata:
  uso: {uso}
  autor: equipo-sb-asistente
---

## Qué hace
- (Describa en viñetas el comportamiento que agrega esta skill.)

## Cuándo usarla
- (Situaciones concretas; el agente decide con la descripción.)

## Reglas
- No reemplaza las reglas del asistente: solo responde con la base pública y cita la fuente.
"""


def nueva_skill(nombre: str, descripcion: str, uso: str = "desarrollo", raiz: Path = PROJECT_ROOT) -> Path:
    """Crea ``.claude/skills/<nombre>/SKILL.md`` desde la plantilla (lo leen Claude Code y OpenCode)."""
    if not (1 <= len(nombre) <= 64 and NOMBRE_VALIDO.match(nombre)):
        raise SkillError(f"Nombre inválido {nombre!r}: use minúsculas, números y guiones simples.")
    if uso not in (USO_ASISTENTE, "desarrollo"):
        raise SkillError("uso debe ser 'asistente' o 'desarrollo'.")
    if nombre in {s.nombre for s in descubrir(raiz)[0]}:
        raise SkillError(f"Ya existe una skill llamada {nombre!r}.")
    archivo = raiz / SKILL_DIRS[0] / nombre / "SKILL.md"
    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_text(PLANTILLA.format(nombre=nombre, descripcion=descripcion, uso=uso), encoding="utf-8")
    leer_skill(archivo)  # la plantilla debe salir válida
    return archivo

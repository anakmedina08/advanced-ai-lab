"""Controlador de las herramientas del equipo: skills, índice y evaluación del RAG, trazas y MLflow.

La CLI y la API llaman a estas funciones en lugar de importar el modelo directamente (MVC,
AGENTS.md): así la vista queda sin lógica y cada caso de uso tiene un solo punto de entrada.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

from sb_asistente import config
from sb_asistente.model import experimentos, skills, trazas

if TYPE_CHECKING:  # el RAG y el agente cargan LangChain: se importan solo cuando se usan
    from sb_asistente.model.rag.evaluacion import ResultadoHit
    from sb_asistente.model.rag.indice import InfoIndice

RAIZ_PROYECTO: Path = skills.PROJECT_ROOT


def skills_del_proyecto() -> tuple[list[skills.Skill], list[str]]:
    """Skills del repositorio y los errores de validación de su frontmatter."""
    return skills.descubrir()


def skills_del_asistente() -> list[dict[str, object]]:
    """Skills que el asistente puede aplicar en el chat público (``metadata.uso: asistente``)."""
    return [
        {"nombre": s.nombre, "descripcion": s.descripcion, "licencia": s.licencia}
        for s in skills.skills_asistente()
    ]


def nueva_skill(nombre: str, descripcion: str, uso: str) -> Path:
    """Crea ``.claude/skills/<nombre>/SKILL.md`` y devuelve su ruta."""
    return skills.nueva_skill(nombre, descripcion, uso)


def indexar_rag(embeddings: str, reset: bool) -> "InfoIndice":
    """Indexa los fragmentos Gold en la base vectorial local."""
    from sb_asistente.model.rag import indice
    from sb_asistente.model.rag.fuentes import fragmentos_rag

    return indice.indexar(fragmentos_rag(), embeddings, reset=reset)


def evaluar_rag(ks: list[int]) -> tuple[str, list["ResultadoHit"]]:
    """hit@k de la recuperación con el banco de preguntas; devuelve también el modo del buscador."""
    from sb_asistente.controller.agente import recuperador_por_defecto
    from sb_asistente.model import evaluation
    from sb_asistente.model.rag.evaluacion import hit_at_k

    recuperador, modo = recuperador_por_defecto()
    preguntas = evaluation.load_questions(config.EVAL_QUESTIONS)
    return modo, [hit_at_k(recuperador, preguntas, k) for k in ks]


def ultimas_trazas(n: int) -> tuple[Path, list[dict[str, Any]]]:
    """Las últimas ``n`` trazas del agente y la ruta del log (leída al llamar: las pruebas la cambian)."""
    return config.TRAZAS_LOG, trazas.ultimas(config.TRAZAS_LOG, n)


def mlflow_disponible() -> bool:
    """Indica si el extra ``mlflow`` está instalado."""
    return experimentos.disponible()

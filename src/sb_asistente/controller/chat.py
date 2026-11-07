"""Controlador del chat: un orquestador que clasifica cada mensaje y llama a una herramienta.

Flujo de un turno (cada paso queda en la ``traza`` que muestra el front):

1. ``clasificador`` → intención, sección y perfil (``model/intencion.py``), sin LLM.
2. ``skill`` (opcional) → instrucciones de formato de una skill del asistente.
3. Herramienta según la intención:
   - ``conocimiento`` → Q&A con contexto reducido y fuentes (``assistant``).
   - ``recomendador`` → top-k por cliente sintético o por el perfil descrito.
   - ``saludo`` / ``fuera_de_alcance`` → respuesta fija, sin gastar tokens.

El modo puede forzarse (``conocimiento``, ``recomendador``, ``clasificador``) o dejarse en
``auto``. Las dependencias costosas (LLM, tablas) se inyectan para probar sin red ni API.
"""

import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Literal

from sb_asistente.controller import recomendador
from sb_asistente.model import skills
from sb_asistente.model.intencion import Intencion, clasificar
from sb_asistente.model.llm.service import Answer

Modo = Literal["auto", "conocimiento", "recomendador", "clasificador"]
Responder = Callable[[str, str | None], Answer]
"""(pregunta, instrucciones de skill) → Answer."""

SALUDO = (
    "¡Hola! Soy el asistente de información pública de Seguros Bolívar (proyecto académico). "
    "Puedo responder dudas sobre seguros y canales de atención citando la página oficial, o "
    "sugerirle seguros si me cuenta su situación, por ejemplo: «tengo carro y un perro»."
)
FUERA = (
    "Solo puedo ayudar con información pública de seguros para personas de Seguros Bolívar "
    "(coberturas, trámites y canales de atención) y con recomendaciones de seguros. "
    "¿Tiene alguna pregunta sobre eso?"
)
PIDE_PERFIL = (
    "Para sugerirle seguros, cuénteme un poco de su situación (sin datos personales): si tiene "
    "carro, moto o vehículo eléctrico; si su vivienda es propia, arrendada o familiar; si tiene "
    "mascota y si tiene algún crédito."
)
AVISO_RECO = (
    "Sugerencia generada con datos sintéticos de práctica, no con clientes reales; confirme "
    "condiciones en los canales oficiales."
)


@dataclass(slots=True)
class Paso:
    """Un paso del orquestador, para mostrar cómo se resolvió el turno."""

    agente: str
    accion: str
    detalle: str
    ms: int


@dataclass(slots=True)
class Turno:
    """Respuesta de un turno del chat."""

    respuesta: str
    intencion: str
    confianza: float
    herramienta: str
    seccion: str | None = None
    perfil: dict[str, object] = field(default_factory=dict)
    fuentes: list[str] = field(default_factory=list)
    recomendaciones: list[dict[str, str]] = field(default_factory=list)
    skill: str | None = None
    traza: list[Paso] = field(default_factory=list)

    def a_dict(self) -> dict[str, object]:
        """Representación serializable (la API la valida con Pydantic)."""
        return asdict(self)


class _Reloj:
    def __init__(self) -> None:
        self.inicio = time.perf_counter()

    def ms(self) -> int:
        ahora = time.perf_counter()
        transcurrido, self.inicio = ahora - self.inicio, ahora
        return round(transcurrido * 1000)


def _recomendar(intencion: Intencion, cliente_id: str | None, k: int, reloj: _Reloj) -> Turno:
    perfil = intencion.perfil.conocido()
    if cliente_id:
        items = recomendador.recomendar(cliente_id, k)
        detalle = f"cliente sintético {cliente_id} · línea base por segmento"
    elif perfil:
        items, similares = recomendador.recomendar_por_perfil(perfil, k)
        detalle = f"perfil {perfil} · {similares:,} clientes similares"
    else:
        return Turno(
            PIDE_PERFIL,
            intencion.etiqueta,
            intencion.confianza,
            "recomendador",
            perfil=perfil,
            traza=[Paso("recomendador", "pide perfil", "el mensaje no describe un perfil", reloj.ms())],
        )
    lineas = [
        f"{i}. **{r['nombre']}** ({r['linea'].replace('_', ' ')}) — {r['razon']}"
        for i, r in enumerate(items, 1)
    ]
    texto = "Estos seguros podrían interesarle:\n\n" + "\n".join(lineas) + f"\n\n_{AVISO_RECO}_"
    return Turno(
        texto,
        intencion.etiqueta,
        intencion.confianza,
        "recomendador",
        intencion.seccion,
        perfil,
        recomendaciones=items,
        traza=[Paso("recomendador", "top-k", detalle, reloj.ms())],
    )


def responder(
    mensaje: str,
    responder_qa: Responder,
    modo: Modo = "auto",
    cliente_id: str | None = None,
    skill: str | None = None,
    k: int = 5,
    extraer_fuentes: Callable[[str], list[str]] = lambda _: [],
) -> Turno:
    """Resuelve un turno del chat y devuelve la respuesta con su traza.

    Raises:
        KeyError: si la skill no existe o no es del asistente, o el cliente no existe.
        FileNotFoundError: si faltan los datos de la herramienta elegida.

    """
    reloj = _Reloj()
    intencion = clasificar(mensaje)
    traza = [
        Paso(
            "clasificador",
            intencion.etiqueta,
            f"confianza {intencion.confianza:.2f} · " + "; ".join(intencion.senales),
            reloj.ms(),
        )
    ]
    if modo == "clasificador":
        resumen = (
            f"Intención: **{intencion.etiqueta}** (confianza {intencion.confianza:.2f})"
            + (f" · sección: {intencion.seccion}" if intencion.seccion else "")
            + (f" · perfil: {intencion.perfil.conocido()}" if intencion.perfil.conocido() else "")
        )
        return Turno(
            resumen,
            intencion.etiqueta,
            intencion.confianza,
            "clasificador",
            intencion.seccion,
            intencion.perfil.conocido(),
            traza=traza,
        )

    destino = {"conocimiento": "conocimiento", "recomendador": "recomendacion"}.get(modo, intencion.etiqueta)
    if destino == "recomendacion":
        turno = _recomendar(intencion, cliente_id, k, reloj)
    elif destino == "saludo":
        turno = Turno(SALUDO, intencion.etiqueta, intencion.confianza, "respuesta_fija")
    elif destino == "fuera_de_alcance":
        turno = Turno(FUERA, intencion.etiqueta, intencion.confianza, "respuesta_fija")
    else:
        texto_skill = skills.instrucciones(skill) if skill else None
        if skill:
            traza.append(Paso("skill", skill, "instrucciones de formato cargadas", reloj.ms()))
        ans = responder_qa(mensaje, texto_skill)
        turno = Turno(
            ans.text,
            intencion.etiqueta,
            intencion.confianza,
            "conocimiento",
            intencion.seccion,
            intencion.perfil.conocido(),
            fuentes=extraer_fuentes(ans.text),
            skill=skill,
        )
        traza.append(
            Paso(
                "conocimiento",
                "Q&A con fuentes",
                f"{ans.context_tokens_est:,} tokens de contexto · {len(turno.fuentes)} fuente(s)",
                round(ans.latency_s * 1000) or reloj.ms(),
            )
        )
    turno.traza = traza + turno.traza
    return turno

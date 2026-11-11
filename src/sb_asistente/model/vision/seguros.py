"""De lo que se ve en la foto a qué seguro de personas aplica (alcance PERSONAS, ADR-002 y ADR-020).

Cada tema agrupa clases del modelo YOLO preentrenado (COCO) y apunta a páginas reales de la base
pública. La ``pregunta`` es la consulta que se le hace al asistente, como si la escribiera el
cliente: el asistente responde con sus propios prompts (``model/llm/prompts.py``) y cita la fuente.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal, Protocol

from sb_asistente.model.vision.deteccion import Deteccion


@dataclass(frozen=True, slots=True)
class Tema:
    """Familia de seguros que se sugiere cuando aparece alguna de sus ``clases``."""

    clave: str
    nombre: str
    clases: frozenset[str]
    pregunta: str
    rutas: tuple[str, ...]  # páginas de la base pública que respaldan la sugerencia


TEMAS: tuple[Tema, ...] = (
    Tema(
        "vehiculo",
        "Carros y motos",
        frozenset({"car", "motorcycle", "truck", "bus"}),
        "¿Qué seguros ofrecen para carros y motos, además del SOAT?",
        ("/soat", "/seguro-todo-riesgo-vehiculo"),
    ),
    Tema(
        "bicicleta",
        "Bicicletas",
        frozenset({"bicycle"}),
        "¿Tienen seguro para bicicletas y qué cubre?",
        ("/clientes-davivienda/maneje-tranquilo/seguro-proteccion-bicicletas",),
    ),
    Tema(
        "mascota",
        "Perros y gatos",
        frozenset({"dog", "cat"}),
        "¿Qué cubre el seguro para mascotas?",
        ("/seguro-para-mascotas",),
    ),
    Tema(
        "hogar",
        "Vivienda y contenidos",
        frozenset(
            {"couch", "bed", "chair", "dining table", "refrigerator", "microwave", "oven", "toaster"}
            | {"sink", "toilet", "tv", "potted plant", "clock", "vase"}
        ),
        "¿Qué cubre el seguro de hogar para la vivienda y sus contenidos?",
        ("/seguro-de-hogar", "/seguro-en-casa"),
    ),
    Tema(
        "tecnologia",
        "Equipos electrónicos",
        frozenset({"laptop", "cell phone", "keyboard", "mouse"}),
        "¿Tienen un seguro para equipos tecnológicos como celulares y portátiles?",
        ("/clientes-davivienda/mantenga-seguro-su-dinero-y-tarjetas/datecnologia",),
    ),
)

ETIQUETAS: dict[str, str] = {
    "car": "carro",
    "motorcycle": "moto",
    "truck": "camión",
    "bus": "bus",
    "bicycle": "bicicleta",
    "dog": "perro",
    "cat": "gato",
    "couch": "sofá",
    "bed": "cama",
    "chair": "silla",
    "dining table": "comedor",
    "refrigerator": "nevera",
    "microwave": "microondas",
    "oven": "horno",
    "toaster": "tostadora",
    "sink": "lavaplatos",
    "toilet": "sanitario",
    "tv": "televisor",
    "potted plant": "planta",
    "clock": "reloj",
    "vase": "florero",
    "laptop": "portátil",
    "cell phone": "celular",
    "keyboard": "teclado",
    "mouse": "mouse",
}


@dataclass(frozen=True, slots=True)
class Sugerencia:
    """Seguro sugerido para una foto, con los objetos que lo motivaron."""

    tema: Tema
    objetos: tuple[str, ...]  # etiquetas en español, sin repetir
    confianza: float  # la mayor entre sus detecciones


def etiqueta(clase: str) -> str:
    """Nombre en español de una clase de COCO (o la clase original si no está traducida)."""
    return ETIQUETAS.get(clase, clase)


def tema_de(clase: str, temas: Iterable[Tema] = TEMAS) -> Tema | None:
    """Tema al que pertenece una clase, o ``None`` si no es un objeto asegurable."""
    return next((t for t in temas if clase in t.clases), None)


def sugerir(detecciones: Iterable[Deteccion], temas: tuple[Tema, ...] = TEMAS) -> list[Sugerencia]:
    """Agrupa las detecciones por tema y las ordena de la más a la menos confiable."""
    por_tema: dict[str, tuple[Tema, dict[str, None], float]] = {}
    for det in detecciones:
        tema = tema_de(det.clase, temas)
        if tema is None:
            continue
        _, objetos, mejor = por_tema.get(tema.clave, (tema, {}, 0.0))
        objetos.setdefault(etiqueta(det.clase), None)
        por_tema[tema.clave] = (tema, objetos, max(mejor, det.confianza))
    sugerencias = [Sugerencia(t, tuple(objs), round(conf, 4)) for t, objs, conf in por_tema.values()]
    return sorted(sugerencias, key=lambda s: -s.confianza)


# --- De la situación de la foto a «¿qué hago?» --------------------------------------------------
@dataclass(frozen=True, slots=True)
class Plan:
    """Qué hacer con una foto: tipo de respuesta, pregunta al asistente y páginas de respaldo."""

    tipo: Literal["siniestro", "asegurar", "documento", "ninguno"]
    nombre: str
    pregunta: str | None = None
    rutas: tuple[str, ...] = ()


SINIESTROS: dict[str, Plan] = {
    "accidente_transito": Plan(
        "siniestro",
        "Accidente de tránsito",
        "¿Qué debo hacer después de un accidente de tránsito y cómo uso el SOAT o el seguro de mi vehículo?",
        ("/soat", "/seguro-todo-riesgo-vehiculo", "/canales-de-atencion"),
    ),
    "dano_hogar": Plan(
        "siniestro",
        "Daño en la vivienda",
        "¿Qué cubre el seguro de hogar ante daños en la vivienda y cómo reporto lo que pasó?",
        ("/seguro-de-hogar", "/canales-de-atencion"),
    ),
    "robo": Plan(
        "siniestro",
        "Posible robo",
        "¿Qué debo hacer si me roban y por qué canal reporto el siniestro a mi seguro?",
        ("/canales-de-atencion", "/seguro-de-hogar", "/seguro-todo-riesgo-vehiculo"),
    ),
}
DOCUMENTO = Plan("documento", "Documento con datos personales")
NINGUNO = Plan("ninguno", "Sin situación asegurable")
MENSAJE_DOCUMENTO = (
    "La foto parece mostrar un documento con datos personales. Por su seguridad no lo analizamos: "
    "no envíe cédulas, pólizas ni facturas. Si necesita un trámite, use los canales oficiales."
)
_TEMA_POR_VEHICULO = {"carro": "vehiculo", "moto": "vehiculo", "electrico": "vehiculo"}


class EscenaLike(Protocol):
    """Lo que se usa de ``escena.Escena`` (evita acoplar este módulo a Pydantic)."""

    situacion: str
    vehiculo: str | None
    tiene_mascota: bool | None
    contiene_documento: bool
    confianza: str


def _tema(clave: str) -> Tema:
    return next(t for t in TEMAS if t.clave == clave)


def _segun_yolo(sugerencias: list[Sugerencia]) -> Plan:
    tema = sugerencias[0].tema if sugerencias else None
    return Plan("asegurar", tema.nombre, tema.pregunta, tema.rutas) if tema else NINGUNO


def planear(escena: EscenaLike | None, sugerencias: list[Sugerencia]) -> Plan:
    """Decide la respuesta: un documento se rechaza, un siniestro va a pasos y canales, un bien a su seguro.

    Si hay ``escena`` (se pidió entender la foto), su lectura manda sobre YOLO: un bus de transporte
    público es «otro», no un vehículo del cliente. Excepción: si el modelo no ve con claridad
    (``confianza`` baja, p. ej. porque una persona difuminada tapaba casi toda la foto), se usa YOLO,
    que vio la foto original en local. Sin ``escena``, se usa la sugerencia de YOLO.
    """
    if escena is None:
        return _segun_yolo(sugerencias)
    if escena.contiene_documento:
        return DOCUMENTO
    if escena.situacion in SINIESTROS:
        return SINIESTROS[escena.situacion]
    if escena.situacion != "asegurar_bien":
        return _segun_yolo(sugerencias) if escena.confianza == "baja" else NINGUNO
    tema: Tema | None = sugerencias[0].tema if sugerencias else None
    if tema is None and escena.vehiculo:
        tema = _tema(_TEMA_POR_VEHICULO[escena.vehiculo])
    elif tema is None and escena.tiene_mascota:
        tema = _tema("mascota")
    return Plan("asegurar", tema.nombre, tema.pregunta, tema.rutas) if tema else NINGUNO


def perfil(escena: EscenaLike | None, sugerencias: list[Sugerencia]) -> dict[str, object]:
    """Perfil para el recomendador de Gestión (solo lo que la foto muestra con claridad)."""
    datos: dict[str, object] = {}
    claves = {s.tema.clave for s in sugerencias}
    if escena is not None and escena.vehiculo:
        datos["vehiculo"] = escena.vehiculo
    elif "vehiculo" in claves:
        objetos = {o for s in sugerencias for o in s.objetos}
        datos["vehiculo"] = "moto" if "moto" in objetos and "carro" not in objetos else "carro"
    if (escena is not None and escena.tiene_mascota) or "mascota" in claves:
        datos["tiene_mascota"] = True
    return datos

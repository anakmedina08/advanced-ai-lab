"""De lo que se ve en la foto a qué seguro de personas aplica (alcance PERSONAS, ADR-002 y ADR-020).

Cada tema agrupa clases del modelo YOLO preentrenado (COCO) y apunta a páginas reales de la base
pública. La ``pregunta`` es la consulta que se le hace al asistente, como si la escribiera el
cliente: el asistente responde con sus propios prompts (``model/llm/prompts.py``) y cita la fuente.
"""

from collections.abc import Iterable
from dataclasses import dataclass

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

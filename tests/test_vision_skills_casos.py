"""Casos tabulados de la foto → sugerencia de seguro y del formato de skills (SPEC-067).

Visión: qué seguro se sugiere por cada objeto de COCO y qué plan sale de cada situación.
Skills: las reglas de OpenCode/Claude Code que validan un ``SKILL.md``.
"""

from dataclasses import dataclass
from pathlib import Path

import pytest

from sb_asistente.model.skills import SkillError, descubrir, instrucciones, leer_skill, nueva_skill
from sb_asistente.model.vision.deteccion import Caja, Deteccion
from sb_asistente.model.vision.seguros import (
    DOCUMENTO,
    ETIQUETAS,
    NINGUNO,
    SINIESTROS,
    TEMAS,
    etiqueta,
    perfil,
    planear,
    sugerir,
    tema_de,
)

CAJA = Caja(0, 0, 10, 10)


def det(clase: str, confianza: float = 0.9) -> Deteccion:
    """Detección de YOLO con una caja fija."""
    return Deteccion(clase, confianza, CAJA)


@dataclass
class Escena:
    """Doble de ``escena.Escena`` con solo los campos que usa ``planear``."""

    situacion: str = "asegurar_bien"
    vehiculo: str | None = None
    tiene_mascota: bool | None = None
    contiene_documento: bool = False
    confianza: str = "alta"


# --- etiqueta y tema_de -------------------------------------------------------------------------


@pytest.mark.parametrize(("clase", "espanol"), sorted(ETIQUETAS.items()))
def test_cada_clase_tiene_nombre_en_espanol(clase, espanol):
    # Arrange
    # Act
    resultado = etiqueta(clase)
    # Assert
    assert resultado == espanol


@pytest.mark.parametrize("clase", ["person", "banana", "kite"])
def test_clase_sin_traduccion_se_devuelve_igual(clase):
    # Arrange
    # Act
    resultado = etiqueta(clase)
    # Assert
    assert resultado == clase


@pytest.mark.parametrize(
    ("clase", "tema"),
    [
        ("car", "vehiculo"),
        ("motorcycle", "vehiculo"),
        ("truck", "vehiculo"),
        ("bus", "vehiculo"),
        ("bicycle", "bicicleta"),
        ("dog", "mascota"),
        ("cat", "mascota"),
        ("couch", "hogar"),
        ("refrigerator", "hogar"),
        ("tv", "hogar"),
        ("laptop", "tecnologia"),
        ("cell phone", "tecnologia"),
        ("person", None),
        ("banana", None),
    ],
)
def test_tema_de(clase, tema):
    # Arrange
    # Act
    resultado = tema_de(clase)
    # Assert
    assert (resultado.clave if resultado else None) == tema


def test_toda_clase_de_un_tema_tiene_etiqueta():
    # Arrange
    clases = {c for t in TEMAS for c in t.clases}
    # Act
    sin_etiqueta = clases - set(ETIQUETAS)
    # Assert
    assert sin_etiqueta == set()


def test_ninguna_clase_pertenece_a_dos_temas():
    # Arrange
    todas = [c for t in TEMAS for c in t.clases]
    # Act
    repetidas = {c for c in todas if todas.count(c) > 1}
    # Assert
    assert repetidas == set()


@pytest.mark.parametrize("tema", TEMAS, ids=lambda t: t.clave)
def test_cada_tema_tiene_pregunta_y_paginas_de_respaldo(tema):
    # Arrange
    # Act
    rutas = tema.rutas
    # Assert
    assert tema.pregunta.startswith("¿") and tema.pregunta.endswith("?")
    assert rutas and all(r.startswith("/") for r in rutas)


# --- sugerir ------------------------------------------------------------------------------------


def test_sugerir_agrupa_por_tema_sin_repetir_objetos():
    # Arrange
    detecciones = [det("car", 0.8), det("car", 0.6), det("motorcycle", 0.7)]
    # Act
    sugerencias = sugerir(detecciones)
    # Assert
    assert (
        len(sugerencias) == 1
        and sugerencias[0].objetos == ("carro", "moto")
        and sugerencias[0].confianza == 0.8
    )


def test_sugerir_ordena_por_confianza():
    # Arrange
    detecciones = [det("dog", 0.5), det("laptop", 0.95), det("couch", 0.7)]
    # Act
    claves = [s.tema.clave for s in sugerir(detecciones)]
    # Assert
    assert claves == ["tecnologia", "hogar", "mascota"]


@pytest.mark.parametrize("clases", [[], ["person"], ["person", "banana", "kite"]])
def test_sugerir_ignora_objetos_no_asegurables(clases):
    # Arrange
    detecciones = [det(c) for c in clases]
    # Act
    sugerencias = sugerir(detecciones)
    # Assert
    assert sugerencias == []


@pytest.mark.parametrize("confianza", [0.12345, 0.99999, 0.5])
def test_sugerir_redondea_la_confianza(confianza):
    # Arrange
    # Act
    sugerencia = sugerir([det("dog", confianza)])[0]
    # Assert
    assert sugerencia.confianza == round(confianza, 4)


# --- planear ------------------------------------------------------------------------------------


def _sug(*clases: str) -> list:
    return sugerir([det(c) for c in clases])


@pytest.mark.parametrize(
    ("clases", "nombre"),
    [(["car"], "Carros y motos"), (["dog"], "Perros y gatos"), (["laptop"], "Equipos electrónicos")],
)
def test_sin_escena_manda_yolo(clases, nombre):
    # Arrange
    # Act
    plan = planear(None, _sug(*clases))
    # Assert
    assert (plan.tipo, plan.nombre) == ("asegurar", nombre)


def test_sin_escena_ni_objetos_no_hay_plan():
    # Arrange
    # Act
    plan = planear(None, [])
    # Assert
    assert plan == NINGUNO


@pytest.mark.parametrize("situacion", ["asegurar_bien", "accidente_transito", "otro"])
def test_un_documento_siempre_se_rechaza(situacion):
    # Arrange
    escena = Escena(situacion=situacion, contiene_documento=True)
    # Act
    plan = planear(escena, _sug("car"))
    # Assert
    assert plan == DOCUMENTO


@pytest.mark.parametrize("situacion", sorted(SINIESTROS))
def test_un_siniestro_lleva_a_pasos_y_canales(situacion):
    # Arrange
    escena = Escena(situacion=situacion)
    # Act
    plan = planear(escena, _sug("dog"))
    # Assert
    assert plan.tipo == "siniestro" and "/canales-de-atencion" in plan.rutas


@pytest.mark.parametrize(
    ("confianza", "esperado"), [("alta", "ninguno"), ("media", "ninguno"), ("baja", "asegurar")]
)
def test_otra_situacion_solo_usa_yolo_si_el_modelo_no_ve_claro(confianza, esperado):
    # Arrange: p. ej. un bus de transporte público
    escena = Escena(situacion="otro", confianza=confianza)
    # Act
    plan = planear(escena, _sug("bus"))
    # Assert
    assert plan.tipo == esperado


@pytest.mark.parametrize(
    ("escena", "clases", "tema"),
    [
        (Escena(vehiculo="carro"), [], "Carros y motos"),
        (Escena(vehiculo="moto"), [], "Carros y motos"),
        (Escena(vehiculo="electrico"), [], "Carros y motos"),
        (Escena(tiene_mascota=True), [], "Perros y gatos"),
        (Escena(vehiculo="carro"), ["couch"], "Vivienda y contenidos"),  # YOLO tiene prioridad
        (Escena(), [], None),
    ],
)
def test_asegurar_un_bien(escena, clases, tema):
    # Arrange
    # Act
    plan = planear(escena, _sug(*clases))
    # Assert
    assert (plan.nombre if plan.tipo == "asegurar" else None) == tema


# --- perfil para el recomendador ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("escena", "clases", "esperado"),
    [
        (None, [], {}),
        (None, ["car"], {"vehiculo": "carro"}),
        (None, ["motorcycle"], {"vehiculo": "moto"}),
        (None, ["motorcycle", "car"], {"vehiculo": "carro"}),
        (None, ["truck"], {"vehiculo": "carro"}),
        (None, ["dog"], {"tiene_mascota": True}),
        (None, ["car", "cat"], {"vehiculo": "carro", "tiene_mascota": True}),
        (Escena(vehiculo="electrico"), ["car"], {"vehiculo": "electrico"}),
        (Escena(tiene_mascota=True), [], {"tiene_mascota": True}),
        (Escena(), ["laptop"], {}),
    ],
)
def test_perfil_desde_la_foto(escena, clases, esperado):
    # Arrange
    # Act
    resultado = perfil(escena, _sug(*clases))
    # Assert
    assert resultado == esperado


# --- skills -------------------------------------------------------------------------------------


def escribir_skill(raiz: Path, carpeta: str, contenido: str, base: str = ".claude/skills") -> Path:
    """Escribe ``<base>/<carpeta>/SKILL.md`` bajo ``raiz`` y devuelve su ruta."""
    archivo = raiz / base / carpeta / "SKILL.md"
    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_text(contenido, encoding="utf-8")
    return archivo


def frontmatter(name: str = "mi-skill", description: str = "Hace algo útil.", extra: str = "") -> str:
    """Contenido de un SKILL.md con el frontmatter indicado y un cuerpo fijo."""
    return f"---\nname: {name}\ndescription: {description}\n{extra}---\nCuerpo de la skill.\n"


@pytest.mark.parametrize("nombre", ["a", "mi-skill", "skill2", "a-b-c", "x" * 64, "v1-0"])
def test_nombres_validos(tmp_path, nombre):
    # Arrange
    archivo = escribir_skill(tmp_path, nombre, frontmatter(name=nombre))
    # Act
    skill, cuerpo = leer_skill(archivo)
    # Assert
    assert skill.nombre == nombre and cuerpo == "Cuerpo de la skill."


@pytest.mark.parametrize(
    "nombre", ["Mayus", "con_guion_bajo", "-inicio", "fin-", "doble--guion", "x" * 65, "con espacio", "ñandu"]
)
def test_nombres_invalidos(tmp_path, nombre):
    # Arrange
    archivo = escribir_skill(tmp_path, "carpeta", frontmatter(name=f"'{nombre}'"))
    # Act / Assert
    with pytest.raises(SkillError, match="name inválido"):
        leer_skill(archivo)


def test_el_nombre_debe_coincidir_con_la_carpeta(tmp_path):
    # Arrange
    archivo = escribir_skill(tmp_path, "otra-carpeta", frontmatter(name="mi-skill"))
    # Act / Assert
    with pytest.raises(SkillError, match="debe ser igual a la carpeta"):
        leer_skill(archivo)


@pytest.mark.parametrize("descripcion", ["''", "'" + "x" * 1025 + "'"])
def test_la_descripcion_tiene_limites(tmp_path, descripcion):
    # Arrange
    archivo = escribir_skill(tmp_path, "mi-skill", frontmatter(description=descripcion))
    # Act / Assert
    with pytest.raises(SkillError, match="description"):
        leer_skill(archivo)


@pytest.mark.parametrize("contenido", ["sin frontmatter", "---\nname: x\n", "name: x\n---\n"])
def test_sin_frontmatter_falla(tmp_path, contenido):
    # Arrange
    archivo = escribir_skill(tmp_path, "mi-skill", contenido)
    # Act / Assert
    with pytest.raises(SkillError, match="frontmatter"):
        leer_skill(archivo)


@pytest.mark.parametrize(
    ("extra", "uso", "licencia"),
    [
        ("", "desarrollo", None),
        ("license: MIT\n", "desarrollo", "MIT"),
        ("metadata:\n  uso: asistente\n", "asistente", None),
        ("metadata: texto\n", "desarrollo", None),
    ],
)
def test_metadatos_opcionales(tmp_path, extra, uso, licencia):
    # Arrange
    archivo = escribir_skill(tmp_path, "mi-skill", frontmatter(extra=extra))
    # Act
    skill, _ = leer_skill(archivo)
    # Assert
    assert (skill.uso, skill.licencia, skill.para_asistente) == (uso, licencia, uso == "asistente")


def test_descubrir_reporta_nombres_repetidos_entre_carpetas(tmp_path):
    # Arrange
    escribir_skill(tmp_path, "mi-skill", frontmatter())
    escribir_skill(tmp_path, "mi-skill", frontmatter(), base=".opencode/skills")
    # Act
    skills, errores = descubrir(tmp_path)
    # Assert
    assert [s.nombre for s in skills] == ["mi-skill"] and any("ya existe" in e for e in errores)


def test_descubrir_sigue_aunque_una_skill_este_rota(tmp_path):
    # Arrange
    escribir_skill(tmp_path, "buena", frontmatter(name="buena"))
    escribir_skill(tmp_path, "rota", "sin frontmatter")
    # Act
    skills, errores = descubrir(tmp_path)
    # Assert
    assert [s.nombre for s in skills] == ["buena"] and len(errores) == 1


def test_instrucciones_solo_de_skills_del_asistente(tmp_path):
    # Arrange
    escribir_skill(tmp_path, "dev", frontmatter(name="dev"))
    # Act / Assert
    with pytest.raises(KeyError, match="desconocida"):
        instrucciones("dev", tmp_path)


def test_instrucciones_se_recortan_al_tope(tmp_path):
    # Arrange
    contenido = frontmatter(extra="metadata:\n  uso: asistente\n").replace(
        "Cuerpo de la skill.", "x" * 10_000
    )
    escribir_skill(tmp_path, "mi-skill", contenido)
    # Act
    texto = instrucciones("mi-skill", tmp_path)
    # Assert
    assert len(texto) == 4000


@pytest.mark.parametrize("uso", ["asistente", "desarrollo"])
def test_nueva_skill_crea_una_plantilla_valida(tmp_path, uso):
    # Arrange
    # Act
    archivo = nueva_skill("nueva", "Descripción.", uso=uso, raiz=tmp_path)
    # Assert
    assert leer_skill(archivo)[0].uso == uso


@pytest.mark.parametrize(
    ("nombre", "uso", "mensaje"), [("Mala", "desarrollo", "inválido"), ("ok", "otro", "uso debe")]
)
def test_nueva_skill_valida_sus_argumentos(tmp_path, nombre, uso, mensaje):
    # Arrange
    # Act / Assert
    with pytest.raises(SkillError, match=mensaje):
        nueva_skill(nombre, "d", uso=uso, raiz=tmp_path)


def test_nueva_skill_no_pisa_una_existente(tmp_path):
    # Arrange
    nueva_skill("unica", "d", raiz=tmp_path)
    # Act / Assert
    with pytest.raises(SkillError, match="Ya existe"):
        nueva_skill("unica", "d", raiz=tmp_path)

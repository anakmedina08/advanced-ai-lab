"""Pruebas del router del agente (``model/router.py``) y su banco etiquetado."""

from pathlib import Path

import pytest
import yaml

from sb_asistente.model.router import TODAS, TOOLS_POR_RUTA, enrutar

BANCO = yaml.safe_load((Path(__file__).parents[1] / "evaluacion" / "router.yaml").read_text(encoding="utf-8"))


def test_saludo_no_habilita_ninguna_tool():
    # Act
    d = enrutar("hola, buenos días")
    # Assert
    assert d.ruta == "directo"
    assert d.tools == ()


def test_pregunta_numerica_solo_usa_los_datos():
    # Act
    d = enrutar("¿Cuántas pólizas se vendieron en 2025?")
    # Assert
    assert d.ruta == "datos"
    assert d.tools == ("consultar_datos",)


def test_pregunta_que_combina_documentos_y_datos_es_mixta():
    # Act
    d = enrutar("¿Qué cubre el SOAT y cuántas pólizas de autos se vendieron?")
    # Assert
    assert d.ruta == "mixto"
    assert set(d.tools) == {"buscar_conocimiento", "consultar_datos"}


def test_dato_personal_va_a_la_memoria_sin_buscar():
    # Act
    d = enrutar("Me llamo Ana y trabajo en Carvajal")
    # Assert
    assert d.ruta == "directo"


def test_plazo_en_dias_no_se_confunde_con_una_cifra_de_la_cartera():
    # Act
    d = enrutar("¿Cuántos días tengo para reclamar un siniestro?")
    # Assert
    assert d.ruta == "rag"


def test_fuera_de_alcance_no_usa_tools():
    # Act
    d = enrutar("¿Quién ganó el mundial de fútbol?")
    # Assert
    assert d.ruta == "fuera_de_alcance"
    assert d.tools == ()


def test_confianza_baja_habilita_todas_las_tools_con_cautela():
    # Act
    d = enrutar("necesito ayuda con algo")
    # Assert
    assert d.cautela is True
    assert d.tools == TODAS


def test_cada_ruta_tiene_su_conjunto_de_tools():
    # Assert
    assert set(TOOLS_POR_RUTA) == {"directo", "datos", "rag", "mixto", "fuera_de_alcance"}


def test_mensaje_vacio_es_un_error():
    # Act / Assert
    with pytest.raises(ValueError, match="vacío"):
        enrutar("   ")


@pytest.mark.parametrize("caso", BANCO, ids=[c["mensaje"][:40] for c in BANCO])
def test_banco_por_caso(caso):
    # Act
    d = enrutar(caso["mensaje"])
    # Assert
    assert d.ruta == caso["ruta"], d.senales


def test_banco_exactitud_de_al_menos_90_por_ciento():
    # Act
    aciertos = sum(enrutar(c["mensaje"]).ruta == c["ruta"] for c in BANCO)
    # Assert
    assert len(BANCO) >= 30
    assert aciertos / len(BANCO) >= 0.9

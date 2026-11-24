"""Pruebas de las 12 tools adicionales (SPEC-079): AAA, sin red ni API.

Las dependencias se inyectan como dobles; no se toca disco salvo en ``estado_codigo_acceso``,
que usa una base temporal.
"""

import base64
import json
from pathlib import Path

from langgraph.prebuilt.tool_node import ToolRuntime
from langgraph.store.memory import InMemoryStore

from sb_asistente.model.acceso import CodigosAcceso
from sb_asistente.model.agente import ContextoTurno
from sb_asistente.model.herramientas import crear_tools_extra
from sb_asistente.model.memoria import PerfilStore
from sb_asistente.model.rag.hibrido import Fragmento


def _runtime(usuario_id: str | None) -> ToolRuntime:
    """Runtime de turno con el usuario ya resuelto (como lo inyecta el ToolNode)."""
    return ToolRuntime(
        state={},
        context=ContextoTurno(usuario_id=usuario_id),
        config={},
        stream_writer=None,
        tool_call_id=None,
        store=None,
    )


def _fragmento(chunk_id: str, url: str, titulo: str) -> Fragmento:
    return Fragmento(chunk_id, url, titulo, "personas", "texto de ejemplo", 0.5, ("bm25",))


class _Recuperador:
    """Recuperador falso: devuelve siempre los mismos fragmentos."""

    def __init__(self, fragmentos: list[Fragmento]) -> None:
        self.fragmentos = fragmentos

    def buscar(self, consulta: str, k: int = 4, seccion: str | None = None, aseguradora: str | None = None):
        return self.fragmentos


def _tools(**kwargs):
    return {t.name: t for t in crear_tools_extra(**kwargs)}


def test_listar_productos_devuelve_catalogo_y_filtra_por_linea():
    # Arrange
    tools = _tools()
    # Act
    todos = json.loads(tools["listar_productos"].invoke({}))
    hogar = json.loads(tools["listar_productos"].invoke({"linea": "hogar"}))
    # Assert
    assert len(todos) >= 5
    assert all(p["linea"] == "hogar" for p in hogar)
    assert any(p["producto"] == "Seguro de Hogar" for p in hogar)


def test_citar_fuente_devuelve_las_urls():
    # Arrange
    frag = [_fragmento("a", "https://sb.co/soat", "SOAT"), _fragmento("b", "https://sb.co/hogar", "Hogar")]
    tools = _tools(recuperador=_Recuperador(frag))
    # Act
    resultado = json.loads(tools["citar_fuente"].invoke({"consulta": "soat"}))
    # Assert
    assert [r["url"] for r in resultado] == ["https://sb.co/soat", "https://sb.co/hogar"]


def test_las_tools_sin_dependencia_no_se_incluyen():
    # Arrange / Act: la fábrica solo devuelve las tools cuya dependencia está presente.
    tools = _tools()
    # Assert
    assert "listar_productos" in tools and "checklist_siniestro" in tools
    assert "citar_fuente" not in tools  # necesita recuperador
    assert "guardar_perfil" not in tools  # necesita perfil
    assert "estado_codigo_acceso" not in tools  # necesita acceso
    assert "escalar_a_humano" not in tools  # necesita el callable de canales


def test_explicar_termino_glosario_y_desconocido():
    # Arrange
    tools = _tools()
    # Act
    prima = tools["explicar_termino"].invoke({"termino": "prima"})
    desconocido = tools["explicar_termino"].invoke({"termino": "algo-raro"})
    # Assert
    assert "pagas" in prima
    assert "No tengo una definición" in desconocido


def test_checklist_siniestro_por_tipo_y_general():
    # Arrange
    tools = _tools()
    # Act
    auto = tools["checklist_siniestro"].invoke({"tipo": "auto"})
    general = tools["checklist_siniestro"].invoke({})
    # Assert
    assert "1." in auto and "SOAT" in auto
    assert "1." in general


def test_guardar_ver_y_olvidar_perfil():
    # Arrange
    tools = _tools(perfil=PerfilStore(InMemoryStore()))
    usuario = "usuario-1"
    runtime = _runtime(usuario)
    # Act
    guardado = json.loads(
        tools["guardar_perfil"].invoke({"runtime": runtime, "hechos": {"aseguradora": "Bolívar"}})
    )
    perfil = json.loads(tools["ver_perfil"].invoke({"runtime": runtime}))
    borrados = json.loads(tools["olvidar_datos"].invoke({"runtime": runtime}))
    vacio = json.loads(tools["ver_perfil"].invoke({"runtime": runtime}))
    # Assert
    assert guardado["guardado"] == ["aseguradora"]
    assert perfil == {"aseguradora": "Bolívar"}
    assert borrados["borrados"] == 1
    assert vacio == {}


def test_la_tool_de_perfil_no_expone_usuario_id_al_modelo():
    # Arrange / Act
    tools = _tools(perfil=PerfilStore(InMemoryStore()))
    schema = tools["ver_perfil"].args
    # Assert: el usuario sale del runtime, el modelo no puede elegirlo.
    assert "usuario_id" not in schema
    assert "usuario_id" not in tools["guardar_perfil"].args


def test_la_tool_de_perfil_sin_usuario_en_el_contexto_lo_dice():
    # Arrange
    tools = _tools(perfil=PerfilStore(InMemoryStore()))
    # Act
    resultado = tools["ver_perfil"].invoke({"runtime": _runtime(None)})
    # Assert
    assert "No hay usuario identificado" in resultado


def test_estado_codigo_acceso(tmp_path: Path):
    # Arrange
    codigos = CodigosAcceso(tmp_path / "codigos.sqlite")
    codigo, _ = codigos.crear(horas=1, cupo=3)
    tools = _tools(acceso=codigos)
    # Act
    estado = json.loads(tools["estado_codigo_acceso"].invoke({"codigo": codigo}))
    inexistente = tools["estado_codigo_acceso"].invoke({"codigo": "NO-EXISTE"})
    # Assert
    assert estado["vigente"] is True
    assert estado["restantes"] == 3
    assert "Código no encontrado" in inexistente


def test_escalar_a_humano_devuelve_canal_pqr():
    # Arrange
    escalar = lambda aseguradora, motivo: {"canal": "pqr", "aseguradora": aseguradora, "resumen": motivo}  # noqa: E731
    tools = _tools(escalar=escalar)
    # Act
    resultado = json.loads(tools["escalar_a_humano"].invoke({"aseguradora": "Bolívar", "motivo": "reclamo"}))
    # Assert
    assert resultado["canal"] == "pqr"
    assert resultado["aseguradora"] == "Bolívar"


def test_analizar_foto_y_leer_documento_con_dobles():
    # Arrange
    analizar = lambda datos: {"objetos": len(datos), "situacion": "accidente"}  # noqa: E731
    leer = lambda datos: {"aseguradora": "seguros-bolivar"}  # noqa: E731
    tools = _tools(analizar_foto_fn=analizar, leer_documento_fn=leer)
    b64 = base64.b64encode(b"abc").decode()
    # Act
    foto = json.loads(tools["analizar_foto"].invoke({"contenido_base64": b64}))
    doc = json.loads(tools["leer_documento"].invoke({"contenido_base64": b64}))
    # Assert
    assert foto["situacion"] == "accidente"
    assert doc["aseguradora"] == "seguros-bolivar"


def test_analizar_foto_base64_invalido():
    # Arrange
    tools = _tools(analizar_foto_fn=lambda datos: {})
    # Act
    resultado = tools["analizar_foto"].invoke({"contenido_base64": "no-es-base64!!!"})
    # Assert
    assert "base64" in resultado

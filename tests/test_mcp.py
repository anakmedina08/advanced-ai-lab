"""Pruebas del MCP propio (SPEC-078): adaptador delgado, delegación y rechazo de Host."""

import asyncio
import json
from contextlib import asynccontextmanager

from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.testclient import TestClient

from sb_asistente.controller.agente import TOOLS_MCP
from sb_asistente.model.agente import HerramientasMercado, crear_tools
from sb_asistente.model.herramientas import crear_tools_extra
from sb_asistente.model.rag.hibrido import Fragmento
from sb_asistente.view.mcp import crear_mcp


def _fragmento(chunk_id: str, url: str, titulo: str) -> Fragmento:
    return Fragmento(chunk_id, url, titulo, "personas", "texto de ejemplo", 0.5, ("bm25",))


class _Recuperador:
    """Recuperador falso: devuelve siempre los mismos fragmentos."""

    def __init__(self, fragmentos: list[Fragmento]) -> None:
        self.fragmentos = fragmentos

    def buscar(self, consulta: str, k: int = 4, seccion: str | None = None, aseguradora: str | None = None):
        return self.fragmentos


def _mercado_fake() -> HerramientasMercado:
    return HerramientasMercado(
        comparar=lambda consulta: [_fragmento("c", "https://sb.co/c", "Comparación")],
        identificar=lambda pistas: {"aseguradora": "seguros-bolivar"},
        canales=lambda aseguradora, servicio: {"canal": "pqr", "aseguradora": aseguradora},
    )


def _tools() -> dict:
    """Las 11 tools aptas para MCP, construidas con dobles (sin red)."""
    recuperador = _Recuperador([_fragmento("a", "https://sb.co/soat", "SOAT")])
    todas = crear_tools(recuperador, lambda p, k: [], None, _mercado_fake()) + crear_tools_extra(
        recuperador=recuperador, escalar=lambda aseguradora, motivo: {"canal": "pqr"}
    )
    return {t.name: t for t in todas if t.name in TOOLS_MCP}


def _texto(res) -> str:
    return res.content[0].text


def test_crear_mcp_expone_las_tools_de_la_lista_blanca():
    # Arrange / Act
    srv = crear_mcp(_tools())
    nombres = {t.name for t in asyncio.run(srv.list_tools())}
    # Assert: expone exactamente las tools marcadas aptas en el controlador.
    assert nombres == TOOLS_MCP
    assert "guardar_perfil" not in nombres


def test_buscar_conocimiento_delega_en_la_tool_de_langchain():
    # Arrange / Act
    srv = crear_mcp(_tools())
    res = asyncio.run(srv.call_tool("buscar_conocimiento", {"consulta": "soat"}))
    # Assert
    assert "https://sb.co/soat" in _texto(res)


def test_app_streamable_inicializa():
    # Arrange
    srv = crear_mcp(_tools())
    mcp_app = srv.streamable_http_app(
        streamable_http_path="/",
        transport_security=TransportSecuritySettings(allowed_hosts=["127.0.0.1:8000", "127.0.0.1"]),
    )

    @asynccontextmanager
    async def lifespan(app):
        async with mcp_app.router.lifespan_context(mcp_app):
            yield

    parent = Starlette(lifespan=lifespan)
    parent.mount("/mcp", mcp_app)
    body = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "prueba", "version": "0"},
            },
        }
    )
    # Act
    with TestClient(parent) as cliente:
        respuesta = cliente.post(
            "/mcp",
            content=body,
            headers={
                "content-type": "application/json",
                "accept": "application/json, text/event-stream",
                "host": "127.0.0.1:8000",
            },
        )
    # Assert
    assert respuesta.status_code == 200


def test_app_rechaza_host_no_permitido():
    # Arrange: protección DNS-rebinding solo admite el loopback.
    srv = crear_mcp(_tools())
    mcp_app = srv.streamable_http_app(
        streamable_http_path="/",
        transport_security=TransportSecuritySettings(allowed_hosts=["127.0.0.1:8000"]),
    )

    @asynccontextmanager
    async def lifespan(app):
        async with mcp_app.router.lifespan_context(mcp_app):
            yield

    parent = Starlette(lifespan=lifespan)
    parent.mount("/mcp", mcp_app)
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    # Act
    with TestClient(parent) as cliente:
        respuesta = cliente.post(
            "/mcp",
            content=body,
            headers={"content-type": "application/json", "host": "evil.example.com"},
        )
    # Assert
    assert respuesta.status_code == 421

"""MCP propio (SPEC-078): adaptador delgado de las tools del agente para OpenClaw.

Vive en la capa ``view`` (es un transporte): no duplica la lógica de las tools. Cada tool MCP
delega en el ``BaseTool`` de LangChain correspondiente (salido de ``crear_tools``/``crear_tools_extra``);
el controlador arma el diccionario ``tools`` y ``crear_mcp`` solo lo expone por streamable HTTP.

Las tools que tocan datos personales (perfil) o necesitan contexto por usuario quedan fuera:
el gateway no autentica por usuario (ver ``controller.agente.tools_mcp``).
"""

from functools import lru_cache

from langchain_core.tools import BaseTool
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette

from sb_asistente.config import API_PORT
from sb_asistente.controller.agente import (
    LINEAS,
    MCP_INSTRUCTIONS,
    TIPOS_SINIESTRO,
    Seccion,
    ServicioCanal,
    Vehiculo,
    Vivienda,
)


def crear_mcp(tools: dict[str, BaseTool]) -> MCPServer:
    """Servidor MCP con las tools dadas, como adaptador delgado sobre LangChain (sin duplicar lógica)."""
    server = MCPServer(
        name="sb-asistente",
        title="Asistente Seguros Bolívar (Yelo)",
        instructions=MCP_INSTRUCTIONS,
    )

    @server.tool()
    def buscar_conocimiento(consulta: str, seccion: Seccion | None = None) -> str:
        """Busca en la base pública de Seguros Bolívar (BM25 + vectores) y devuelve pasajes con su URL."""
        return tools["buscar_conocimiento"].invoke({"consulta": consulta, "seccion": seccion})

    @server.tool()
    def recomendar_seguros(
        vehiculo: Vehiculo | None = None,
        vivienda: Vivienda | None = None,
        tiene_mascota: bool | None = None,
        tiene_credito: bool | None = None,
        k: int = 3,
    ) -> str:
        """Sugiere seguros según el perfil descrito, con datos sintéticos de práctica."""
        return tools["recomendar_seguros"].invoke(
            {
                "vehiculo": vehiculo,
                "vivienda": vivienda,
                "tiene_mascota": tiene_mascota,
                "tiene_credito": tiene_credito,
                "k": k,
            }
        )

    @server.tool()
    def comparar_aseguradoras(consulta: str) -> str:
        """Busca en lo que publican varias aseguradoras de Colombia y devuelve sus pasajes con URL."""
        return tools["comparar_aseguradoras"].invoke({"consulta": consulta})

    @server.tool()
    def identificar_aseguradora(pistas: str) -> str:
        """Dice con qué aseguradora está la persona a partir de sus pistas (sin datos personales)."""
        return tools["identificar_aseguradora"].invoke({"pistas": pistas})

    @server.tool()
    def canales_aseguradora(aseguradora: str, servicio: ServicioCanal | None = None) -> str:
        """WhatsApp y líneas oficiales de una aseguradora para un servicio, con su página de origen."""
        return tools["canales_aseguradora"].invoke({"aseguradora": aseguradora, "servicio": servicio})

    @server.tool()
    def listar_productos(linea: LINEAS | None = None) -> str:
        """Lista los productos de seguros para personas (catálogo sintético de práctica)."""
        return tools["listar_productos"].invoke({"linea": linea})

    @server.tool()
    def citar_fuente(consulta: str) -> str:
        """Devuelve las páginas de origen (URL y título) de la base pública para una consulta."""
        return tools["citar_fuente"].invoke({"consulta": consulta})

    @server.tool()
    def explicar_termino(termino: str) -> str:
        """Explica un término de seguros en lenguaje sencillo (prima, deducible, cobertura, siniestro…)."""
        return tools["explicar_termino"].invoke({"termino": termino})

    @server.tool()
    def guia_tramite(tramite: str) -> str:
        """Da los pasos para un trámite (reclamar, contactar, cambiar datos) con su fuente."""
        return tools["guia_tramite"].invoke({"tramite": tramite})

    @server.tool()
    def checklist_siniestro(tipo: TIPOS_SINIESTRO = "general") -> str:
        """Entrega una lista de pasos para atender un siniestro (auto, hogar, salud o general)."""
        return tools["checklist_siniestro"].invoke({"tipo": tipo})

    @server.tool()
    def escalar_a_humano(aseguradora: str, motivo: str) -> str:
        """Escala a un humano: entrega el canal oficial (PQR) con el resumen del caso."""
        return tools["escalar_a_humano"].invoke({"aseguradora": aseguradora, "motivo": motivo})

    return server


@lru_cache(maxsize=1)
def app_mcp() -> Starlette:
    """ASGI app del MCP con streamable HTTP en ``/``, para montar en ``/mcp`` (solo loopback)."""
    from sb_asistente.controller import agente as agente_ctrl

    return crear_mcp(agente_ctrl.tools_mcp()).streamable_http_app(
        streamable_http_path="/",
        transport_security=TransportSecuritySettings(
            allowed_hosts=[f"127.0.0.1:{API_PORT}", "127.0.0.1"],
        ),
    )

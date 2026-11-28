"""Lista las tools del agente con su esquema Pydantic (rúbrica 1.1 de Técnicas).

Arma las tools con las mismas fábricas del agente (`crear_tools` y `crear_tools_extra`), con
Store en memoria y una base de códigos temporal, y muestra el modelo Pydantic y sus campos:

    uv run python scripts/listar_tools.py

La vigésima tool, `search_knowledge`, es la del agente RAG de la Fase 2 (`model/llm/agent.py`).
"""

import tempfile
from pathlib import Path

from langgraph.store.memory import InMemoryStore

from sb_asistente.controller import recomendador
from sb_asistente.controller.agente import _tablas, escalar_a_humano, herramientas_mercado, recuperador_cached
from sb_asistente.model.acceso import CodigosAcceso
from sb_asistente.model.agente import crear_tools
from sb_asistente.model.datos import crear_tool_datos
from sb_asistente.model.herramientas import crear_tools_extra
from sb_asistente.model.memoria import PerfilStore

recuperador, _ = recuperador_cached()
reco = lambda perfil, k: recomendador.recomendar_por_perfil(perfil, k)[0]  # noqa: E731
tools = crear_tools(recuperador, reco, crear_tool_datos(_tablas), herramientas_mercado())
tools += crear_tools_extra(
    perfil=PerfilStore(InMemoryStore()),
    acceso=CodigosAcceso(Path(tempfile.mkdtemp()) / "acceso.db"),
    recuperador=recuperador,
    escalar=escalar_a_humano,
    analizar_foto_fn=lambda b: {},
    leer_documento_fn=lambda b: {},
)
print(f"Total: {len(tools)} tools\n")
for i, t in enumerate(tools, 1):
    esquema = t.tool_call_schema
    campos = ", ".join(getattr(esquema, "model_fields", {})) or "-"
    print(f"{i:2}. {t.name:24} {esquema.__name__:22} {campos}")

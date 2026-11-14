"""Pruebas del agente con router: tools por ruta, respuesta fija fuera de alcance y API REST."""

import json

import pandas as pd
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, SystemMessage

from sb_asistente.controller.agente import AgenteAsistente, TurnoAgente, abrir_memoria
from sb_asistente.model.agente import RespuestaAgente
from sb_asistente.model.datos import crear_tool_datos
from sb_asistente.model.rag.hibrido import RecuperadorHibrido
from sb_asistente.view import api, dependencias
from test_agente import CHUNKS, URL_CANALES, ModeloGuionado, final, llamada


class ModeloQueAnotaTools(ModeloGuionado):
    """Además de guionar respuestas, recuerda qué tools le ofrecieron en cada llamada."""

    ofrecidas: list = []

    def bind_tools(self, tools, **kwargs):
        self.ofrecidas.append([getattr(t, "name", None) or t.get("name") for t in tools])
        return self


def tablas() -> dict[str, pd.DataFrame]:
    return {
        "productos": pd.DataFrame(
            {"product_id": ["P01"], "nombre": ["Seguro de Autos"], "linea": ["movilidad"]}
        ),
        "clientes": pd.DataFrame(
            {
                "cliente_id": ["C1"],
                "ciudad": ["Cali"],
                "canal_preferido": ["digital"],
                "fecha_vinculacion": pd.to_datetime(["2024-01-01"]),
            }
        ),
        "polizas": pd.DataFrame(
            {
                "poliza_id": ["Z1", "Z2"],
                "cliente_id": ["C1", "C1"],
                "product_id": ["P01", "P01"],
                "fecha_inicio": pd.to_datetime(["2025-07-01", "2025-08-01"]),
                "canal_venta": ["digital", "digital"],
                "prima_mensual_cop": [100, 200],
            }
        ),
        "siniestros": pd.DataFrame(columns=["siniestro_id", "poliza_id", "fecha", "monto_cop", "estado"]),
    }


def armar(tmp_path, *mensajes):
    modelo = ModeloQueAnotaTools(messages=iter(mensajes))
    modelo.vistos, modelo.ofrecidas = [], []
    agente = AgenteAsistente(
        modelo,
        RecuperadorHibrido(CHUNKS),
        abrir_memoria(tmp_path / "m.sqlite"),
        lambda perfil, k: [],
        datos=crear_tool_datos(tablas),
    )
    return agente, modelo


def test_saludo_no_ofrece_tools_al_modelo(tmp_path):
    # Arrange
    agente, modelo = armar(tmp_path, final(respuesta="¡Hola!", intencion="saludo"))
    # Act
    turno = agente.responder("hola", "hilo-001-aaa")
    # Assert
    assert turno.decision["ruta"] == "directo"
    assert all(t == "RespuestaAgente" for t in modelo.ofrecidas[-1])
    assert turno.pasos == []


def test_pregunta_numerica_solo_ofrece_consultar_datos(tmp_path):
    # Arrange
    agente, modelo = armar(
        tmp_path,
        AIMessage(
            "", tool_calls=[llamada("consultar_datos", metrica="polizas_vendidas", anio=2025, trimestre=3)]
        ),
        final(respuesta="Se vendieron 2 pólizas.", intencion="datos"),
    )
    # Act
    turno = agente.responder("¿Cuántas pólizas se vendieron en el tercer trimestre de 2025?", "hilo-002-bbb")
    # Assert
    assert turno.decision["ruta"] == "datos"
    assert set(modelo.ofrecidas[0]) - {"RespuestaAgente"} == {"consultar_datos"}
    assert json.loads(turno.pasos[0].resultado)["valor"] == 2


def test_pregunta_mixta_combina_documentos_y_datos(tmp_path):
    # Arrange
    agente, modelo = armar(
        tmp_path,
        AIMessage(
            "",
            tool_calls=[
                llamada("buscar_conocimiento", consulta="SOAT cobertura"),
                llamada("consultar_datos", metrica="polizas_vendidas", anio=2025),
            ],
        ),
        final(respuesta="Cubre gastos médicos; 2 pólizas.", fuentes=["https://www.segurosbolivar.com/soat"]),
    )
    # Act
    turno = agente.responder(
        "¿Qué cubre el SOAT y cuántas pólizas de autos se vendieron en 2025?", "hilo-003"
    )
    # Assert
    assert turno.decision["ruta"] == "mixto"
    assert {p.tool for p in turno.pasos} == {"buscar_conocimiento", "consultar_datos"}
    assert set(modelo.ofrecidas[0]) - {"RespuestaAgente"} == {"buscar_conocimiento", "consultar_datos"}


def test_fuera_de_alcance_responde_sin_llamar_al_modelo(tmp_path):
    # Arrange
    agente, modelo = armar(tmp_path)  # sin respuestas guionadas: llamar al modelo fallaría
    # Act
    turno = agente.responder("¿Quién ganó el mundial de fútbol?", "hilo-004-ddd")
    # Assert
    assert turno.decision["ruta"] == "fuera_de_alcance"
    assert turno.salida.intencion == "fuera_de_alcance"
    assert modelo.vistos == []


def test_el_prompt_incluye_la_guia_de_la_ruta(tmp_path):
    # Arrange
    agente, modelo = armar(tmp_path, final(respuesta="ok"))
    # Act
    agente.responder("¿Cuántas pólizas se vendieron en 2025?", "hilo-005-eee")
    # Assert
    sistema = next(m for m in modelo.vistos[-1] if isinstance(m, SystemMessage))
    assert '<ruta_router ruta="datos">' in sistema.content


class AgenteFijo:
    def responder(self, mensaje, conversacion_id, usuario_id=None):
        salida = RespuestaAgente(
            respuesta="Por WhatsApp.", fuentes=[URL_CANALES], intencion="conocimiento", confianza="alta"
        )
        decision = {
            "ruta": "rag",
            "confianza": 0.7,
            "senales": ["x"],
            "tools": ["buscar_conocimiento"],
            "cautela": False,
        }
        return TurnoAgente(conversacion_id, salida, decision=decision, usuario_id=usuario_id)


def test_api_rest_devuelve_la_decision_del_router():
    # Arrange
    api.app.dependency_overrides[dependencias.get_agente] = lambda: lambda proveedor: AgenteFijo()
    try:
        # Act
        r = TestClient(api.app).post(
            "/agente/mensajes",
            json={"mensaje": "¿WhatsApp?", "conversacion_id": "hilo-006", "usuario_id": "usuario-1"},
        )
    finally:
        api.app.dependency_overrides.clear()
    # Assert
    assert r.status_code == 200
    assert r.json()["decision"]["ruta"] == "rag"
    assert r.json()["salida"]["fuentes"] == [URL_CANALES]


def test_api_rest_rechaza_un_id_de_conversacion_inseguro():
    # Act
    r = TestClient(api.app).post("/agente/mensajes", json={"mensaje": "hola", "conversacion_id": "../x"})
    # Assert
    assert r.status_code == 422

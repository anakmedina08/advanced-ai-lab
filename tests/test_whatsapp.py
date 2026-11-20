"""Asistente por WhatsApp (SPEC-073): verificación, firma, códigos de acceso y respuesta.

Cada prueba sigue Arrange / Act / Assert. Meta y el LLM son dobles: ninguna prueba sale a internet.
"""

import hashlib
import hmac
import json
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from sb_asistente import config
from sb_asistente.controller import acceso as acceso_ctrl
from sb_asistente.controller import whatsapp as whatsapp_ctrl
from sb_asistente.model import whatsapp
from sb_asistente.view import api, dependencias

SECRETO = "secreto-de-prueba"
VERIFICAR = "yelo-token-de-prueba"
NUMERO = "573001112233"


def evento(texto: str | None, mensaje_id: str = "wamid.1", tipo: str = "text") -> dict:
    mensaje = {"id": mensaje_id, "from": NUMERO, "type": tipo}
    if texto is not None:
        mensaje["text"] = {"body": texto}
    return {"entry": [{"changes": [{"value": {"messages": [mensaje]}}]}]}


def firmar(cuerpo: bytes) -> str:
    return "sha256=" + hmac.new(SECRETO.encode(), cuerpo, hashlib.sha256).hexdigest()


class Enviador:
    def __init__(self) -> None:
        self.enviados: list[tuple[str, str]] = []

    def enviar(self, para: str, texto: str) -> None:
        self.enviados.append((para, texto))


class Agente:
    def __init__(self) -> None:
        self.preguntas: list[tuple[str, str]] = []
        self.olvidadas: list[str] = []

    def responder(self, mensaje, conversacion_id, usuario_id=None):
        self.preguntas.append((mensaje, conversacion_id))
        salida = SimpleNamespace(
            respuesta="## SOAT\n**Cubre** gastos médicos.", fuentes=["https://x.co/soat"]
        )
        return SimpleNamespace(salida=salida)

    def olvidar(self, conversacion_id):
        self.olvidadas.append(conversacion_id)


@pytest.fixture(autouse=True)
def entorno(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "WHATSAPP_APP_SECRET", SECRETO)
    monkeypatch.setattr(config, "WHATSAPP_VERIFY_TOKEN", VERIFICAR)
    monkeypatch.setattr(config, "WHATSAPP_EXIGE_CODIGO", True)
    monkeypatch.setattr(config, "ACCESO_DB", tmp_path / "acceso.sqlite")
    whatsapp_ctrl._atendidos.clear()


# --- Modelo -------------------------------------------------------------------------------------


def test_firma_valida_solo_con_la_clave_de_la_app():
    # Arrange
    cuerpo = b'{"a": 1}'
    # Act / Assert
    assert whatsapp.firma_valida(cuerpo, firmar(cuerpo), SECRETO)
    assert not whatsapp.firma_valida(cuerpo, firmar(b"otro"), SECRETO)
    assert not whatsapp.firma_valida(cuerpo, None, SECRETO)
    assert not whatsapp.firma_valida(cuerpo, firmar(cuerpo), "")


def test_mensajes_lee_texto_y_marca_lo_que_no_es_texto():
    # Arrange
    ev = evento("hola")
    ev["entry"][0]["changes"][0]["value"]["messages"].append(
        {"id": "wamid.2", "from": NUMERO, "type": "audio"}
    )
    ev["entry"][0]["changes"].append({"value": {"statuses": [{"id": "x", "status": "read"}]}})
    # Act
    entrantes = whatsapp.mensajes(ev)
    # Assert
    assert [(m.id, m.texto) for m in entrantes] == [("wamid.1", "hola"), ("wamid.2", None)]


def test_el_canal_es_anonimo_y_valido_como_id_de_conversacion():
    # Arrange / Act
    canal = whatsapp.canal_de(NUMERO)
    # Assert
    assert NUMERO not in canal and canal.startswith("wa-") and len(canal) <= 64
    assert canal == whatsapp.canal_de(NUMERO)


def test_markdown_a_formato_de_whatsapp_con_fuentes_y_limite():
    # Arrange / Act
    texto = whatsapp.para_whatsapp("## Título\n**Cubre** daños.", ["https://a", "https://b", "https://c"])
    largo = whatsapp.para_whatsapp("x" * 5000, [])
    # Assert
    assert texto == "Título\n*Cubre* daños.\n\nFuente: https://a\nhttps://b"
    assert len(largo) == whatsapp.MAX_TEXTO


@pytest.mark.parametrize(
    ("texto", "codigo"), [("mi código es yelo-7k3m-q9td", "yelo-7k3m-q9td"), ("hola", None)]
)
def test_codigo_en_el_mensaje(texto, codigo):
    # Arrange / Act / Assert
    assert whatsapp.codigo_en(texto) == codigo


def test_cliente_graph_envia_con_el_token_y_el_formato_de_meta():
    # Arrange
    pedidos: list[httpx.Request] = []

    def transporte(pedido: httpx.Request) -> httpx.Response:
        pedidos.append(pedido)
        return httpx.Response(200, json={"messages": [{"id": "wamid.out"}]})

    cliente = whatsapp.ClienteGraph(
        "tok", "123", "v23.0", httpx.Client(transport=httpx.MockTransport(transporte))
    )
    # Act
    cliente.enviar(NUMERO, "hola")
    # Assert
    assert str(pedidos[0].url) == "https://graph.facebook.com/v23.0/123/messages"
    assert pedidos[0].headers["Authorization"] == "Bearer tok"
    assert json.loads(pedidos[0].content)["text"]["body"] == "hola"


# --- Controlador: códigos de acceso antes del LLM -----------------------------------------------


def test_sin_codigo_no_llama_al_llm_y_explica_como_pedirlo():
    # Arrange
    agente, enviador = Agente(), Enviador()
    # Act
    whatsapp_ctrl.atender(evento("¿qué cubre el SOAT?"), lambda: agente, enviador)
    # Assert
    assert agente.preguntas == [] and "código de acceso" in enviador.enviados[0][1]


def test_con_codigo_activado_responde_el_agente_y_gasta_cupo():
    # Arrange
    codigo, _ = acceso_ctrl.crear(24, 2)
    agente, enviador = Agente(), Enviador()
    # Act
    whatsapp_ctrl.atender(evento(f"Hola, mi código es {codigo}", "m1"), lambda: agente, enviador)
    whatsapp_ctrl.atender(evento("¿qué cubre el SOAT?", "m2"), lambda: agente, enviador)
    # Assert
    assert "Código activado: tienes 2 mensajes" in enviador.enviados[0][1]
    assert enviador.enviados[1] == (NUMERO, "SOAT\n*Cubre* gastos médicos.\n\nFuente: https://x.co/soat")
    assert agente.preguntas == [("¿qué cubre el SOAT?", whatsapp.canal_de(NUMERO))]
    assert acceso_ctrl._codigos().estado(codigo).restantes == 1


def test_con_cupo_agotado_no_llama_al_llm():
    # Arrange
    codigo, _ = acceso_ctrl.crear(24, 1)
    agente, enviador = Agente(), Enviador()
    whatsapp_ctrl.atender(evento(codigo, "m1"), lambda: agente, enviador)
    whatsapp_ctrl.atender(evento("pregunta 1", "m2"), lambda: agente, enviador)
    # Act
    whatsapp_ctrl.atender(evento("pregunta 2", "m3"), lambda: agente, enviador)
    # Assert
    assert len(agente.preguntas) == 1 and "todos sus mensajes" in enviador.enviados[-1][1]


def test_codigo_inexistente_se_rechaza():
    # Arrange
    enviador = Enviador()
    # Act
    whatsapp_ctrl.atender(evento("YELO-AAAA-AAAA"), lambda: Agente(), enviador)
    # Assert
    assert "no existe" in enviador.enviados[0][1]


def test_meta_reintenta_y_no_se_responde_dos_veces():
    # Arrange
    enviador = Enviador()
    # Act
    whatsapp_ctrl.atender(evento("hola", "repetido"), lambda: Agente(), enviador)
    whatsapp_ctrl.atender(evento("hola", "repetido"), lambda: Agente(), enviador)
    # Assert
    assert len(enviador.enviados) == 1


def test_olvidar_borra_la_conversacion_y_el_codigo():
    # Arrange
    codigo, _ = acceso_ctrl.crear(24, 5)
    agente, enviador = Agente(), Enviador()
    whatsapp_ctrl.atender(evento(codigo, "m1"), lambda: agente, enviador)
    # Act
    whatsapp_ctrl.atender(evento("olvidar", "m2"), lambda: agente, enviador)
    whatsapp_ctrl.atender(evento("¿y ahora?", "m3"), lambda: agente, enviador)
    # Assert
    assert agente.olvidadas == [whatsapp.canal_de(NUMERO)] and agente.preguntas == []


def test_un_audio_recibe_aviso_de_solo_texto():
    # Arrange
    enviador = Enviador()
    # Act
    whatsapp_ctrl.atender(evento(None, tipo="audio"), lambda: Agente(), enviador)
    # Assert
    assert enviador.enviados[0][1] == whatsapp_ctrl.SOLO_TEXTO


def test_si_el_agente_falla_la_persona_recibe_un_aviso():
    # Arrange
    class Roto(Agente):
        def responder(self, *a, **k):
            raise RuntimeError("caído")

    acceso_codigo, _ = acceso_ctrl.crear(24, 5)
    enviador = Enviador()
    whatsapp_ctrl.atender(evento(acceso_codigo, "m1"), Roto, enviador)
    # Act
    whatsapp_ctrl.atender(evento("hola", "m2"), Roto, enviador)
    # Assert
    assert enviador.enviados[-1][1] == whatsapp_ctrl.ERROR


# --- Vista: webhook -----------------------------------------------------------------------------


@pytest.fixture
def client():
    enviador = Enviador()
    agente = Agente()
    o = api.app.dependency_overrides
    o[dependencias.get_whatsapp] = lambda: enviador
    o[dependencias.get_agente] = lambda: lambda proveedor: agente
    yield TestClient(api.app), enviador, agente
    o.clear()


def test_get_verificacion_devuelve_el_reto_con_el_token_correcto(client):
    # Arrange
    c, _, _ = client
    params = {"hub.mode": "subscribe", "hub.verify_token": VERIFICAR, "hub.challenge": "12345"}
    # Act
    bien = c.get("/whatsapp/webhook", params=params)
    mal = c.get("/whatsapp/webhook", params={**params, "hub.verify_token": "otro"})
    # Assert
    assert bien.status_code == 200 and bien.text == "12345"
    assert mal.status_code == 403


def test_sin_configuracion_el_webhook_responde_503(client, monkeypatch):
    # Arrange
    monkeypatch.setattr(config, "WHATSAPP_VERIFY_TOKEN", "")
    c, _, _ = client
    # Act
    r = c.get(
        "/whatsapp/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "", "hub.challenge": "1"}
    )
    # Assert
    assert r.status_code == 503


def test_post_sin_firma_valida_es_403_y_no_responde(client):
    # Arrange
    c, enviador, _ = client
    cuerpo = json.dumps(evento("hola")).encode()
    # Act
    r = c.post("/whatsapp/webhook", content=cuerpo, headers={"X-Hub-Signature-256": "sha256=falsa"})
    # Assert
    assert r.status_code == 403 and enviador.enviados == []


def test_post_firmado_responde_200_y_contesta_en_segundo_plano(client):
    # Arrange
    c, enviador, _ = client
    cuerpo = json.dumps(evento("hola")).encode()
    # Act
    r = c.post(
        "/whatsapp/webhook",
        content=cuerpo,
        headers={"X-Hub-Signature-256": firmar(cuerpo), "Content-Type": "application/json"},
    )
    # Assert: TestClient ejecuta las tareas en segundo plano antes de volver
    assert r.status_code == 200 and r.json() == {"ok": True}
    assert enviador.enviados and "código de acceso" in enviador.enviados[0][1]

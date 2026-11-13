"""Pruebas del flujo «foto → ¿qué hago?»: privacidad, escena (Claude simulado), plan y recomendador."""

import base64
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from sb_asistente.controller import vision
from sb_asistente.model.vision import deteccion, seguros
from sb_asistente.model.vision.deteccion import Caja, DetectorYolo
from sb_asistente.model.vision.escena import Escena, InterpreteEscena, contenido_imagen
from sb_asistente.model.vision.privacidad import difuminar
from sb_asistente.view import cli
from sb_asistente.view.api import app
from sb_asistente.view.dependencias import get_detector, get_foto_qa, get_interprete, get_recomendar
from test_vision import FakeDetector, RecordingAssistant, _Caja, _Resultado, det, foto

PERSONA = Caja(20, 10, 60, 70)


def foto_a_cuadros(ancho: int = 120, alto: int = 80) -> bytes:
    """Imagen con detalle fino (cuadros blanco y negro) para notar el difuminado."""
    imagen = Image.new("RGB", (ancho, alto), "white")
    for x in range(ancho):
        for y in range(alto):
            if (x // 2 + y // 2) % 2:
                imagen.putpixel((x, y), (0, 0, 0))
    buffer = BytesIO()
    imagen.save(buffer, format="PNG")
    return buffer.getvalue()


def escena(situacion: str = "asegurar_bien", **campos: object) -> Escena:
    return Escena(situacion=situacion, descripcion="Escena de prueba.", **campos)


class FakeInterprete:
    """Intérprete falso: guarda la imagen recibida y devuelve una escena fija."""

    def __init__(self, resultado: Escena) -> None:
        self.resultado = resultado
        self.imagenes: list[Image.Image] = []

    def interpretar(self, imagen):
        self.imagenes.append(imagen)
        return self.resultado


class FakeRecomendador:
    def __init__(self, error: Exception | None = None) -> None:
        self.perfiles: list[dict] = []
        self.error = error

    def __call__(self, perfil):
        self.perfiles.append(perfil)
        if self.error:
            raise self.error
        return [{"product_id": "P01", "nombre": "SOAT", "linea": "movilidad", "razon": "Perfil similar."}]


# --- Privacidad ---------------------------------------------------------------------------------
def test_difuminar_borra_el_detalle_dentro_de_la_caja_y_respeta_el_resto():
    original = deteccion.abrir_imagen(foto_a_cuadros())
    privada = difuminar(original, [PERSONA], margen=0)
    dentro = {privada.getpixel((x, y)) for x in range(24, 56) for y in range(14, 66)}
    assert (0, 0, 0) not in dentro and (255, 255, 255) not in dentro  # sin cuadros nítidos
    assert privada.getpixel((100, 4)) == original.getpixel((100, 4))  # fuera de la caja, intacta
    assert original.getpixel((24, 14)) in {(0, 0, 0), (255, 255, 255)}  # el original no cambia


def test_detector_yolo_aparta_personas_aun_con_baja_confianza():
    detector = DetectorYolo("falso.pt", confianza=0.3)
    detector._yolo = lambda imagen, conf, verbose: [
        _Resultado([_Caja(0, 0.2, (1, 2, 3, 4)), _Caja(2, 0.9, (5, 5, 9, 9))])
    ]
    resultado = detector.detectar(foto())
    assert resultado.personas == (Caja(1.0, 2.0, 3.0, 4.0),)
    assert [d.clase for d in resultado.detecciones] == ["car"]


# --- Escena (Claude simulado) -------------------------------------------------------------------
def test_contenido_imagen_reduce_fotos_grandes_y_usa_jpeg():
    bloque = contenido_imagen(Image.new("RGB", (4000, 3000)), lado_maximo=400)
    imagen = Image.open(BytesIO(base64.b64decode(bloque["base64"])))
    assert bloque["mime_type"] == "image/jpeg" and max(imagen.size) == 400


class _LLMConVision:
    """Doble de BaseChatModel: registra los mensajes y devuelve una escena estructurada."""

    def __init__(self) -> None:
        self.mensajes = None
        self.metodo = None

    def with_structured_output(self, esquema, method):
        self.metodo = method
        llm = self

        class _Runnable:
            def invoke(self, mensajes):
                llm.mensajes = mensajes
                return esquema(situacion="accidente_transito", descripcion="Choque leve.")

        return _Runnable()


def test_interprete_envia_imagen_y_reglas_y_valida_con_pydantic():
    llm = _LLMConVision()
    resultado = InterpreteEscena(llm).interpretar(Image.new("RGB", (50, 50)))
    sistema, humano = llm.mensajes
    assert resultado.situacion == "accidente_transito" and llm.metodo == "json_schema"
    assert "Nunca identifiques personas" in sistema.content
    assert humano.content[0]["type"] == "image"


def test_interprete_por_defecto_rechaza_proveedores_sin_vision():
    with pytest.raises(deteccion.VisionNoDisponibleError, match="solo procesa texto"):
        vision.interprete_por_defecto("deepseek")


# --- Plan: qué hacer con la foto ----------------------------------------------------------------
def test_planear_documento_se_rechaza():
    assert seguros.planear(escena("otro", contiene_documento=True), []).tipo == "documento"


def test_planear_accidente_lleva_a_pasos_y_canales():
    plan = seguros.planear(escena("accidente_transito"), seguros.sugerir([det("car")]))
    assert plan.tipo == "siniestro" and "/canales-de-atencion" in plan.rutas and "SOAT" in plan.pregunta


def test_planear_la_escena_manda_sobre_yolo():
    # Un bus de transporte público: YOLO ve un vehículo, pero no es un bien del cliente.
    assert seguros.planear(escena("otro"), seguros.sugerir([det("bus")])).tipo == "ninguno"


def test_planear_bien_sin_yolo_usa_lo_que_vio_claude():
    plan = seguros.planear(escena("asegurar_bien", vehiculo="moto"), [])
    assert plan.tipo == "asegurar" and plan.nombre == "Carros y motos"


def test_planear_sin_escena_usa_yolo():
    assert seguros.planear(None, seguros.sugerir([det("dog")])).nombre == "Perros y gatos"
    assert seguros.planear(None, []).tipo == "ninguno"


def test_perfil_solo_con_lo_que_se_ve():
    assert seguros.perfil(escena(vehiculo="electrico"), []) == {"vehiculo": "electrico"}
    sugerencias = seguros.sugerir([det("motorcycle"), det("cat")])
    assert seguros.perfil(None, sugerencias) == {"vehiculo": "moto", "tiene_mascota": True}
    assert seguros.perfil(None, []) == {}


# --- Controlador: flujo completo ----------------------------------------------------------------
def test_flujo_envia_a_claude_la_foto_ya_difuminada():
    interprete = FakeInterprete(escena("otro"))
    datos = foto_a_cuadros()
    analisis = vision.analizar_foto(datos, FakeDetector(personas=(PERSONA,)), interprete=interprete)
    assert analisis.personas_difuminadas == 1
    assert interprete.imagenes == [analisis.imagen_privada]
    assert analisis.imagen_privada.tobytes() != deteccion.abrir_imagen(datos).tobytes()


def test_flujo_siniestro_responde_pasos_sin_recomendar_productos():
    asistente, reco = RecordingAssistant(), FakeRecomendador()
    analisis = vision.analizar_foto(
        foto(), FakeDetector(det("car")), asistente, FakeInterprete(escena("accidente_transito")), reco
    )
    assert analisis.plan.tipo == "siniestro" and asistente.preguntas == [analisis.plan.pregunta]
    assert reco.perfiles == [] and analisis.recomendaciones == []


def test_flujo_bien_asegurable_consulta_el_recomendador():
    reco = FakeRecomendador()
    analisis = vision.analizar_foto(
        foto(), FakeDetector(det("dog")), RecordingAssistant(), FakeInterprete(escena("asegurar_bien")), reco
    )
    assert reco.perfiles == [{"tiene_mascota": True}] and analisis.recomendaciones[0]["nombre"] == "SOAT"


def test_flujo_sin_datos_del_recomendador_no_falla():
    reco = FakeRecomendador(FileNotFoundError("sb reco generar"))
    analisis = vision.analizar_foto(foto(), FakeDetector(det("car")), RecordingAssistant(), None, reco)
    assert analisis.recomendaciones == [] and analisis.respuesta is not None


def test_flujo_documento_no_gasta_llm_y_avisa():
    asistente = RecordingAssistant()
    analisis = vision.analizar_foto(
        foto(), FakeDetector(), asistente, FakeInterprete(escena("otro", contiene_documento=True))
    )
    assert asistente.preguntas == [] and "datos personales" in analisis.aviso


# --- API y CLI con interpretación ---------------------------------------------------------------
@pytest.fixture
def api_completa():
    reco = FakeRecomendador()
    app.dependency_overrides[get_detector] = lambda: lambda: FakeDetector(det("car"), personas=(PERSONA,))
    app.dependency_overrides[get_foto_qa] = lambda: lambda proveedor: RecordingAssistant()
    app.dependency_overrides[get_interprete] = lambda: (
        lambda proveedor: FakeInterprete(escena("asegurar_bien", vehiculo="carro"))
    )
    app.dependency_overrides[get_recomendar] = lambda: reco
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_api_flujo_completo(api_completa):
    r = api_completa.post(
        "/fotos?interpretar=true&responder=true", files={"archivo": ("carro.png", foto(), "image/png")}
    )
    cuerpo = r.json()
    assert r.status_code == 200 and cuerpo["personas_difuminadas"] == 1
    assert cuerpo["escena"]["situacion"] == "asegurar_bien" and cuerpo["plan"]["tipo"] == "asegurar"
    assert cuerpo["respuesta"]["cita_fuente"] and cuerpo["recomendaciones"][0]["nombre"] == "SOAT"


def test_api_interpretar_con_proveedor_sin_vision_responde_503():
    app.dependency_overrides[get_detector] = lambda: lambda: FakeDetector(det("car"))
    try:
        r = TestClient(app).post(
            "/fotos?interpretar=true&proveedor=deepseek", files={"archivo": ("a.png", foto(), "image/png")}
        )
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 503 and "solo procesa texto" in r.json()["detalle"]


def test_cli_foto_con_interpretacion(monkeypatch, capsys, tmp_path):
    ruta = tmp_path / "choque.png"
    ruta.write_bytes(foto())
    monkeypatch.setattr(vision, "detector_por_defecto", lambda: FakeDetector(det("car")))
    monkeypatch.setattr(
        vision, "interprete_por_defecto", lambda p: FakeInterprete(escena("accidente_transito"))
    )
    assert cli.main(["foto", str(ruta), "--interpretar"]) == 0
    salida = capsys.readouterr().out
    assert "Situación: accidente_transito" in salida and "Plan: Accidente de tránsito" in salida


def test_planear_usa_yolo_si_el_modelo_no_ve_claro():
    # Una persona abrazando a su perro: al difuminarla, la foto queda casi toda borrosa.
    sugerencias = seguros.sugerir([det("dog")])
    assert seguros.planear(escena("otro", confianza="baja"), sugerencias).nombre == "Perros y gatos"
    assert seguros.planear(escena("otro", confianza="alta"), sugerencias).tipo == "ninguno"

"""Pruebas de detección y sugerencias por foto (YOLO simulado; sin red, sin API y sin ultralytics)."""

import base64
import sys
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from PIL import Image

from sb_asistente.controller import vision
from sb_asistente.model.llm.assistants import RetrievalAssistant
from sb_asistente.model.vision import deteccion, seguros
from sb_asistente.model.vision.deteccion import Caja, Deteccion, DetectorYolo, ResultadoDeteccion
from sb_asistente.model.vision.privacidad import a_jpeg_b64
from sb_asistente.view import cli
from sb_asistente.view.anotaciones import COLOR_ASEGURABLE, dibujar_detecciones
from sb_asistente.view.api import app
from sb_asistente.view.api_client import ClienteAPI
from sb_asistente.view.dependencias import get_detector, get_foto_qa

URL_MOTOS = "https://www.segurosbolivar.com/soat"


def foto(ancho: int = 120, alto: int = 80, formato: str = "PNG") -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (ancho, alto), "white").save(buffer, format=formato)
    return buffer.getvalue()


def det(clase: str, confianza: float = 0.9) -> Deteccion:
    return Deteccion(clase, confianza, Caja(10, 10, 60, 50))


class FakeDetector:
    """Detector falso: devuelve detecciones fijas y registra las fotos recibidas."""

    def __init__(self, *detecciones: Deteccion, personas: tuple[Caja, ...] = ()) -> None:
        self.detecciones = detecciones
        self.personas = personas
        self.llamadas = 0

    def detectar(self, datos: bytes) -> ResultadoDeteccion:
        imagen = deteccion.abrir_imagen(datos)
        self.llamadas += 1
        return ResultadoDeteccion(self.detecciones, 12.5, *imagen.size, self.personas)


class RecordingAssistant:
    def __init__(self) -> None:
        self.preguntas: list[str] = []

    def answer(self, question, version="v3", skill=None):
        self.preguntas.append(question)
        return RetrievalAssistant(
            FakeListChatModel(responses=[f"Cubre gastos médicos.\nFuente: {URL_MOTOS}"]),
            lambda q: f"### SOAT\nFuente: {URL_MOTOS}\n\nEl SOAT cubre gastos médicos.",
            "",
        ).answer(question)


# --- Imagen -----------------------------------------------------------------------------------
def test_abrir_imagen_devuelve_rgb_con_su_tamano():
    imagen = deteccion.abrir_imagen(foto(120, 80, "JPEG"))
    assert imagen.mode == "RGB" and imagen.size == (120, 80)


@pytest.mark.parametrize(("datos", "mensaje"), [(b"", "vacío"), (b"no soy una imagen", "imagen válida")])
def test_abrir_imagen_rechaza_archivos_invalidos(datos, mensaje):
    with pytest.raises(deteccion.ImagenInvalidaError, match=mensaje):
        deteccion.abrir_imagen(datos)


def test_abrir_imagen_rechaza_archivos_grandes():
    with pytest.raises(deteccion.ImagenInvalidaError, match="MB"):
        deteccion.abrir_imagen(foto(), max_bytes=10)


# --- Filtro de privacidad y umbral ------------------------------------------------------------
def test_filtrar_nunca_reporta_personas():
    assert [d.clase for d in deteccion.filtrar([det("person"), det("car")], confianza_minima=0.1)] == ["car"]


def test_filtrar_descarta_baja_confianza():
    assert deteccion.filtrar([det("dog", 0.2), det("cat", 0.8)], confianza_minima=0.5) == (det("cat", 0.8),)


# --- Objeto → seguro ---------------------------------------------------------------------------
def test_sugerir_agrupa_por_tema_y_ordena_por_confianza():
    sugerencias = seguros.sugerir([det("dog", 0.6), det("car", 0.9), det("motorcycle", 0.7), det("cat", 0.5)])
    assert [s.tema.clave for s in sugerencias] == ["vehiculo", "mascota"]
    assert sugerencias[0].objetos == ("carro", "moto") and sugerencias[0].confianza == 0.9
    assert sugerencias[1].objetos == ("perro", "gato")


def test_sugerir_ignora_objetos_no_asegurables():
    assert seguros.sugerir([det("tie"), det("banana")]) == []


def test_cada_clase_pertenece_a_un_solo_tema():
    clases = [c for t in seguros.TEMAS for c in t.clases]
    assert len(clases) == len(set(clases))


def test_temas_tienen_pregunta_y_paginas():
    for tema in seguros.TEMAS:
        assert tema.pregunta.startswith("¿") and tema.rutas and all(r.startswith("/") for r in tema.rutas)


def test_etiqueta_en_espanol_y_respaldo_en_ingles():
    assert seguros.etiqueta("cell phone") == "celular" and seguros.etiqueta("kite") == "kite"


# --- DetectorYolo (sin ultralytics real) -------------------------------------------------------
def test_detector_sin_extra_vision_explica_como_instalarlo(monkeypatch):
    monkeypatch.setitem(sys.modules, "ultralytics", None)  # simula que el extra no está instalado
    with pytest.raises(deteccion.VisionNoDisponibleError, match="--extra vision"):
        DetectorYolo("no-existe.pt").detectar(foto())


class _Valor:
    def __init__(self, valor):
        self.valor = valor

    def item(self):
        return self.valor

    def tolist(self):
        return list(self.valor)


class _Caja:
    def __init__(self, clase_id, confianza, xyxy):
        self.cls, self.conf, self.xyxy = [_Valor(clase_id)], [_Valor(confianza)], [_Valor(xyxy)]


class _Resultado:
    names = {0: "person", 1: "bicycle", 2: "car"}

    def __init__(self, cajas):
        self.boxes = cajas


def test_detector_yolo_convierte_resultados_y_oculta_personas():
    detector = DetectorYolo("falso.pt", confianza=0.3)
    detector._yolo = lambda imagen, conf, verbose: [  # modelo ya cargado (simulado)
        _Resultado(
            [_Caja(0, 0.99, (0, 0, 5, 5)), _Caja(1, 0.8, (1.04, 2, 30, 40)), _Caja(2, 0.1, (0, 0, 1, 1))]
        )
    ]
    resultado = detector.detectar(foto(64, 48))
    assert [(d.clase, d.confianza) for d in resultado.detecciones] == [("bicycle", 0.8)]
    assert resultado.detecciones[0].caja == Caja(1.0, 2.0, 30.0, 40.0)
    assert (resultado.ancho, resultado.alto) == (64, 48)


# --- Controlador -------------------------------------------------------------------------------
def test_analizar_foto_sin_asistente_solo_sugiere():
    analisis = vision.analizar_foto(foto(), FakeDetector(det("bicycle")))
    assert analisis.sugerencias[0].tema.clave == "bicicleta" and analisis.respuesta is None


def test_analizar_foto_pregunta_por_la_sugerencia_mas_confiable():
    asistente = RecordingAssistant()
    analisis = vision.analizar_foto(foto(), FakeDetector(det("dog", 0.5), det("car", 0.9)), asistente)
    assert asistente.preguntas == [seguros.TEMAS[0].pregunta]
    assert analisis.respuesta.cites_source


def test_analizar_foto_sin_objetos_asegurables_no_gasta_llm():
    asistente = RecordingAssistant()
    assert vision.analizar_foto(foto(), FakeDetector(det("tie")), asistente).respuesta is None
    assert asistente.preguntas == []


# --- API POST /fotos ---------------------------------------------------------------------------
@pytest.fixture
def api():
    detector = FakeDetector(det("car", 0.88), det("dog", 0.6))
    app.dependency_overrides[get_detector] = lambda: lambda: detector
    app.dependency_overrides[get_foto_qa] = lambda: lambda proveedor: RecordingAssistant()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_api_foto_devuelve_detecciones_y_sugerencias(api):
    r = api.post("/fotos", files={"archivo": ("carro.png", foto(), "image/png")})
    assert r.status_code == 200
    cuerpo = r.json()
    assert [d["etiqueta"] for d in cuerpo["detecciones"]] == ["carro", "perro"]
    assert cuerpo["sugerencias"][0]["paginas"][0] == "https://www.segurosbolivar.com/soat"
    assert cuerpo["respuesta"] is None


def test_api_foto_con_responder_trae_respuesta_y_fuentes(api):
    r = api.post("/fotos?responder=true", files={"archivo": ("carro.png", foto(), "image/png")})
    assert r.json()["respuesta"]["fuentes"] == [URL_MOTOS]


def test_api_foto_rechaza_archivos_que_no_son_imagen(api):
    assert api.post("/fotos", files={"archivo": ("a.txt", b"hola", "text/plain")}).status_code == 400


def test_api_foto_rechaza_imagen_corrupta(api):
    assert api.post("/fotos", files={"archivo": ("a.png", b"xx", "image/png")}).status_code == 422


def test_api_foto_sin_extra_vision_responde_503():
    class SinVision:
        def detectar(self, datos):
            raise deteccion.VisionNoDisponibleError("uv sync --extra vision")

    app.dependency_overrides[get_detector] = lambda: SinVision
    try:
        r = TestClient(app).post("/fotos", files={"archivo": ("a.png", foto(), "image/png")})
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 503 and "extra vision" in r.json()["detalle"]


# --- Cliente httpx -----------------------------------------------------------------------------
def test_cliente_httpx_consume_la_api(api):
    cliente = ClienteAPI("http://testserver", http=api)  # TestClient es un httpx.Client
    out = cliente.analizar_foto(foto(), "perro.png", responder=True)
    assert out.sugerencias[0].tema == "vehiculo" and out.respuesta.cita_fuente
    assert cliente.salud().estado == "ok"


# --- Vista: anotaciones y CLI ------------------------------------------------------------------
def test_dibujar_detecciones_pinta_la_caja_sin_cambiar_tamano():
    imagen = Image.new("RGB", (100, 80), "white")
    anotada = dibujar_detecciones(imagen, [det("car")])
    assert anotada.size == imagen.size and imagen.getpixel((10, 30)) == (255, 255, 255)
    assert anotada.getpixel((10, 30)) == Image.new("RGB", (1, 1), COLOR_ASEGURABLE).getpixel((0, 0))


def test_cli_foto_muestra_la_sugerencia(monkeypatch, capsys, tmp_path):
    ruta = tmp_path / "bici.png"
    ruta.write_bytes(foto())
    monkeypatch.setattr(vision, "detector_por_defecto", lambda: FakeDetector(det("bicycle", 0.77)))
    assert cli.main(["foto", str(ruta)]) == 0
    salida = capsys.readouterr().out
    assert "bicicleta" in salida and "Plan: Bicicletas" in salida


def test_api_foto_devuelve_la_imagen_difuminada_si_se_pide(api):
    # Act
    r = api.post("/fotos?devolver_imagen=true", files={"archivo": ("carro.png", foto(), "image/png")})
    # Assert
    datos = base64.b64decode(r.json()["imagen_jpeg_b64"])
    assert datos[:2] == b"\xff\xd8"  # JPEG


def test_api_foto_no_devuelve_imagen_por_defecto(api):
    # Act
    r = api.post("/fotos", files={"archivo": ("carro.png", foto(), "image/png")})
    # Assert
    assert r.json()["imagen_jpeg_b64"] is None


def test_jpeg_b64_reduce_el_lado_mayor():
    # Arrange
    grande = Image.new("RGB", (3000, 1500), "white")
    # Act
    reducida = Image.open(BytesIO(base64.b64decode(a_jpeg_b64(grande, lado_maximo=1280))))
    # Assert
    assert reducida.size == (1280, 640)

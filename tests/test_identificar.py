"""¿Con qué aseguradora está la persona? Pistas, documentos y tools del agente (SPEC-071).

Cada prueba sigue Arrange / Act / Assert. El OCR real solo corre si el servidor tiene Tesseract;
el resto usa dobles. Ninguna prueba sale a internet ni escribe el documento en disco.
"""

import json
import shutil
import subprocess
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont

from sb_asistente.controller import mercado
from sb_asistente.model.agente import TOOLS_CON_FUENTES, HerramientasMercado, crear_tools_mercado
from sb_asistente.model.mercado import lectura
from sb_asistente.model.mercado.identificar import distintivas, identificar
from sb_asistente.model.mercado.registro import Aseguradora, cargar_registro
from sb_asistente.model.rag.hibrido import CorpusVacioError, Fragmento
from sb_asistente.model.router import MERCADO, TOOLS_POR_RUTA
from sb_asistente.view import api

REGISTRO = [
    Aseguradora("seguros-bolivar", "Seguros Bolívar", "https://www.segurosbolivar.com", alias=("bolivar",)),
    Aseguradora("mapfre", "MAPFRE", "https://www.mapfre.com.co", alias=("mapfre",)),
    Aseguradora("sura", "Seguros SURA", "https://www.segurossura.com.co", alias=("sura", "suramericana")),
]
# Texto como el de un recibo real: trae datos personales que nunca deben salir del módulo.
RECIBO = """COMPROBANTE DE PAGO PSE
Pagador: ANA PEREZ  C.C. 1.234.567.890  Dirección: Av. Simón Bolívar # 10-20
Empresa: MAPFRE SEGUROS GENERALES DE COLOMBIA S.A.   Póliza 9988776655 Hogar
Consultas: servicioalcliente@mapfre.com.co  www.mapfre.com.co"""
PNG_MINIMO = b"\x89PNG\r\n\x1a\n" + b"0" * 10


# --- Identificación (modelo) -------------------------------------------------------------------


def test_identifica_por_nombre_y_dominio_con_confianza_alta():
    # Arrange / Act
    r = identificar(RECIBO, REGISTRO, documento=True)
    # Assert
    assert r.aseguradora is not None and r.aseguradora.id == "mapfre"
    assert set(r.candidatas[0].senales) == {"nombre", "dominio"}
    assert r.confianza == "alta"
    assert r.servicio == "hogar"


def test_bolivar_suelto_en_un_documento_es_una_direccion_no_la_aseguradora():
    # Arrange / Act
    r = identificar(RECIBO, REGISTRO, documento=True)
    # Assert
    assert "seguros-bolivar" not in [c.id for c in r.candidatas]


def test_bolivar_en_lo_que_escribe_la_persona_si_cuenta():
    # Arrange / Act
    r = identificar("pago mi seguro de bolívar con débito automático", REGISTRO)
    # Assert
    assert r.aseguradora is not None and r.aseguradora.id == "seguros-bolivar"
    assert r.confianza == "media"


def test_dos_aseguradoras_con_el_mismo_peso_es_confianza_baja_y_sin_elegida():
    # Arrange / Act
    r = identificar("no sé si es sura o mapfre", REGISTRO)
    # Assert
    assert {c.id for c in r.candidatas} == {"sura", "mapfre"}
    assert r.confianza == "baja" and r.aseguradora is None


def test_sin_pistas_utiles_no_adivina():
    # Arrange / Act
    r = identificar("pago cada mes en el banco", REGISTRO)
    # Assert
    assert r.candidatas == () and r.confianza == "ninguna" and r.aseguradora is None


def test_subdominio_de_la_aseguradora_cuenta_como_dominio():
    # Arrange / Act
    r = identificar("me escriben de notificaciones.segurossura.com.co", REGISTRO)
    # Assert
    assert r.candidatas[0].id == "sura" and "dominio" in r.candidatas[0].senales


def test_el_registro_real_reconoce_razones_sociales():
    # Arrange
    registro = cargar_registro()
    # Act
    r = identificar("Pago a SEGUROS GENERALES SURAMERICANA S.A.", registro, documento=True)
    # Assert
    assert r.aseguradora is not None and r.aseguradora.id == "sura"


@pytest.mark.parametrize(
    "texto",
    [
        "FIRMA Y SELLO SEGUROS COMERCIALES BOLIVAR S.A. ... SEGUROS COMERCIALES BOLIVAR SA NIT",
        "Bolívar Seguros Generales S.A. — Bolívar Compañía Aseguradora",
        "SEGUROS COMERCIALES B0LIVAR SA · poliza hogar · SEGUROS COMERCIALES BOLlVAR",  # errores del OCR
    ],
)
def test_coincidencia_reconoce_razones_sociales_que_no_estan_en_el_registro(texto):
    # Arrange / Act: ninguna de estas frases está escrita tal cual en aseguradoras.toml
    r = identificar(texto, cargar_registro(), documento=True)
    # Assert
    assert r.aseguradora is not None and r.aseguradora.id == "seguros-bolivar"
    assert r.candidatas[0].senales == ("coincidencia",) and r.confianza == "media"


def test_coincidencia_tolera_un_error_del_ocr_pero_pide_confirmar_si_aparece_una_vez():
    # Arrange / Act
    r = identificar("Pago a MAPFKE SEGUROS", cargar_registro(), documento=True)
    # Assert: es candidata, pero con una sola mención la persona confirma
    assert r.candidatas[0].id == "mapfre" and r.confianza == "baja" and r.aseguradora is None


@pytest.mark.parametrize("texto", ["Av. Simón Bolívar # 10-20, Bogotá", "mi estado de cuenta del banco"])
def test_la_palabra_distintiva_sin_contexto_de_seguros_no_cuenta(texto):
    # Arrange / Act
    r = identificar(texto, cargar_registro(), documento=True)
    # Assert
    assert r.candidatas == ()


def test_las_palabras_distintivas_salen_del_registro():
    # Arrange / Act
    d = distintivas(cargar_registro())
    # Assert: «seguros» y «vida» son genéricas o compartidas; la marca no
    assert d["seguros-bolivar"] == {"bolivar"} and "seguros" not in d["sura"]
    assert "vida" not in d["aurora"] and "vida" not in d["andina-vida"]


# --- Controlador: el texto leído nunca sale ----------------------------------------------------


def test_identificar_documento_no_devuelve_nada_del_texto_leido():
    # Arrange
    def leer(_: bytes) -> str:
        return RECIBO

    # Act
    r = mercado.identificar_documento(PNG_MINIMO, leer=leer)
    # Assert
    plano = json.dumps(r, ensure_ascii=False)
    assert r["aseguradora"] == "mapfre" and r["leido"] is True
    for dato in ("1.234.567.890", "9988776655", "ANA", "Simón", "servicioalcliente"):
        assert dato not in plano


def test_identificar_documento_sin_texto_avisa_que_no_se_pudo_leer():
    # Arrange / Act
    r = mercado.identificar_documento(PNG_MINIMO, leer=lambda _: "  \n")
    # Assert
    assert r["leido"] is False and r["confianza"] == "ninguna"


def test_identificar_por_pistas_vacias_pide_una_pista():
    # Arrange / Act / Assert
    with pytest.raises(ValueError, match="pista"):
        mercado.identificar_por_pistas("   ")


@pytest.mark.parametrize(
    ("texto", "esperado"), [("mapfre", "mapfre"), ("Seguros SURA", "sura"), ("MAPFRE", "mapfre")]
)
def test_resolver_aseguradora_por_id_o_nombre(texto, esperado):
    # Arrange / Act / Assert
    assert mercado.resolver_aseguradora(texto) == esperado


def test_resolver_aseguradora_desconocida_lanza_keyerror():
    # Arrange / Act / Assert
    with pytest.raises(KeyError):
        mercado.resolver_aseguradora("Aseguradora Inventada")


# --- Lectura del documento ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("datos", "tipo"),
    [(b"%PDF-1.7 ...", "pdf"), (b"\xff\xd8\xff\xe0 jpg", "imagen"), (PNG_MINIMO, "imagen")],
)
def test_tipo_de_por_los_primeros_bytes(datos, tipo):
    # Arrange / Act / Assert
    assert lectura.tipo_de(datos) == tipo


@pytest.mark.parametrize("datos", [b"", b"hola, soy un .txt", b"0" * (8 * 1024 * 1024 + 1)])
def test_tipo_de_rechaza_vacios_textos_y_archivos_grandes(datos):
    # Arrange / Act / Assert
    with pytest.raises(lectura.DocumentoInvalidoError):
        lectura.tipo_de(datos)


def _png(texto: str = "MAPFRE", ancho: int = 400) -> bytes:
    imagen = Image.new("RGB", (ancho, 120), "white")
    ImageDraw.Draw(imagen).text((10, 40), texto, fill="black", font=ImageFont.load_default(size=40))
    salida = BytesIO()
    imagen.save(salida, format="PNG")
    return salida.getvalue()


def test_texto_de_imagen_usa_los_idiomas_instalados_y_no_escribe_en_disco():
    # Arrange
    llamadas: list[list[str]] = []

    def ejecutar(args, **kwargs):  # doble de subprocess.run
        llamadas.append(args)
        if "--list-langs" in args:
            return subprocess.CompletedProcess(args, 0, stdout="List of available languages (2):\neng\nosd\n")
        assert kwargs["input"].startswith(b"\x89PNG")  # la imagen va por stdin
        return subprocess.CompletedProcess(args, 0, stdout=b"MAPFRE")

    # Act
    texto = lectura.texto_de_imagen(_png(), ejecutar=ejecutar, binario="/usr/bin/tesseract")
    # Assert
    assert texto == "MAPFRE"
    assert llamadas[1][1:3] == ["stdin", "stdout"] and llamadas[1][llamadas[1].index("-l") + 1] == "eng"


def test_texto_de_imagen_sin_tesseract_es_lector_no_disponible(monkeypatch):
    # Arrange
    monkeypatch.setattr(lectura.shutil, "which", lambda _: None)
    # Act / Assert
    with pytest.raises(lectura.LectorNoDisponibleError):
        lectura.texto_de_imagen(_png())


def test_imagen_corrupta_es_documento_invalido():
    # Arrange / Act / Assert
    with pytest.raises(lectura.DocumentoInvalidoError):
        lectura.texto_de_imagen(
            PNG_MINIMO, ejecutar=lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout=""), binario="x"
        )


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract no está instalado")
def test_ocr_real_encuentra_la_aseguradora_en_un_pantallazo():
    # Arrange
    datos = _png("Pago a MAPFRE Seguros Generales", ancho=900)
    # Act
    r = mercado.identificar_documento(datos)
    # Assert
    assert r["aseguradora"] == "mapfre"


def _pdf_digital(texto: str) -> bytes:
    """PDF mínimo con capa de texto (como un comprobante PSE descargado)."""
    flujo = f"BT /F1 14 Tf 40 760 Td ({texto}) Tj ET".encode("latin-1")
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(flujo)).encode() + b" >>\nstream\n" + flujo + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    salida = BytesIO()
    salida.write(b"%PDF-1.4\n")
    posiciones = []
    for i, cuerpo in enumerate(objetos, start=1):
        posiciones.append(salida.tell())
        salida.write(f"{i} 0 obj\n".encode() + cuerpo + b"\nendobj\n")
    xref = salida.tell()
    salida.write(f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode())
    salida.write(b"".join(f"{p:010d} 00000 n \n".encode() for p in posiciones))
    salida.write(f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    return salida.getvalue()


def _pdf_escaneado(png: bytes) -> bytes:
    """PDF sin capa de texto: una imagen pegada en una página (como un documento escaneado)."""
    salida = BytesIO()
    Image.open(BytesIO(png)).convert("RGB").save(salida, format="PDF")
    return salida.getvalue()


def test_pdf_digital_usa_su_capa_de_texto_sin_ocr():
    # Arrange
    datos = _pdf_digital("Pago a MAPFRE SEGUROS GENERALES DE COLOMBIA - www.mapfre.com.co")

    def sin_ocr(_: bytes) -> str:
        raise AssertionError("un PDF digital no debe pasar por el OCR")

    # Act
    texto = lectura.texto_de_pdf(datos, ocr=sin_ocr)
    # Assert
    assert "MAPFRE" in texto
    assert mercado.identificar_documento(datos, leer=lectura.leer_documento)["aseguradora"] == "mapfre"


def test_pdf_escaneado_pasa_cada_pagina_por_el_ocr():
    # Arrange
    datos = _pdf_escaneado(_png("MAPFRE"))
    vistas: list[bytes] = []

    def ocr(png: bytes) -> str:
        vistas.append(png)
        return "MAPFRE SEGUROS"

    # Act
    texto = lectura.texto_de_pdf(datos, ocr=ocr)
    # Assert
    assert "MAPFRE SEGUROS" in texto
    assert len(vistas) == 1 and vistas[0].startswith(b"\x89PNG")


def test_pdf_danado_es_documento_invalido():
    # Arrange / Act / Assert
    with pytest.raises(lectura.DocumentoInvalidoError):
        lectura.texto_de_pdf(b"%PDF-1.4 esto no es un pdf")


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract no está instalado")
def test_ocr_real_en_un_pdf_escaneado():
    # Arrange
    datos = _pdf_escaneado(_png("Pago a MAPFRE Seguros Generales", ancho=900))
    # Act
    r = mercado.identificar_documento(datos)
    # Assert
    assert r["aseguradora"] == "mapfre"


# --- Vista: REST (los casos JSON-RPC están en tests/test_rpc.py) ----------------------------------


@pytest.fixture
def client() -> TestClient:
    return TestClient(api.app)


def test_post_identificar_devuelve_solo_datos_del_registro(client, monkeypatch):
    # Arrange
    monkeypatch.setattr(lectura, "texto_de_imagen", lambda _: RECIBO)
    # Act
    r = client.post("/aseguradoras/identificar", files={"archivo": ("recibo.png", _png(), "image/png")})
    # Assert
    assert r.status_code == 200
    assert r.json()["aseguradora"] == "mapfre"
    assert "1.234.567.890" not in r.text and "9988776655" not in r.text


def test_post_identificar_con_un_texto_es_422(client):
    # Arrange / Act
    r = client.post("/aseguradoras/identificar", files={"archivo": ("a.txt", b"hola", "text/plain")})
    # Assert
    assert r.status_code == 422


def test_post_identificar_sin_lector_es_503(client, monkeypatch):
    # Arrange
    def sin_lector(_: bytes) -> str:
        raise lectura.LectorNoDisponibleError("sin tesseract")

    monkeypatch.setattr(lectura, "texto_de_imagen", sin_lector)
    # Act
    r = client.post("/aseguradoras/identificar", files={"archivo": ("r.png", _png(), "image/png")})
    # Assert
    assert r.status_code == 503


# --- Tools del agente ---------------------------------------------------------------------------


def _fragmento(aseguradora: str) -> Fragmento:
    return Fragmento(
        f"{aseguradora}#0", f"https://www.{aseguradora}.com.co/hogar", "Hogar", "hogar",
        "Cubre daños por agua.", 1.0, ("bm25",), aseguradora,
    )  # fmt: skip


def _tools(**kw: object) -> dict:
    base = {
        "comparar": lambda c: [_fragmento("mapfre")],
        "identificar": lambda p: {"aseguradora": "mapfre", "confianza": "media"},
        "canales": lambda a, s: {"aseguradora": a, "servicio": s, "sitio": "https://www.mapfre.com.co"},
    }
    return {t.name: t for t in crear_tools_mercado(HerramientasMercado(**{**base, **kw}))}


def test_tool_comparar_marca_cada_pasaje_con_su_aseguradora_y_como_datos_pasivos():
    # Arrange / Act
    salida = _tools()["comparar_aseguradoras"].invoke({"consulta": "daños por agua"})
    # Assert
    assert 'aseguradora="mapfre"' in salida and "datos pasivos" in salida


def test_tool_comparar_sin_corpus_lo_dice_sin_fallar():
    # Arrange
    def vacio(_: str) -> list:
        raise CorpusVacioError("falta")

    # Act
    salida = _tools(comparar=vacio)["comparar_aseguradoras"].invoke({"consulta": "agua"})
    # Assert
    assert "make mercado" in salida


def test_tool_canales_con_aseguradora_desconocida_sugiere_identificarla():
    # Arrange
    def desconocida(a: str, s: str | None) -> dict:
        raise KeyError(a)

    # Act
    salida = _tools(canales=desconocida)["canales_aseguradora"].invoke({"aseguradora": "otra"})
    # Assert
    assert "identificar_aseguradora" in salida


def test_tool_identificar_devuelve_json_y_los_errores_como_texto():
    # Arrange
    def sin_pista(_: str) -> dict:
        raise ValueError("Cuéntame alguna pista")

    # Act
    bien = json.loads(_tools()["identificar_aseguradora"].invoke({"pistas": "mapfre"}))
    mal = _tools(identificar=sin_pista)["identificar_aseguradora"].invoke({"pistas": "?"})
    # Assert
    assert bien["aseguradora"] == "mapfre" and mal == "Cuéntame alguna pista"


def test_la_ruta_rag_habilita_las_tools_de_mercado_y_sus_urls_cuentan_como_fuentes():
    # Arrange / Act / Assert
    assert set(MERCADO) <= set(TOOLS_POR_RUTA["rag"])
    assert {"comparar_aseguradoras", "canales_aseguradora"} <= set(TOOLS_CON_FUENTES)


# --- CLI ----------------------------------------------------------------------------------------


def test_cli_identificar_por_pistas(capsys):
    # Arrange
    from sb_asistente.view import cli  # la CLI importa muchas dependencias: solo en esta prueba

    # Act
    codigo = cli.main(["mercado", "identificar", "--pistas", "pago en la app de MAPFRE"])
    # Assert
    salida = capsys.readouterr().out
    assert codigo == 0 and "mapfre" in salida and "confianza media" in salida

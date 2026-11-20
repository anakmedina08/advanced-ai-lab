# Plan · SPEC-071

1. **Modelo** `model/mercado/identificar.py`: señales `nombre` (frases del registro, palabra
   completa) y `dominio` (correos y enlaces del sitio oficial o un subdominio); puntaje por
   señales y menciones; confianza; servicio con `canales.servicio_de`. Alias ambiguos en
   documentos (`AMBIGUAS_EN_DOCUMENTO`).
2. **Lectura** `model/mercado/lectura.py`: tipo por los primeros bytes; imagen → escala de grises,
   orientación EXIF, tamaño mínimo → Tesseract por `stdin`/`stdout` con los idiomas instalados;
   PDF → `pypdf` si está (opcional). Nada en disco.
3. **Controlador** `controller/mercado.py`: `identificar_por_pistas`, `identificar_documento`
   (devuelve solo datos del registro), `resolver_aseguradora` y `fragmentos_comparados`.
4. **Vista**: `mercado.identificar` (JSON-RPC, rechaza correos y números), `POST
   /aseguradoras/identificar` (multipart) y `sb mercado identificar --pistas | --archivo`.
5. **Agente**: `HerramientasMercado` inyectable, tres tools nuevas, prompt multiaseguradora,
   `aseguradora` en la salida, `TOOLS_CON_FUENTES` y el atributo `aseguradora` en el blindaje.
6. **Skill** `identificar-aseguradora` (uso: asistente).
7. **Imagen Docker** con `tesseract-ocr-spa`.
8. Pruebas `tests/test_identificar.py` (OCR real solo si hay Tesseract) y `make check`.

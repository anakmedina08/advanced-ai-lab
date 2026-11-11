# ADR-020 · Foto → seguro sugerido con YOLO (ejercicio de FastAPI)

- **Fecha:** 2026-11-11
- **What:** se integra el ejercicio del curso
  [`ejercicio_gestion_fastapi`](https://github.com/anakmedina08/ejercicio_gestion_fastapi). El
  cliente sube una foto, YOLO (`yolo26n.pt`, preentrenado en COCO) detecta objetos asegurables y el
  sistema sugiere el seguro de personas que aplica. Si se pide, el asistente lo explica citando la
  página oficial. Está disponible en:
  - `POST /fotos` (multipart, `?responder=true`),
  - la pestaña «📷 Foto → seguro» de Streamlit,
  - `sb foto RUTA` (en local o con `--api URL` a través del cliente `httpx`).
- **Why:**
  - Une los dos ejercicios del curso, visión y lenguaje (RAG), en un caso de uso del alcance
    PERSONAS (ADR-002): vehículo → SOAT y todo riesgo; bicicleta; perro o gato → mascotas; muebles
    y electrodomésticos → hogar; celular o portátil → Datecnologia.
  - Cada tema apunta a páginas que existen en la base pública.
  - Funciona con el modelo preentrenado, sin entrenar nada.
- **Qué se tomó del ejercicio:**
  - el modelo se carga una sola vez en el `lifespan` de FastAPI,
  - la inferencia corre en un *threadpool* y se serializa con un candado,
  - contratos Pydantic de la respuesta (cajas, clases y confianza),
  - cliente HTTP con `httpx`,
  - dibujo de cajas y etiquetas sobre la imagen.
- **Qué se cambió:**
  - Las rutas siguen el estilo en español de la API (`/fotos`).
  - Las dependencias son inyectables (`get_detector`, `get_foto_qa`) para probar sin modelo.
  - El modelo se «calienta» al cargarse: la primera inferencia de `torch` tardaba ~40 s y ahora
    cada foto toma ~0,2 s en CPU.
- **Privacidad y alcance:**
  - La foto se procesa en memoria y no se guarda.
  - Las personas detectadas no se reportan ni se dibujan (`VISION_IGNORED_CLASSES`).
  - No se aceptan documentos: tienen datos personales (Ley 1581) y YOLO detecta objetos, no lee texto.
  - Detectar *daños* (abolladuras, vidrios rotos) queda fuera de alcance: exigiría entrenar con un
    dataset propio.
- **Where:**
  - Modelo: `model/vision/deteccion.py` (detector, imagen y filtro) y `model/vision/seguros.py`
    (tabla objeto → tema).
  - Controlador: `controller/vision.py`.
  - Vista: `view/api.py` (`POST /fotos` y `lifespan`), `view/schemas.py` (`FotoOut`),
    `view/dependencias.py`, `view/api_client.py`, `view/anotaciones.py`, `view/cli.py` (`sb foto`)
    y `view/streamlit_app.py`.
  - Configuración: `YOLO_MODEL_PATH`, `YOLO_CONFIDENCE`, `MAX_IMAGE_BYTES`,
    `VISION_IGNORED_CLASSES` y `API_URL` en `config.py`.
  - Pruebas: `tests/test_vision.py`.
- **Dependencias:**
  - `ultralytics` (con `torch`, ~1 GB) es el extra opcional `vision`: `uv sync --extra vision`.
  - Sin el extra, el resto del proyecto, la CI y la imagen Docker funcionan igual, y `POST /fotos`
    responde 503 con la instrucción de instalación.
  - `python-multipart`, `httpx` y `pillow` son dependencias normales.
- **Learned:**
  - La primera inferencia de `torch` en CPU es muy lenta: hay que pagarla al arrancar, no en la
    primera petición de un usuario.
  - Las dataclasses con `slots` no tienen `__dict__`; para pasarlas a Pydantic se usa
    `dataclasses.asdict`.
  - `TestClient` de FastAPI es un `httpx.Client`, así que el cliente HTTP se prueba de punta a punta
    contra la app sin levantar un servidor.

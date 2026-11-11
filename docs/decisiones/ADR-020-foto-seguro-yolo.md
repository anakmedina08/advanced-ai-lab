# ADR-020 · Foto → «¿qué hago?»: YOLO local, Claude con visión y FastAPI

- **Fecha:** 2026-11-11
- **What:** se integra el ejercicio del curso
  [`ejercicio_gestion_fastapi`](https://github.com/anakmedina08/ejercicio_gestion_fastapi). El
  cliente sube una foto y recibe **qué hacer**, con la fuente oficial. El flujo tiene cuatro pasos:
  1. **YOLO (local)** detecta objetos y **difumina a las personas** antes de que la foto salga del equipo.
  2. **Claude con visión** entiende la situación con salida estructurada (Pydantic `Escena`):
     accidente de tránsito, daño en el hogar, robo, un bien que asegurar u otra cosa.
  3. **Plan:**
     - un siniestro lleva a los pasos, la cobertura y los canales,
     - un bien lleva a su seguro, y el **recomendador de Gestión** sugiere qué más contratan
       perfiles similares,
     - un documento se rechaza sin gastar LLM.
  4. **Asistente (RAG)** responde la pregunta del plan citando la página oficial.

  Está disponible en `POST /fotos?interpretar=true&responder=true`, en la pestaña
  «📷 Foto → ¿qué hago?» de Streamlit y en `sb foto RUTA --interpretar --responder` (también por
  HTTP con `--api URL`).
- **Why:**
  - Con solo YOLO, el resultado era una tabla obvia («hay un carro → seguro de carro»), porque
    YOLO solo conoce 80 objetos genéricos.
  - Un modelo multimodal entiende la **situación**, que es lo que la persona necesita resolver. En
    la prueba con una gotera en el techo, YOLO no detectó nada y Claude la clasificó como daño en la
    vivienda.
  - Se eligió Claude porque el proyecto ya usa su API y LangChain acepta imágenes.
  - DeepSeek, también en el proyecto, solo procesa texto.
  - Ollama con un modelo de visión es gratis y local, pero en CPU tarda minutos por foto.
- **Qué se tomó del ejercicio:**
  - el modelo se carga una sola vez en el `lifespan` de FastAPI,
  - la inferencia corre en un *threadpool* y se serializa con un candado,
  - `UploadFile` y contratos Pydantic de la respuesta,
  - cliente HTTP con `httpx` (`view/api_client.py`),
  - dibujo de cajas y etiquetas (`view/anotaciones.py`),
  - interfaz en Streamlit.
- **Privacidad (Ley 1581):**
  - La foto se procesa en memoria y no se guarda.
  - Las personas se difuminan **en local** con un umbral bajo (mejor de más que de menos) y nunca se
    reportan.
  - El prompt prohíbe identificar personas o transcribir placas, documentos o direcciones.
  - Si la foto es un documento, no se procesa.
  - YOLO (COCO) no detecta **placas**: la interfaz pide no enviarlas.
- **Decisiones del plan (`model/vision/seguros.py::planear`):**
  - La lectura de Claude manda sobre la de YOLO: un bus de transporte público es «otro», no un bien
    del cliente.
  - Excepción: si Claude ve con confianza **baja**, se usa YOLO. Pasa, por ejemplo, cuando una
    persona difuminada tapa casi toda la foto; YOLO vio la original en local.
- **Fuera de alcance:** avalúos, gravedad del daño o promesas de cobertura. Detectar daños
  específicos exigiría entrenar un modelo propio.
- **Where:**
  - Modelo: `model/vision/` (`deteccion.py`, `privacidad.py`, `escena.py` y `seguros.py`) y los
    prompts `ESCENA_SYSTEM` y `ESCENA_HUMAN` en `model/llm/prompts.py`.
  - Controlador: `controller/vision.py`.
  - Vista: `view/api.py` (`POST /fotos` y `lifespan`), `view/schemas.py` (`FotoOut`, `EscenaOut`,
    `PlanOut`), `view/dependencias.py`, `view/api_client.py`, `view/anotaciones.py`,
    `view/cli.py` y `view/streamlit_app.py`.
  - Pruebas: `tests/test_vision.py` y `tests/test_vision_flujo.py`.
- **Dependencias:**
  - `ultralytics` (con `torch`, ~1 GB) es el extra opcional `vision`: `uv sync --extra vision`.
  - Sin el extra, la CI y Docker funcionan y `/fotos` responde 503.
  - `python-multipart`, `httpx` y `pillow` son dependencias normales.
- **Learned:**
  - La primera inferencia de `torch` en CPU tardaba ~40 s; ahora se paga al cargar el modelo (~8 s)
    y cada foto toma ~0,2 s.
  - `with_structured_output(..., method="json_schema")` usa la salida estructurada nativa de la API
    y no depende de forzar herramientas, que algunos modelos nuevos de Claude rechazan.
  - Difuminar puede dejar la foto sin información: hay que diseñar qué hacer cuando el modelo no ve
    claro, en vez de debilitar la privacidad.
  - Pruebas reales con fotos de Wikimedia Commons:
    - choque: accidente, pasos y SOAT con fuente;
    - gotera: daño en la vivienda, seguro de hogar con fuente;
    - moto de primeros auxilios: «otro» (correcto);
    - niña con su perro: persona difuminada y seguro para mascotas gracias al respaldo de YOLO.

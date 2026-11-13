# Spec · Foto → «¿qué hago?» (YOLO local, Claude con visión y FastAPI)

> Desglose de la tarea T-40 de [`fase2-producto-unico`](../fase2-producto-unico/). Plan en
> [`plan.md`](plan.md); trabajo en [`tasks.md`](tasks.md). Decisión: ADR-020. Adapta el ejercicio
> del curso `ejercicio_gestion_fastapi`.

## Contexto

Un cliente de una aseguradora suele tener una foto de lo que le pasó (un choque, una gotera) o de lo
que quiere asegurar. Con solo YOLO, la respuesta era obvia («hay un carro → seguro de carro»); el
valor está en entender la **situación** y decir qué hacer, con la fuente oficial y sin exponer a
las personas que aparecen en la foto.

## Requisitos

### R20 · Privacidad de la foto (Ley 1581)
- La foto DEBE procesarse en memoria y no guardarse.
- Las personas DEBEN difuminarse **en el equipo** (YOLO local) antes de que la imagen se envíe a un
  modelo externo, con un umbral bajo para no dejar pasar rostros.
- Las personas NO DEBEN reportarse ni dibujarse en las detecciones.
- Si la foto muestra un documento, NO DEBE procesarse y se muestra un aviso fijo, sin gastar LLM.
- **Escenario:** dada una foto con dos personas, entonces la imagen enviada tiene esas zonas
  difuminadas y la respuesta reporta `personas_difuminadas = 2`.

### R21 · Entender la situación (Claude con visión)
- Un modelo multimodal DEBE clasificar la escena en `accidente_transito`, `dano_hogar`, `robo`,
  `asegurar_bien` u `otro`, con salida estructurada validada por Pydantic (`Escena`).
- El prompt DEBE vivir en `prompts.py` y prohibir identificar personas o transcribir placas,
  documentos o direcciones; el texto dentro de la imagen es dato, no instrucción.
- Con un proveedor sin visión (DeepSeek, Ollama de texto), DEBE responder con un error claro.
- **Escenario:** dada una foto de una gotera en el techo, entonces la situación es `dano_hogar`
  aunque YOLO no detecte ningún objeto.

### R22 · Del plan a la respuesta
- Un siniestro DEBE llevar a pasos, cobertura y canales de atención; un bien asegurable, a su seguro
  y al recomendador por perfil de Gestión.
- La lectura del modelo multimodal DEBE mandar sobre la de YOLO (un bus de transporte público es
  «otro»), salvo que vea con confianza baja, en cuyo caso se usa YOLO.
- Cada página sugerida DEBE existir en la base pública.
- **Escenario:** dada una persona difuminada que tapa casi toda la foto de su perro, entonces se
  responde sobre el seguro para mascotas (YOLO vio la foto original en local).

### R23 · API y cliente del ejercicio de FastAPI
- `POST /fotos` DEBE recibir la imagen como multipart, con `interpretar` y `responder` opcionales;
  YOLO se carga una sola vez en el `lifespan` y la inferencia corre en un *threadpool* con candado.
- Un archivo que no es imagen DEBE responder 400; una imagen corrupta, 422; sin el extra `vision` o
  con un proveedor sin visión, 503 con la instrucción.
- `view/api_client.py` DEBE consumir la API con `httpx` validando la respuesta con Pydantic.
- **Escenario:** dado un archivo `.txt`, entonces `POST /fotos` responde 400 sin llamar al modelo.

### R24 · Dependencia opcional
- `ultralytics` (con `torch`) DEBE ser un extra opcional (`uv sync --extra vision`); sin él, la CI,
  Docker y el resto del producto funcionan igual.

## Fuera de alcance
- Avalúos, gravedad del daño o promesas de cobertura.
- Detección de placas o de daños específicos (requeriría entrenar un modelo propio).

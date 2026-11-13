# Model Card · YOLO26-L en «Foto: ¿qué hago?»

> Modelo MaaS (*Model as a Service*) que sirve la API en `POST /fotos`. Registrado en MLflow como
> **`sb-yolo-difuminado@produccion`** (versión 1). Spec: [SPEC-037](../openspec/specs/037-model-card/).
> Evaluación: [SPEC-034](../openspec/specs/034-evaluacion-yolo/) · Registry: [SPEC-035](../openspec/specs/035-model-registry/).

## 1. Modelo base

| Campo | Valor |
|---|---|
| Nombre | YOLO26-L (`yolo26l.pt`), detección de objetos |
| Autor | Ultralytics |
| Repositorio y revisión | `ultralytics/assets@v8.4.0` (release de donde `ultralytics` 8.4 descarga los pesos) |
| sha256 de los pesos | `9fe3c544f2b19bebad7ea41e76d7ad3d88b7c2f10d11d24430c5311f6b32db26` (53,2 MB) |
| Arquitectura | detector de una etapa YOLO26 (backbone + cuello + cabeza sin NMS), tamaño L |
| Tarea | detección de 80 clases COCO: cajas, clase y confianza |
| Cómo se obtiene | la API lo descarga la primera vez en `data/modelos/` (no versionado). Ruta configurable con `YOLO_MODEL_PATH` |
| Uso en el sistema | 1) **difumina a las personas** antes de que la foto salga del equipo; 2) sugiere el tipo de seguro según los objetos (carro, moto, perro, casa…) |
| Umbral en producción | `YOLO_CONFIDENCE = 0,35` |
| Carga | una sola vez al arrancar la API (`lifespan`), con inferencia calentada y un candado |

## 2. Datos de origen

- **Entrenamiento (del proveedor):** COCO 2017, unas 118 000 imágenes con 80 clases de objetos
  comunes, en su mayoría de Flickr. Predominan escenas de Norteamérica y Europa.
- **Validación del equipo:** COCO128, las primeras 128 imágenes etiquetadas de COCO (929 objetos).
  Ultralytics lo descarga (~7 MB) fuera del repositorio.
- **Limitaciones de representatividad:** COCO tiene pocas escenas colombianas:
  - motos de reparto, buses urbanos locales y viviendas de ladrillo están subrepresentados;
  - no tiene clases para daños (abolladuras, humedades, vidrios rotos), que el sistema delega al
    modelo multimodal.

## 3. Métricas

Medidas por el equipo en CPU (MLflow, experimento `vision-yolo`; `make mlflow-yolo`):

| Configuración | Precisión | Recall | F1 | mAP50 | mAP50-95 | AP50 `person` | Latencia media | p95 | Throughput |
|---|---|---|---|---|---|---|---|---|---|
| yolo26l · umbral 0,25 | 0,796 | 0,730 | 0,762 | 0,707 | 0,566 | 0,744 | 383 ms | 465 ms | 2,6 img/s |
| **yolo26l · umbral 0,35 (API)** | **0,834** | 0,685 | 0,752 | 0,668 | 0,547 | 0,709 | 356 ms | 438 ms | 2,8 img/s |
| yolo26n · umbral 0,35 | 0,784 | 0,481 | 0,596 | 0,467 | 0,378 | 0,575 | 86 ms | 128 ms | 11,6 img/s |

Los valores de cada corrida están en la UI de MLflow:
`make mlflow-server` → http://127.0.0.1:5050.

Además, en la comparación con fotos reales (`docs/evaluacion-resultados.md` §4), yolo26l detectó a
las personas con una confianza media de 0,90 (mínima 0,81) en 335 ms.

**Por qué L con 0,35:**
- **Frente a N:** L detecta muchas más personas (AP50 de *person* 0,709 frente a 0,575). Una
  persona no detectada **no se difumina**, así que el modelo grande protege mejor la privacidad.
- **Frente al umbral 0,25:** 0,35 sube la precisión de las sugerencias (0,834 frente a 0,796) con
  una pérdida pequeña de recall.
- **Respaldo para personas:** se difuminan con un umbral aún más bajo, `VISION_BLUR_CONFIDENCE = 0,15`,
  como red de seguridad.

## 4. Limitaciones y sesgos

- **Falsos negativos de `person` (riesgo principal).** Personas pequeñas, de espaldas, en sombra o
  parcialmente tapadas pueden no detectarse y quedar sin difuminar. Mitigaciones:
  - umbral de difuminado bajo (0,15) y margen del 12 % alrededor de cada caja;
  - aviso al usuario para que no suba fotos con terceros;
  - la foto no se guarda.
- **Placas y documentos:** COCO no detecta placas ni documentos.
  - El modelo multimodal tiene prohibido transcribirlos.
  - Si ve un documento, el plan es «documento: no se procesa».
- **Sesgo geográfico y de dominio:** entrenado con fotos de otros países, puede confundir vehículos
  o viviendas locales; las sugerencias de seguro dependen de esas clases.
- **Sin clase de daño:** YOLO no sabe si un carro está chocado. La situación (siniestro o bien por
  asegurar) la decide el modelo multimodal, y con confianza baja el sistema vuelve a las
  sugerencias de YOLO.
- **Uso no previsto:**
  - identificar personas;
  - tasar daños o decidir una reclamación;
  - vigilancia.

  El sistema es un orientador académico, no un canal oficial.

## 5. Licencia y uso

- **Pesos y librería:** AGPL-3.0 (Ultralytics).
  - Es compatible con el uso académico de este repositorio, que es público y tiene licencia MIT
    para el código propio.
  - Un uso comercial cerrado requeriría la licencia Enterprise de Ultralytics.
- **Dataset COCO:** anotaciones CC BY 4.0; las imágenes conservan las licencias de Flickr.
- **Atribución:** «YOLO26 por Ultralytics (https://github.com/ultralytics/ultralytics)».

## 6. Trazabilidad

| Dónde | Qué comprobar |
|---|---|
| `GET /health` → `modelo_yolo_sha256` | `9fe3c544f2b19beb`, igual al tag `sha256` de la versión del Registry |
| MLflow → Models → `sb-yolo-difuminado` | versión 1, alias `produccion`, tags `repo_rev`, `licencia`, `umbral_confianza`, `corrida_evaluacion` |
| MLflow → `vision-yolo` | las 3 corridas comparables con parámetros, métricas, artefactos y tags |

# ADR-022 · MLflow como bitácora de experimentos

- **Fecha:** 2026-11-13
- **What:** cada experimento del proyecto se registra en MLflow con sus parámetros (qué se probó),
  métricas (cómo salió), artefactos (archivos) y el commit de git. Hay tres experimentos:
  - `asistente-qa`: proveedor, modelo, modo de contexto y versión del prompt → palabras clave, cita
    de la fuente, rechazo correcto y latencia, con el CSV de respuestas.
  - `recomendador`: líneas base de Gestión (popularidad y segmento) → Recall@5 y NDCG@5. Aquí se
    registrará el LightGBM de T-23.
  - `recuperacion`: BM25, híbrido Chroma, Qdrant denso y búsqueda por palabras → hit@k.

  Se registra solo al correr `sb eval`, `sb reco baseline` y `scripts/comparar_recuperacion.py`.
  `sb mlflow importar` carga las evaluaciones ya guardadas sin volver a llamar al LLM y no duplica
  (cada CSV lleva su huella). `sb mlflow ui` abre la interfaz en `http://127.0.0.1:5000`.
- **Why:** la tarea T-24 y la historia «Ranking LightGBM con trazabilidad en MLflow» del backlog de
  Gestión piden trazabilidad. Antes, los resultados quedaban en CSV sueltos, en la terminal y en el
  informe, y no había forma directa de saber qué configuración y qué versión del código produjo cada
  número.
- **Decisiones de diseño:**
  - **Local y sin servidor:** SQLite en `data/mlflow.db` y artefactos en `data/mlflow-artefactos/`,
    que no se versionan, como el resto de `data/`.
  - **Extra opcional** (`uv sync --extra mlflow`). Sin él, o con `SB_MLFLOW=0`, se usa una bitácora
    nula: la CI, Docker y las pruebas no escriben nada.
  - **MLflow no se usa para trazas del LLM:** eso ya lo hace LangSmith (ADR-017). MLflow se queda con
    lo que hace mejor: comparar experimentos.
  - **Corrida independiente de MLflow:** la `Corrida` (`model/experimentos.py`) no depende de MLflow,
    y `Bitacora` es un protocolo, así que las pruebas usan un doble.
- **Where:**
  - Modelo: `model/experimentos.py`.
  - Controlador: `controller/experimentos.py`.
  - Vista: `view/cli.py` (`sb mlflow importar|ui` y el registro en `eval` y `reco baseline`).
  - Script: `scripts/comparar_recuperacion.py`.
  - Configuración: `MLFLOW_*` y `EXPERIMENTO_*` en `config.py`.
  - Pruebas: `tests/test_experimentos.py`.
- **Learned:**
  - MLflow rechaza la «@» en los nombres de métricas: `recall@5` se registra como `recall_at_5`.
  - Con SQLite hay que fijar `artifact_location` por experimento; si no, los artefactos se guardan
    relativos a la carpeta desde donde se corre el comando.
  - `data/` se ignoraba carpeta por carpeta, así que la base de MLflow se habría versionado. Se
    agregó al `.gitignore` junto con `data/modelos/`.
  - Primeras corridas reales: 7 evaluaciones con Claude, 4 métodos de recuperación y 2 líneas base.
    La de segmento da Recall@5 = 0,639, el mismo valor documentado por el equipo.

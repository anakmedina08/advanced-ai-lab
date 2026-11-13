# Spec · Bitácora de experimentos con MLflow

> Tarea T-24 de [`fase2-producto-unico`](../fase2-producto-unico/) e historia «Ranking LightGBM con
> trazabilidad en MLflow» del backlog de Gestión. Plan en [`plan.md`](plan.md); trabajo en
> [`tasks.md`](tasks.md). Decisión: ADR-022.

## Contexto

Los resultados de los experimentos (versiones del prompt, modos de contexto, recuperación, líneas
base del recomendador) quedaban en CSV sueltos y en la terminal. No había forma directa de saber qué
configuración y qué versión del código produjo cada número del informe.

## Requisitos

### R29 · Trazabilidad de cada corrida
- `sb eval`, `sb reco baseline` y `scripts/comparar_recuperacion.py` DEBEN registrar cada corrida
  con sus parámetros, métricas, artefactos y el commit de git.
- Los nombres de métricas no válidos para MLflow DEBEN convertirse (`recall@5` → `recall_at_5`).
- **Escenario:** dada `sb eval --modo rag --limit 2`, entonces queda una corrida en `asistente-qa`
  con `modo = rag` y el CSV de respuestas como artefacto.

### R30 · Importar sin volver a llamar al LLM
- `sb mlflow importar` DEBE cargar los `resultados_*.csv` completos (no las muestras) sin llamar al
  LLM, y NO DEBE duplicar si se ejecuta dos veces.
- **Escenario:** dado un CSV ya importado, cuando se importa de nuevo, entonces su estado es «ya estaba».

### R31 · Opcional y local
- MLflow DEBE ser un extra opcional; sin él o con `SB_MLFLOW=0`, todo funciona y no se registra nada.
- La bitácora DEBE vivir en `data/` y NO DEBE versionarse; las pruebas NO DEBEN escribir en la real.
- **Escenario:** sin el extra, `sb mlflow importar` responde con la instrucción de instalación.

## Fuera de alcance
- Trazas del LLM (LangSmith, ADR-017), registro de modelos y despliegue desde MLflow.

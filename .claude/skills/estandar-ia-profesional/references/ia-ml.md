# 7 · IA/ML responsable

## M1-M2 · Model card y data card
- **Model card:**
  - uso previsto y fuera de alcance;
  - datos de entrenamiento o evaluación;
  - métricas por segmento;
  - limitaciones, sesgos conocidos, licencia y versión.
- **Data card** (`assets/plantillas/data-card.md`):
  - origen y licencia de los datos;
  - método de recolección (scraping respetando robots.txt);
  - PII y su tratamiento;
  - frecuencia de actualización;
  - particiones;
  - quién puede acceder.

## M3 · Golden set
Banco versionado (`evaluacion/banco.csv`) con pregunta, respuesta esperada o criterios, fuente,
categoría y dificultad. Incluye casos adversariales:
- prompt injection;
- preguntas fuera de dominio;
- datos personales.

## M4 · Experimentos
MLflow:
- un experimento por línea de trabajo;
- parámetros, métricas y artefactos;
- tag con el SHA de git;
- `mlflow.autolog()` cuando aplique.

## M5 · Puerta de evals en CI (la más importante)
`assets/plantillas/workflows/evals.yml`:
- corre en PRs que tocan `src/**/prompts*`, `src/**/rag/**`, `src/**/agente*` o `evaluacion/**`;
- ejecuta el banco con un modelo barato y semilla fija;
- **falla si la métrica cae más de X puntos** respecto a la línea base de `evaluacion/linea_base.json`.

La llave del LLM se guarda como secreto del repo y el job usa `environment: evals` para exigir
aprobación cuando cuesta dinero.

Métricas sugeridas:
- **RAG:** hit@k, faithfulness y answer relevancy (ragas / deepeval).
- **Clasificación:** F1 por clase.
- **Visión:** mAP@50.

## M6 · Prompts como código
- Los prompts viven en un módulo (`prompts.py`) o en archivos versionados, con nombre y versión (`v1`..`vN`).
- Nunca se arman inline en el controlador.
- Un cambio de prompt es un PR que pasa por M5.

## M7 · Observabilidad
- LangSmith, Langfuse u OpenTelemetry, con un proyecto por entorno.
- Se registran latencia, tokens, costo, herramientas usadas y errores.
- No se envía PII a las trazas: se enmascara antes.

## M8 · Privacidad (Colombia: Ley 1581 de 2012)
- Solo datos públicos, salvo autorización expresa.
- Minimización: no se guarda lo que no se necesita.
- Memoria del agente con opción de olvido (endpoint `/olvidar`).
- Aviso al usuario de que habla con una IA y de que no es asesoría oficial.

## M9 · Sesgo
- Métricas por segmento (canal, producto, tipo de cliente) en la model card.
- Para recomendadores: cobertura y popularidad por segmento.

## M10 · Registro de modelos
MLflow Model Registry con alias (`@produccion`, `@candidato`). La API carga el modelo por
alias, no por ruta; la promoción es un cambio de alias registrado y reversible.

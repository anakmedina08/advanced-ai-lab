# Plan · SPEC-044 · Guías y panel del equipo en React: pipeline, evaluación y experimentos

## Diseño
Endpoints finos sobre los controladores existentes (`pipeline`, `assistant`, `experimentos`); páginas React con barras en CSS (sin librerías de gráficos).

## Decisiones
- Barras con CSS: suficiente para comparar 3 métricas y sin peso extra.

## Contrato
`CorpusOut`, `EvaluacionOut`, `DetalleEvaluacionOut`, `ExperimentosOut`.

## Riesgos
- Corridas de MLflow con muchos campos: se muestran solo parámetros y métricas clave.

## Alternativas descartadas
- Incrustar Streamlit en un iframe: seguiría siendo Streamlit.

## Estrategia de pruebas
Pytest de los endpoints y Vitest de las páginas con `fetch` falso. Pruebas AAA sin red ni API de pago.

# Plan · SPEC-034 · Evaluación de YOLO en MLflow: 3 corridas comparables

## Diseño
Ultralytics `model.val(data="coco128.yaml")` para calidad + bucle de inferencia cronometrado para latencia; registro con la `Bitacora`.

## Decisiones
- COCO128: etiquetado, pequeño (CPU) y del mismo dominio del modelo.
- p95 medido imagen por imagen, no del promedio.

## Contrato
Experimento `vision-yolo`.

## Riesgos
- Descarga de COCO128 (7 MB) la primera vez.

## Alternativas descartadas
- Fotos propias sin etiquetas: no permiten precisión ni recall.

## Estrategia de pruebas
Pruebas de las funciones de métricas (p95, F1) sin red. Pruebas AAA sin red ni API de pago.

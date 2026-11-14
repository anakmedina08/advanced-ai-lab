# Plan · SPEC-036 · Evaluación del retrieval con recall@10 y nDCG@10

## Diseño
Funciones puras de métricas + adaptador del híbrido en el script.

## Decisiones
- nDCG premia encontrar la fuente arriba; recall@10, que esté entre los 10.

## Contrato
Experimento `recuperacion`.

## Riesgos
- Etiquetas por URL: varias páginas pueden ser válidas.

## Alternativas descartadas
- Solo hit@k: no pondera la posición.

## Estrategia de pruebas
Pruebas de las métricas con casos calculados a mano. Pruebas AAA sin red ni API de pago.

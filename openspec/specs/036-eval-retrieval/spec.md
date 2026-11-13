# SPEC-036 · Evaluación del retrieval con recall@10 y nDCG@10

> Curso: Técnicas M2 (4.2) · Story points: **3** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
Se midió hit@k, pero la rúbrica pide recall@10 o nDCG@10 con 20–30 consultas etiquetadas y comparar el híbrido sobre Qdrant que ahora usa el agente.

## Historia
**Como** jurado de Técnicas, **quiero** ver recall@10 y nDCG@10 de BM25, Qdrant denso y el híbrido BM25 + Qdrant, **para** justificar la elección del retrieval del agente.

## Requisitos
- **R036.1** `model/rag/evaluacion.py` DEBE calcular recall@k y nDCG@k a partir de URLs relevantes por consulta.
- **R036.2** El banco DEBE tener entre 20 y 30 consultas etiquetadas (`evaluacion/preguntas.yaml`).
- **R036.3** `scripts/comparar_recuperacion.py` DEBE incluir el híbrido sobre Qdrant y registrar recall@10 y nDCG@10 en MLflow.
- **R036.4** `docs/evaluacion-resultados.md` DEBE documentar la tabla y la decisión.

## Criterios de aceptación
- **AC1** · **Dado** una consulta con su URL relevante en la posición 2, **cuando** se calcula nDCG@10, **entonces** vale 1/log2(3).

## Fuera de alcance
Ragas.

## Métricas de éxito
Tabla con los 3 métodos en el documento y en MLflow.

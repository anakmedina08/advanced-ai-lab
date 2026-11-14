# SPEC-013 · RAG híbrido del agente sobre Qdrant con filtro por payload

> Curso: Técnicas M2 (2.2) · Story points: **5** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
El agente busca en Chroma; el módulo pide Qdrant con índice ANN, filtros por payload y cita de la fuente.

## Historia
**Como** usuaria del asistente, **quiero** que el agente recupere los fragmentos de Qdrant (HNSW) combinados con BM25 y filtrados por sección, **para** recibir respuestas citadas con el mismo índice que se evalúa con hit@k.

## Requisitos
- **R013.1** `model/rag/qdrant.py` DEBE adaptar el índice Qdrant al protocolo `BuscadorVectorial` (`similarity_search(query, k, filter)`).
- **R013.2** El filtro `{'section': s}` DEBE traducirse a un filtro de payload de Qdrant (`metadata.section`).
- **R013.3** `recuperador_por_defecto` DEBE preferir Qdrant, luego Chroma, luego solo BM25, e informar cuál usa.
- **R013.4** Cada fragmento devuelto DEBE conservar URL y `chunk_id` para la cita.

## Criterios de aceptación
- **AC1** · **Dado** un índice Qdrant en memoria con 3 fragmentos, **cuando** se busca con sección `movilidad`, **entonces** solo vuelven fragmentos de esa sección.
- **AC2** · **Dado** sin índice Qdrant, **cuando** se arma el recuperador, **entonces** el modo informado es Chroma o BM25.

## Fuera de alcance
Vectores dispersos de Qdrant (BM25 queda en memoria).

## Métricas de éxito
hit@10 del híbrido sobre Qdrant ≥ al de BM25 solo (se registra en MLflow).

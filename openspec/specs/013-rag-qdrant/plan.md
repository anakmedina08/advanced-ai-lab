# Plan · SPEC-013 · RAG híbrido del agente sobre Qdrant con filtro por payload

## Diseño
Adaptador sobre `QdrantVectorStore` + `models.Filter`; reusa `vector_store.open_client` (caché por proceso).

## Decisiones
- RRF con BM25 en memoria: no requiere índice disperso ni reindexar.
- Qdrant local en disco: HNSW por defecto (ANN).

## Contrato
`BuscadorQdrant.similarity_search(query, k, filter) → list[Document]`

## Riesgos
- Qdrant necesita Ollama para el embedding de la consulta: sin Ollama cae a BM25 y lo informa.

## Alternativas descartadas
- Mantener Chroma: duplicaría índices y no cumple la rúbrica.

## Estrategia de pruebas
`tests/test_rag_qdrant_agente.py` con `QdrantClient(':memory:')` y embeddings falsos. Pruebas AAA sin red ni API de pago.

# ADR-016 · RAG con Chroma y recuperación híbrida (BM25 + vectores)

- **Fecha:** 2026-11-07
- **What:** la base vectorial es Chroma persistente en `data/vector/` (no versionado) con los fragmentos Gold más el bloque de canales del pie de página. Embeddings configurables: `nomic-embed-text` en Ollama (por defecto, igual al ejercicio de clase), Voyage AI (`voyage-multilingual-2`) o falsos para pruebas. La búsqueda combina BM25 y similitud vectorial con Reciprocal Rank Fusion. `sb rag indexar|buscar|evaluar`.
- **Why:** BM25 encuentra datos literales («#322», «PQRSF») y los vectores encuentran paráfrasis; juntos son más robustos que cada uno. Anthropic no ofrece embeddings y recomienda Voyage; Ollama evita costos y no envía datos fuera.
- **Where:** `model/rag/{embeddings,indice,hibrido,fuentes,evaluacion}.py`, `tests/test_rag.py`.
- **Learned:** medido con el banco real (hit@k estricto: todas las palabras clave en los k fragmentos): BM25 solo pasó de 10/21 a 13/21 (hit@3) y de 15/21 a 16/21 (hit@6) al agregar el fragmento de canales y quitar «bolivar» y «numero» de BM25; quitar también «seguro(s)» empeoró (14/21). El índice guarda proveedor y modelo y se niega a consultar con otros embeddings. Pendiente: medir el híbrido con `nomic-embed-text` (`sb rag evaluar`).

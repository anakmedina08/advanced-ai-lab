# Plan · SPEC-084

1. **Modelo** `model/rag/proyeccion.py` (solo NumPy y scikit-learn):
   - `normalizar(vectores)`: vectores unitarios, para que el producto punto sea el coseno.
   - `vecinos(consulta, vectores, k)`: índices de los k más parecidos por coseno.
   - `proyectar(vectores, metodo="tsne", semilla=42)`: t-SNE (métrica coseno, perplejidad acotada al
     número de puntos) o PCA.
   - `separacion(vectores, etiquetas)`: *silhouette* por coseno; `None` si hay menos de 2 grupos.
2. **Script** `scripts/proyectar_embeddings.py`: lee la colección `chunks_seguros_bolivar*` de
   `data/gold/qdrant`, embebe las preguntas con `build_embeddings()` (el mismo proveedor del índice),
   marca acierto/fallo con `es_relevante` (la misma regla de SPEC-036), proyecta fragmentos y preguntas
   juntos, dibuja con matplotlib y registra en MLflow con `Bitacora`.
3. **Dependencia** `scikit-learn` declarada en `pyproject.toml` (hoy llega solo como transitiva).

## Decisiones
- **t-SNE y no UMAP:** scikit-learn ya está en el entorno; UMAP sumaría `umap-learn` y `numba`.
- **Proyectar preguntas y fragmentos juntos:** t-SNE no proyecta puntos nuevos, así que las preguntas
  entran al mismo ajuste.
- **Silhouette en el espacio original:** la proyección 2D deforma distancias; la métrica se calcula
  sobre los 768 dimensiones y el mapa solo ilustra.

## Riesgos
- t-SNE es estocástico: semilla fija para que el mapa sea reproducible.

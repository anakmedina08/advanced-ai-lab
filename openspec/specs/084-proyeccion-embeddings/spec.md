# SPEC-084 · Proyección 2D (t-SNE) de los embeddings para diagnosticar el retrieval

> Curso: Técnicas Avanzadas de IA (551462) · Story points: **3** · Responsable: Katherine Medina ·
> Rúbrica del anuncio 007: ítem **2.3** (4 %) y bonus de excelencia científica (hasta +10 %).
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
El ítem 2.3 pide recall@10/nDCG@10 (ya están, SPEC-036) **y** una proyección t-SNE o UMAP de los
embeddings que se use para diagnosticar clústeres o fallos. El proyecto no tiene ninguna proyección,
así que hoy no se puede ver si las secciones del corpus forman grupos ni por qué fallan algunas
preguntas del banco de evaluación.

## Historia
**Como** equipo que defiende el RAG, **quiero** ver en un mapa 2D dónde caen los fragmentos del corpus y
las preguntas de evaluación **para** explicar con evidencia qué recupera bien la búsqueda densa y
dónde se confunde.

## Requisitos
- **R084.1** La lógica (proyección, vecinos por coseno y métricas) DEBE vivir en
  `model/rag/proyeccion.py`, sin red ni modelo, y probarse con datos sintéticos.
- **R084.2** `scripts/proyectar_embeddings.py` DEBE leer los vectores del índice Qdrant local, embeber
  las preguntas del banco con el mismo proveedor del índice y proyectar todo junto con t-SNE
  (semilla fija) o PCA.
- **R084.3** El mapa DEBE colorear los fragmentos por sección y marcar cada pregunta como acierto o
  fallo de la búsqueda densa (top-10 por coseno con un fragmento relevante según sus palabras clave).
- **R084.4** DEBE reportar: puntos, proporción de la sección más grande, *silhouette* por sección en
  el espacio original (coseno) y hit@10 denso.
- **R084.5** El PNG y el resumen DEBEN guardarse en `docs/figuras/` y, si MLflow está disponible,
  registrarse como corrida del experimento `recuperacion`.

## Criterios de aceptación
- **AC1** · **Dado** dos grupos de vectores separados, **cuando** se proyectan, **entonces** la
  *silhouette* es alta y cada grupo queda junto en 2D.
- **AC2** · **Dado** una consulta igual a un vector del corpus, **cuando** se buscan sus vecinos,
  **entonces** ese vector sale primero.
- **AC3** · **Dado** el índice local, **cuando** se corre el script, **entonces** se genera
  `docs/figuras/tsne-embeddings.png` con fragmentos y preguntas.

## Fuera de alcance
- UMAP (t-SNE cubre el ítem y evita otra dependencia pesada).
- Cambiar el retriever: esta spec diagnostica, no corrige.

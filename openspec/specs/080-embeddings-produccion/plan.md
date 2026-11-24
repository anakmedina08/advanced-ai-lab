# Plan · SPEC-080

1. **Repo.** `Dockerfile`: añadir `--extra voyage` a los dos `uv sync` del builder. Actualizar
   `deploy/app.env.example` a `EMBEDDINGS_PROVIDER=voyage` con `VOYAGE_API_KEY=`/`VOYAGE_MODEL=`.
2. **CI/servidor.** En GitLab, `ENV_PRODUCCION` (File protegida) pasa a `voyage` y agrega la
   `VOYAGE_API_KEY` real. Redesplegar la imagen (el job `deploy` ya la publica).
3. **Reindexar.** En el Droplet (dentro del contenedor `api`, que monta `data/`):
   `uv run sb rag indexar --embeddings voyage --reset`.
4. **Verificar.** `uv run sb rag buscar "¿Qué cubre el SOAT?"` y una consulta RAG por la API con
   fuentes y sin «Error interno».

## Orden de dependencias
El paso 3 depende del 2 (la imagen ya trae `langchain-voyageai` y el `.env` apunta a `voyage`). El
paso 4 cierra el AC. Ningún paso toca secretos en el repo.

# SPEC-080 · Embeddings Voyage en producción y reindexado

> Curso: Técnicas Avanzadas de IA (551462) · Story points: **5** · Responsable: Daniel Silva ·
> Anuncio: [551462 · 007](../../../docs/anuncios/551462-anuncio-007.md) (ítem 2.2, 6 %; y arregla la
> prioridad 1 del handoff). No confundir con [SPEC-069](../069-mercado-aseguradoras/spec.md), que es
> el corpus de mercado.

## Problema
En el Droplet el `ENV_PRODUCCION` trae `EMBEDDINGS_PROVIDER=fake` (no hay Ollama en el servidor).
El índice de `data/vector/` se construyó con otra dimensionalidad, así que la búsqueda vectorial
falla por desajuste de dimensiones y el modo RAG devuelve «Error interno del servidor». Además, la
rúbrica prohíbe Ollama como motor en producción: los embeddings deben salir de un servicio en la
nube. La fábrica `build_embeddings` **ya soporta `voyage`** (ADR-018); falta activarlo y reindexar.

## Requisitos
- **R080.1** La imagen de producción DEBE incluir el extra `voyage` (`langchain-voyageai`), hoy
  ausente del `Dockerfile`.
- **R080.2** La plantilla de producción DEBE declarar `EMBEDDINGS_PROVIDER=voyage` (y las variables
  `VOYAGE_API_KEY`/`VOYAGE_MODEL` vacías), sin valores reales.
- **R080.3** El índice de `data/vector/` DEBE reconstruirse con embeddings `voyage` para que las
  dimensiones coincidan con las de consulta.
- **R080.4** El modo RAG en producción DEBE responder con pasajes y su cita (sin error interno).

## Criterios de aceptación
- **AC1** · La imagen construye con `uv sync --extra voyage` y `langchain_voyageai` importa.
- **AC2** · En el Droplet, `uv run sb rag indexar --embeddings voyage` termina y deja el índice con
  la dimensión del modelo `voyage-multilingual-2`.
- **AC3** · `uv run sb rag buscar "¿Qué cubre el SOAT?"` devuelve fragmentos con URL.
- **AC4** · `/preguntas` con `modo=rag` (o el chat) responde con fuentes, sin «Error interno».

## Repo vs servidor
| Va al repo (versionado, sin secretos) | Va solo al servidor / CI (nunca al repo) |
|---|---|
| `Dockerfile`: `--extra voyage` | `ENV_PRODUCCION` (var CI File): `EMBEDDINGS_PROVIDER=voyage` + `VOYAGE_API_KEY` |
| `deploy/app.env.example`: plantilla `voyage` | Reindexar: `uv run sb rag indexar --embeddings voyage` |
| SPEC-080 (spec/plan/tasks) | Redesplegar la imagen y reiniciar `api` |

## Riesgos
| Riesgo | Mitigación |
|---|---|
| No hay `VOYAGE_API_KEY` todavía | Pedirla al equipo antes de redesplegar; sin ella, dejar `fake` no arregla nada |
| El reindexado tarda o cuesta | Corpus pequeño (~500 chunks), costo de Voyage despreciable |
| El índice viejo queda con otra dimensión | `--reset` al reindexar |

## Fuera de alcance
Mover `langchain-ollama` a un extra opcional (limpieza del ⛔ de la rúbrica; se decide aparte) y el
t-SNE/UMAP del corpus (SPEC siguiente).

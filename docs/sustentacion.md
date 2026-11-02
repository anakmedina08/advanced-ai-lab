# Guion de sustentación · Módulo 1 (15 min)

| Min | Quién | Qué se muestra |
|---|---|---|
| 0:00 – 1:30 | Katherine | **Contexto:** Seguros Bolívar, problema de información dispersa y alcance (personas + canales, solo información pública). |
| 1:30 – 6:30 | Katherine | **UI en acción** (`make app`): pestaña Pipeline (5 etapas y métricas), botón **Reprocesar**, tabla del corpus con metadatos, Q&A «¿Cuál es el WhatsApp de atención?» y «¿Puedo comprar el SOAT en línea?» con **Fuentes citadas**. |
| 6:30 – 8:30 | Daniel | **Repositorio:** público, PRs con descripción y aprobación del Code Reviewer, Conventional Commits, `.gitignore`, README, LICENSE y `CONSTITUTION.md`. |
| 8:30 – 10:30 | Daniel | **Pipeline en terminal:** `make process` (o `uv run python scripts/scrape_empresa.py --solo-proceso`), luego `data/gold/pages/*.md` (frontmatter) y `data/gold/corpus.jsonl`. |
| 10:30 – 12:00 | Los dos | **IDE:** estructura MVC; Daniel explica `config.py` y `select_urls`; Katherine explica la deduplicación antes del boilerplate en `controller/pipeline.py`; `git show --stat HEAD~1` como diff. |
| 12:00 – 15:00 | Cada uno | **Preguntas:** Daniel (scraping, ética, robots.txt, Medallion); Katherine (limpieza, contexto reducido, citas, pruebas). |

## Antes de entrar

```bash
git pull
make dev
make process
make app
```

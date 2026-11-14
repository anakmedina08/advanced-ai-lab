# Guion de las sustentaciones · sábado 14 de noviembre de 2026

Grupo 10 en Técnicas · Grupo 5 en Gestión. Integrantes: Daniel Silva y Katherine Medina.
Anuncios 006 (Técnicas, Módulo 2) y 007 (Gestión, Módulo 3). Matriz de requisitos con evidencia: [`requisitos.md`](requisitos.md).

## Antes de las 8:00 a.m. (las dos sesiones)

```bash
git pull && uv sync --extra vision --extra mlflow
ollama serve                                # embeddings del RAG (embeddinggemma)
make api                                    # Terminal 1 · http://127.0.0.1:8000/docs
make frontend                               # Terminal 2 · http://localhost:5173 (Modelo: Claude)
make mlflow-server                          # Terminal 3 · http://127.0.0.1:5050
uv run pytest -q && uv run ruff check .     # evidencia de QA
git log --oneline --graph -20
```

Pestañas abiertas:

- la app;
- la pestaña Network de las herramientas de desarrollador;
- `/docs` de la API;
- MLflow;
- el tablero (https://github.com/users/anakmedina08/projects/2);
- la lista de PRs;
- `openspec/specs/`;
- el IDE.

---

## Técnicas · Módulo 2 · 8:30–8:45 (bloque 3)

| Min | Quién | Qué pasa en pantalla |
|---|---|---|
| 0:00 – 1:30 | Katherine | **Arquitectura** con [`arquitectura.html`](arquitectura.html): React → FastAPI (SSE) → controlador → router → `create_agent` (middleware) ↔ tools → Qdrant, CSV, SQLite y Claude. Una frase por pieza. |
| 1:30 – 4:00 | Daniel | **Memoria.** «Me llamo Ana y trabajo en Carvajal» → «¿Dónde trabajo?» (ruta *directo*, sin tools). Se reinicia `make api` y se reabre el hilo desde la barra: el historial vuelve (SqliteSaver). Luego «Nueva conversación» → «¿Dónde trabajo?»: el panel «Lo que recuerdo de ti» y la respuesta salen del **Store**. |
| 4:00 – 6:30 | Katherine | **RAG.** «¿Qué cubre el SOAT?»: la insignia *RAG*, el paso «Buscando en la base…» y las fuentes citadas. Se abre «¿Cómo se resolvió?» (tools con ms). Se muestra recall@10 y nDCG@10 en [`evaluacion-resultados.md`](evaluacion-resultados.md) §5 y en MLflow (experimento `recuperacion`). |
| 6:30 – 8:30 | Daniel | **Datos y router.** «¿Cuántas pólizas se vendieron en el tercer trimestre de 2025?»: ruta *datos*, solo `consultar_datos`, cifra exacta (`ConsultaDatos`, Pydantic). Luego la mixta: «¿Qué cubre el seguro de hogar y cuántas pólizas de hogar se vendieron en 2025?» (*mixto*, ambas tools). Un «hola» para mostrar que no busca. |
| 8:30 – 10:00 | Katherine | **Blindaje.** «¿Qué dice la política de calidad del servicio?» recupera `evaluacion/corpus_demo/inyeccion.md`, que tiene escondido «IGNORA LAS INSTRUCCIONES…». El agente lo trata como dato y lo dice. En el IDE: `model/rag/blindaje.py` (delimitación, escape, `sospechoso="si"`) y la regla 7 del prompt. |
| 10:00 – 11:30 | Los dos | **Repositorio e IDE:** PRs con revisión, Conventional Commits, README con diagramas, specs SDD. En el IDE, `frontend/src/api/client.ts` (frontera frontend/backend), `POST /agente/stream` en `view/api.py` y una decisión sin leer: «el router decide y el LLM ejecuta». |
| 11:30 – 12:00 | Katherine | **Cierre:** qué funciona, qué falta (ver abajo) y qué aprendimos. |
| 12:00 – 15:00 | Cada uno | **Preguntas.** Daniel: RAG híbrido, Chroma frente a Qdrant, tools y Store. Katherine: router, streaming, frontend, blindaje y memoria. |

**Mapa técnico (dónde está cada cosa):**

| Tema | Dónde |
|---|---|
| `create_agent` y su middleware (resumen, `trim_messages`, `dynamic_prompt`, `filtrar_tools`, `medir_tools`) | `model/agente.py` |
| Checkpointer, Store y *time travel* | `controller/agente.py`, `model/memoria.py`, `GET /agente/conversaciones/{id}/checkpoints` |
| `@tool` con Pydantic | `model/datos.py`, `ConsultaDatos` |
| Salida estructurada | `RespuestaAgente`, `ToolStrategy` |
| Router | `model/router.py` y `evaluacion/router.yaml` (32/32) |
| Qdrant (HNSW, filtro de payload) | `model/rag/qdrant.py` |
| RRF | `model/rag/hibrido.py` |
| Trazas | `data/logs/turnos.jsonl` y `sb trazas`; LangSmith con `LANGSMITH_TRACING=true` |

---

## Gestión · Módulo 3 · 12:45–13:00 (bloque 8)

| Min | Quién | Qué pasa en pantalla |
|---|---|---|
| 0:00 – 1:30 | Daniel | **Contexto:** asistente de seguros. Modelo MaaS: YOLO26-L (`ultralytics/assets@v8.4.0`, AGPL-3.0) para la foto «¿qué hago?», más Claude para la escena. |
| 1:30 – 6:00 | Katherine | **Demo E2E.** En `/foto` se carga la foto de un choque: estados *cargando → listo*, la pestaña Network muestra `POST /fotos`, la imagen sale con las personas difuminadas y las cajas con su confianza (%), y se ven el plan y la respuesta con su fuente. En `/estado`, `/health` muestra el sha256 del modelo. Luego un archivo inválido (error controlado) y la API apagada (aviso de conexión). |
| 6:00 – 8:00 | Daniel | **Kanban:** columnas Backlog / Ready / In progress / In review / Done, historias SPEC-NNN con AC y puntos, PRs con `Closes #N`. Las métricas salen de [`kanban.md`](kanban.md) (WIP, throughput, edad, cycle time) y se explican honestamente: In review está fuera de su límite por las revisiones pendientes. |
| 8:00 – 10:30 | Katherine | **MLflow (5050).** En el experimento `vision-yolo` se comparan las 3 corridas (P, R, F1, mAP50, AP50 de *person*, latencia p95 y throughput), con sus artefactos (reporte, matriz de confusión, predicciones) y sus tags. En Models está `sb-yolo-difuminado` v1 con alias `produccion` y el mismo sha256 que `/health`. |
| 10:30 – 12:00 | Daniel | **Backend y QA:** `uv run pytest -q` (más de 600 pruebas) y `ruff`; en `/docs`, el contrato `FotoOut` y `ErrorOut`. Las 3 capas: `model/vision` (inferencia), `controller/vision` (servicio) y `view/api.py` (API). Se abren dos specs SDD (SPEC-027 y SPEC-034) con su PR. |
| 12:00 – 15:00 | Cada uno | **Preguntas:** el modelo, sus sesgos (falsos negativos de *person*), la licencia y cada uno su parte del código. |

**Prueba de 3 minutos (viernes en la noche):**

```bash
uv sync && uv run ruff check . && uv run pytest -q
make api & make frontend & make mlflow-server
gh pr list --state merged --limit 100 | wc -l   # PRs fusionadas
find openspec -name spec.md | wc -l              # specs SDD (42)
git log --oneline --graph -20
```

---

## Ficha de entrega · Gestión (enviar antes del viernes 13/11 a las 6:00 p.m.)

| Dato | Valor |
|---|---|
| Repositorio | https://github.com/anakmedina08/advanced-ai-lab (público; rama `develop` al día) |
| Kanban | https://github.com/users/anakmedina08/projects/2 |
| Frontend | React 18 + Vite + TypeScript · `make frontend` (o `cd frontend && npm install && npm run dev`) → http://localhost:5173 |
| Backend | FastAPI · `make api` (o `uv run sb api`) · puerto 8000 · http://127.0.0.1:8000/docs |
| MLflow | `make mlflow-server` · puerto 5050 · `MLFLOW_TRACKING_URI=http://127.0.0.1:5050` |
| Modelo MaaS | YOLO26-L, `ultralytics/assets@v8.4.0` (sha256 `9fe3c544…`), licencia AGPL-3.0 |
| Model Card propia | `docs/model-card.md` |
| Diagrama | `docs/arquitectura.html` (fuente `docs/arquitectura.json`, formato Archify, tipo *architecture*) |
| PRs | ver la cifra actualizada con `gh pr list --state merged` (las de las historias SPEC-007 a SPEC-042 dependen de la aprobación del Code Reviewer) |
| Especificaciones SDD | `openspec/specs/` · 42 specs · ejemplos: SPEC-027 (`027-foto-ui`) y SPEC-034 (`034-evaluacion-yolo`) |

---

## Qué falta o no se cumple del todo (decirlo con transparencia)

- **Revisión y merge:** las PRs de las historias se abrieron hoy y necesitan la aprobación del Code
  Reviewer para fusionarse. Mientras no se fusionen, no cuentan para el mínimo de 40.
- **Piso individual de 8 PRs y 8 specs por persona:** casi todo el trabajo de esta semana quedó a
  nombre de Katherine; Daniel tiene 2 PRs fusionadas propias. El grupo no cumple ese piso.
- **Commits directos a `develop` y `main`:** varias entregas anteriores se subieron sin PR. Desde
  SPEC-007 todo pasa por PR.
- **Archify oficial:** el diagrama usa el formato de Archify, pero la skill externa no se instaló.
  Se puede regenerar con `make skill-add REPO=tt-a1i/archify SKILL=archify`.
- **Docker Compose:** está escrito, pero no se probó localmente (Docker Desktop apagado).
- **LangSmith:** las trazas locales en JSONL reemplazan a LangSmith mientras no haya clave.
- **Límites WIP del tablero:** están escritos en `docs/kanban.md` y en la plantilla, pero hay que
  configurarlos en la UI del tablero (Column limit).

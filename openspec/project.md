# Proyecto · Asistente de conocimiento Seguros Bolívar

- **Curso:** Técnicas Avanzadas de IA en Modelos de Lenguaje (UAO) · Grupo 10 (Daniel Silva, Katherine Medina)
- **Stack:** Python 3.13 + uv · requests/BeautifulSoup/trafilatura · LangChain · Claude (Anthropic API) / Ollama · Streamlit
- **Convenciones:** ver `AGENTS.md` (reglas que también usa GGA).

## Specs
| Spec | Alcance | Requisitos |
|---|---|---|
| [`fase1-base-conocimiento`](specs/fase1-base-conocimiento/) | scraping Medallion, Q&A, resumen y FAQ con fuente | R1–R7 |
| [`fase2-producto-unico`](specs/fase2-producto-unico/) | API, recomendador, proveedores, agentes, chat, skills, RPC, RAG Chroma | R7–R15 |
| [`rag-qdrant-agente`](specs/rag-qdrant-agente/) | modos «rag» y «agente», Claude sin `temperature` | R16–R19 |
| [`vision-foto`](specs/vision-foto/) | foto → «¿qué hago?» con YOLO, Claude con visión y FastAPI | R20–R24 |
| [`interfaz-dos-areas`](specs/interfaz-dos-areas/) | interfaz cliente / equipo, chat, tema corporativo, sustentación y experimentos | R25–R28, R32 |
| [`experimentos-mlflow`](specs/experimentos-mlflow/) | bitácora de experimentos con MLflow | R29–R31 |

Las 6 specs anteriores son SPEC-001 a SPEC-006 en ese orden.

## Specs por historia (SPEC-007 a SPEC-042)

Una spec por historia del tablero, escrita antes del código y vinculada a su issue y PR.

| Spec | Historia |
|---|---|
| [`007-salud-health`](specs/007-salud-health/) | SPEC-007 · Endpoint /health con el estado de cada dependencia |
| [`008-errores-http`](specs/008-errores-http/) | SPEC-008 · Errores HTTP uniformes con código, detalle y request id |
| [`009-logs-latencia`](specs/009-logs-latencia/) | SPEC-009 · Logs estructurados y latencia por petición |
| [`010-cors-config`](specs/010-cors-config/) | SPEC-010 · CORS configurable para el frontend desacoplado |
| [`011-tool-datos`](specs/011-tool-datos/) | SPEC-011 · Herramienta determinista sobre los CSV con @tool y Pydantic |
| [`012-router`](specs/012-router/) | SPEC-012 · Router que decide entre respuesta directa, datos, RAG o ambas |
| [`013-rag-qdrant`](specs/013-rag-qdrant/) | SPEC-013 · RAG híbrido del agente sobre Qdrant con filtro por payload |
| [`014-blindaje-rag`](specs/014-blindaje-rag/) | SPEC-014 · Blindaje del RAG contra inyección indirecta |
| [`015-memoria-largo-plazo`](specs/015-memoria-largo-plazo/) | SPEC-015 · Memoria de largo plazo con Store y namespace por usuario |
| [`016-contexto-resumen`](specs/016-contexto-resumen/) | SPEC-016 · Gestión del contexto multi-turno: recorte por tokens y resumen |
| [`017-agente-enrutado`](specs/017-agente-enrutado/) | SPEC-017 · Agente con router: tools por ruta y decisión visible |
| [`018-ci-ramas-apiladas`](specs/018-ci-ramas-apiladas/) | SPEC-018 · CI en las PR apiladas (base feature/*) |
| [`019-streaming-sse`](specs/019-streaming-sse/) | SPEC-019 · Streaming de la respuesta del agente por SSE |
| [`020-sesiones-api`](specs/020-sesiones-api/) | SPEC-020 · Sesiones: historial, checkpoints (time travel) y borrado por REST |
| [`021-trazas`](specs/021-trazas/) | SPEC-021 · Trazas de cada turno en JSONL y LangSmith |
| [`022-frontend-base`](specs/022-frontend-base/) | SPEC-022 · Frontend propio con React, Vite y TypeScript |
| [`023-cliente-api`](specs/023-cliente-api/) | SPEC-023 · Cliente tipado de la API con timeout, reintentos y SSE |
| [`024-chat-streaming`](specs/024-chat-streaming/) | SPEC-024 · Chat con streaming de la respuesta del agente |
| [`025-sesiones-ui`](specs/025-sesiones-ui/) | SPEC-025 · Sesiones en el frontend: hilos, usuario y memoria visible |
| [`026-traza-router-ui`](specs/026-traza-router-ui/) | SPEC-026 · Panel de la decisión del router, tools y fuentes |
| [`027-foto-ui`](specs/027-foto-ui/) | SPEC-027 · Foto «¿qué hago?» en el frontend con confianza y estados |
| [`028-estado-ui`](specs/028-estado-ui/) | SPEC-028 · Página de estado del servicio y aviso de API caída |
| [`029-responsive-a11y`](specs/029-responsive-a11y/) | SPEC-029 · Diseño responsive y accesible |
| [`030-tests-ui`](specs/030-tests-ui/) | SPEC-030 · Pruebas del frontend con Vitest y Testing Library |
| [`031-ci-frontend`](specs/031-ci-frontend/) | SPEC-031 · CI del frontend: tipos, pruebas y build |
| [`032-selector-proveedor`](specs/032-selector-proveedor/) | SPEC-032 · Elegir el proveedor del LLM desde el frontend |
| [`033-mlflow-servidor`](specs/033-mlflow-servidor/) | SPEC-033 · Servidor MLflow en el puerto 5050 |
| [`034-evaluacion-yolo`](specs/034-evaluacion-yolo/) | SPEC-034 · Evaluación de YOLO en MLflow: 3 corridas comparables |
| [`035-model-registry`](specs/035-model-registry/) | SPEC-035 · Model Registry del YOLO que usa la API |
| [`036-eval-retrieval`](specs/036-eval-retrieval/) | SPEC-036 · Evaluación del retrieval con recall@10 y nDCG@10 |
| [`037-model-card`](specs/037-model-card/) | SPEC-037 · Model Card del modelo YOLO de la API |
| [`038-arquitectura-archify`](specs/038-arquitectura-archify/) | SPEC-038 · Diagramas de arquitectura (Archify) y del grafo del agente |
| [`039-readme-m2-m3`](specs/039-readme-m2-m3/) | SPEC-039 · README del Módulo 2 y 3: cómo correr y qué demostrar |
| [`040-kanban-politicas`](specs/040-kanban-politicas/) | SPEC-040 · Políticas del tablero Kanban: WIP, historias y métricas |
| [`041-docker-compose`](specs/041-docker-compose/) | SPEC-041 · Docker Compose: API, frontend y MLflow |
| [`042-requisitos-sustentacion`](specs/042-requisitos-sustentacion/) | SPEC-042 · Matriz de requisitos y guion de las dos sustentaciones |

Las tareas de todas las specs alimentan el tablero con `scripts/crear_kanban.py` (IDs `T-NN` únicos).

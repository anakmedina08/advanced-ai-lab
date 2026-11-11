# Tareas · Fase 2 — Producto único

> Se suman al mismo tablero Kanban: `uv run python scripts/crear_kanban.py --repo anakmedina08/advanced-ai-lab --project N`.

## Hecho
- [x] T-17 [refactor] Integrar el recomendador de Gestión en model/recomendador con CLI `sb reco` (Daniel)
- [x] T-18 [backend] API FastAPI + Pydantic con validación de datos personales (Daniel)
- [x] T-19 [ml] Proveedor DeepSeek intercambiable con Anthropic y Ollama (Daniel)
- [x] T-20 [infra] Subagentes de Claude Code y hooks de telemetría saneada (Daniel)
- [x] T-21 [documentation] Matriz de requisitos de ambos cursos, spec fase 2 y ADR-009 a ADR-012 (Daniel)
- [x] T-30 [backend] Chat orquestado POST /chat con clasificador por reglas, recomendación por perfil y traza (Daniel)
- [x] T-31 [infra] Skills propias y de terceros: cargador, sb skills, make skill-add/skill-find y opencode.json (Daniel)
- [x] T-32 [ui] Pestaña de chat estilo ChatGPT en yellowdata.com.co/casos (Daniel)
- [x] T-35 [backend] JSON-RPC 2.0 en POST /rpc con métodos Pydantic y rpc.descubrir (Daniel)
- [x] T-36 [ml] Base vectorial Chroma y recuperación híbrida BM25 + vectores con evaluación hit@k (Daniel)
- [x] T-37 [ml] Agente con tools, salida estructurada, memoria SQLite y trazas LangSmith (Daniel)
- [x] T-38 [ml] Modos rag (Ollama + Qdrant) y agente (Deep Agents) en sb ask, y Claude sin temperature (Katherine)
- [x] T-40 [ml] Foto → ¿qué hago?: YOLO difumina personas, Claude entiende la situación, RAG y recomendador (Katherine)

## Pendiente
- [ ] T-22 [infra] Publicar el panel en vivo en yellowdata.com.co y cargar los secretos AGENT_EVENTS_* (Daniel)
- [ ] T-23 [ml] Candidatos con multilingual-e5-small y ranking LightGBM (Recall@5 ≥ 0,70) (Daniel)
- [ ] T-24 [ml] Seguimiento de experimentos con MLflow (Katherine)
- [ ] T-25 [ml] Auditoría de sesgo por segmento del recomendador (Katherine)
- [ ] T-26 [ui] Consola del asesor en el front web (historial, recomendaciones por cliente) (Katherine)
- [ ] T-27 [ml] Clasificador de intención entrenado que supere la línea base por reglas (Katherine)
- [ ] T-28 [infra] Imagen Docker con la API (uvicorn) y despliegue (Daniel)
- [ ] T-29 [documentation] Registrar ADR-009 a ADR-014 en Engram (Katherine)
- [ ] T-34 [ml] Indexar con nomic-embed-text, medir hit@k del híbrido y subir el dataset a LangSmith (Katherine)
- [ ] T-33 [infra] Publicar la API en cPanel (Setup Python App + passenger_wsgi.py) y ASSISTANT_API_URL (Daniel)
- [ ] T-39 [ml] Evaluar los modos rag (Qdrant) y agente (Deep Agents) frente a Chroma y la Fase 1 (Daniel y Katherine)

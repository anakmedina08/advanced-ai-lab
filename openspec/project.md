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
| [`interfaz-dos-areas`](specs/interfaz-dos-areas/) | interfaz cliente / equipo, chat y tema corporativo | R25–R28 |

Las tareas de todas las specs alimentan el tablero con `scripts/crear_kanban.py` (IDs `T-NN` únicos).

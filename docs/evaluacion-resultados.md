# Resultados de la evaluación

- **Fecha:** 2026-11-13.
- **Modelo:** Claude Haiku (`claude-haiku-5-5`, esfuerzo `low`).
- **Banco:** [`evaluacion/preguntas.yaml`](../evaluacion/preguntas.yaml), 25 preguntas: productos,
  canales, preguntas fuera de alcance y un intento de inyección.
- **Cómo reproducirlo:** `uv run sb eval --provider anthropic --version vN [--modo …]`. Cada corrida
  guarda `evaluacion/resultados_*.csv` (no se versiona) y la pestaña «Evaluación» del panel del
  equipo los compara.

**Métricas automáticas** (de 0 a 1; más alto es mejor):
- **Palabras clave:** proporción de las palabras esperadas que aparecen en la respuesta.
- **Cita la fuente:** proporción de respuestas con una URL de segurosbolivar.com.
- **Rechazo correcto:** el modelo se niega solo cuando la pregunta está fuera de alcance.

## 1. Versiones del prompt (base completa) · T-14

| Métrica | v1 ingenuo | v2 grounding simple | v3 estructurado | v4 few-shot |
|---|---|---|---|---|
| Palabras clave | 1,00 | 0,98 | 0,98 | 0,98 |
| Cita la fuente | **0,20** | **0,16** | **1,00** | **1,00** |
| Rechazo correcto | 0,84 | 0,84 | **0,96** | **0,96** |
| Latencia (s) | 2,45 | 2,27 | 1,63 | 1,50 |

**Lectura:**
- El contenido es parecido en las cuatro versiones.
- Solo las estructuradas (reglas, XML, citación obligatoria) **citan la fuente siempre** y rechazan
  bien lo que está fuera de alcance.
- v4 no mejora a v3, así que v3 sigue siendo la versión por defecto.

## 2. Estrategias de contexto (prompt v3) · T-39

| Métrica | Completo (~36K tokens) | Por palabras (~2,5K) | RAG Qdrant (k = 4) | Agente |
|---|---|---|---|---|
| Palabras clave | 0,98 | 0,98 | 0,66 | 0,71 |
| Cita la fuente | 1,00 | 1,00 | 1,00 | 1,00 |
| Rechazo correcto | 0,96 | 0,96 | 0,88 | 0,88 |
| Latencia (s) | 1,63 | 1,44 | 1,35 | 10,81 |

**Lectura:**
- La búsqueda **por palabras igualó a la base completa** con una fracción del contexto.
- El **RAG denso con 4 fragmentos perdió páginas** en preguntas amplias de producto:
  - P02: todo riesgo vehículos;
  - P07: seguro de vida;
  - P10: clientes Davivienda;
  - P11: carros eléctricos;
  - C05: PQRS;
  - C08: horario de los sábados.

  Las muchas páginas casi idénticas de Davivienda desplazan a la correcta entre las 4 más parecidas.
- El agente recupera parte de esa pérdida con búsquedas adicionales, pero tarda ~7 veces más.
- **Conclusión:** la recuperación densa pura necesita más fragmentos o combinarse con búsqueda léxica.
  Esto respalda el RAG híbrido BM25 + vectores (ADR-016).

## Pendiente

- **T-65:** comparar con el RAG híbrido de Chroma (`sb rag evaluar`, hit@k). Requiere indexar con
  `nomic-embed-text`.

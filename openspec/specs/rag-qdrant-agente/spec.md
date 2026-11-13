# Spec · Modos de contexto «rag» (Qdrant) y «agente» (Deep Agents)

> Desglose de la tarea T-38 de [`fase2-producto-unico`](../fase2-producto-unico/). Plan en
> [`plan.md`](plan.md); trabajo en [`tasks.md`](tasks.md). Decisiones: ADR-018 y ADR-019.

## Contexto

La Fase 1 envía toda la base (~36 000 tokens) en el *system prompt*; con Ollama en CPU eso tarda
minutos y con Claude cuesta más por pregunta. Esta spec agrega dos modos que recuperan solo los
fragmentos relevantes, adaptando el ejercicio del curso `ejercicio_langchain`, y corrige el error
400 de Claude con `temperature`.

## Requisitos

### R16 · Modos de contexto intercambiables
- `sb ask`, `sb eval` y la interfaz DEBEN aceptar los modos `completo`, `reducido`, `rag` y `agente`
  sin cambiar los prompts v1–v4.
- Los modos con contexto recuperado DEBEN anteponer siempre el bloque de canales de atención.
- **Escenario:** dada «¿Cuál es el WhatsApp de atención?» en modo `rag`, entonces la respuesta trae
  el número del bloque de canales y una URL de segurosbolivar.com.

### R17 · Índice vectorial local y reutilizable (ADR-018)
- Los fragmentos de `data/gold/chunks.jsonl` DEBEN indexarse en Qdrant con embeddings locales de
  Ollama (`embeddinggemma`); el texto no sale del equipo.
- El nombre de la colección DEBE llevar una huella del contenido: si los fragmentos no cambian, el
  índice se reutiliza sin recalcular embeddings; si cambian, se reconstruye y se borra el anterior.
- Si Ollama no responde, DEBE fallar con un mensaje que explique cómo instalar el modelo y sin dejar
  un índice a medias.
- **Escenario:** dado un índice ya creado, cuando se vuelve a abrir, entonces no se recalcula
  ningún embedding de fragmentos.
- **Escenario:** dada la app de Streamlit con el índice abierto, cuando la CLI lo abre, entonces usa
  una copia temporal en lugar de fallar por el candado de Qdrant.

### R18 · Agente con subagente analista
- El modo `agente` DEBE buscar con una herramienta, guardar cada fragmento en `/retrieved/` y delegar
  su análisis al subagente `chunk-analyst`.
- Los prompts del agente DEBEN vivir en `prompts.py` y conservar las reglas de la Fase 1
  (no-información, citación, datos como datos, sin datos personales).
- **Escenario:** dada una búsqueda sin resultados, entonces la herramienta lo dice y no inventa rutas.

### R19 · Claude sin parámetros de muestreo (ADR-019)
- Las peticiones a Claude NO DEBEN enviar `temperature`; el determinismo lo dan el prompt y
  `output_config.effort = low`. Ollama conserva temperatura 0.
- **Escenario:** dada la configuración de Claude, cuando se arma la petición, entonces no contiene
  `temperature` y sí `output_config`.

## Fuera de alcance
- Reemplazar el RAG híbrido con Chroma (ADR-016): ambos conviven para compararlos en la evaluación.

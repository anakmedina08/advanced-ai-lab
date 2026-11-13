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

## 3. Recuperación: hit@k con la misma métrica para los cuatro métodos · T-34 y T-65

`hit@k` (`model/rag/evaluacion.hit_at_k`, de Daniel): una pregunta acierta si los k fragmentos
recuperados traen **todas** sus palabras clave. Se mide sobre las 21 preguntas en alcance.

- **Índices:** Chroma con `nomic-embed-text` (414 fragmentos, `sb rag indexar`) y Qdrant con
  `embeddinggemma` (`sb index`).
- **Cómo reproducirlo:** `uv run python scripts/comparar_recuperacion.py -k 4 6 10`.

| Método | hit@4 | hit@6 | hit@10 |
|---|---|---|---|
| BM25 (léxico) | 67 % | 71 % | 86 % |
| Híbrido Chroma (BM25 + vectores, RRF) | 62 % | 76 % | 81 % |
| Qdrant denso (modo «rag») | 62 % | 62 % | 71 % |
| **Por palabras (modo «reducido»)** | **86 %** | **90 %** | **95 %** |

**Prueba oficial del híbrido** (`uv run sb rag evaluar -k 3 6`):
- hit@3 = 57 %: falla en C03, C06, C07, P02, P03, P04, P05, P07 y P10.
- hit@6 = 76 %: falla en P02, P03, P04, P07 y P10.

**Lectura:**
- En este corpus, la **recuperación densa es la más débil**: Qdrant solo vectores queda último y el
  híbrido no supera claramente a BM25 solo. Las páginas casi idénticas de Davivienda confunden a los
  *embeddings*, lo mismo que mostró la evaluación de respuestas (sección 2).
- La **búsqueda por palabras** (cuenta coincidencias en título, ruta y texto) es la mejor.
  - Salvedad: los modos «rag» y «reducido» siempre agregan el bloque de canales, y eso favorece las
    preguntas de canales (C03, C06, C07).
  - Aun así, en las preguntas de producto falla en 1 (P04) frente a 4 del híbrido (P02, P03, P07,
    P10).
- **Mejoras posibles:**
  - deduplicar o agrupar las páginas de Davivienda antes de indexar;
  - subir k;
  - dar más peso al título y a la ruta en el componente denso.

## 4. Elección del modelo YOLO para «Foto: ¿qué hago?»

Se compararon los cuatro tamaños de YOLO26 en CPU, con 6 fotos: choque, gotera, niña con su perro,
moto, bus con peatones y dos personas. Los tiempos son la mediana de 3 inferencias tras calentar el
modelo. La confianza se midió con umbral 0,15, el mismo que se usa para difuminar personas.

| Modelo | Tamaño | Mediana | Personas: confianza media / mínima | Objetos: confianza media |
|---|---|---|---|---|
| yolo26n | 5 MB | 57 ms | 0,83 / 0,66 | 0,56 |
| yolo26s | 20 MB | 110 ms | 0,88 / 0,78 | 0,88 |
| yolo26m | 44 MB | 271 ms | 0,83 / 0,15 | 0,65 |
| **yolo26l** | **53 MB** | **335 ms** | **0,90 / 0,81** | **0,80** |

**Lectura:**
- Los cuatro detectan los mismos objetos y personas en estas fotos.
- **yolo26l** detecta a las personas con la mayor confianza; su peor caso (0,81) es el más alto.
  Por eso es el más seguro para difuminarlas antes de enviar la foto.
- Su costo (~0,3 s) es pequeño frente a la llamada a Claude (~2 s), así que es el modelo por defecto.
- yolo26s es la alternativa rápida, configurable con `YOLO_MODEL_PATH`.

## Pendiente

- **T-66:** subir el banco de preguntas como dataset de LangSmith (`make langsmith-dataset`).
  Requiere `LANGSMITH_API_KEY`, que no está configurada.

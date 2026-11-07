# Spec · Fase 2 — Producto único: Asistente Seguros Bolívar

> Un solo repositorio y un solo producto para los dos cursos de la maestría: **Técnicas Avanzadas
> de IA en Modelos de Lenguaje** (módulo de conocimiento) y **Gestión de Proyectos en IA y CD**
> (módulo de recomendación). Plan en [`plan.md`](plan.md); trabajo en [`tasks.md`](tasks.md).
> La Fase 1 sigue vigente en [`../fase1-base-conocimiento/`](../fase1-base-conocimiento/).

## Contexto

Ambos cursos construían piezas del mismo cliente (Seguros Bolívar) en repositorios separados. Se
unifican (ADR-009) para que cada entrega muestre el producto completo, con la misma gobernanza,
y para que el desarrollo con agentes sea visible en vivo (ADR-011).

## Requisitos

### R7 · API REST con contratos validados (ADR-010)
- DEBE exponer `/salud`, `/pipeline`, `/preguntas`, `/resumen`, `/faq` y
  `/recomendaciones/{cliente_id}` con FastAPI, documentación OpenAPI en `/docs`.
- Cada entrada y salida DEBE ser un modelo Pydantic con type hints; los campos desconocidos se rechazan.
- `/preguntas` DEBE rechazar con 422 textos con correo, teléfono o número de documento (Ley 1581).
- Las respuestas DEBEN traer `fuentes` (URLs de segurosbolivar.com citadas).
- **Escenario:** dada la pregunta «Mi cédula es 1012345678», entonces la API responde 422 sin llamar al LLM.
- **Escenario:** sin `data/gold/chunks.jsonl`, `/preguntas` responde 503 con la instrucción para generarlo.

### R8 · Recomendador integrado (curso de Gestión)
- El módulo `model/recomendador` DEBE generar datos sintéticos que cumplan el contrato de datos
  (sin PII) y calcular Recall@5 y NDCG@5 con partición *leave-last-out*.
- `/recomendaciones` DEBE devolver top-k productos que el cliente no tiene, con nombre, línea y razón legible.
- Meta del modelo e5-small + LightGBM (M3): Recall@5 ≥ 0,70 (línea base por segmento: 0,639).
- **Escenario:** dado un cliente inexistente, entonces la API responde 404.

### R9 · Proveedor de LLM intercambiable (ADR-012)
- El proveedor DEBE elegirse por `LLM_PROVIDER` (`anthropic`, `deepseek`, `ollama`) sin cambiar la lógica.
- El presupuesto de contexto DEBE ajustarse a la ventana de cada proveedor.

### R10 · Desarrollo con agentes trazable y en vivo (ADR-011)
- `.claude/agents/` DEBE versionar los subagentes del equipo con herramientas mínimas y modelo por costo.
- Los hooks de `.claude/settings.json` DEBEN registrar SessionStart, SubagentStart/Stop,
  PostToolUse (Edit, Write, Bash) y Stop en `logs/agent-events.jsonl` y, si hay URL, publicarlos.
- Los eventos publicados NO DEBEN contener prompts, contenido de archivos, salidas ni comandos
  completos, ni rutas de `data/` o `.env`.
- La CI DEBE publicar su resultado como evento.
- **Escenario:** dado un `Write` sobre `.env`, cuando el hook publica, entonces el evento no trae la ruta.

### R11 · Chat orquestado (ADR-013)
- `POST /chat` DEBE clasificar el mensaje antes de usar el LLM y devolver intención, herramienta,
  fuentes, recomendaciones y la `traza` de pasos.
- Saludos y temas ajenos NO DEBEN llamar al LLM.
- Una recomendación DEBE poder pedirse describiendo el perfil, sin identificación.
- **Escenario:** dado «¿Qué seguro me recomiendas? Tengo carro y un perro», entonces responde el
  recomendador con perfil `{vehiculo: carro, tiene_mascota: true}`.

### R12 · Skills (ADR-014)
- El proyecto DEBE aceptar skills en `.claude/skills`, `.agents/skills` y `.opencode/skills` con las
  reglas de OpenCode, y solo las de `metadata.uso: asistente` DEBEN llegar al chat.
- **Escenario:** dada una skill instalada con `npx skills add`, entonces no aparece en `GET /skills`
  hasta que se marque con `uso: asistente`.

### R13 · RPC (ADR-015)
- `POST /rpc` DEBE cumplir JSON-RPC 2.0: lotes, notificaciones y códigos de error del estándar; los
  parámetros de cada método DEBEN validarse con Pydantic y `rpc.descubrir` DEBE listar sus esquemas.
- **Escenario:** dado `{"jsonrpc":"2.0","method":"no.existe","id":1}`, entonces responde `error.code = -32601`.

### R14 · RAG con base vectorial (ADR-016)
- Los fragmentos Gold DEBEN indexarse en Chroma persistente; la búsqueda DEBE combinar BM25 y
  vectores; el índice DEBE rechazar consultas con embeddings distintos a los de su creación.
- `sb rag evaluar` DEBE reportar hit@k sobre el banco de preguntas en alcance.

### R15 · Agente (ADR-017)
- El agente DEBE responder con `RespuestaAgente` y solo DEBE conservar fuentes que devolvieron sus tools.
- La memoria DEBE persistir por `conversacion_id` entre reinicios y DEBE poder borrarse.
- Correos, tarjetas y números de documento DEBEN redactarse antes de llegar al modelo o a la memoria.
- **Escenario:** dado «mi cédula es 1012345678», entonces el modelo recibe `[REDACTED…]` en su lugar.

## Criterios de aceptación de la fase
- `make check` en verde con cobertura ≥ 85 %.
- Matriz [`docs/requisitos.md`](../../../docs/requisitos.md) sin requisitos en estado «falta».
- Panel de yellowdata.com.co/casos mostrando eventos reales de una sesión del equipo.

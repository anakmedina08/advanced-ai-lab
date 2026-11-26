# SPEC-082 · Panel en vivo: el producto y el pipeline encienden el grafo de /casos

> Cursos: Técnicas Avanzadas de IA (551462) y Gestión de Proyectos en IA y CD (551475) ·
> Story points: **3** · Responsable: Daniel Silva · Anuncios:
> [551462 · 007](../../../docs/anuncios/551462-anuncio-007.md) (20 tools trazables, OpenClaw) y
> [551475 · 008](../../../docs/anuncios/551475-anuncio-008.md) (pipeline «trazable por commit»).
> Amplía la telemetría del [ADR-011](../../../docs/decisiones/ADR-011-subagentes-y-telemetria.md).

## Problema
El panel «Desarrollo agéntico» de Yellowdata (`/casos/asistente-seguros#agentes`) solo recibe los
hooks de Claude Code y el chat web. Lo que pasa fuera de Yellowdata no se ve: las tools que el gateway
de OpenClaw llama por el MCP (WhatsApp), las trazas de LangSmith y el pipeline de GitLab
(lint → test → build → deploy). Yellowdata ya pinta un grafo vivo con esos nodos; falta que la API y
la CI publiquen sus eventos.

## Requisitos
- **R082.1** La API DEBE publicar un evento `Tecnologia` por cada tool llamada por el MCP propio, con
  agente `whatsapp` y solo el **nombre** de la tool (nunca sus argumentos).
- **R082.2** La API DEBE publicar un evento `langsmith` por turno del agente **solo** si
  `LANGSMITH_TRACING` está activo.
- **R082.3** Los jobs `lint`, `test`, `build_api`, `build_frontend` y `deploy` DEBEN avisar su
  resultado (`CI_JOB_STATUS`) con el commit corto, en `after_script`.
- **R082.4** Todo es opcional: sin `AGENT_EVENTS_URL` y `AGENT_EVENTS_TOKEN` no se envía nada.
- **R082.5** Un fallo del panel NUNCA rompe una respuesta ni un job (timeout corto, errores
  ignorados, `|| true`), y el token nunca aparece en el repositorio ni en el log.

## Criterios de aceptación
- **AC1** · `tests/test_panel_eventos.py`: sin variables no hay petición; con variables, solo los
  campos del panel y el token en la cabecera; un fallo de red no lanza.
- **AC2** · Una tool del MCP publica `whatsapp` con su nombre y devuelve lo mismo que la tool.
- **AC3** · Cada job del pipeline incluye el aviso y la llave SSH se sigue borrando primero.
- **AC4** · En producción, una pregunta por WhatsApp enciende «WhatsApp» y la tool usada en el grafo,
  y un push a `develop` enciende las etapas del pipeline con el commit.

## Repo vs servidor
| Va al repo (versionado, sin secretos) | Va solo al servidor / CI (nunca al repo) |
|---|---|
| `model/panel.py`, envoltura en `view/mcp.py`, aviso en `controller/agente.py` | `AGENT_EVENTS_TOKEN` en `ENV_PRODUCCION` y en `yellowdata.env` (mismo valor) |
| `.gitlab-ci.yml`: `.aviso_panel` con ancla YAML | Variables de CI enmascaradas `AGENT_EVENTS_URL` y `AGENT_EVENTS_TOKEN` |
| `deploy/app.env.example`: URL interna, token vacío | — |

## Riesgos
| Riesgo | Mitigación |
|---|---|
| El panel cae o tarda | Hilo *daemon*, timeout de 3 s y errores ignorados; en CI, `|| true` |
| Fuga de texto del usuario | Solo nombres de tools y etiquetas; prueba que lo verifica |
| El token aparece en el log de CI | Variable enmascarada; el script solo nombra `$AGENT_EVENTS_TOKEN` |

## Fuera de alcance
Eventos de MLflow (en producción no hay servidor MLflow: `SB_MLFLOW=0`) y del propio gateway de
OpenClaw (sin hooks); el grafo de Yellowdata, que vive en `daalrasi/yellowdata`.

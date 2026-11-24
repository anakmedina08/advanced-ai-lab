# SPEC-079 · Doce tools nuevas y workspace del agente

> Curso: Técnicas Avanzadas de IA (551462) · Story points: **8** · Responsable: Daniel Silva ·
> Anuncio: [551462 · 007](../../../docs/anuncios/551462-anuncio-007.md) (ítems 1.1 y 3.3 de la
> rúbrica = 17 %).

## Problema
La rúbrica pide **20 tools** `@tool` con Pydantic y trazables (hoy hay 8) y un **workspace** del
agente (`SOUL.md`, `AGENTS.md`, `USER.md`, `MEMORY.md` y bitácora diaria); hoy solo existe
`AGENTS.md`. Las 12 tools salen casi todas de lógica que ya existe en el repo; el workspace define
la identidad y las fuentes del agente.

## Requisitos
- **R079.1** DEBEN existir **20 tools** `@tool` en total (8 actuales + 12 nuevas), cada una con su
  docstring en español, argumentos tipados (Pydantic `args_schema=` cuando los argumentos sean
  estructurados) y retorno en texto/JSON.
- **R079.2** Las 12 nuevas DEBEN envolver lógica existente y DEBEN poder probarse **sin red ni API**
  (dependencias por constructor y dobles en pruebas).
- **R079.3** Las tools que tocan datos personales (`guardar_perfil`, `ver_perfil`, `olvidar_datos`)
  DEBEN operar por `usuario_id` (hash, nunca el número o dato en claro; Ley 1581).
- **R079.4** Las tools de conocimiento (`explicar_termino`, `guia_tramite`, `checklist_siniestro`,
  `citar_fuente`) DEBEN responder **solo** con información pública y DEBEN citar la URL de origen.
- **R079.5** `escalar_a_humano` DEBE entregar el canal oficial (WhatsApp/línea/PQR) con el resumen
  del caso, sin exponer datos (HITL, ítem 4.2).
- **R079.6** El workspace DEBE incluir `SOUL.md`, `USER.md`, `MEMORY.md` y una bitácora diaria
  versionada, coherentes con `AGENTS.md` y con `CONSTITUTION.md`.

## Criterios de aceptación
- **AC1** · `grep -rc "@tool" src/` totaliza **20** y `uv run pytest` sigue en verde (sin red).
- **AC2** · `listar_productos` y `citar_fuente` responden sin red ni modelo.
- **AC3** · `guardar_perfil`/`ver_perfil`/`olvidar_datos` sobre un `BaseStore` falso guardan, leen y
  borran por `usuario_id`.
- **AC4** · `explicar_termino`, `guia_tramite` y `checklist_siniestro` devuelven la URL de origen.
- **AC5** · El workspace existe y `make madurez` no baja (la CI lo verifica).

## Las 12 tools
| Tool | Envuelve | Nuevo | Fuente |
|---|---|---|---|
| `analizar_foto` | `controller.vision.analizar_foto` | no | YOLO + escena |
| `leer_documento` | `controller.mercado.identificar_documento` | no | OCR local (pypdf/tesseract) |
| `listar_productos` | `model.recomendador.catalogo.CATALOGO` | no | catálogo sintético |
| `citar_fuente` | `model.rag.hibrido.Fragmento` / `como_contexto` | no | — |
| `guardar_perfil` | `model.memoria.PerfilStore.guardar` | no | Store SQLite |
| `ver_perfil` | `model.memoria.PerfilStore.leer` | no | Store SQLite |
| `olvidar_datos` | `model.memoria.PerfilStore.borrar` + `olvidar_perfil` | no | Store + checkpointer |
| `estado_codigo_acceso` | `controller.acceso.estado` | no | SQLite `ACCESO_DB` |
| `explicar_termino` | glosario propio **o** `buscar_conocimiento` | **sí** | corpus Gold |
| `guia_tramite` | pasos propios **o** `buscar_conocimiento` | **sí** | corpus Gold |
| `checklist_siniestro` | tabla propia | **sí** | pública / corpus |
| `escalar_a_humano` | `controller.mercado.canales_para` (servicio `pqr`) | **sí** | canales oficiales |

## Riesgos
| Riesgo | Mitigación |
|---|---|
| Las tools de contenido (`glosario`, `pasos`, `checklist`) inventan datos | Se basan en el corpus Gold con cita de URL; nunca en conocimiento interno |
| `analizar_foto`/`leer_documento` cargan modelos pesados | Extra opcional `vision`; en pruebas se inyectan detectores/lectores falsos |
| El conteo de `@tool` se dispara por decoradores de pruebas | Contar solo los de `src/`, no los de `tests/` |

## Fuera de alcance
El servidor MCP que las expone (SPEC-078) y la corrección de embeddings en producción (SPEC-069).

# Tablero Kanban · políticas y métricas de flujo

> Generado con `uv run python scripts/metricas_kanban.py` el 2026-11-14 00:19 UTC · 115 historias.
> Tablero: https://github.com/users/anakmedina08/projects/2

## Políticas

| Columna | Entra cuando… | Límite WIP |
|---|---|---|
| Backlog | la historia tiene «Como/quiero/para», criterios Dado/Cuando/Entonces y puntos | — |
| Ready | su spec SDD (`spec.md`, `plan.md`, `tasks.md`) está escrita | — |
| In progress | se crea la rama `feature/NNN-*` | **2** (una por integrante) |
| In review | la PR está abierta con `Closes #N`, revisor asignado y checks corriendo | **2** |
| Done | la PR se fusionó, los AC se cumplen y hay demo local | — |

**Definition of Done:** spec SDD + código + pruebas + documentación + PR aprobada + demo local.
Plantilla de historia: `.github/ISSUE_TEMPLATE/historia.yml`.

## WIP (trabajo empezado y no terminado)

| Columna | Historias | Límite |
|---|---|---|
| In progress | 0 | 2 |
| In review | 0 | 2 |

Dentro de los límites WIP.

## Throughput (historias cerradas por semana)

| Semana ISO | Cerradas |
|---|---|
| 2026-S46 | 115 |

## Work item age (días abiertas, las 10 más antiguas en curso)

| Historia | Días |
|---|---|
| — | — |

## Cycle time (inicio → cierre)

- Mediana: **0.0 h** · percentil 85:
  **4.7 h** sobre 115 historias cerradas.
- El percentil 85 es la base del SLE (*service level expectation*): «el 85 % de las historias se
  cierran en menos de ese tiempo».

## Lectura

- **WIP alto en In review:** las PR apiladas esperan la aprobación del Code Reviewer. El cuello de
  botella es la revisión, no el desarrollo. La acción es revisar y fusionar antes de empezar otra
  historia.
- **Throughput:** se concentra en la semana de la sustentación; para el Módulo 4 conviene un flujo
  más parejo, con historias más pequeñas cada semana.
- **Cycle time:** las tareas de las fases anteriores (T-01 a T-74) se registraron en el tablero
  después de terminarlas: se crearon y cerraron en el mismo minuto, así que su cycle time (≈ 0 h)
  no es representativo. El cycle time real se mide con las historias SPEC-007 en adelante, que
  se abren al empezar y se cierran al fusionar su PR.

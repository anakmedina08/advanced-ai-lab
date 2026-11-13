"""Calcula las métricas de flujo del tablero (WIP, throughput, edad, cycle time) y escribe docs/kanban.md.

Lee el tablero y los issues con GitHub CLI (``gh`` autenticado con permiso ``project``):

    uv run python scripts/metricas_kanban.py --owner anakmedina08 --project 2
"""

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from sb_asistente.model.kanban import LIMITES_WIP, Historia, calcular, excede_wip

RAIZ = Path(__file__).resolve().parents[1]
REPO = "anakmedina08/advanced-ai-lab"


def _gh(*args: str) -> object:
    salida = subprocess.run(["gh", *args], capture_output=True, check=True)
    return json.loads(salida.stdout.decode("utf-8"))


def _fecha(texto: str | None) -> datetime | None:
    return datetime.fromisoformat(texto.replace("Z", "+00:00")) if texto else None


def historias(owner: str, proyecto: int) -> list[Historia]:
    """Issues del tablero con su estado (las PR y los bots no son historias)."""
    items = _gh("project", "item-list", str(proyecto), "--owner", owner, "--format", "json", "--limit", "500")
    estados = {
        i["content"]["number"]: i.get("status") or "Backlog"
        for i in items["items"]
        if i.get("content", {}).get("type") == "Issue"
    }
    issues = _gh(
        "issue",
        "list",
        "-R",
        REPO,
        "--state",
        "all",
        "--limit",
        "500",
        "--json",
        "number,title,createdAt,closedAt",
    )
    return [
        Historia(i["number"], i["title"], estados[i["number"]], _fecha(i["createdAt"]), _fecha(i["closedAt"]))
        for i in issues
        if i["number"] in estados
    ]


def markdown(metricas: object, ahora: datetime, total: int) -> str:
    """Documento con las métricas y su lectura."""
    m = metricas
    filas_wip = "\n".join(f"| {c} | {n} | {LIMITES_WIP[c]} |" for c, n in m.wip.items())
    semanas = "\n".join(f"| {s} | {n} |" for s, n in m.throughput_semanal.items())
    edades = sorted(m.edad_dias.items(), key=lambda par: -par[1])[:10]
    filas_edad = "\n".join(f"| #{n} | {d:.2f} |" for n, d in edades) or "| — | — |"
    exceso = excede_wip(m)
    alerta = (
        "**Fuera de política:** " + ", ".join(f"{c} supera su límite en {d}" for c, d in exceso.items())
        if exceso
        else "Dentro de los límites WIP."
    )
    return f"""# Tablero Kanban · políticas y métricas de flujo

> Generado con `uv run python scripts/metricas_kanban.py` el {ahora:%Y-%m-%d %H:%M} UTC · {total} historias.
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
{filas_wip}

{alerta}

## Throughput (historias cerradas por semana)

| Semana ISO | Cerradas |
|---|---|
{semanas or "| — | 0 |"}

## Work item age (días abiertas, las 10 más antiguas en curso)

| Historia | Días |
|---|---|
{filas_edad}

## Cycle time (inicio → cierre)

- Mediana: **{m.cycle_time_mediana_h if m.cycle_time_mediana_h is not None else "—"} h** · percentil 85:
  **{m.cycle_time_p85_h if m.cycle_time_p85_h is not None else "—"} h** sobre {m.cerradas} historias cerradas.
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
"""


def main() -> None:
    """Calcula y escribe ``docs/kanban.md``."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--owner", default="anakmedina08")
    parser.add_argument("--project", type=int, default=2)
    args = parser.parse_args()
    ahora = datetime.now(UTC)
    lista = historias(args.owner, args.project)
    (RAIZ / "docs" / "kanban.md").write_text(
        markdown(calcular(lista, ahora), ahora, len(lista)), encoding="utf-8"
    )
    print(f"docs/kanban.md · {len(lista)} historias")


if __name__ == "__main__":
    main()

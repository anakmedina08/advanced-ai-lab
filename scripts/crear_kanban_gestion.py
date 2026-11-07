"""Crea o actualiza en GitHub los issues del Capítulo 5 (docs/gestion/backlog.json) y los agrega al tablero.

Uso (requiere GitHub CLI autenticado con el permiso ``project``: ``gh auth refresh -s project``):

    uv run python scripts/crear_kanban.py --repo OWNER/REPO --dry-run
    uv run python scripts/crear_kanban.py --repo OWNER/REPO --project 1

Así el tablero queda sincronizado con el documento: una sola fuente para ambos. Si un issue ya existe
(mismo prefijo ``[HU-xx]``) se actualizan su título, cuerpo y etiqueta en vez de duplicarlo.
"""

import argparse
import json
import subprocess
from pathlib import Path

BACKLOG = Path(__file__).resolve().parents[1] / "docs" / "gestion" / "backlog.json"
ETIQUETAS = {
    "ML": ("1d76db", "Modelo, embeddings, ranking y métricas"),
    "Backend": ("5319e7", "Datos, API y servicios"),
    "Frontend": ("0e8a16", "Interfaz de usuario"),
    "Testing": ("d93f0b", "Pruebas, CI/CD, Docker y auditoría"),
}


def cuerpo(h: dict) -> str:
    marca = "x" if h["estado"] == "Done" else " "
    ac = "\n".join(
        f"- [{marca}] **Dado:** {c['dado']}. **Cuando:** {c['cuando']}. **Entonces:** {c['entonces']}."
        for c in h["ac"]
    )
    depende = ", ".join(h.get("depende", [])) or "—"
    return (
        f"**Como** {h['como']}, **quiero** {h['quiero']}, **para** {h['para']}.\n\n"
        f"### Criterios de aceptación (Given-When-Then)\n{ac}\n\n"
        f"### Estimación\n{h['sp']} SP (Fibonacci 1:1 ≈ {h['sp']} día(s)): {h['justificacion']}\n\n"
        f"| Etiqueta | Responsable | Depende de |\n|---|---|---|\n"
        f"| {h['etiqueta']} | {h['responsable']} | {depende} |\n\n"
        "_Generado desde `docs/gestion/backlog.json` (Capítulo 5 de la propuesta M2). No editar a mano: "
        "cambiar el JSON y volver a ejecutar `scripts/crear_kanban.py`._"
    )


def gh(*args: str, dry: bool) -> str:
    if args[:2] != ("issue", "list"):
        print("gh", " ".join(a if len(a) < 80 else a[:77] + "..." for a in args))
    if dry:
        return "https://github.com/OWNER/REPO/issues/0"
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="OWNER/REPO")
    parser.add_argument("--project", type=int, help="Número del GitHub Project (opcional)")
    parser.add_argument("--dry-run", action="store_true", help="Solo muestra los comandos")
    args = parser.parse_args()
    backlog = json.loads(BACKLOG.read_text(encoding="utf-8"))
    owner = args.repo.split("/")[0]
    for nombre, (color, descripcion) in ETIQUETAS.items():
        gh(
            "label",
            "create",
            nombre,
            "--repo",
            args.repo,
            "--color",
            color,
            "--description",
            descripcion,
            "--force",
            dry=args.dry_run,
        )
    # Idempotente: si el issue ya existe (misma historia), se reutiliza en vez de duplicarlo.
    existentes = {}
    if not args.dry_run:
        listado = gh(
            "issue",
            "list",
            "--repo",
            args.repo,
            "--state",
            "all",
            "--limit",
            "200",
            "--json",
            "title,url,state",
            dry=False,
        )
        existentes = {i["title"].split("]")[0] + "]": i for i in json.loads(listado or "[]")}
    for h in backlog["historias"]:
        titulo = f"[{h['id']}] {h['titulo']} ({h['sp']} SP)"
        previo = existentes.get(f"[{h['id']}]")
        if previo:
            url = previo["url"]
            print(f"= {h['id']} ya existe: se actualizan título, cuerpo y etiqueta ({url})")
            gh(
                "issue",
                "edit",
                url,
                "--title",
                titulo,
                "--body",
                cuerpo(h),
                "--add-label",
                h["etiqueta"],
                dry=args.dry_run,
            )
        else:
            url = gh(
                "issue",
                "create",
                "--repo",
                args.repo,
                "--title",
                titulo,
                "--body",
                cuerpo(h),
                "--label",
                h["etiqueta"],
                dry=args.dry_run,
            )
        if args.project:
            gh("project", "item-add", str(args.project), "--owner", owner, "--url", url, dry=args.dry_run)
        if h["estado"] == "Done" and (not previo or previo["state"] == "OPEN"):
            gh("issue", "close", url, "--reason", "completed", dry=args.dry_run)
    total = sum(h["sp"] for h in backlog["historias"] if h["estado"] != "Done")
    print(f"\n{len(backlog['historias'])} historias · {total} SP en el sprint.")
    print("En el tablero: columnas To Do · In Progress · Review / PR · Done (WIP 1 por integrante).")


if __name__ == "__main__":
    main()

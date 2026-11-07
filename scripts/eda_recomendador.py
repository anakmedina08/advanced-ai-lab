"""EDA del dataset sintético: cifras para el documento M2 y figuras en docs/gestion/figuras/."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sb_asistente.controller.recomendador import comparar_baselines, leer_tablas
from sb_asistente.model.recomendador.catalogo import POR_ID

INK, MUTED, GRID, BAR = "#1f2933", "#52606d", "#e4e7eb", "#2563eb"
OUT = Path("docs/gestion/figuras")


def estilo(ax):
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=8, length=0)
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def main():
    t = leer_tablas()
    cl, pz, si = t["clientes"], t["polizas"], t["siniestros"]
    por_cliente = pz.groupby("cliente_id").size()
    penetracion = (pz.groupby("product_id")["cliente_id"].nunique() / len(cl)).sort_values()
    resumen = {
        "clientes": len(cl),
        "productos": len(t["productos"]),
        "polizas": len(pz),
        "siniestros": len(si),
        "polizas_por_cliente_media": round(por_cliente.mean(), 2),
        "clientes_con_2_o_mas": int((por_cliente >= 2).sum()),
        "dist_polizas_por_cliente": por_cliente.value_counts().sort_index().to_dict(),
        "pct_canceladas": round((pz["estado"] == "cancelada").mean() * 100, 1),
        "nulos_fecha_fin_pct": round(pz["fecha_fin"].isna().mean() * 100, 1),
        "nulos_otras_columnas": int(
            sum(df.drop(columns=["fecha_fin"], errors="ignore").isna().sum().sum() for df in t.values())
        ),
        "penetracion_top3": {
            POR_ID[p].nombre: round(v * 100, 1)
            for p, v in penetracion.sort_values(ascending=False).head(3).items()
        },
        "penetracion_min": {POR_ID[p].nombre: round(v * 100, 1) for p, v in penetracion.head(2).items()},
        "baselines": comparar_baselines(t),
        "rango_fechas": [str(pz["fecha_inicio"].min().date()), str(pz["fecha_inicio"].max().date())],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT.parent / "eda.json").write_text(
        json.dumps(resumen, indent=2, ensure_ascii=False, default=int) + "\n", encoding="utf-8"
    )

    fig, (a, b) = plt.subplots(1, 2, figsize=(9.2, 3.6), gridspec_kw={"width_ratios": [1.9, 1]})
    nombres = [f"{p} · {POR_ID[p].nombre}" for p in penetracion.index]
    a.barh(nombres, penetracion.values * 100, color=BAR, height=0.62)
    a.set_xlabel("% de clientes con el producto", color=MUTED, fontsize=8)
    a.set_title("Penetración por producto", loc="left", color=INK, fontsize=10, fontweight="bold")
    estilo(a)
    a.tick_params(axis="y", labelsize=7)
    dist = por_cliente.value_counts().sort_index()
    b.bar(dist.index.astype(str), dist.values / len(cl) * 100, color=BAR, width=0.62)
    b.set_xlabel("n.º de pólizas (eje y: % de clientes)", color=MUTED, fontsize=8)
    b.set_title("Pólizas por cliente", loc="left", color=INK, fontsize=10, fontweight="bold")
    estilo(b)
    b.grid(axis="x", visible=False)
    b.grid(axis="y", color=GRID, linewidth=0.6)
    fig.tight_layout()
    fig.savefig(OUT / "eda.png", dpi=200)
    print(json.dumps(resumen, indent=2, ensure_ascii=False, default=int))


if __name__ == "__main__":
    main()

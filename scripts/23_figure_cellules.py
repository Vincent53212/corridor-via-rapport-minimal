"""Étape 23 — Figure du rapport : carte des cellules voie × propriétaire (cœur).

Chaque inter-gare du cœur du corridor est tracée dans la couleur de sa cellule
du 2×2 (palette catégorielle validée CVD : bleu double-CN, vermillon simple-CN,
vert simple-VIA) ; les paires exclues (blocs urbains, ponts, chevauchements)
sont en gris neutre. La légende porte la marge médiane mesurée par cellule.
Sortie : livrables/figure_cellules.png (300 dpi, pour insertion pandoc).
"""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

from utils import INTERMEDIATES, DELIVERABLES

COLORS = {"double-CN": "#0072B2", "simple-CN": "#D55E00", "simple-VIA": "#009E73"}
GREY = "#B0B0B0"
CORE = ["MTL-QC", "MTL-Ott", "Ott-TO", "MTL-TO"]
CITIES = {"Montréal": (-73.567, 45.5), "Québec": (-71.22, 46.81),
          "Ottawa": (-75.65, 45.42), "Toronto": (-79.38, 43.65),
          "Kingston": (-76.49, 44.23), "Drummondville": (-72.48, 45.88)}


def main() -> None:
    m = pd.read_csv(DELIVERABLES / "marges_par_intergare.csv", sep=";", encoding="utf-8-sig")
    m = m[m.region == "coeur"]
    gj = json.load(open(INTERMEDIATES / "corridor_matched.geojson", encoding="utf-8"))
    lines = {f["properties"]["troncon_id"]: f["geometry"]["coordinates"]
             for f in gj["features"]
             if f["geometry"]["type"] == "LineString" and f["properties"].get("troncon_id")}

    # abscisse cumulée (km) le long de chaque tracé pour découper par paire
    import math
    def cum_km(coords):
        s = [0.0]
        for (x1, y1), (x2, y2) in zip(coords, coords[1:]):
            dx = (x2 - x1) * 111.32 * math.cos(math.radians((y1 + y2) / 2))
            dy = (y2 - y1) * 110.57
            s.append(s[-1] + math.hypot(dx, dy))
        return s

    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=300)
    for t in CORE:
        coords = lines[t]
        s = cum_km(coords)
        total = s[-1]
        for _, r in m[m.troncon == t].iterrows():
            k0, k1 = r.km_debut / (m[m.troncon == t].km_fin.max()) * total, \
                     r.km_fin / (m[m.troncon == t].km_fin.max()) * total
            seg = [(x, y) for (x, y), sk in zip(coords, s) if k0 - 2 <= sk <= k1 + 2]
            if len(seg) < 2:
                continue
            excl = isinstance(r.exclue_du_2x2, str) and r.exclue_du_2x2 != ""
            c = GREY if excl or r.cellule not in COLORS else COLORS[r.cellule]
            xs, ys = zip(*seg)
            ax.plot(xs, ys, color=c, linewidth=2.6 if not excl else 1.6,
                    solid_capstyle="round", zorder=3 if not excl else 2)

    for name, (x, y) in CITIES.items():
        ax.plot(x, y, "o", color="#333333", markersize=4, zorder=5)
        ax.annotate(name, (x, y), textcoords="offset points", xytext=(5, 5),
                    fontsize=8, color="#333333")

    med = m[(m.exclue_du_2x2.isna()) & (m.cellule.isin(COLORS))].groupby("cellule").marge_pct.median()
    handles = [Line2D([], [], color=COLORS[c], lw=3,
                      label=f"{c} : marge médiane {med[c]:.0f} %".replace(".", ","))
               for c in ["double-CN", "simple-CN", "simple-VIA"]] + \
              [Line2D([], [], color=GREY, lw=2, label="hors 2×2 (urbain, ponts, frontières)")]
    ax.legend(handles=handles, loc="lower right", fontsize=8, frameon=False)
    ax.set_title("Le 2×2 du corridor : marge d'horaire par cellule voie × propriétaire",
                 fontsize=11, loc="left")
    ax.set_axis_off()
    ax.set_aspect(1.4)
    fig.tight_layout()
    out = DELIVERABLES / "figure_cellules.png"
    fig.savefig(out, bbox_inches="tight")
    print(f"Écrit {out.name}")


if __name__ == "__main__":
    main()

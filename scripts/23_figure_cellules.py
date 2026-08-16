"""Étape 23 — Figure du rapport : carte des cellules voie × propriétaire (cœur).

Chaque inter-gare du cœur du corridor est tracée dans la couleur de sa cellule
du 2×2 ; les paires exclues (blocs urbains, ponts, chevauchements) sont en grège
neutre. La légende porte la marge médiane mesurée par cellule.
Sortie : livrables/figure_cellules.png (300 dpi).

Codage des couleurs : identite/identite.json, section `cellules`. La TEINTE porte
le propriétaire (acier pour le CN, brique pour VIA), la VALEUR porte le nombre de
voies (foncé pour la double, clair pour la simple). Les six paires de figurés,
grège des exclus compris, se distinguent d'au moins 17 de dE2000 sous protanopie,
deutéranopie et tritanopie : c'est ce que vérifie 27_verif_identite.py.
"""
from __future__ import annotations

import json
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

from identite import (CELLULES, PAPIER, appliquer_rcparams, police_mono,
                      police_titre)
from utils import INTERMEDIATES, DELIVERABLES

appliquer_rcparams(matplotlib)

COLORS = {c: CELLULES[c] for c in ("double-CN", "simple-CN", "simple-VIA")}
GREY = CELLULES["hors"]
CORE = ["MTL-QC", "MTL-Ott", "Ott-TO", "MTL-TO"]
CITIES = {"Montréal": (-73.567, 45.5), "Québec": (-71.22, 46.81),
          "Ottawa": (-75.65, 45.42), "Toronto": (-79.38, 43.65),
          "Kingston": (-76.49, 44.23), "Drummondville": (-72.48, 45.88)}
POLES = {"Montréal", "Québec", "Ottawa", "Toronto"}


def main() -> None:
    m = pd.read_csv(DELIVERABLES / "marges_par_intergare.csv", sep=";", encoding="utf-8-sig")
    m = m[m.region == "coeur"]
    gj = json.load(open(INTERMEDIATES / "corridor_matched.geojson", encoding="utf-8"))
    lines = {f["properties"]["troncon_id"]: f["geometry"]["coordinates"]
             for f in gj["features"]
             if f["geometry"]["type"] == "LineString" and f["properties"].get("troncon_id")}

    # abscisse cumulée (km) le long de chaque tracé pour découper par paire
    def cum_km(coords):
        s = [0.0]
        for (x1, y1), (x2, y2) in zip(coords, coords[1:]):
            dx = (x2 - x1) * 111.32 * math.cos(math.radians((y1 + y2) / 2))
            dy = (y2 - y1) * 110.57
            s.append(s[-1] + math.hypot(dx, dy))
        return s

    fig, ax = plt.subplots(figsize=(9, 5.0), dpi=300)
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
            ax.plot(xs, ys, color=c, linewidth=3.0 if not excl else 1.7,
                    solid_capstyle="round", zorder=3 if not excl else 2)

    for name, (x, y) in CITIES.items():
        pole = name in POLES
        ax.plot(x, y, "o", color=PAPIER["encre"], markersize=5.2 if pole else 3.4,
                markeredgecolor=PAPIER["fond"], markeredgewidth=1.1, zorder=5)
        ax.annotate(name, (x, y), textcoords="offset points", xytext=(7, 5),
                    fontsize=7.6 if pole else 6.8, zorder=6,
                    color=PAPIER["encre"] if pole else PAPIER["encre_pale"],
                    **police_mono("semibold" if pole else "normal"))

    # Les médianes sont LUES dans la synthèse du 2×2, elles ne sont pas
    # recalculées ici. Recalculées sur marges_par_intergare, elles comptaient
    # deux fois les paires de Montréal-Toronto, qui est la concaténation de
    # Montréal-Ottawa et d'Ottawa-Toronto : la légende annonçait 40, 68 et 34
    # là où la mesure donne 37, 68 et 34, et la figure contredisait le tableau
    # de la même page.
    syn = pd.read_csv(DELIVERABLES / "marges_2x2_synthese.csv", sep=";",
                      encoding="utf-8-sig")
    med = syn[syn.region == "coeur"].set_index("cellule").mediane
    handles = [Line2D([], [], color=COLORS[c], lw=3.4,
                      label=f"{c}   marge médiane {med[c]:.0f} %".replace(".", ","))
               for c in ["double-CN", "simple-CN", "simple-VIA"]] + \
              [Line2D([], [], color=GREY, lw=2,
                      label="hors 2×2   urbain, ponts, frontières")]
    leg = ax.legend(handles=handles, loc="lower right", fontsize=7.4, frameon=False,
                    handlelength=2.2, labelspacing=0.7, borderpad=0.9)
    for txt in leg.get_texts():
        txt.set_color(PAPIER["encre_douce"])
        txt.set_fontfamily(police_mono()["fontfamily"])

    ax.set_axis_off()
    ax.set_aspect(1.4)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.text(0.008, 0.985, "Le 2×2 du corridor : marge d'horaire par cellule "
                           "voie × propriétaire",
             fontsize=12.5, ha="left", va="top", color=PAPIER["encre"],
             **police_titre(600))
    fig.text(0.008, 0.928, "Teinte : le propriétaire.  Valeur : le nombre de voies.",
             fontsize=7.6, ha="left", va="top", color=PAPIER["encre_pale"],
             **police_mono())
    out = DELIVERABLES / "figure_cellules.png"
    fig.savefig(out, bbox_inches="tight", facecolor=PAPIER["fond"])
    print(f"Écrit {out.name}")


if __name__ == "__main__":
    main()

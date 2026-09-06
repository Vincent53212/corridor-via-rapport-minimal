"""Étape 35 — Figures : gros plan sur les zones urbaines de Montréal et de Québec.

Deux cartes (livrables/figure_zoom_montreal.png, figure_zoom_quebec.png) qui
montrent, sur la géométrie publiée :
  - le tracé VIA coloré selon la vitesse que la courbe permet au train
    pendulaire (moteur interne S2, plafond 201 km/h), palette `vitesse` de la charte ;
  - le bloc urbain FIGÉ à l'horaire (voile grège), borné par les gares GTFS qui
    servent d'ancre (script 21 : URBAN_GTFS_BLOCKS) ;
  - les gares, et un cartouche : longueur du bloc, minutes GTFS actuelles,
    vitesse moyenne réelle, et minutes « fluides » que la géométrie seule
    permettrait (∫ dx / min(v_courbe, 201)).
Les autres voies ferrées OSM sont en filigrane pour situer le lecteur.
"""
from __future__ import annotations

import json
import math
import pickle

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from identite import (ACCENT, PAPIER, VITESSE, VITESSE_COULEURS,
                      appliquer_rcparams, couleur_pour_vitesse, police_mono,
                      police_titre)
from utils import INTERMEDIATES, DELIVERABLES

appliquer_rcparams(matplotlib)

PLAFOND = 201.0
VOILE = "#CFC7B2"        # grège du voile urbain (entre sable et filet_fort)

# (nom fichier, titre, emprise lon/lat, tronçons à tracer, blocs (tronçon, km0, km1,
#  libellé, minutes GTFS), gares à nommer (nom, dx, dy en points))
CARTES = [
    dict(
        fichier="figure_zoom_montreal.png",
        titre="Montréal : deux sorties, deux blocs urbains figés",
        emprise=(-73.80, -73.44, 45.40, 45.57),
        troncons=["MTL-Ott", "MTL-QC"],
        blocs=[("MTL-Ott", 0.0, 17.79, "Central ↔ Dorval", 23.5),
               ("MTL-QC", 0.0, 5.50, "Central ↔ pont Victoria (culée sud)", 11.8)],
        gares={"Montréal": (6, 7), "Dorval": (-4, -12), "Saint-Lambert": (6, -11),
               "Aéroport Montréal Pierre-Elliott Trudeau": (-4, 8)},
        repere=[("pont Victoria", -73.528, 45.478)],
        legende="lower left", cartouche=(0.985, 0.975, "right"),
    ),
    dict(
        fichier="figure_zoom_quebec.png",
        titre="Québec : un seul bloc, de Charny à la gare du Palais",
        emprise=(-71.42, -71.08, 46.68, 46.86),
        troncons=["MTL-QC"],
        blocs=[("MTL-QC", 245.04, 269.85, "Charny ↔ Québec (pont de Québec)", 33.0)],
        gares={"Charny": (8, -12), "Sainte-Foy": (6, 9), "Québec": (6, 6)},
        repere=[("pont de Québec", -71.283, 46.738)],
        legende="lower right", cartouche=(0.015, 0.975, "left"),
    ),
]


def dans(emprise, x, y, marge=0.02):
    x0, x1, y0, y1 = emprise
    return x0 - marge <= x <= x1 + marge and y0 - marge <= y <= y1 + marge


def main() -> None:
    seg = json.load(open(INTERMEDIATES / "segments_publies.geojson", encoding="utf-8"))
    gtfs = json.load(open(INTERMEDIATES / "corridor_gtfs.geojson", encoding="utf-8"))
    gares = [(f["properties"]["stop_name"], f["properties"]["troncon_id"],
              f["properties"]["km_along_segment"], *f["geometry"]["coordinates"])
             for f in gtfs["features"] if f["geometry"]["type"] == "Point"]
    G = pickle.load(open(INTERMEDIATES / "osm_rails_graph.pkl", "rb"))

    for carte in CARTES:
        x0, x1, y0, y1 = carte["emprise"]
        fig, ax = plt.subplots(figsize=(8.6, 5.6), dpi=300)

        # --- filigrane : toutes les voies OSM de l'emprise
        for _, _, d in G.edges(data=True):
            c = d.get("coords")
            if not c or not any(dans(carte["emprise"], lon, lat) for lat, lon in c[::4]):
                continue
            ax.plot([p[1] for p in c], [p[0] for p in c], color=PAPIER["filet_fort"],
                    linewidth=0.55, zorder=1, solid_capstyle="round")

        # --- voile des blocs urbains + tracé coloré par vitesse pendulaire
        cartouches = []
        for t in carte["troncons"]:
            feats = [f for f in seg["features"] if f["properties"]["troncon_id"] == t]
            blocs_t = [b for b in carte["blocs"] if b[0] == t]
            for f in feats:
                p = f["properties"]
                coords = f["geometry"]["coordinates"]
                if f["geometry"]["type"] == "MultiLineString":
                    coords = [pt for part in coords for pt in part]
                if not any(dans(carte["emprise"], x, y, 0.05) for x, y in coords[::3]):
                    continue
                xs, ys = zip(*coords)
                v = min(p["vmax_S2_kmh"], PLAFOND)
                L = max(p["km_fin"] - p["km_debut"], 1e-6)
                en_bloc = any((min(p["km_fin"], b[2]) - max(p["km_debut"], b[1])) / L > 0.5
                              for b in blocs_t)
                if en_bloc:
                    ax.plot(xs, ys, color=VOILE, linewidth=11, alpha=0.75, zorder=2,
                            solid_capstyle="round")
                ax.plot(xs, ys, color=couleur_pour_vitesse(v), linewidth=2.6,
                        zorder=4, solid_capstyle="round")

            # minutes « fluides » de la géométrie seule dans chaque bloc
            for (_, k0, k1, lib, mn) in blocs_t:
                fl = 0.0
                for f in feats:
                    p = f["properties"]
                    lo, hi = max(p["km_debut"], k0), min(p["km_fin"], k1)
                    if hi > lo:
                        fl += (hi - lo) / min(p["vmax_S2_kmh"], PLAFOND) * 60
                L = k1 - k0
                cartouches.append((lib, L, mn, L / mn * 60, fl))

        # --- gares
        for nom, t, km, x, y in gares:
            if t not in carte["troncons"] or not dans(carte["emprise"], x, y, 0):
                continue
            if nom not in carte["gares"]:
                continue
            ax.plot(x, y, "o", color=PAPIER["encre"], markersize=5.0,
                    markeredgecolor=PAPIER["fond"], markeredgewidth=1.1, zorder=6)
            dx, dy = carte["gares"][nom]
            lab = nom if not nom.startswith("Aéroport") else "Aéroport (Dorval)"
            ax.annotate(lab, (x, y), textcoords="offset points", xytext=(dx, dy),
                        fontsize=7.4, color=PAPIER["encre"], zorder=7,
                        ha="right" if dx < 0 else "left", **police_mono("semibold"))
        for lab, x, y in carte["repere"]:
            ax.annotate(lab, (x, y), fontsize=6.6, color=PAPIER["encre_pale"],
                        ha="center", zorder=7, style="italic", **police_mono())

        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_aspect(1 / math.cos(math.radians((y0 + y1) / 2)))
        ax.set_axis_off()

        # --- légende vitesse + voile
        handles = [Line2D([], [], color=VITESSE_COULEURS[p["cle"]], lw=2.8,
                          label=p["libelle"].replace("300 km/h et plus", "201 km/h (plafond)"))
                   for p in VITESSE if p["cle"] in ("sous_100", "100_160", "160_200", "200_250")]
        handles[-1].set_label("200 à 201 km/h (plafond)")
        handles.append(Patch(facecolor=VOILE, edgecolor="none", alpha=0.75,
                             label="bloc urbain figé à l'horaire (scénario 1)"))
        handles.append(Line2D([], [], color=PAPIER["filet_fort"], lw=1.0,
                              label="autres voies ferrées (OSM)"))
        leg = ax.legend(handles=handles, loc=carte["legende"], fontsize=6.8, frameon=True,
                        bbox_to_anchor=carte.get("legende_bbox"),
                        facecolor=PAPIER["fond_bloc"], edgecolor=PAPIER["filet"],
                        handlelength=2.0, labelspacing=0.55, borderpad=0.8,
                        title="Vitesse permise par la courbe, train pendulaire")
        leg.get_title().set_fontsize(6.8)
        leg.get_title().set_color(PAPIER["encre_douce"])
        for txt in leg.get_texts():
            txt.set_color(PAPIER["encre_douce"])
            txt.set_fontfamily(police_mono()["fontfamily"])

        # --- cartouche des blocs
        lignes = []
        for lib, L, mn, vmoy, fl in cartouches:
            lignes.append(f"{lib}\n"
                          f"   {L:.1f} km · horaire {mn:.0f} min · {vmoy:.0f} km/h de moyenne\n"
                          f"   géométrie seule, sans arrêt : {fl:.0f} min"
                          .replace(".", ","))
        cx, cy, cha = carte["cartouche"]
        ax.text(cx, cy, "\n".join(lignes), transform=ax.transAxes, fontsize=6.6,
                ha=cha, va="top", color=PAPIER["encre_douce"], zorder=8,
                linespacing=1.45, **police_mono(),
                bbox=dict(boxstyle="round,pad=0.6", facecolor=PAPIER["fond_bloc"],
                          edgecolor=PAPIER["filet"]))

        fig.tight_layout(rect=(0, 0, 1, 0.905))
        fig.text(0.008, 0.985, carte["titre"], fontsize=12.5, ha="left", va="top",
                 color=PAPIER["encre"], **police_titre(600))
        fig.text(0.008, 0.930,
                 "Le voile marque ce que le scénario 1 laisse à l'horaire actuel ; "
                 "les scénarios 2 et 3 y appliquent le calcul de vitesse.",
                 fontsize=7.4, ha="left", va="top", color=PAPIER["encre_pale"],
                 **police_mono())
        out = DELIVERABLES / carte["fichier"]
        fig.savefig(out, bbox_inches="tight", facecolor=PAPIER["fond"])
        plt.close(fig)
        print(f"Écrit {out.name}")
        for lib, L, mn, vmoy, fl in cartouches:
            print(f"  {lib}: {L:.1f} km, GTFS {mn} min ({vmoy:.0f} km/h), fluide {fl:.1f} min")


if __name__ == "__main__":
    main()

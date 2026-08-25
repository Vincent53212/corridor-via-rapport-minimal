"""Étape 24 — Figure : le train contre l'auto, quatre trajets (remodelage 24 août).

Cinq barres par trajet : l'auto (repère évidé), l'horaire VIA d'aujourd'hui,
puis les trois scénarios publiés (échelle du rapport, moteur pendulaire interne
S2 plafonné 201 km/h / 125 mi/h — remodelage 2026-08-24) :
  scénario 1 = temps_scenario_1.csv (blocs urbains figés)
  scénario 2 = temps_scenario_2.csv (zones urbaines modernisées)
  scénario 3 = temps_scenario_3.csv (+ courbes corrigées au doublement)

Temps publiés EN POINT : T_base × 1,10 (décision 2026-08-24 : marge unique de
10 %, légèrement plus conservatrice que la médiane des règles publiées et
alignée sur la majoration de 10 % du référent britannique, rfli2026tpr ; l'UIC
donne d'ailleurs 9 % à 200 km/h). Plus de fourchette : la marge MESURÉE du
corridor reste un diagnostic de cohabitation, ailleurs dans le rapport.

Repère ALTO : trait vertical pointillé au temps annoncé (altotrain2026faq ;
Montréal-Toronto 3 h confirmé par le premier ministre, pmcanada2025alto).

Sortie : livrables/figure_vs_auto.png.
Mise en forme : identite/identite.json (voir scripts/identite.py)."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from utils import DELIVERABLES
import identite
from identite import PAPIER, SCENARIOS, appliquer_rcparams, police_mono, police_titre

appliquer_rcparams(matplotlib)

def hm(m):
    """Minutes → « h hh mm ». Arrondir AVANT de séparer : sinon 239,98 min
    s'affiche « 3 h 60 » au lieu de « 4 h 00 »."""
    total = int(round(m))
    return f"{total // 60} h {total % 60:02d}"

def pct(m, auto): return int(m / auto * 100 + 0.5)

MARGE = 1.10   # point unique (décision 2026-08-24), voir docstring

import csv as _csv
from pathlib import Path as _Path

_LIV = _Path(__file__).resolve().parent.parent / "livrables"

def _lire(nom):
    t = {}
    with open(_LIV / nom, encoding="utf-8-sig", newline="") as f:
        for r in _csv.DictReader(f, delimiter=";"):
            t[(r["troncon"], r["scenario"], int(r["bande_kmh"]))] = r
    return t

_T1 = _lire("temps_scenario_1.csv")
_T2 = _lire("temps_scenario_2.csv")
_T3 = _lire("temps_scenario_3.csv")

def _pt(table, troncon):
    """Temps publié (point) : T_base(pendulaire, 201) × marge."""
    return float(table[(troncon, "pendulaire", 201)]["tbase_sans_marge_min"]) * MARGE

def _horaire(troncon):
    return float(_T1[(troncon, "base", 160)]["t_horaire_actuel_min"])

# Le temps en auto reste une hypothèse externe (ordre de grandeur, annoncé
# comme approximatif) : il ne vient pas du pipeline. Vérifiés 2026-08-17.
AUTO_MIN = {"MTL-QC": 170, "MTL-TO": 330, "MTL-Ott": 140, "Ott-TO": 260}
# Temps ALTO annoncés (altotrain2026faq ; MTL-TO aussi pmcanada2025alto).
# Qc-Mtl ~1 h 30 ; Mtl-TO ~3 h ; Mtl-Ott ~1 h ; Ott-TO ~2 h.
ALTO_MIN = {"MTL-QC": 90, "MTL-TO": 180, "MTL-Ott": 60, "Ott-TO": 120}

S1_LBL, S2_LBL, S3_LBL = "Scénario 1", "Scénario 2", "Scénario 3"

def panel(troncon, titre, repere):
    return (troncon, titre, repere, AUTO_MIN[troncon], [
        ("VIA aujourd'hui", _horaire(troncon)),
        (S1_LBL, _pt(_T1, troncon)),
        (S2_LBL, _pt(_T2, troncon)),
        (S3_LBL, _pt(_T3, troncon))])

DATA = [
 panel("MTL-QC",  "Montréal-Québec",  "auto ≈ 2 h 50, approx."),
 panel("MTL-TO",  "Montréal-Toronto", "auto ≈ 5 h 30, approx."),
 panel("MTL-Ott", "Montréal-Ottawa",  "auto ≈ 2 h 20, approx."),
 panel("Ott-TO",  "Ottawa-Toronto",   "auto ≈ 4 h 20, approx."),
]
COLS = {"auto": SCENARIOS["auto"], "VIA aujourd'hui": SCENARIOS["actuel"],
        S1_LBL: SCENARIOS["S1"], S2_LBL: SCENARIOS["S2"], S3_LBL: SCENARIOS["S3"]}

fig, axes = plt.subplots(2, 2, figsize=(11, 7.6), dpi=300)
for ax, (troncon, title, repere, auto, rows) in zip(axes.flat, DATA):
    labels = ["Auto"] + [r[0] for r in rows]
    vals = [auto] + [v for _, v in rows]
    cols = [COLS["auto"]] + [COLS[r[0]] for r in rows]
    y = range(len(labels))[::-1]
    # L'auto est un REPÈRE, pas une mesure de l'étude : sa barre est évidée.
    ax.barh(list(y)[:1], vals[:1], height=0.58, facecolor="none",
            edgecolor=COLS["auto"], linewidth=1.3)
    ax.barh(list(y)[1:], vals[1:], color=cols[1:], height=0.58)
    for yi, (lab, v) in zip(y, zip(labels, vals)):
        if lab == "Auto":
            txt = hm(v) + "  (repère)"
        else:
            txt = hm(v) + f"  ({pct(v, auto)} % de l'auto)"
        ax.text(v + 7, yi, txt, va="center", fontsize=7.6,
                color=PAPIER["encre_douce"], **police_mono())
    # Repère ALTO : trait pointillé vertical au temps annoncé par le promoteur.
    alto = ALTO_MIN[troncon]
    ax.axvline(alto, color=PAPIER["encre_pale"], lw=1.0, ls=(0, (4, 3)),
               zorder=1)
    ax.text(alto, max(y) + 0.78, f"ALTO annoncé ~{hm(alto)}", ha="center",
            fontsize=6.8, color=PAPIER["encre_pale"], zorder=3,
            bbox=dict(facecolor=PAPIER["fond"], edgecolor="none", pad=1.2),
            **police_mono())
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=7.8, color=PAPIER["encre_douce"],
                       **police_mono())
    ax.tick_params(axis="y", length=0, pad=6)
    ax.set_xlim(0, max(vals) * 2.05)
    ax.set_ylim(-0.6, max(y) + 1.25)
    ax.set_xticks([])
    ax.set_title(title, fontsize=11, loc="left", color=PAPIER["encre"],
                 pad=15, **police_titre(600))
    ax.text(0, 1.015, repere, transform=ax.transAxes, fontsize=7.2,
            color=PAPIER["encre_pale"], **police_mono())
    for s in ax.spines.values(): s.set_visible(False)
fig.tight_layout(rect=(0, 0.065, 1, 0.885))
fig.text(0.008, 0.978, "Le train contre l'auto : temps de parcours, marge de 10 % incluse",
         fontsize=12.5, ha="left", va="top", color=PAPIER["encre"],
         **police_titre(600))
fig.text(0.008, 0.922,
         "Scénario 1 : train pendulaire · 2 : + zones urbaines modernisées · "
         "3 : + courbes corrigées au doublement",
         fontsize=7.6, ha="left", va="top", color=PAPIER["encre_pale"],
         **police_mono())
fig.text(0.008, 0.012,
         "Marge de 10 % sur le temps de base : légèrement au-dessus de la médiane des "
         "règles publiées (8 %) et alignée sur le référent britannique. Repère ALTO : "
         "temps annoncés par le promoteur (le 3 h Montréal-Toronto est un engagement "
         "gouvernemental).",
         fontsize=7.0, ha="left", va="bottom", color=PAPIER["encre_pale"],
         **police_mono())
fig.savefig(DELIVERABLES / "figure_vs_auto.png", bbox_inches="tight",
            facecolor=PAPIER["fond"])
print("Écrit figure_vs_auto.png")
for troncon, title, _, auto, rows in DATA:
    ligne = " · ".join(f"{lab} {hm(v)} ({pct(v, auto)} %)" for lab, v in rows)
    print(f"  {title:<18} auto {hm(auto)} · {ligne} · ALTO {hm(ALTO_MIN[troncon])}")

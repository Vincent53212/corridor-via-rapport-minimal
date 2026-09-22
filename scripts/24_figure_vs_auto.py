"""Étape 24 — Figures : le train contre l'auto, UNE IMAGE PAR TRAJET (JPEG).

Remodelage du 3 septembre (décision Vincent) : la planche 2×2 était illisible
une fois réduite à la largeur de la page ; chaque trajet a maintenant sa figure
pleine largeur, en JPEG : livrables/figure_vs_auto_<trajet>.jpg.

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

Sorties : livrables/figure_vs_auto_{montreal_quebec,montreal_toronto,
          montreal_ottawa,ottawa_toronto}.jpg
Mise en forme : identite/identite.json (voir scripts/identite.py)."""
import csv as _csv
from pathlib import Path as _Path

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from utils import DELIVERABLES
from identite import PAPIER, SCENARIOS, appliquer_rcparams, police_mono, police_titre

appliquer_rcparams(matplotlib)

def hm(m):
    """Minutes → « h hh mm ». Arrondir AVANT de séparer : sinon 239,98 min
    s'affiche « 3 h 60 » au lieu de « 4 h 00 »."""
    total = int(round(m))
    return f"{total // 60} h {total % 60:02d}"

def pct(m, auto): return int(m / auto * 100 + 0.5)

MARGE = 1.10   # point unique (décision 2026-08-24), voir docstring

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

# Un seul scénario publié depuis la réécriture du 14 sept. 2026 : l'emprise
# optimisée (moteur interne S2 : pendulaire, dévers, PN, signalisation, zones
# urbaines modernisées). Les temps des scénarios 1 et 3 restent dans les CSV.
OPT_LBL = "Emprise optimisée"

def panel(troncon, cle, titre, repere):
    return (troncon, cle, titre, repere, AUTO_MIN[troncon], [
        ("VIA aujourd'hui", _horaire(troncon)),
        (OPT_LBL, _pt(_T2, troncon))])

DATA = [
 panel("MTL-QC",  "montreal_quebec",  "Montréal-Québec",  "auto ≈ 2 h 50, approx."),
 panel("MTL-TO",  "montreal_toronto", "Montréal-Toronto", "auto ≈ 5 h 30, approx."),
 panel("MTL-Ott", "montreal_ottawa",  "Montréal-Ottawa",  "auto ≈ 2 h 20, approx."),
 panel("Ott-TO",  "ottawa_toronto",   "Ottawa-Toronto",   "auto ≈ 4 h 20, approx."),
]
COLS = {"auto": SCENARIOS["auto"], "VIA aujourd'hui": SCENARIOS["actuel"],
        OPT_LBL: SCENARIOS["S2"]}

# Une figure par trajet : 7,4 po de large (la justification de la page est
# 6,8 po), 250 dpi, JPEG. Les corps de texte sont dimensionnés pour cette
# largeur d'impression, pas pour une planche réduite.
for troncon, cle, title, repere, auto, rows in DATA:
    fig, ax = plt.subplots(figsize=(7.4, 2.9), dpi=250)
    labels = ["Auto"] + [r[0] for r in rows]
    vals = [auto] + [v for _, v in rows]
    cols = [COLS["auto"]] + [COLS[r[0]] for r in rows]
    y = list(range(len(labels)))[::-1]
    # L'auto est un REPÈRE, pas une mesure de l'étude : sa barre est évidée.
    ax.barh(y[:1], vals[:1], height=0.62, facecolor="none",
            edgecolor=COLS["auto"], linewidth=1.5)
    ax.barh(y[1:], vals[1:], color=cols[1:], height=0.62)
    for yi, lab, v in zip(y, labels, vals):
        txt = hm(v) + ("  (repère)" if lab == "Auto" else f"  ({pct(v, auto)} % de l'auto)")
        ax.text(v + max(vals) * 0.012, yi, txt, va="center", fontsize=9.4,
                color=PAPIER["encre_douce"], **police_mono())
    # Repère ALTO : trait pointillé vertical au temps annoncé par le promoteur.
    alto = ALTO_MIN[troncon]
    ax.axvline(alto, color=PAPIER["encre_pale"], lw=1.1, ls=(0, (4, 3)), zorder=1)
    ax.text(alto, max(y) + 0.82, f"ALTO annoncé ~{hm(alto)}", ha="center",
            fontsize=8.4, color=PAPIER["encre_pale"], zorder=3,
            bbox=dict(facecolor=PAPIER["fond"], edgecolor="none", pad=1.4),
            **police_mono())
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9.6, color=PAPIER["encre_douce"],
                       **police_mono())
    ax.tick_params(axis="y", length=0, pad=7)
    ax.set_xlim(0, max(vals) * 1.62)
    ax.set_ylim(-0.6, max(y) + 1.3)
    ax.set_xticks([])
    for s in ax.spines.values(): s.set_visible(False)

    fig.tight_layout(rect=(0, 0.075, 1, 0.845))
    fig.text(0.008, 0.985, f"{title} : le train contre l'auto, marge de 10 % incluse",
             fontsize=13.5, ha="left", va="top", color=PAPIER["encre"],
             **police_titre(600))
    fig.text(0.008, 0.905,
             f"{repere}  ·  Emprise optimisée : train pendulaire, dévers de 5 po, "
             "passages sécurisés, contrôle en cabine, voie doublée, zones urbaines modernisées",
             fontsize=8.0, ha="left", va="top", color=PAPIER["encre_pale"],
             **police_mono())
    fig.text(0.008, 0.012,
             "Marge de 10 % sur le temps de base (médiane des règles publiées : 8 % ; "
             "référent britannique : 10 %). Repère ALTO : temps annoncé par le promoteur.",
             fontsize=7.6, ha="left", va="bottom", color=PAPIER["encre_pale"],
             **police_mono())
    out = DELIVERABLES / f"figure_vs_auto_{cle}.jpg"
    fig.savefig(out, bbox_inches="tight", facecolor=PAPIER["fond"],
                format="jpg", pil_kwargs={"quality": 92})
    plt.close(fig)
    print(f"Écrit {out.name}")

for troncon, _cle, title, _, auto, rows in DATA:
    ligne = " · ".join(f"{lab} {hm(v)} ({pct(v, auto)} %)" for lab, v in rows)
    print(f"  {title:<18} auto {hm(auto)} · {ligne} · ALTO {hm(ALTO_MIN[troncon])}")

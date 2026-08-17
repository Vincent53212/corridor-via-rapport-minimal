"""Étape 32 — Figure : d'où viennent les minutes (barre décomposée par trajet).

Une barre par trajet : la longueur totale est l'horaire d'AUJOURD'HUI ; le
segment de gauche est le temps du SCÉNARIO RECOMMANDÉ avec sa marge normative
(8 %) ; les tranches suivantes disent d'où vient chaque minute gagnée.

MÉTHODE D'ATTRIBUTION (les parts sont des ATTRIBUTIONS comptables qui somment
exactement au gain, pas des mesures indépendantes) :

    H  = horaire actuel (médiane GTFS)  =  T_base(S1,160) × (1 + marge actuelle)
    C  = T_base(recommandé, 177) × 1,08  (marge normative interpolée à 177)
    G  = H − C, décomposé en :

    1) relèvement du plafond   : T(S1,160) − T(S1,177), et
    2) train pendulaire        : T(S1,177) − T(S2,177),
       chacun moyenné sur les DEUX ordres d'application (décomposition de
       Shapley à deux facteurs : l'écart entre ordres est publié en contrôle),
       puis multiplié par 1,08 (la marge normative s'applique au temps de base).
       La figure fusionne 1) et 2) en une seule tranche « train pendulaire,
       plafond 177 » ; le CSV garde le détail.
    3) doublement des voies    : (médiane simple-CN − médiane double-CN) / 100
       × Σ T_base(S1,160) des paires inter-gares en cellule simple-CN du trajet
       (marges_par_intergare.csv, cœur, hors paires exclues du 2×2).
       Sur un trajet sans voie simple du CN, la part est nulle.
    4) cohabitation            : le RÉSIDU G − 1) − 2) − 3), borné à ≥ 0.
       C'est la définition honnête : ce que l'étude ne peut allouer autrement,
       et précisément l'objet de l'étude de circulation recommandée. Les
       arrondis y sont absorbés.

Trajet Québec-Toronto : composé de Québec-Montréal + Montréal-Toronto plus un
arrêt à Montréal (HYPOTHÈSE : 10 min, déclarée ; il s'annule dans le gain
puisqu'il est compté des deux côtés).

Entrées : livrables/tbase_par_bande.csv, marges_2x2_synthese.csv,
          marges_par_intergare.csv
Sorties : livrables/figure_gains.png, livrables/decomposition_gains.csv
"""
import csv
from pathlib import Path

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

from utils import DELIVERABLES
from identite import PAPIER, SCENARIOS, CELLULES, appliquer_rcparams, \
    police_mono, police_titre

appliquer_rcparams(matplotlib)

MARGE_NORMATIVE = 1.08          # à 177 km/h : 7 % (160) → 9 % (200), interpolé
ARRET_MTL_MIN = 10.0            # HYPOTHÈSE : arrêt à Montréal du trajet composé
BANDE = 177

_T = {}
with open(DELIVERABLES / "tbase_par_bande.csv", encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f, delimiter=";"):
        _T[(r["troncon"], r["scenario"], int(r["bande_kmh"]))] = r


def tbase(tr, sc, bande):
    return float(_T[(tr, sc, bande)]["tbase_sans_marge_min"])


def horaire(tr):
    return float(_T[(tr, "S1", 160)]["t_horaire_actuel_min"])


# ---- médianes du 2×2 (cœur) et km simple-CN par trajet
med = {}
with open(DELIVERABLES / "marges_2x2_synthese.csv", encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f, delimiter=";"):
        if r["region"] == "coeur":
            med[r["cellule"]] = float(r["mediane"])

tb_simple_cn = {}          # Σ t_base_S1cap160 des paires simple-CN, par tronçon
with open(DELIVERABLES / "marges_par_intergare.csv", encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f, delimiter=";"):
        if (r["region"] == "coeur" and r["cellule"] == "simple-CN"
                and not r["exclue_du_2x2"].strip()
                and not r["doublon_physique_de"].strip()):
            tb_simple_cn[r["troncon"]] = (tb_simple_cn.get(r["troncon"], 0.0)
                                          + float(r["t_base_S1cap160_min"]))


def decompose(troncons, label):
    """Décompose le gain d'un trajet (somme de tronçons du pipeline)."""
    H = sum(horaire(t) for t in troncons)
    B1_160 = sum(tbase(t, "S1", 160) for t in troncons)
    B1_177 = sum(tbase(t, "S1", BANDE) for t in troncons)
    B2_160 = sum(tbase(t, "S2", 160) for t in troncons)
    B2_177 = sum(tbase(t, "S2", BANDE) for t in troncons)
    C = B2_177 * MARGE_NORMATIVE
    if len(troncons) > 1:                       # trajet composé : arrêt déclaré
        H += ARRET_MTL_MIN
        C += ARRET_MTL_MIN
    G = H - C

    # Shapley à deux facteurs (plafond, pendulaire), sur les temps de base
    plafond_a = B1_160 - B1_177                 # plafond d'abord
    pend_a = B1_177 - B2_177
    pend_b = B1_160 - B2_160                    # pendulaire d'abord
    plafond_b = B2_160 - B2_177
    plafond = (plafond_a + plafond_b) / 2 * MARGE_NORMATIVE
    pend = (pend_a + pend_b) / 2 * MARGE_NORMATIVE
    ecart_ordres = abs(plafond_a - plafond_b)

    marge_part = G - plafond - pend             # = B1_160 × (marge actuelle − 8 %)
    ratio = (med["simple-CN"] - med["double-CN"]) / 100.0
    doublement = min(ratio * sum(tb_simple_cn.get(t, 0.0) for t in troncons),
                     max(marge_part, 0.0))
    cohab = max(marge_part - doublement, 0.0)
    return {"trajet": label, "H": H, "C": C, "G": G, "plafond": plafond,
            "pendulaire": pend, "doublement": doublement,
            "cohabitation": cohab, "ecart_ordres_min": ecart_ordres}


TRAJETS = [
    (["MTL-QC", "MTL-TO"], "Québec-Toronto (via Montréal)"),
    (["MTL-QC"], "Québec-Montréal"),
    (["MTL-Ott"], "Montréal-Ottawa"),
]
rows = [decompose(tr, lab) for tr, lab in TRAJETS]

# ---- CSV (une ligne par trajet × poste + contrôles)
POSTES = [("temps_recommande_avec_marge", "C"),
          ("gain_releve_plafond", "plafond"), ("gain_pendulaire", "pendulaire"),
          ("gain_doublement", "doublement"), ("gain_cohabitation", "cohabitation")]
with open(DELIVERABLES / "decomposition_gains.csv", "w",
          encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["trajet", "poste", "minutes", "part_pct_du_gain", "source"])
    for r in rows:
        for nom, k in POSTES:
            pct = round(100 * r[k] / r["G"], 1) if k != "C" and r["G"] else ""
            src = ("tbase_par_bande.csv" if k in ("C", "plafond", "pendulaire")
                   else "marges_2x2_synthese.csv + marges_par_intergare.csv"
                   if k == "doublement" else "résidu (G − autres parts)")
            w.writerow([r["trajet"], nom, round(r[k], 1), pct, src])
        w.writerow([r["trajet"], "controle_horaire_actuel_H", round(r["H"], 1),
                    "", "tbase_par_bande.csv (médiane GTFS)"])
        w.writerow([r["trajet"], "controle_gain_total_G", round(r["G"], 1),
                    "", "H − C ; somme des quatre parts = G par construction"])
        w.writerow([r["trajet"], "controle_ecart_ordres_shapley",
                    round(r["ecart_ordres_min"], 1), "",
                    "écart |plafond d'abord − pendulaire d'abord|"])

# ---- figure
COL_PEND = SCENARIOS["S2"]          # le matériel : la teinte du recommandé
COL_DOUBLE = CELLULES["double-CN"]  # ce que la voie double rachète
COL_COHAB = CELLULES["simple-VIA"]  # le chaud dit la contrainte de régime


def hm(m):
    total = int(round(m))
    return f"{total // 60} h {total % 60:02d}"


fig, ax = plt.subplots(figsize=(11, 4.1), dpi=300)
ylabels = []
for yi, r in enumerate(reversed(rows)):
    y = yi
    x = 0.0
    # le temps qui reste : barre évidée (résultat, pas un gain)
    ax.barh(y, r["C"], left=x, height=0.52, facecolor="none",
            edgecolor=PAPIER["encre_douce"], linewidth=1.2)
    ax.text(r["C"] / 2, y, hm(r["C"]), ha="center", va="center",
            fontsize=8.2, color=PAPIER["encre"], **police_mono())
    x += r["C"]
    tranches = [(r["plafond"] + r["pendulaire"], COL_PEND, "pendulaire"),
                (r["doublement"], COL_DOUBLE, "doublement"),
                (r["cohabitation"], COL_COHAB, "cohabitation")]
    x_gains = x
    for val, col, nom in tranches:
        if val < 0.5:
            continue
        ax.barh(y, val, left=x, height=0.52, color=col)
        x += val
    ax.text(x + 4, y, f"aujourd'hui {hm(r['H'])}", va="center",
            fontsize=7.6, color=PAPIER["encre_pale"], **police_mono())
    # le détail des tranches, sous la barre (les tranches sont trop étroites
    # pour loger leur étiquette dedans)
    detail = "   ".join(f"{nom} −{val:.0f} min" for val, _c, nom in tranches
                        if val >= 0.5)
    ax.text(x_gains, y - 0.46, detail, ha="left", va="top",
            fontsize=6.9, color=PAPIER["encre_pale"], **police_mono())
    ylabels.append(r["trajet"])

ax.set_yticks(range(len(rows)))
ax.set_yticklabels(ylabels, fontsize=8.4, color=PAPIER["encre_douce"],
                   **police_mono())
ax.tick_params(axis="y", length=0, pad=8)
ax.set_xlim(0, max(r["H"] for r in rows) * 1.24)
ax.set_ylim(-0.85, len(rows) - 0.3)
ax.set_xticks([])
for s in ax.spines.values():
    s.set_visible(False)

# légende des tranches
handles = [plt.Rectangle((0, 0), 1, 1, facecolor="none",
                         edgecolor=PAPIER["encre_douce"], linewidth=1.2),
           plt.Rectangle((0, 0), 1, 1, color=COL_PEND),
           plt.Rectangle((0, 0), 1, 1, color=COL_DOUBLE),
           plt.Rectangle((0, 0), 1, 1, color=COL_COHAB)]
leg = ax.legend(handles,
                ["Scénario recommandé, marge normative incluse",
                 "Train pendulaire, plafond 177 km/h",
                 "Doublement des voies",
                 "Cohabitation (résidu : objet de l'étude de circulation)"],
                loc="lower right", bbox_to_anchor=(1.0, 0.98), ncol=2,
                frameon=False, fontsize=7.4,
                prop={"family": "IBM Plex Mono", "size": 7.4})
for txt in leg.get_texts():
    txt.set_color(PAPIER["encre_douce"])

fig.tight_layout(rect=(0, 0.13, 1, 0.80))
fig.text(0.008, 0.985, "D'où viennent les minutes : du train, des voies, du régime",
         fontsize=12.5, ha="left", va="top", color=PAPIER["encre"],
         **police_titre(600))
fig.text(0.008, 0.905,
         "Barre pleine = horaire actuel ; les tranches sont des attributions "
         "qui somment au gain, pas des mesures indépendantes",
         fontsize=7.4, ha="left", va="top", color=PAPIER["encre_pale"],
         **police_mono())
fig.text(0.008, 0.085,
         "Conditions :  + Superposition de contrôle en cabine (signalisation PTC)",
         fontsize=7.8, ha="left", va="top", color=PAPIER["encre_douce"],
         **police_mono())
fig.text(0.008, 0.038,
         "              + Corridor scellé (barrières quatre-quadrants, terre-pleins, "
         "détection) : 891 passages, dont 563 à équiper de feux-cloches-barrières",
         fontsize=7.8, ha="left", va="top", color=PAPIER["encre_douce"],
         **police_mono())
fig.savefig(DELIVERABLES / "figure_gains.png", bbox_inches="tight",
            facecolor=PAPIER["fond"])

for r in rows:
    print(f"{r['trajet']:<32} H {r['H']:6.1f}  C {r['C']:6.1f}  G {r['G']:5.1f} = "
          f"plafond {r['plafond']:5.1f} + pend {r['pendulaire']:5.1f} + "
          f"doubl {r['doublement']:5.1f} + cohab {r['cohabitation']:5.1f} "
          f"(écart ordres {r['ecart_ordres_min']:.1f})")
print("Écrit figure_gains.png et decomposition_gains.csv")

"""Étape 32 — Figure : d'où viennent les minutes (barre décomposée par trajet).

Remodelage du 24 août : une barre par trajet ; la longueur totale est l'horaire
d'AUJOURD'HUI ; le segment de gauche (évidé) est le temps du SCÉNARIO 3 avec la
marge de 10 % ; les tranches disent d'où vient chaque minute gagnée, dans
l'ordre de l'échelle des scénarios.

MÉTHODE D'ATTRIBUTION (les parts sont des ATTRIBUTIONS comptables qui somment
exactement au gain, pas des mesures indépendantes) :

    H   = horaire actuel (médiane GTFS)  =  T_base(S1,160) × (1 + marge actuelle)
    C1  = T_base(scénario 1, 177) × 1,10     (temps_scenario_1.csv)
    C2  = idem scénario 2 (zones urbaines modernisées, temps_scenario_2.csv)
    C3  = idem scénario 3 (+ courbes corrigées au doublement, temps_scenario_3.csv)
    G   = H − C3, décomposé en :

    1) train pendulaire, plafond 177 : Shapley à deux facteurs (relèvement du
       plafond 160→177 ; pendulaire S1→S2 interne), sur les temps de base du
       scénario 1, × 1,10. La figure fusionne les deux en une tranche ; le CSV
       garde le détail. → amène de H à C1 avec 3) et 4).
    2) doublement des voies : (médiane simple-CN − médiane double-CN) / 100
       × Σ T_base(S1,160) des paires inter-gares en cellule simple-CN du trajet
       (marges_par_intergare.csv, cœur). Nul sans voie simple du CN.
    3) cohabitation : le RÉSIDU (H − C1) − 1) − 2), borné à ≥ 0. Définition
       honnête : ce que l'étude ne peut allouer autrement, objet de l'étude de
       circulation recommandée. Les arrondis y sont absorbés.
    4) zones urbaines modernisées : C1 − C2.
    5) courbes corrigées au doublement : C2 − C3 (nulle sur un trajet déjà
       tout double, ex. Montréal-Toronto).

Trajet Québec-Toronto : composé de Québec-Montréal + Montréal-Toronto plus un
arrêt à Montréal (HYPOTHÈSE : 10 min, déclarée ; il s'annule dans le gain).

Entrées : livrables/temps_scenario_{1,2,3}.csv, marges_2x2_synthese.csv,
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

MARGE = 1.10                    # point unique (décision 2026-08-24)
ARRET_MTL_MIN = 10.0            # HYPOTHÈSE : arrêt à Montréal du trajet composé
BANDE = 177


def _lire(nom):
    t = {}
    with open(DELIVERABLES / nom, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter=";"):
            t[(r["troncon"], r["scenario"], int(r["bande_kmh"]))] = r
    return t


_T1, _T2, _T3 = (_lire(f"temps_scenario_{i}.csv") for i in (1, 2, 3))


def tbase(table, tr, sc, bande):
    return float(table[(tr, sc, bande)]["tbase_sans_marge_min"])


def horaire(tr):
    return float(_T1[(tr, "base", 160)]["t_horaire_actuel_min"])


# ---- médianes du 2×2 (cœur) et km simple-CN par trajet
med = {}
with open(DELIVERABLES / "marges_2x2_synthese.csv", encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f, delimiter=";"):
        if r["region"] == "coeur":
            med[r["cellule"]] = float(r["mediane"])

tb_simple_cn = {}          # Σ t_base_cap160 des paires simple-CN, par tronçon
with open(DELIVERABLES / "marges_par_intergare.csv", encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f, delimiter=";"):
        if (r["region"] == "coeur" and r["cellule"] == "simple-CN"
                and not r["exclue_du_2x2"].strip()
                and not r["doublon_physique_de"].strip()):
            tb_simple_cn[r["troncon"]] = (tb_simple_cn.get(r["troncon"], 0.0)
                                          + float(r["t_base_cap160_min"]))


def decompose(troncons, label):
    """Décompose le gain d'un trajet (somme de tronçons du pipeline)."""
    H = sum(horaire(t) for t in troncons)
    B1_160 = sum(tbase(_T1, t, "base", 160) for t in troncons)
    B1_177 = sum(tbase(_T1, t, "base", BANDE) for t in troncons)
    B2_160 = sum(tbase(_T1, t, "pendulaire", 160) for t in troncons)
    B2_177 = sum(tbase(_T1, t, "pendulaire", BANDE) for t in troncons)
    C1 = B2_177 * MARGE
    C2 = sum(tbase(_T2, t, "pendulaire", BANDE) for t in troncons) * MARGE
    C3 = sum(tbase(_T3, t, "pendulaire", BANDE) for t in troncons) * MARGE
    if len(troncons) > 1:                       # trajet composé : arrêt déclaré
        H += ARRET_MTL_MIN
        C1 += ARRET_MTL_MIN
        C2 += ARRET_MTL_MIN
        C3 += ARRET_MTL_MIN
    G = H - C3

    # Shapley à deux facteurs (plafond, pendulaire), sur les temps de base
    plafond_a = B1_160 - B1_177                 # plafond d'abord
    pend_a = B1_177 - B2_177
    pend_b = B1_160 - B2_160                    # pendulaire d'abord
    plafond_b = B2_160 - B2_177
    plafond = (plafond_a + plafond_b) / 2 * MARGE
    pend = (pend_a + pend_b) / 2 * MARGE
    ecart_ordres = abs(plafond_a - plafond_b)

    zones_urbaines = C1 - C2
    courbes = C2 - C3

    marge_part = (H - C1) - plafond - pend      # = B1_160 × (marge actuelle − 10 %)
    # Si l'horaire actuel porte MOINS de 10 % de marge (marge_part < 0), la
    # marge normative mange une part du gain pendulaire : on borne l'attribution
    # plafond+pendulaire à l'écart observé H − C1, pour que la somme des
    # tranches reste exactement le gain (l'écrasement est tracé au CSV).
    ecrasement = 0.0
    if marge_part < 0:
        ecrasement = -marge_part
        facteur = max(H - C1, 0.0) / max(plafond + pend, 1e-9)
        plafond *= facteur
        pend *= facteur
        marge_part = 0.0
    ratio = (med["simple-CN"] - med["double-CN"]) / 100.0
    doublement = min(ratio * sum(tb_simple_cn.get(t, 0.0) for t in troncons),
                     max(marge_part, 0.0))
    cohab = max(marge_part - doublement, 0.0)
    # Sur un trajet SANS voie simple du CN, la part « doublement » vaut zéro sur
    # les horaires courants, mais la mesure inter-saisons (GTFS 2023) empêche de
    # l'affirmer : le résidu y est affiché comme INDISCERNABLE entre doublement
    # et cohabitation.
    indiscernable = (doublement < 0.5 and cohab >= 0.5)
    return {"trajet": label, "H": H, "C1": C1, "C2": C2, "C3": C3, "G": G,
            "plafond": plafond, "pendulaire": pend,
            "zones_urbaines": zones_urbaines, "courbes": courbes,
            "doublement": doublement, "cohabitation": cohab,
            "ecart_ordres_min": ecart_ordres, "indiscernable": indiscernable,
            "ecrasement_min": ecrasement}


TRAJETS = [
    (["MTL-QC", "MTL-TO"], "Québec-Toronto (via Montréal)"),
    (["MTL-QC"], "Québec-Montréal"),
    (["MTL-Ott"], "Montréal-Ottawa"),
]
rows = [decompose(tr, lab) for tr, lab in TRAJETS]

# ---- CSV (une ligne par trajet × poste + contrôles)
POSTES = [("temps_scenario_3_avec_marge", "C3"),
          ("gain_releve_plafond", "plafond"), ("gain_pendulaire", "pendulaire"),
          ("gain_zones_urbaines", "zones_urbaines"),
          ("gain_courbes_au_doublement", "courbes"),
          ("gain_doublement", "doublement"), ("gain_cohabitation", "cohabitation")]
with open(DELIVERABLES / "decomposition_gains.csv", "w",
          encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["trajet", "poste", "minutes", "part_pct_du_gain", "source"])
    for r in rows:
        for nom, k in POSTES:
            pct = round(100 * r[k] / r["G"], 1) if k != "C3" and r["G"] else ""
            src = ("temps_scenario_1.csv" if k in ("plafond", "pendulaire")
                   else "temps_scenario_2.csv (C1 − C2)" if k == "zones_urbaines"
                   else "temps_scenario_3.csv (C2 − C3)" if k == "courbes"
                   else "marges_2x2_synthese.csv + marges_par_intergare.csv"
                   if k == "doublement"
                   else "résidu (H − C1 − autres parts)" if k == "cohabitation"
                   else "temps_scenario_3.csv")
            w.writerow([r["trajet"], nom, round(r[k], 1), pct, src])
        w.writerow([r["trajet"], "controle_horaire_actuel_H", round(r["H"], 1),
                    "", "temps_scenario_1.csv (médiane GTFS)"])
        w.writerow([r["trajet"], "controle_gain_total_G", round(r["G"], 1),
                    "", "H − C3 ; somme des parts = G par construction"])
        w.writerow([r["trajet"], "controle_ecart_ordres_shapley",
                    round(r["ecart_ordres_min"], 1), "",
                    "écart |plafond d'abord − pendulaire d'abord|"])
        if r["ecrasement_min"] > 0.05:
            w.writerow([r["trajet"], "info_marge_normative_excedentaire",
                        round(r["ecrasement_min"], 1), "",
                        "l'horaire actuel porte moins de 10 % de marge : la "
                        "marge normative absorbe cette part du gain pendulaire "
                        "(attribution plafond+pendulaire réduite d'autant)"])
        if r["indiscernable"]:
            w.writerow([r["trajet"], "info_doublement_fourchette",
                        round(r["cohabitation"], 1), "",
                        "part doublement/cohabitation indiscernable : 0 sur les "
                        "horaires courants, jusqu'à ~12 points de marge sur GTFS "
                        "2023, bornée par la marge actuelle du tronçon"])

# ---- figure
COL_PEND = SCENARIOS["S1"]          # tranche du scénario 1 (le train)
COL_URBAIN = SCENARIOS["S2"]        # tranche du scénario 2 (les zones urbaines)
COL_COURBES = SCENARIOS["S3"]       # tranche du scénario 3 (les courbes)
COL_DOUBLE = CELLULES["double-CN"]  # ce que la voie double rachète
COL_COHAB = CELLULES["simple-VIA"]  # le chaud dit la contrainte de régime


def hm(m):
    total = int(round(m))
    return f"{total // 60} h {total % 60:02d}"


fig, ax = plt.subplots(figsize=(11, 4.35), dpi=300)
ylabels = []
for yi, r in enumerate(reversed(rows)):
    y = yi
    x = 0.0
    # le temps qui reste (scénario 3) : barre évidée (résultat, pas un gain)
    ax.barh(y, r["C3"], left=x, height=0.52, facecolor="none",
            edgecolor=PAPIER["encre_douce"], linewidth=1.2)
    ax.text(r["C3"] / 2, y, hm(r["C3"]), ha="center", va="center",
            fontsize=8.2, color=PAPIER["encre"], **police_mono())
    x += r["C3"]
    tranches = [(r["courbes"], COL_COURBES, "courbes au doublement", False),
                (r["zones_urbaines"], COL_URBAIN, "zones urbaines", False),
                (r["plafond"] + r["pendulaire"], COL_PEND, "pendulaire", False)]
    if r["indiscernable"]:
        tranches += [(r["cohabitation"], COL_COHAB,
                      "doublement ou cohabitation", True)]
    else:
        tranches += [(r["doublement"], COL_DOUBLE, "doublement", False),
                     (r["cohabitation"], COL_COHAB, "cohabitation", False)]
    x_gains = x
    for val, col, nom, hach in tranches:
        if val < 0.5:
            continue
        if hach:
            ax.barh(y, val, left=x, height=0.52, facecolor=col,
                    edgecolor=COL_DOUBLE, hatch="///", linewidth=0.8)
        else:
            ax.barh(y, val, left=x, height=0.52, color=col)
        x += val
    ax.text(x + 4, y, f"aujourd'hui {hm(r['H'])}", va="center",
            fontsize=7.6, color=PAPIER["encre_pale"], **police_mono())
    detail = "   ".join(f"{nom} −{val:.0f} min" for val, _c, nom, _h in tranches
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
           plt.Rectangle((0, 0), 1, 1, color=COL_COURBES),
           plt.Rectangle((0, 0), 1, 1, color=COL_URBAIN),
           plt.Rectangle((0, 0), 1, 1, color=COL_PEND),
           plt.Rectangle((0, 0), 1, 1, color=COL_DOUBLE),
           plt.Rectangle((0, 0), 1, 1, color=COL_COHAB),
           plt.Rectangle((0, 0), 1, 1, facecolor=COL_COHAB,
                         edgecolor=COL_DOUBLE, hatch="///", linewidth=0.8)]
leg = ax.legend(handles,
                ["Scénario 3, marge de 10 % incluse",
                 "Courbes corrigées au doublement (scénario 3)",
                 "Zones urbaines modernisées (scénario 2)",
                 "Train pendulaire, plafond 177 km/h (scénario 1)",
                 "Doublement des voies",
                 "Cohabitation (résidu : objet de l'étude de circulation)",
                 "Doublement ou cohabitation, indiscernables"],
                loc="lower right", bbox_to_anchor=(1.0, 0.98), ncol=2,
                frameon=False, fontsize=7.4,
                prop={"family": "IBM Plex Mono", "size": 7.4})
for txt in leg.get_texts():
    txt.set_color(PAPIER["encre_douce"])

fig.tight_layout(rect=(0, 0.13, 1, 0.76))
fig.text(0.008, 0.985, "D'où viennent les minutes : du train, des villes, des voies, du régime",
         fontsize=12.5, ha="left", va="top", color=PAPIER["encre"],
         **police_titre(600))
fig.text(0.008, 0.912,
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
         "détection) : 833 passages, dont 533 à équiper de feux-cloches-barrières",
         fontsize=7.8, ha="left", va="top", color=PAPIER["encre_douce"],
         **police_mono())
fig.savefig(DELIVERABLES / "figure_gains.png", bbox_inches="tight",
            facecolor=PAPIER["fond"])

for r in rows:
    print(f"{r['trajet']:<32} H {r['H']:6.1f}  C3 {r['C3']:6.1f}  G {r['G']:5.1f} = "
          f"plafond {r['plafond']:5.1f} + pend {r['pendulaire']:5.1f} + "
          f"urbain {r['zones_urbaines']:5.1f} + courbes {r['courbes']:5.1f} + "
          f"doubl {r['doublement']:5.1f} + cohab {r['cohabitation']:5.1f} "
          f"(écart ordres {r['ecart_ordres_min']:.1f})")
print("Écrit figure_gains.png et decomposition_gains.csv")

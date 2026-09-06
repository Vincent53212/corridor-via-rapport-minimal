"""Étape 32 — Figure : facteurs de réduction des temps de parcours (barre par trajet).

Remodelage du 3 septembre (décision Vincent) : une barre par trajet ; la longueur
totale est l'horaire d'AUJOURD'HUI ; le segment de gauche (évidé) est le temps du
SCÉNARIO 2 (zones urbaines modernisées, SANS correction de courbes) avec la marge
de 10 % ; QUATRE tranches disent d'où vient chaque minute gagnée.

MÉTHODE D'ATTRIBUTION (les parts sont des ATTRIBUTIONS comptables qui somment
exactement au gain, pas des mesures indépendantes) :

    H      = horaire actuel (médiane GTFS)
    B1(p)  = T_base(voie et train actuels, plafond p)      temps_scenario_1.csv, base
    B2(p)  = T_base(train pendulaire, blocs figés, p)       temps_scenario_1.csv, pendulaire
    U2(p)  = T_base(train pendulaire, blocs libres, p)      temps_scenario_2.csv, pendulaire
    C      = U2(201) × 1,10  = temps publié du scénario 2
    G      = H − C, décomposé en :

    1) cohabitation : voir après 4) (c'est le reste).
    2) train pendulaire  = [B1(153) − B2(153)] × 1,10     (sous la classe actuelle)
    3) zones urbaines    = Σ blocs (courbes + signalisation), gains_urbains.csv
       (étape 36 : profil roulé À L'INTÉRIEUR de chaque bloc urbain ;
       courbes = train pendulaire sous 153, signalisation = 153 → 201).
       Décision Vincent 2026-09-06 : le mou de cohabitation que porte l'horaire
       urbain (l'essentiel de l'écart horaire ↔ géométrie en ville) N'EST PAS un
       gain « zones urbaines » : il retourne à la cohabitation.
    4) changement de classe (passages à niveau et signalisation, interurbain)
                         = [U2(153) − U2(201)] × 1,10 − Σ blocs signalisation
       = ce que les facteurs précédents rapportent EN PLUS une fois le
       plafond porté de 153 à 201 km/h, hors la part urbaine déjà comptée en 3).
    1) cohabitation      = G − 2) − 3) − 4)   (borné à ≥ 0)
       = H − B1(153) × 1,10 en interurbain, plus le mou urbain ; réunit le
       DOUBLEMENT et le RÉGIME de cohabitation (part rachetée par le doublement
       estimée à part : 2×2, ligne info du CSV).

    Somme 1)+2)+3)+4) = H − U2(201) × 1,10 = G par construction.
    Si 1) sort négatif (l'horaire porte MOINS de 10 % de marge), 1) est nul et
    2)-4) sont réduits au prorata pour que la somme reste G (écrasement tracé
    au CSV).

Plafond 153 km/h = 95 mi/h, la limite au-delà de laquelle le corridor scellé et
le contrôle en cabine deviennent obligatoires (bandes des passages à niveau du
rapport : ≤ 153 / 154-177 / 178-201). BANDES_KMH du 21 doit contenir 153.

Trajet Québec-Toronto : composé de Québec-Montréal + Montréal-Toronto plus un
arrêt à Montréal (HYPOTHÈSE : 10 min, déclarée ; il s'annule dans le gain).

Entrées : livrables/temps_scenario_{1,2}.csv, gains_urbains.csv (36),
          marges_2x2_synthese.csv, marges_par_intergare.csv
Sorties : livrables/figure_gains.png, livrables/decomposition_gains.csv
"""
import csv

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

from utils import DELIVERABLES
from identite import PAPIER, SCENARIOS, CELLULES, appliquer_rcparams, \
    police_mono, police_titre

appliquer_rcparams(matplotlib)

MARGE = 1.10                    # point unique (décision 2026-08-24)
ARRET_MTL_MIN = 10.0            # HYPOTHÈSE : arrêt à Montréal du trajet composé
P_CLASSE = 153                  # classe actuelle : 95 mi/h
P_PLAFOND = 201                 # plafond des scénarios publiés (125 mi/h)


def _lire(nom):
    t = {}
    with open(DELIVERABLES / nom, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter=";"):
            t[(r["troncon"], r["scenario"], int(r["bande_kmh"]))] = r
    return t


_T1, _T2 = (_lire(f"temps_scenario_{i}.csv") for i in (1, 2))


def tbase(table, tr, sc, bande):
    return float(table[(tr, sc, bande)]["tbase_sans_marge_min"])


def horaire(tr):
    return float(_T1[(tr, "base", 160)]["t_horaire_actuel_min"])


# ---- médianes du 2×2 (cœur) et km simple-CN par trajet (part « doublement »
#      de la cohabitation, ligne info du CSV et note de la figure)
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


urb_courbes, urb_sign, urb_cohab = {}, {}, {}
with open(DELIVERABLES / "gains_urbains.csv", encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f, delimiter=";"):
        t = r["troncon"]
        urb_courbes[t] = urb_courbes.get(t, 0.0) + float(r["gain_courbes_min"])
        urb_sign[t] = urb_sign.get(t, 0.0) + float(r["gain_signalisation_pn_min"])
        urb_cohab[t] = urb_cohab.get(t, 0.0) + float(r["gain_cohabitation_min"])


def decompose(troncons, label):
    """Décompose le gain d'un trajet (somme de tronçons du pipeline)."""
    S = lambda table, sc, p: sum(tbase(table, t, sc, p) for t in troncons)
    H = sum(horaire(t) for t in troncons)
    B1c, B2c, U2c = S(_T1, "base", P_CLASSE), S(_T1, "pendulaire", P_CLASSE), \
        S(_T2, "pendulaire", P_CLASSE)
    U2p = S(_T2, "pendulaire", P_PLAFOND)
    arret = ARRET_MTL_MIN if len(troncons) > 1 else 0.0   # trajet composé
    H += arret
    C = U2p * MARGE + arret
    G = H - C

    pend = (B1c - B2c) * MARGE
    urbain = sum(urb_courbes[t] + urb_sign[t] for t in troncons)
    classe = (U2c - U2p) * MARGE - sum(urb_sign[t] for t in troncons)
    cohab_brut = G - pend - urbain - classe
    cohab_urbain = sum(urb_cohab[t] for t in troncons)
    ecrasement = 0.0
    if cohab_brut < 0:          # l'horaire porte moins de 10 % : la marge
        ecrasement = -cohab_brut    # normative mange une part des gains
        facteur = G / max(pend + urbain + classe, 1e-9)
        pend, urbain, classe = pend * facteur, urbain * facteur, classe * facteur
        cohab = 0.0
    else:
        cohab = cohab_brut
    ratio = (med["simple-CN"] - med["double-CN"]) / 100.0
    doublement = min(ratio * sum(tb_simple_cn.get(t, 0.0) for t in troncons), cohab)
    return {"trajet": label, "H": H, "C": C, "G": G,
            "cohabitation": cohab, "pendulaire": pend, "zones_urbaines": urbain,
            "classe": classe, "doublement_inclus": doublement,
            "cohab_urbain": min(cohab_urbain, cohab),
            "ecrasement_min": ecrasement}


TRAJETS = [
    (["MTL-QC", "MTL-TO"], "Québec-Toronto (via Montréal)"),
    (["MTL-QC"], "Québec-Montréal"),
    (["MTL-TO"], "Montréal-Toronto"),
    (["MTL-Ott"], "Montréal-Ottawa"),
]
rows = [decompose(tr, lab) for tr, lab in TRAJETS]

# ---- CSV (une ligne par trajet × poste + contrôles)
POSTES = [("temps_scenario_2_avec_marge", "C", "temps_scenario_2.csv (pendulaire, 201) × 1,10"),
          ("gain_cohabitation", "cohabitation",
           "G − les trois autres postes : mou de l'horaire au-delà de 10 %, interurbain "
           "et zones urbaines ; doublement et régime réunis"),
          ("gain_pendulaire", "pendulaire", "temps_scenario_1.csv (base − pendulaire, 153) × 1,10"),
          ("gain_zones_urbaines", "zones_urbaines",
           "gains_urbains.csv : courbes (pendulaire) + signalisation des blocs urbains, "
           "sans le mou de cohabitation"),
          ("gain_changement_classe", "classe",
           "temps_scenario_2.csv (pendulaire, 153 − 201) × 1,10 − signalisation urbaine : "
           "passages à niveau et signalisation, interurbain")]
with open(DELIVERABLES / "decomposition_gains.csv", "w",
          encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["trajet", "poste", "minutes", "part_pct_du_gain", "source"])
    for r in rows:
        for nom, k, src in POSTES:
            pct = round(100 * r[k] / r["G"], 1) if k != "C" and r["G"] else ""
            w.writerow([r["trajet"], nom, round(r[k], 1), pct, src])
        w.writerow([r["trajet"], "info_cohabitation_dont_doublement",
                    round(r["doublement_inclus"], 1), "",
                    "part de la cohabitation que le doublement rachète : (médiane simple-CN − "
                    "médiane double-CN) × Σ T_base des paires simple-CN (marges_2x2_synthese.csv, "
                    "marges_par_intergare.csv) ; le reste est l'objet de l'étude de circulation"])
        w.writerow([r["trajet"], "info_cohabitation_dont_zones_urbaines",
                    round(r["cohab_urbain"], 1), "",
                    "mou de l'horaire actuel dans les blocs urbains (gains_urbains.csv), "
                    "compté dans la cohabitation et non dans les zones urbaines"])
        w.writerow([r["trajet"], "controle_horaire_actuel_H", round(r["H"], 1),
                    "", "temps_scenario_1.csv (médiane GTFS)"])
        w.writerow([r["trajet"], "controle_gain_total_G", round(r["G"], 1),
                    "", "H − C ; somme des quatre parts = G par construction"])
        if r["ecrasement_min"] > 0.05:
            w.writerow([r["trajet"], "info_marge_normative_excedentaire",
                        round(r["ecrasement_min"], 1), "",
                        "l'horaire actuel porte moins de 10 % de marge : la "
                        "cohabitation est nulle et les trois autres parts sont "
                        "réduites au prorata d'autant"])

# ---- figure
COL_PEND = SCENARIOS["S1"]          # le train
COL_URBAIN = SCENARIOS["S2"]        # les zones urbaines
COL_CLASSE = SCENARIOS["S3"]        # le changement de classe (le plus foncé de la rampe)
COL_COHAB = CELLULES["simple-VIA"]  # le chaud dit la contrainte de régime


def hm(m):
    total = int(round(m))
    return f"{total // 60} h {total % 60:02d}"


import textwrap

# Format pleine largeur de page (7,4 po), polices dimensionnées pour cette
# largeur : barres espacées, facteurs sur deux lignes sous chaque barre,
# légende en colonne, note repliée (remodelage du 3 septembre).
fig, ax = plt.subplots(figsize=(7.4, 7.4), dpi=250)
ylabels = []
for yi, r in enumerate(reversed(rows)):
    y = yi
    x = 0.0
    # le temps qui reste (scénario 2) : barre évidée (résultat, pas un gain)
    ax.barh(y, r["C"], left=x, height=0.42, facecolor="none",
            edgecolor=PAPIER["encre_douce"], linewidth=1.4)
    ax.text(r["C"] / 2, y, hm(r["C"]), ha="center", va="center",
            fontsize=10, color=PAPIER["encre"], **police_mono())
    x += r["C"]
    tranches = [(r["classe"], COL_CLASSE, "changement de classe"),
                (r["zones_urbaines"], COL_URBAIN, "zones urbaines"),
                (r["pendulaire"], COL_PEND, "pendulaire"),
                (r["cohabitation"], COL_COHAB, "cohabitation")]
    x_gains = x
    for val, col, nom in tranches:
        if val < 0.5:
            continue
        ax.barh(y, val, left=x, height=0.42, color=col)
        x += val
    ax.text(x + 6, y, "aujourd'hui" + chr(10) + hm(r['H']), va="center",
            fontsize=9.6, color=PAPIER["encre_pale"], linespacing=1.25, **police_mono())
    items = [f"{nom} −{val:.0f} min" for val, _c, nom in tranches if val >= 0.5]
    detail = " · ".join(items[:2]) + (chr(10) + " · ".join(items[2:]) if items[2:] else "")
    ax.text(x_gains, y - 0.30, detail, ha="left", va="top", linespacing=1.35,
            fontsize=8.6, color=PAPIER["encre_douce"], **police_mono())
    ylabels.append(r["trajet"].replace(" (via Montréal)", chr(10) + "(via Montréal)"))

ax.set_yticks(range(len(rows)))
ax.set_yticklabels(ylabels, fontsize=10.2, color=PAPIER["encre_douce"],
                   linespacing=1.25, **police_mono())
ax.tick_params(axis="y", length=0, pad=10)
ax.set_xlim(0, max(r["H"] for r in rows) * 1.34)
ax.set_ylim(-0.75, len(rows) - 0.45)
ax.set_xticks([])
for s_ in ax.spines.values():
    s_.set_visible(False)

# légende des tranches, en colonne
handles = [plt.Rectangle((0, 0), 1, 1, facecolor="none",
                         edgecolor=PAPIER["encre_douce"], linewidth=1.4),
           plt.Rectangle((0, 0), 1, 1, color=COL_COHAB),
           plt.Rectangle((0, 0), 1, 1, color=COL_PEND),
           plt.Rectangle((0, 0), 1, 1, color=COL_URBAIN),
           plt.Rectangle((0, 0), 1, 1, color=COL_CLASSE)]
leg = fig.legend(handles,
                 ["Scénario 2, marge de 10 % incluse (sans correction de courbes)",
                  "Cohabitation : régime et doublement des voies, zones" + chr(10) +
                  "urbaines comprises (voir la note)",
                  "Train pendulaire, sous la classe actuelle (153 km/h, 95 mi/h)",
                  "Zones urbaines modernisées : courbes et signalisation" + chr(10) +
                  "seulement, sans le mou de cohabitation",
                  "Changement de classe : passages à niveau et signalisation," + chr(10) +
                  "de 153 à 201 km/h (125 mi/h)"],
                 loc="upper left", bbox_to_anchor=(0.004, 0.895), ncol=1,
                 frameon=False, handlelength=1.6, labelspacing=0.55,
                 prop={"family": "IBM Plex Mono", "size": 8.8})
for txt in leg.get_texts():
    txt.set_color(PAPIER["encre_douce"])

fig.tight_layout(rect=(0, 0.19, 1, 0.68))
fig.text(0.008, 0.985, "Facteurs de réduction des temps de parcours",
         fontsize=15, ha="left", va="top", color=PAPIER["encre"],
         **police_titre(600))
fig.text(0.008, 0.945,
         "Barre pleine = horaire actuel ; les tranches sont des attributions" + chr(10) +
         "qui somment au gain, pas des mesures indépendantes",
         fontsize=8.8, ha="left", va="top", color=PAPIER["encre_pale"],
         linespacing=1.3, **police_mono())
_d = {r["trajet"]: r for r in rows}
note = ("Note. Cohabitation = ce que l'horaire d'aujourd'hui porte au-delà d'une marge de "
        "10 %, train et voie actuels, en interurbain comme dans les zones urbaines (où c'est "
        f"la plus grande part de l'écart : {_d['Québec-Montréal']['cohab_urbain']:.0f} min sur "
        "Québec-Montréal). Elle réunit le régime de circulation avec le fret et le doublement "
        "des voies : d'après le 2×2 (section 4), le doublement peut en racheter une bonne part "
        f"(environ {_d['Québec-Montréal']['doublement_inclus']:.0f} min sur Québec-Montréal) ; "
        "le reste relève de l'étude de circulation. Zones urbaines = courbes prises par le "
        "pendulaire et signalisation dans les approches de Montréal, Québec et Toronto. "
        "Pendulaire et zones urbaines sont comptés sous la classe actuelle (153 km/h) ; "
        "« changement de classe » est ce que l'interurbain rapporte en plus une fois le "
        "plafond porté à 201 km/h, ce qui exige le corridor scellé et le contrôle en cabine.")
fig.text(0.008, 0.165, chr(10).join(textwrap.wrap(note, 94)),
         fontsize=8.4, ha="left", va="top", color=PAPIER["encre_douce"],
         linespacing=1.45, **police_mono())
fig.savefig(DELIVERABLES / "figure_gains.png", bbox_inches="tight",
            facecolor=PAPIER["fond"])

for r in rows:
    print(f"{r['trajet']:<32} H {r['H']:6.1f}  C2 {r['C']:6.1f}  G {r['G']:5.1f} = "
          f"cohab {r['cohabitation']:5.1f} (dont doubl {r['doublement_inclus']:4.1f}) + "
          f"pend {r['pendulaire']:5.1f} + urbain {r['zones_urbaines']:5.1f} + "
          f"classe {r['classe']:5.1f}  [cohab urbain {r['cohab_urbain']:4.1f}]"
          + (f"  [écrasement {r['ecrasement_min']:.1f}]" if r['ecrasement_min'] > 0.05 else ""))
print("Écrit figure_gains.png et decomposition_gains.csv")

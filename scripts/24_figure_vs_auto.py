"""Étape 24 — Figure : le train contre l'auto, quatre trajets (fourchettes avec marge).
Temps auto = approximation de connaissance générale (étiquetée) ; train = T_base
+ marge (borne 8 % à marge actuelle du tronçon), milieu de fourchette en barre,
fourchette en moustache. Les pourcentages face à l'auto sont publiés en bornes
(borne basse et borne haute de la fourchette), jamais en point.
Deux barres par trajet : l'horaire d'aujourd'hui (scénario de base) et le
scénario recommandé (pendulaire, plafond d'exploitation 177 km/h — interne S2).
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
    s'affiche « 3 h 60 » au lieu de « 4 h 00 » (l'heure est tronquée sur la
    valeur non arrondie, les minutes sont arrondies à 60)."""
    total = int(round(m))
    return f"{total // 60} h {total % 60:02d}"

def pct(m, auto): return int(m / auto * 100 + 0.5)

# Fourchette avec marge calculée comme dans le rapport : lo = T_base × 1,08
# (borne normative à 177 km/h : interpolation UIC entre 7 % à 160 et 9 % à 200,
# soit 1 + 0,07 + (177−160)/(200−160) × 0,02 ≈ 1,078, arrondi 1,08),
# hi = T_base × (1 + marge actuelle du tronçon), où marge actuelle =
# t_horaire / T_base(S1, 160) − 1 (tbase_par_bande.csv).
# T_base = profil dynamique (étape 21, 2026-08-08).
MARGE_LO = 1.08
def four(base, m_troncon): return (base * MARGE_LO, base * m_troncon)

# T_base, horaire actuel et marge de tronçon sont LUS dans le livrable de
# l'étape 21 : ces valeurs étaient auparavant recopiées à la main ici, donc
# la figure ne suivait pas un recalcul du pipeline.
import csv as _csv
from pathlib import Path as _Path

_CSV = _Path(__file__).resolve().parent.parent / "livrables" / "tbase_par_bande.csv"
_T = {}
with open(_CSV, encoding="utf-8-sig", newline="") as _f:
    for _r in _csv.DictReader(_f, delimiter=";"):
        _T[(_r["troncon"], _r["scenario"], int(_r["bande_kmh"]))] = _r


def _base(troncon, scenario, bande):
    return float(_T[(troncon, scenario, bande)]["tbase_sans_marge_min"])


def _horaire(troncon):
    return float(_T[(troncon, "S1", 160)]["t_horaire_actuel_min"])


def _marge(troncon):
    """Marge actuelle du tronçon = horaire / T_base(S1, 160)."""
    return _horaire(troncon) / _base(troncon, "S1", 160)


# Le temps en auto reste une hypothèse externe (ordre de grandeur, annoncé
# comme approximatif dans le titre) : il ne vient pas du pipeline.
# Vérifiés sur cartographie routière grand public (2026-08-17).
AUTO_MIN = {"MTL-QC": 170, "MTL-TO": 330, "MTL-Ott": 140, "Ott-TO": 260}
RECO = "Scénario recommandé"

def panel(troncon, titre, repere):
    return (titre, repere, AUTO_MIN[troncon], [
        ("VIA aujourd'hui", _horaire(troncon), _horaire(troncon)),
        (RECO, *four(_base(troncon, "S2", 177), _marge(troncon)))])

# (corridor, auto_min, [(label, lo, hi — lo == hi pour un point)])
DATA = [
 panel("MTL-QC",  "Montréal-Québec",  "auto ≈ 2 h 50, approx."),
 panel("MTL-TO",  "Montréal-Toronto", "auto ≈ 5 h 30, approx."),
 panel("MTL-Ott", "Montréal-Ottawa",  "auto ≈ 2 h 20, approx."),
 panel("Ott-TO",  "Ottawa-Toronto",   "auto ≈ 4 h 20, approx."),
]
COLS = {"auto": SCENARIOS["auto"], "VIA aujourd'hui": SCENARIOS["actuel"],
        RECO: SCENARIOS["S2"]}

fig, axes = plt.subplots(2, 2, figsize=(11, 5.6), dpi=300)
for ax, (title, repere, auto, rows) in zip(axes.flat, DATA):
    labels = ["Auto"] + [r[0] for r in rows]
    mids = [auto] + [(lo+hi)/2 for _, lo, hi in rows]
    cols = [COLS["auto"]] + [COLS[r[0]] for r in rows]
    y = range(len(labels))[::-1]
    # L'auto est un REPÈRE, pas une mesure de l'étude : sa barre est évidée. Deux
    # aplats grèges voisins (auto et horaire actuel) se lisaient comme deux
    # scénarios de même famille, ce que l'un des deux n'est pas.
    ax.barh(list(y)[:1], mids[:1], height=0.58, facecolor="none",
            edgecolor=COLS["auto"], linewidth=1.3, hatch=None)
    ax.barh(list(y)[1:], mids[1:], color=cols[1:], height=0.58)
    for yi, (lab, mid) in zip(y, zip(labels, mids)):
        if lab == "Auto":
            txt = hm(mid) + "  (repère)"
        else:
            lo, hi = next((l, h) for n, l, h in rows if n == lab)
            if lo == hi:
                txt = hm(lo) + f"  ({pct(lo, auto)} % de l'auto)"
            else:
                txt = (f"{hm(lo)} à {hm(hi)}"
                       f"  ({pct(lo, auto)} à {pct(hi, auto)} % de l'auto)")
                # La moustache déborde la barre : elle porte l'incertitude, elle
                # doit donc se voir par-dessus l'aplat, pas se confondre avec lui.
                ax.plot([lo, hi], [yi, yi], color=PAPIER["encre"], lw=1.1, zorder=4)
                for b in (lo, hi):
                    ax.plot([b, b], [yi - 0.17, yi + 0.17],
                            color=PAPIER["encre"], lw=1.1, zorder=4)
        xtxt = mid + 6 if lab == 'Auto' else max(h for n, l, h in rows if n == lab) + 9
        ax.text(xtxt, yi, txt, va="center", fontsize=7.6,
                color=PAPIER["encre_douce"], **police_mono())
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=7.8, color=PAPIER["encre_douce"],
                       **police_mono())
    ax.tick_params(axis="y", length=0, pad=6)
    ax.set_xlim(0, max(mids)*2.45); ax.set_xticks([])
    ax.set_title(title, fontsize=11, loc="left", color=PAPIER["encre"],
                 pad=15, **police_titre(600))
    ax.text(0, 1.015, repere, transform=ax.transAxes, fontsize=7.2,
            color=PAPIER["encre_pale"], **police_mono())
    for s in ax.spines.values(): s.set_visible(False)
# Titre et sous-titre posés APRÈS tight_layout, en coordonnées de figure : placés
# avant, suptitle et fig.text se recouvraient parce que tight_layout ne tient pas
# compte des textes libres pour calculer le rectangle du tracé.
fig.tight_layout(rect=(0, 0, 1, 0.845))
fig.text(0.008, 0.975, "Le train contre l'auto : temps de parcours avec marge",
         fontsize=12.5, ha="left", va="top", color=PAPIER["encre"],
         **police_titre(600))
fig.text(0.008, 0.895, "Fourchette en trait, pourcentages en bornes",
         fontsize=7.6, ha="left", va="top", color=PAPIER["encre_pale"],
         **police_mono())
fig.savefig(DELIVERABLES / "figure_vs_auto.png", bbox_inches="tight",
            facecolor=PAPIER["fond"])
print("Écrit figure_vs_auto.png")

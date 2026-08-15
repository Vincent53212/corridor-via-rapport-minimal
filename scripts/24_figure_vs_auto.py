"""Étape 24 — Figure : le train contre l'auto, par scénario (fourchettes avec marge).
Temps auto = approximation de connaissance générale (étiquetée) ; train = T_base
+ marge (borne 9 % à marge actuelle du tronçon), milieu de fourchette en barre,
fourchette en moustache. Les pourcentages face à l'auto sont publiés en bornes
(borne basse et borne haute de la fourchette), jamais en point.
Sortie : livrables/figure_vs_auto.png."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from utils import DELIVERABLES

def hm(m):
    """Minutes → « h hh mm ». Arrondir AVANT de séparer : sinon 239,98 min
    s'affiche « 3 h 60 » au lieu de « 4 h 00 » (l'heure est tronquée sur la
    valeur non arrondie, les minutes sont arrondies à 60)."""
    total = int(round(m))
    return f"{total // 60} h {total % 60:02d}"

def pct(m, auto): return int(m / auto * 100 + 0.5)

# Fourchette avec marge calculée comme dans le rapport : lo = T_base × 1,09
# (borne normative 9 % aux bandes 200+), hi = T_base × (1 + marge actuelle du
# tronçon), où marge actuelle = t_horaire / T_base(S1, 160) − 1 (tbase_par_bande.csv).
# T_base = profil dynamique (étape 21, 2026-08-08).
MARGE_LO = 1.09
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
AUTO_QC_MIN, AUTO_TO_MIN = 170, 330

# (corridor, auto_min, [(label, lo, hi — lo == hi pour un point)])
DATA = [
 ("Montréal-Québec\n(auto ≈ 2 h 50, approx.)", AUTO_QC_MIN, [
   ("VIA aujourd'hui", _horaire("MTL-QC"), _horaire("MTL-QC")),
   ("S2, bande 200", *four(_base("MTL-QC", "S2", 200), _marge("MTL-QC"))),
   ("S3, bande 300", *four(_base("MTL-QC", "S3", 300), _marge("MTL-QC")))]),
 ("Montréal-Toronto\n(auto ≈ 5 h 30, approx.)", AUTO_TO_MIN, [
   ("VIA aujourd'hui", _horaire("MTL-TO"), _horaire("MTL-TO")),
   ("S2, bande 200", *four(_base("MTL-TO", "S2", 200), _marge("MTL-TO"))),
   ("S3, bande 300", *four(_base("MTL-TO", "S3", 300), _marge("MTL-TO")))]),
]
COLS = {"auto": "#999999", "VIA aujourd'hui": "#9ecae1", "S2, bande 200": "#4292c6",
        "S3, bande 200": "#2171b5", "S3, bande 300": "#08519c"}

fig, axes = plt.subplots(1, 2, figsize=(10, 3.7), dpi=300)
for ax, (title, auto, rows) in zip(axes, DATA):
    labels = ["Auto"] + [r[0] for r in rows]
    mids = [auto] + [(lo+hi)/2 for _, lo, hi in rows]
    cols = [COLS["auto"]] + [COLS[r[0]] for r in rows]
    y = range(len(labels))[::-1]
    ax.barh(list(y), mids, color=cols, height=0.62)
    for yi, (lab, mid) in zip(y, zip(labels, mids)):
        if lab == "Auto":
            txt = hm(mid) + " (repère)"
        else:
            lo, hi = next((l, h) for n, l, h in rows if n == lab)
            if lo == hi:
                txt = hm(lo) + f"  ({pct(lo, auto)} % de l'auto)"
            else:
                txt = (f"{hm(lo)} à {hm(hi)}"
                       f"  ({pct(lo, auto)} à {pct(hi, auto)} % de l'auto)")
                ax.plot([lo, hi], [yi, yi], color="#333333", lw=1.2, zorder=4)
        xtxt = mid + 6 if lab == 'Auto' else max(h for n, l, h in rows if n == lab) + 8
        ax.text(xtxt, yi, txt, va="center", fontsize=8, color="#222222")
    ax.set_yticks(list(y)); ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlim(0, max(mids)*1.95); ax.set_xticks([])
    ax.set_title(title, fontsize=9, loc="left")
    for s in ax.spines.values(): s.set_visible(False)
fig.suptitle("Le train contre l'auto : temps de parcours avec marge (fourchette en trait, pourcentages en bornes)",
             fontsize=11, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.93))
fig.savefig(DELIVERABLES / "figure_vs_auto.png", bbox_inches="tight")
print("Écrit figure_vs_auto.png")

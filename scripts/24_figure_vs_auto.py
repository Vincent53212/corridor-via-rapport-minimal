"""Étape 24 — Figure : le train contre l'auto, par scénario (fourchettes avec marge).
Temps auto = approximation de connaissance générale (étiquetée) ; train = T_base
+ marge (borne 9 % à marge actuelle du tronçon), milieu de fourchette en barre,
fourchette en moustache. Les pourcentages face à l'auto sont publiés en bornes
(borne basse et borne haute de la fourchette), jamais en point.
Sortie : livrables/figure_vs_auto.png."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from utils import DELIVERABLES

def hm(m): return f"{int(m//60)} h {int(round(m%60)):02d}"

def pct(m, auto): return int(m / auto * 100 + 0.5)

# Fourchette avec marge calculée comme dans le rapport : lo = T_base × 1,09
# (borne normative 9 % aux bandes 200+), hi = T_base × (1 + marge actuelle du
# tronçon), où marge actuelle = t_horaire / T_base(S1, 160) − 1 (tbase_par_bande.csv).
# T_base = profil dynamique (étape 21, 2026-08-08).
MARGE_LO = 1.09
def four(base, m_troncon): return (base * MARGE_LO, base * m_troncon)

M_QC = 202.5 / 153.5   # marge actuelle Montréal-Québec (≈ 32 %)
M_TO = 318.0 / 272.4   # marge actuelle Montréal-Toronto (≈ 17 %)

# (corridor, auto_min, [(label, lo, hi — lo == hi pour un point)])
DATA = [
 ("Montréal-Québec\n(auto ≈ 2 h 50, approx.)", 170, [
   ("VIA aujourd'hui", 203, 203),
   ("S2, bande 200", *four(133.4, M_QC)),
   ("S3, bande 300", *four(117.4, M_QC))]),
 ("Montréal-Toronto\n(auto ≈ 5 h 30, approx.)", 330, [
   ("VIA aujourd'hui", 318, 318),
   ("S2, bande 200", *four(234.1, M_TO)),
   ("S3, bande 300", *four(197.5, M_TO))]),
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

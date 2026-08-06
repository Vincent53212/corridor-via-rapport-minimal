"""Étape 24 — Figure : le train contre l'auto, par scénario (fourchettes avec marge).
Temps auto = approximation de connaissance générale (étiquetée) ; train = T_base
+ marge (borne 9 % à marge actuelle du tronçon), milieu de fourchette en barre,
fourchette en moustache. Sortie : livrables/figure_vs_auto.png."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from utils import DELIVERABLES

def hm(m): return f"{int(m//60)} h {int(round(m%60)):02d}"

# (corridor, auto_min, [(label, lo, hi ou None pour point)])
DATA = [
 ("Montréal-Québec\n(auto ≈ 2 h 50, approx.)", 170, [
   ("VIA aujourd'hui", 203, 203), ("S2, bande 200", 144, 176), ("S3, bande 300", 122, 149)]),
 ("Montréal-Toronto\n(auto ≈ 5 h 30, approx.)", 330, [
   ("VIA aujourd'hui", 318, 318), ("S2, bande 200", 261, 274), ("S3, bande 300", 212, 222)]),
]
COLS = {"auto": "#999999", "VIA aujourd'hui": "#9ecae1", "S2, bande 200": "#4292c6", "S3, bande 300": "#08519c"}

fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), dpi=300)
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
            pct = round(100*mid/auto)
            txt = (hm(lo) if lo == hi else f"{hm(lo)} à {hm(hi)}") + f"  ({pct} % de l'auto)"
            if lo != hi:
                ax.plot([lo, hi], [yi, yi], color="#333333", lw=1.2, zorder=4)
        xtxt = mid + 6 if lab == 'Auto' else max(h for n, l, h in rows if n == lab) + 8
        ax.text(xtxt, yi, txt, va="center", fontsize=8, color="#222222")
    ax.set_yticks(list(y)); ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlim(0, max(mids)*1.75); ax.set_xticks([])
    ax.set_title(title, fontsize=9, loc="left")
    for s in ax.spines.values(): s.set_visible(False)
fig.suptitle("Le train contre l'auto : temps de parcours avec marge (fourchette en trait)",
             fontsize=11, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.92))
fig.savefig(DELIVERABLES / "figure_vs_auto.png", bbox_inches="tight")
print("Écrit figure_vs_auto.png")

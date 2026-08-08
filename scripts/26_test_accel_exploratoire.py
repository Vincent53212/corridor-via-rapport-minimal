"""Test EXPLORATOIRE (hors rapport) — l'accélération/freinage change-t-il le headline?

NOTE HISTORIQUE (2026-08-08) : ce test a précédé l'intégration du profil dynamique
dans le moteur officiel (étape 21). Les constantes REPORT_* ci-dessous décrivent
l'ANCIEN moteur (intégrale fluide + 5 min/arrêt) et servent de trace de la
comparaison qui a motivé le changement. Ne pas les rafraîchir.

Question de Vincent (2026-08-08) : T_base traite les changements de vitesse comme
instantanés (+5 min/arrêt forfaitaires). Si on simule un vrai profil de vitesse
(accélération limitée par la puissance, freinage constant, arrêt complet en gare),
le headline S2 bande 200 bouge-t-il « pas mal »?

Méthode : profil de vitesse classique en deux passes (avant : accélération ;
arrière : freinage), sur les limites v(x) = min(vmax_S2(x), bande) des segments
réels, avec arrêt (v=0) à chaque gare intermédiaire hors blocs urbains et aux
extrémités de chaque tronçon interurbain libre. Les blocs urbains GTFS et les
fenêtres d'Ottawa restent traités comme au rapport (minutes identiques des deux
côtés de la comparaison : elles s'annulent).

Paramètres (HYPOTHÈSES plausibles, étiquetées, pas des specs constructeur) :
  - « LRC » : locomotive 3 725 hp ≈ 2 780 kW (≈ 2 400 kW au rail), rame ≈ 370 t
    → P/m ≈ 6,5 W/kg ; a0 = 0,42 m/s² ; freinage service 0,5 m/s².
  - « EMU moderne » (référence haute) : P/m ≈ 12 W/kg ; a0 = 0,6 ; freinage 0,6.
  - Arrêt en gare (dwell) : 2 min (sensibilité 1-3 min).
Résistances à l'avancement et pentes ignorées (test d'ordre de grandeur).

Comparaison, par tronçon (S2, bande 200) :
  rapport  : interurbain fluide + 5 min × n arrêts
  simulé   : profil dynamique (mêmes limites) + dwell × n arrêts
puis effet sur le headline « avec marge » (lo = ×1,09 ; hi = ×(1+marge tronçon)).
"""
from __future__ import annotations

import json
import math

from utils import INTERMEDIATES

SEGMENTS = INTERMEDIATES / "segments.geojson"
BANDE = 200.0
DX = 25.0  # pas d'intégration (m)

# Copié de 21_tbase_bande.py (blocs urbains et arrêts intermédiaires)
URBAN_BLOCKS = {
    "MTL-QC":  [(0.0, 6.11), (249.98, 269.85)],
    "MTL-Ott": [(0.0, 17.79), (175.42, 185.42)],
    "Ott-TO":  [(0.0, 10.0), (423.93, 444.05)],
    "MTL-TO":  [(0.0, 17.79), (517.94, 538.06)],
}
STOPS = {
    "MTL-QC":  [53.24, 100.01, 245.04],
    "MTL-Ott": [62.28, 99.43, 138.78],
    "Ott-TO":  [64.62, 110.0, 155.83, 191.99, 227.49, 262.44, 281.92, 332.06, 342.88, 393.31],
    "MTL-TO":  [204.72, 249.75, 285.97, 321.47, 356.42, 375.9, 426.05, 436.86, 487.24],
}
# Rapport (tbase_par_bande.csv, S2 bande 200) : interurbain fluide + arrêts forfaitaires
REPORT_INTER_MIN = {"MTL-QC": 79.4, "MTL-Ott": 50.8, "Ott-TO": 128.3, "MTL-TO": 153.0}
REPORT_STOP_MIN = 5.0
# T_base complets et marges pour l'effet headline
REPORT_TBASE = {"MTL-QC": 132.4, "MTL-Ott": 93.4, "Ott-TO": 200.8, "MTL-TO": 239.5}
MARGE_HAUTE = {"MTL-QC": 202.5 / 152.5 - 1, "MTL-Ott": 122.0 / 106.6 - 1,
               "Ott-TO": 275.0 / 233.2 - 1, "MTL-TO": 318.0 / 277.9 - 1}

TRAINS = {
    "LRC (hyp. 6,5 W/kg, a0 0,42, frein 0,5)":   dict(pm=6.5, a0=0.42, ab=0.5),
    "EMU moderne (hyp. 12 W/kg, 0,6, 0,6)":       dict(pm=12.0, a0=0.6, ab=0.6),
}
DWELL_MIN = 2.0


def load_limits(troncon: str) -> list[tuple[float, float, float]]:
    """[(km0, km1, vlim_kmh)] hors blocs urbains, triés."""
    gj = json.load(open(SEGMENTS, encoding="utf-8"))
    segs = sorted((f["properties"] for f in gj["features"]
                   if f["properties"]["troncon_id"] == troncon),
                  key=lambda p: p["km_debut"])
    out = []
    for p in segs:
        km0, km1 = p["km_debut"], p["km_fin"]
        v = min(p["vmax_S2_kmh"], BANDE)
        # soustraire les blocs urbains
        pieces = [(km0, km1)]
        for lo, hi in URBAN_BLOCKS[troncon]:
            nxt = []
            for a, b in pieces:
                if hi <= a or lo >= b:
                    nxt.append((a, b))
                else:
                    if a < lo:
                        nxt.append((a, lo))
                    if hi < b:
                        nxt.append((hi, b))
            pieces = nxt
        for a, b in pieces:
            if b - a > 1e-6:
                out.append((a, b, v))
    return out


def simulate(troncon: str, pm: float, a0: float, ab: float) -> float:
    """Minutes du profil dynamique sur l'interurbain libre (sans dwell)."""
    limits = load_limits(troncon)
    stops = set()
    # regrouper en tronçons contigus (séparés par les blocs urbains)
    stretches: list[list[tuple[float, float, float]]] = []
    for seg in limits:
        # tolérance de contiguïté 50 m : les frontières de segments ne sont pas
        # exactes en flottants ; sans elle, chaque segment devient un « tronçon »
        # avec arrêt complet à ses deux bouts (bogue de la v1 de ce test).
        if stretches and abs(seg[0] - stretches[-1][-1][1]) < 0.05:
            stretches[-1].append(seg)
        else:
            stretches.append([seg])
    total_s = 0.0
    fluid_s = sum((b - a) * 1000 / (v / 3.6) for a, b, v in limits if v > 0)
    for stretch in stretches:
        k0, k1 = stretch[0][0], stretch[-1][1]
        n = max(2, int((k1 - k0) * 1000 / DX) + 1)
        xs = [k0 + (k1 - k0) * i / (n - 1) for i in range(n)]
        vlim = []
        j = 0
        for x in xs:
            while j < len(stretch) - 1 and x > stretch[j][1] + 1e-9:
                j += 1
            vlim.append(stretch[j][2] / 3.6)
        # v = 0 aux extrémités du tronçon libre et aux gares intérieures
        zero_at = {0, n - 1}
        for skm in STOPS[troncon]:
            if k0 - 1e-6 <= skm <= k1 + 1e-6:
                zero_at.add(min(range(n), key=lambda i: abs(xs[i] - skm)))
        v = vlim[:]
        for i in zero_at:
            v[i] = 0.0
        dx = (k1 - k0) * 1000 / (n - 1)
        # passe avant (accélération limitée par a0 et P/m)
        for i in range(1, n):
            if i in zero_at:
                v[i] = 0.0
                continue
            a = min(a0, pm / max(v[i - 1], 1.0))
            v[i] = min(vlim[i], math.sqrt(v[i - 1] ** 2 + 2 * a * dx), v[i])
        # passe arrière (freinage)
        for i in range(n - 2, -1, -1):
            if i in zero_at:
                continue
            v[i] = min(v[i], math.sqrt(v[i + 1] ** 2 + 2 * ab * dx))
        # temps
        for i in range(n - 1):
            vm = max((v[i] + v[i + 1]) / 2, 0.5)
            total_s += dx / vm
    return total_s / 60.0, fluid_s / 60.0, len(stretches)


def hm(m: float) -> str:
    return f"{int(m // 60)} h {int(round(m % 60)):02d}"


def main() -> None:
    print("=== TEST EXPLORATOIRE accélération/freinage — S2, bande 200 (hors rapport) ===\n")
    for label, prm in TRAINS.items():
        print(f"--- {label} ---")
        print(f"{'tronçon':<8} {'rapport (fluide+5/arrêt)':>26} {'simulé (dyn.+2/arrêt)':>24} "
              f"{'écart':>7}  {'headline avant → après (lo)':>30}")
        for t in ("MTL-QC", "MTL-Ott", "Ott-TO", "MTL-TO"):
            n = len(STOPS[t])
            rep = REPORT_INTER_MIN[t] + REPORT_STOP_MIN * n
            dyn, fluid, nst = simulate(t, **prm)
            if abs(fluid - REPORT_INTER_MIN[t]) > 1.5:
                print(f"  [contrôle] {t} : fluide recalculé {fluid:.1f} vs rapport "
                      f"{REPORT_INTER_MIN[t]} ({nst} tronçons libres)")
            sim = dyn + DWELL_MIN * n
            delta = sim - rep
            tb_new = REPORT_TBASE[t] + delta
            lo_old, lo_new = REPORT_TBASE[t] * 1.09, tb_new * 1.09
            hi_old = REPORT_TBASE[t] * (1 + MARGE_HAUTE[t])
            hi_new = tb_new * (1 + MARGE_HAUTE[t])
            print(f"{t:<8} {rep:>22.1f} min {sim:>20.1f} min {delta:>+6.1f}  "
                  f"{hm(lo_old)} à {hm(hi_old)} → {hm(lo_new)} à {hm(hi_new)}")
        print()
    print(f"Sensibilité dwell : le « simulé » ci-dessus prend {DWELL_MIN:.0f} min d'arrêt en gare ;")
    print("chaque minute de dwell en plus ajoute n_arrêts minutes au tronçon (3 à 10 selon le tronçon).")


if __name__ == "__main__":
    main()

"""Étape 36 — Ce que valent les blocs urbains, poste par poste.

Question posée le 2026-09-06 (Pierre, via François : « 3 à 4 minutes de gain
crédibles dans la zone urbaine de Québec ») : combien les COURBES SEULES
rapportent-elles dans chaque bloc urbain, une fois séparées de la signalisation
et du mou de cohabitation que porte l'horaire actuel ?

Pour chaque bloc urbain GTFS (délimitation du 21), le profil dynamique du 21 est
roulé À L'INTÉRIEUR du bloc seulement (v = 0 aux deux bornes et aux gares
intermédiaires du bloc, immobilisation DWELL_MIN à ces gares), avec la même rame
et la même géométrie publiée que les scénarios :

    G      = minutes figées du bloc (médiane GTFS des sillons, moins l'approche de
             gare hors bloc pour Montréal : bloc_minutes_figees du 21)
    A1     = profil train actuel, plafond 153 km/h (classe actuelle)
    A2     = profil train pendulaire, plafond 153
    A2p    = profil train pendulaire, plafond 201

    cohabitation urbaine = G − A1 × 1,10        (borné à ≥ 0)
    courbes (pendulaire)  = (A1 − A2) × 1,10
    signalisation et PN   = (A2 − A2p) × 1,10

La somme des trois vaut G − A2p × 1,10 = le gain total du bloc, tel qu'il entre
dans le scénario 2 (blocs libres) ; à l'écrasement près quand G porte moins de
10 % de marge (alors la cohabitation est nulle et les deux autres postes sont
réduits au prorata, même règle que le 32).

Sortie : livrables/gains_urbains.csv (une ligne par bloc), lue par le 32 pour
attribuer à la tranche « zones urbaines » les courbes et la signalisation
seulement, et reverser le reste à la cohabitation.
"""
import csv
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
m21 = importlib.import_module("21_tbase_bande")
from utils import DELIVERABLES

MARGE = 1.10
P_CLASSE, P_PLAFOND = 153, 201


def bloc_minutes(t, segs, km0, km1, scenario, bande):
    """Minutes de roulement + immobilisation dans [km0, km1], v=0 aux bornes."""
    pieces = []
    for p in segs:
        a, b = max(p["km_debut"], km0), min(p["km_fin"], km1)
        if b - a > 1e-6:
            pieces.append((a, b, min(p[f"vmax_{scenario}_kmh"], bande)))
    pieces.sort()
    a0, ab = m21.TRAIN_A[scenario]
    pm = m21.train_pm(scenario, bande)
    # gares intermédiaires strictement à l'intérieur du bloc
    inner = [km for (_, km) in m21.INTERMEDIATE_STOPS[t] if km0 + 0.1 < km < km1 - 0.1]
    saved = m21.INTERMEDIATE_STOPS[t]
    m21.INTERMEDIATE_STOPS[t] = [("x", km) for km in inner]
    try:
        roul = m21._dynamic_minutes(t, pieces, pm, a0, ab)
    finally:
        m21.INTERMEDIATE_STOPS[t] = saved
    return roul + m21.DWELL_MIN * len(inner), len(inner)


def main():
    pair_minutes, _ = m21.load_gtfs_pair_minutes()
    by_t = m21.load_segments()
    rows = []
    for blk in m21.URBAN_GTFS_BLOCKS:
        (t, a, b, name, km0, km1) = blk
        G = m21.bloc_minutes_figees(pair_minutes, by_t, blk)
        A1, n = bloc_minutes(t, by_t[t], km0, km1, "S1", P_CLASSE)
        A2, _ = bloc_minutes(t, by_t[t], km0, km1, "S2", P_CLASSE)
        A2p, _ = bloc_minutes(t, by_t[t], km0, km1, "S2", P_PLAFOND)
        gain = G - A2p * MARGE
        cohab = G - A1 * MARGE
        courbes = (A1 - A2) * MARGE
        classe = (A2 - A2p) * MARGE
        ecr = 0.0
        if cohab < 0:
            ecr = -cohab
            f = gain / max(courbes + classe, 1e-9)
            courbes, classe, cohab = courbes * f, classe * f, 0.0
        rows.append({"troncon": t, "bloc": name, "km_debut": km0, "km_fin": km1,
                     "longueur_km": round(km1 - km0, 1), "n_arrets_internes": n,
                     "minutes_gtfs": round(G, 1),
                     "profil_actuel_153_min": round(A1, 1),
                     "profil_pendulaire_153_min": round(A2, 1),
                     "profil_pendulaire_201_min": round(A2p, 1),
                     "gain_total_min": round(gain, 1),
                     "gain_cohabitation_min": round(cohab, 1),
                     "gain_courbes_min": round(courbes, 1),
                     "gain_signalisation_pn_min": round(classe, 1),
                     "info_marge_normative_excedentaire_min": round(ecr, 1)})
    out = DELIVERABLES / "gains_urbains.csv"
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
        w.writeheader(); w.writerows(rows)
    print(f"{'tronçon':<8} {'bloc':<50} {'GTFS':>5} {'A1':>5} {'A2':>5} {'A2p':>5} | "
          f"{'gain':>5} {'cohab':>5} {'courb':>5} {'sign':>5}")
    for r in rows:
        print(f"{r['troncon']:<8} {r['bloc']:<50} {r['minutes_gtfs']:>5} "
              f"{r['profil_actuel_153_min']:>5} {r['profil_pendulaire_153_min']:>5} "
              f"{r['profil_pendulaire_201_min']:>5} | {r['gain_total_min']:>5} "
              f"{r['gain_cohabitation_min']:>5} {r['gain_courbes_min']:>5} "
              f"{r['gain_signalisation_pn_min']:>5}")
    print(f"Écrit {out.name}")


if __name__ == "__main__":
    main()

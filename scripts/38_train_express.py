"""Étape 38 — Contre-hypothèse 2 : un train express (ronde UPA, novembre 2026).

Même voie, même train et même marge que l'emprise optimisée publiée (S2 pendulaire,
plafond 201 km/h, blocs urbains libres, × 1,10), mais sans aucun arrêt intermédiaire :
le train ne s'arrête qu'aux extrémités, comme ALTO ne dessert sur ce corridor que les
grandes villes (Québec, Montréal, Ottawa, Toronto). L'écart avec la table publiée
mesure ce que coûtent les arrêts dans les villes intermédiaires.

Sortie : livrables/train_express.csv.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pandas as pd

os.environ["BLOCS_URBAINS"] = "libres"          # configuration publiée (scénario 2)
sys.path.insert(0, str(Path(__file__).parent))
from utils import DELIVERABLES                    # noqa: E402

_spec = importlib.util.spec_from_file_location("m21", Path(__file__).parent / "21_tbase_bande.py")
m21 = importlib.util.module_from_spec(_spec)
sys.modules["m21"] = m21            # requis par @dataclass
_spec.loader.exec_module(m21)

MARGE = 1.10
SCENARIO, BANDE = "S2", 201.0
LIBELLES = {"MTL-QC": "Montréal-Québec", "MTL-Ott": "Montréal-Ottawa",
            "Ott-TO": "Ottawa-Toronto", "MTL-TO": "Montréal-Toronto"}
OUT = DELIVERABLES / "train_express.csv"


def main() -> None:
    by_t = m21.load_segments()
    pub = pd.read_csv(DELIVERABLES / "temps_scenario_2.csv", sep=";")
    rows = []
    for t, lib in LIBELLES.items():
        ref = pub[(pub.troncon == t) & (pub.scenario == "pendulaire") & (pub.bande_kmh == 201)].iloc[0]
        arrets = m21.INTERMEDIATE_STOPS[t]
        m21.INTERMEDIATE_STOPS[t] = []
        try:
            inter, fenetre = m21.integrate(t, by_t[t], SCENARIO, BANDE)
        finally:
            m21.INTERMEDIATE_STOPS[t] = arrets
        express = inter + fenetre
        rows.append({"trajet": lib, "n_arrets_omnibus": len(arrets),
                     "gares_omnibus": ", ".join(n for n, _ in arrets),
                     "omnibus_base_min": ref.tbase_sans_marge_min,
                     "omnibus_avec_marge_min": round(ref.tbase_sans_marge_min * MARGE, 1),
                     "express_base_min": round(express, 1),
                     "express_avec_marge_min": round(express * MARGE, 1),
                     "gain_min": round((ref.tbase_sans_marge_min - express) * MARGE, 1),
                     "source": "moteur de l'étape 21, S2 pendulaire, 201 km/h, blocs urbains libres, "
                               "aucun arrêt intermédiaire ; × 1,10"})
    df = pd.DataFrame(rows)
    df.to_csv(OUT, sep=";", index=False, encoding="utf-8-sig")
    print(df[["trajet", "n_arrets_omnibus", "omnibus_avec_marge_min", "express_avec_marge_min", "gain_min"]]
          .to_string(index=False))
    print(f"\nÉcrit {OUT.name}.")


if __name__ == "__main__":
    main()

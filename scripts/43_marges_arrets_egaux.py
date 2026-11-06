"""Étape 43 — La marge réelle et le gain, à arrêts égaux.

Pourquoi. L'horaire de VIA est une médiane de trains qui alternent leurs arrêts. Notre train,
lui, s'arrête à toutes les gares à chaque passage. Les comparer directement sous-estime la
marge d'aujourd'hui et le gain du projet, surtout sur Ottawa-Toronto (12 arrêts contre 7).

Ce que ça mesure, trajet par trajet (décision Vincent, 2026-11-06) :

  Marge réelle : chaque train de l'horaire contre le train actuel simulé avec SES arrêts,
  zones urbaines à l'horaire, régime actuel de 160 km/h. On garde la médiane des trains.

  Gain à arrêts égaux, par trois voies, parce qu'aucune ne suffit seule :
    - train par train : chaque train de l'horaire contre NOTRE train avec les mêmes arrêts ;
    - tendance de l'horaire : droite horaire = a + b × arrêts, prolongée à tous les arrêts,
      sans passer par le modèle ;
    - trains complets : les trains réels qui font tous les arrêts, ou un de moins.

La marge sert aussi à la règle de scenarios.marge_de : 10 %, ou la marge actuelle si elle est
plus basse. Le garde-fou arrête le pipeline si MARGE_MESUREE ne correspond plus à la mesure.

Lecture seule pour le moteur : les temps de base ne changent pas. À lancer après les trois
passes de l'étape 21 et avant 38. Sortie : livrables/marges_arrets_egaux.csv.
"""
from __future__ import annotations

import importlib.util
import io
import os
import statistics as st
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
from scenarios import MARGE_MESUREE, MARGE_NORMALE, PLAFOND_PUBLIE, marge_de   # noqa: E402
from utils import DELIVERABLES                                                 # noqa: E402

REGIME_ACTUEL_KMH = 160.0      # le même que l'étape 22 : régime de vitesse actuel du corridor
TOLERANCE_MARGE = 0.001        # écart permis entre MARGE_MESUREE et la mesure
LIBELLES = {"MTL-QC": "Montréal-Québec", "MTL-Ott": "Montréal-Ottawa",
            "Ott-TO": "Ottawa-Toronto", "MTL-TO": "Montréal-Toronto"}
OUT = DELIVERABLES / "marges_arrets_egaux.csv"


def charger(nom: str, libres: bool):
    """Le moteur lit BLOCS_URBAINS à l'import : il faut deux instances, une par mode."""
    os.environ.pop("SEGMENTS_OVERRIDE", None)
    os.environ.pop("BLOCS_URBAINS", None)
    if libres:
        os.environ["BLOCS_URBAINS"] = "libres"
    spec = importlib.util.spec_from_file_location(nom, ICI / "21_tbase_bande.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nom] = mod              # requis par @dataclass
    spec.loader.exec_module(mod)
    os.environ.pop("BLOCS_URBAINS", None)
    return mod


LIBRES = charger("m21_libres", True)
FIGES = charger("m21_figes", False)
TOUS = {t: list(v) for t, v in FIGES.INTERMEDIATE_STOPS.items()}


def simple(s: str) -> str:
    return s.replace("é", "e").replace("è", "e").lower()


def gare(t: str, nom: str):
    for n, km in TOUS[t]:
        if simple(n) in simple(nom) or simple(nom) in simple(n):
            return n, km
    return None


def notre_train(t: str, arrets: list, segs: list) -> float:
    """Train de référence au plafond publié, zones urbaines libres, avec CES arrêts, marge comprise."""
    LIBRES.INTERMEDIATE_STOPS[t] = arrets
    try:
        roule = LIBRES._dynamic_minutes(t, LIBRES._free_pieces(t, segs, "S2", float(PLAFOND_PUBLIE)),
                                        LIBRES.RAME_PENDULAIRE)
    finally:
        LIBRES.INTERMEDIATE_STOPS[t] = TOUS[t]
    return (roule + len(arrets) * LIBRES.DWELL_MIN) * marge_de(t)


def train_actuel(t: str, arrets: list, segs: list, urbain: float) -> float:
    """Temps de base du train actuel, zones urbaines à l'horaire, avec CES arrêts."""
    FIGES.INTERMEDIATE_STOPS[t] = arrets
    try:
        inter, ottawa = FIGES.integrate(t, segs, "S1", REGIME_ACTUEL_KMH)
    finally:
        FIGES.INTERMEDIATE_STOPS[t] = TOUS[t]
    blocs = [b for b in FIGES.URBAN_GTFS_BLOCKS + FIGES.URBAN_KM_BLOCKS if b[0] == t]
    n = sum(1 for _, km in arrets if FIGES.in_any_block(t, km - 1e-6, km + 1e-6, blocs) == 0)
    return urbain + ottawa + inter + n * FIGES.DWELL_MIN


def voyages_gtfs() -> tuple[dict, dict]:
    with zipfile.ZipFile(FIGES.GTFS_ZIP) as z:
        stt = pd.read_csv(io.BytesIO(z.read("stop_times.txt")), dtype={"trip_id": str, "stop_id": str})
        stops = pd.read_csv(io.BytesIO(z.read("stops.txt")), dtype={"stop_id": str})
    stt = stt.sort_values(["trip_id", "stop_sequence"])
    v = {tid: list(zip(g.stop_id, g.arrival_time, g.departure_time)) for tid, g in stt.groupby("trip_id")}
    return v, dict(zip(stops.stop_id, stops.stop_name))


def trains_du_trajet(t: str, voyages: dict, noms: dict) -> list[tuple[float, tuple]]:
    """(minutes à l'horaire, arrêts) de chaque train qui fait le trajet entier."""
    a, b = FIGES.ENDPOINTS[t]
    out = []
    for seq in voyages.values():
        ids = [s for s, _, _ in seq]
        if a not in ids or b not in ids:
            continue
        i, j = sorted((ids.index(a), ids.index(b)))
        h = FIGES._hms_to_min(seq[j][1]) - FIGES._hms_to_min(seq[i][2])
        arrets = {g for g in (gare(t, noms[s]) for s, _, _ in seq[i + 1:j]) if g}
        out.append((h, tuple(sorted(arrets, key=lambda x: x[1]))))
    return out


def main() -> None:
    voyages, noms = voyages_gtfs()
    by_t = FIGES.load_segments()
    paires, _ = FIGES.load_gtfs_pair_minutes()
    urbain = {t: 0.0 for t in FIGES.TRONCONS}
    for bloc in FIGES.URBAN_GTFS_BLOCKS:
        urbain[bloc[0]] += FIGES.bloc_minutes_figees(paires, by_t, bloc)

    lignes = []
    for t, lib in LIBELLES.items():
        trains = trains_du_trajet(t, voyages, noms)
        cache: dict[tuple, tuple[float, float]] = {}
        for _, p in trains:
            if p not in cache:
                cache[p] = (notre_train(t, list(p), by_t[t]), train_actuel(t, list(p), by_t[t], urbain[t]))
        h = np.array([x for x, _ in trains])
        n = np.array([len(p) for _, p in trains], float)
        nous = np.array([cache[p][0] for _, p in trains])
        actuel = np.array([cache[p][1] for _, p in trains])

        nmax = len(TOUS[t])
        publie = notre_train(t, TOUS[t], by_t[t])
        tous_arrets = train_actuel(t, TOUS[t], by_t[t], urbain[t])
        pente, origine = np.polyfit(n, h, 1)
        complets = h[n >= nmax - 1]
        lignes.append({
            "troncon": t, "trajet": lib, "trains": len(trains), "combinaisons_arrets": len(cache),
            "arrets_notre_train": nmax, "arrets_train_median": float(np.median(n)),
            "horaire_median_min": round(float(np.median(h)), 1),
            "base_tous_arrets_min": round(tous_arrets, 1),
            "marge_tous_arrets_pct": round((np.median(h) / tous_arrets - 1) * 100, 1),
            "marge_arrets_egaux_pct": round(float(np.median(h / actuel - 1)) * 100, 1),
            "marge_arrets_egaux_min": round(float(np.median(h - actuel)), 1),
            "marge_retenue_pct": round((marge_de(t) - 1) * 100, 1),
            "notre_train_publie_min": round(publie, 1),
            "gain_publie_min": round(float(np.median(h)) - publie, 1),
            "gain_train_par_train_min": round(float(np.median(h - nous)), 1),
            "gain_tendance_horaire_min": round(origine + pente * nmax - publie, 1),
            "gain_trains_complets_min": round(float(np.median(complets)) - publie, 1),
            "trains_complets": int(len(complets)),
            "minutes_par_arret_horaire": round(float(pente), 1),
            "minutes_par_arret_modele": round(float(np.polyfit(n, nous, 1)[0]), 1),
        })

    df = pd.DataFrame(lignes)
    df.to_csv(OUT, sep=";", index=False, encoding="utf-8-sig")
    print(df.drop(columns=["troncon"]).T.to_string(header=False))

    # Garde-fou : la règle de scenarios.marge_de doit refléter la mesure.
    for r in lignes:
        t, mesuree = r["troncon"], r["marge_arrets_egaux_pct"] / 100
        sous_seuil = mesuree < MARGE_NORMALE - 1
        if sous_seuil and abs(marge_de(t) - 1 - mesuree) > TOLERANCE_MARGE:
            sys.exit(f"{t} : marge mesurée {mesuree:.3f}, scenarios.MARGE_MESUREE à mettre à jour")
        if not sous_seuil and t in MARGE_MESUREE:
            sys.exit(f"{t} : marge mesurée {mesuree:.3f}, au-dessus du seuil : retirer de MARGE_MESUREE")
    print(f"\nMarges conformes à scenarios.py ; écrit {OUT.name}")


if __name__ == "__main__":
    main()

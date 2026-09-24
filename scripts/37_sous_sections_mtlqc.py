"""Étape 37 — Montréal-Québec par sous-section (demande de Vision Transport, sept. 2026).

Découpe le trajet Montréal-Québec aux gares de Saint-Hilaire (km 34,6 : gare
exo de Mont-Saint-Hilaire, projetée sur le tracé ; VIA n'y arrête pas),
Saint-Hyacinthe (km 53,2) et Drummondville (km 100,0), et compare :
  - aujourd'hui : médiane des horaires VIA entre gares (GTFS, arrivée − départ,
    donc SANS l'immobilisation à la gare de départ) ; pour Montréal-Saint-Hilaire,
    où VIA passe sans arrêt, la médiane des trains de banlieue exo (ligne
    Mont-Saint-Hilaire, ressources/exo_trains_GTFS.zip) ;
  - emprise optimisée : temps de passage cumulés du moteur de l'étape 21 dans la
    configuration publiée (S2 pendulaire, plafond 201 km/h, blocs urbains libres),
    × 1,10 de marge. Les sous-sections vont du départ d'une gare à l'arrivée à la
    suivante ; le total Montréal-Québec ajoute les deux immobilisations (2 min)
    à Saint-Hyacinthe et à Drummondville. Sa somme est le temps publié (135,7 min).

Sortie : livrables/sous_sections_montreal_quebec.csv.
"""
from __future__ import annotations

import importlib.util
import io
import math
import os
import sys
import zipfile
from pathlib import Path
from statistics import median

import pandas as pd

os.environ["BLOCS_URBAINS"] = "libres"          # configuration publiée (scénario 2)
sys.path.insert(0, str(Path(__file__).parent))
from utils import DELIVERABLES, RESOURCES         # noqa: E402

_spec = importlib.util.spec_from_file_location("m21", Path(__file__).parent / "21_tbase_bande.py")
m21 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m21)

T = "MTL-QC"
MARGE = 1.10
SCENARIO, BANDE = "S2", 201.0
GARES = [("Saint-Hilaire", 34.59, False), ("Saint-Hyacinthe", 53.24, True),
         ("Drummondville", 100.01, True), ("Québec", 269.85, False)]
VIA_IDS = {"Montréal": "226", "Saint-Hyacinthe": "631", "Drummondville": "630", "Québec": "628"}
OUT = DELIVERABLES / "sous_sections_montreal_quebec.csv"


def _hms(s: str) -> float:
    h, m, sec = s.split(":")
    return int(h) * 60 + int(m) + int(sec) / 60


def gtfs_medians(zip_path: Path, pairs: list[tuple[str, str]], names_to_ids=None) -> dict:
    """Médiane (arrivée B − départ A) des voyages desservant A puis B."""
    with zipfile.ZipFile(zip_path) as z:
        st = pd.read_csv(io.BytesIO(z.read("stop_times.txt")), dtype={"trip_id": str, "stop_id": str})
        if names_to_ids is None:
            stops = pd.read_csv(io.BytesIO(z.read("stops.txt")), dtype={"stop_id": str})
            names_to_ids = {}
            for name in {n for p in pairs for n in p}:
                names_to_ids[name] = set(stops[stops.stop_name.str.contains(name, regex=False)].stop_id)
    st = st.sort_values(["trip_id", "stop_sequence"])
    samp: dict[tuple[str, str], list[float]] = {p: [] for p in pairs}
    for _, g in st.groupby("trip_id"):
        seq = list(zip(g.stop_id, g.departure_time, g.arrival_time))
        for a, b in pairs:
            ia = [i for i, s in enumerate(seq) if s[0] in names_to_ids[a]]
            ib = [i for i, s in enumerate(seq) if s[0] in names_to_ids[b]]
            if ia and ib:
                lo, hi = sorted([ia[0], ib[0]])
                dt = _hms(seq[hi][2]) - _hms(seq[lo][1])
                if 0 < dt < 1440:
                    samp[(a, b)].append(dt)
    return {p: (round(median(v), 1), len(v)) for p, v in samp.items() if v}


def cumulative_profile() -> tuple[list[float], list[float]]:
    """Temps cumulé (min, sans marge) le long du tronçon, immobilisations incluses.
    Même profil que 21_tbase_bande._dynamic_minutes, mais en gardant la courbe."""
    segs = m21.load_segments()[T]
    pieces = m21._free_pieces(T, segs, SCENARIO, BANDE)
    a0, ab = m21.TRAIN_A[SCENARIO]
    pm = m21.train_pm(SCENARIO, BANDE)
    stop_kms = [km for (_, km) in m21.INTERMEDIATE_STOPS[T]]
    stretches: list[list] = []
    for seg in pieces:
        if stretches and abs(seg[0] - stretches[-1][-1][1]) < m21.CONTIG_TOL_KM:
            stretches[-1].append(seg)
        else:
            stretches.append([seg])
    xs_all, t_all, t = [], [], 0.0
    for stretch in stretches:
        k0, k1 = stretch[0][0], stretch[-1][1]
        n = max(2, int((k1 - k0) * 1000 / m21.DX_M) + 1)
        xs = [k0 + (k1 - k0) * i / (n - 1) for i in range(n)]
        vlim, j = [], 0
        for x in xs:
            while j < len(stretch) - 1 and x > stretch[j][1] + 1e-9:
                j += 1
            vlim.append(stretch[j][2] / 3.6)
        zero_at = {0, n - 1}
        for skm in stop_kms:
            if k0 - 1e-6 <= skm <= k1 + 1e-6:
                zero_at.add(min(range(n), key=lambda i: abs(xs[i] - skm)))
        v = vlim[:]
        for i in zero_at:
            v[i] = 0.0
        dx = (k1 - k0) * 1000 / (n - 1)
        for i in range(1, n):
            if i in zero_at:
                v[i] = 0.0
                continue
            a = min(a0, pm / max(v[i - 1], 1.0))
            v[i] = min(vlim[i], math.sqrt(v[i - 1] ** 2 + 2 * a * dx), v[i])
        for i in range(n - 2, -1, -1):
            if i in zero_at:
                continue
            v[i] = min(v[i], math.sqrt(v[i + 1] ** 2 + 2 * ab * dx))
        for i in range(n - 1):
            xs_all.append(xs[i])
            t_all.append(t)
            t += dx / max((v[i] + v[i + 1]) / 2, 0.5) / 60
            if (i + 1) in zero_at and i + 1 != n - 1:      # arrivée en gare intermédiaire
                t += m21.DWELL_MIN
        xs_all.append(xs[-1])
        t_all.append(t)
    return xs_all, t_all


def main() -> None:
    xs, tc = cumulative_profile()
    total_base = tc[-1]                                    # = tbase du CSV publié (123,4)
    pub = pd.read_csv(DELIVERABLES / "temps_scenario_2.csv", sep=";")
    ref = float(pub[(pub.troncon == T) & (pub.scenario == "pendulaire") & (pub.bande_kmh == 201)]
                .tbase_sans_marge_min.iloc[0])
    assert abs(total_base - ref) < 0.15, (total_base, ref)

    via = gtfs_medians(RESOURCES / "viarail_GTFS.zip",
                       [("Montréal", "Saint-Hyacinthe"), ("Saint-Hyacinthe", "Drummondville"),
                        ("Drummondville", "Québec"), ("Montréal", "Québec"),
                        ("Montréal", "Drummondville")],
                       {k: {v} for k, v in VIA_IDS.items()})
    exo = gtfs_medians(RESOURCES / "exo_trains_GTFS.zip", [("Gare Centrale", "Mont-Saint-Hilaire")])
    exo_min, exo_n = exo[("Gare Centrale", "Mont-Saint-Hilaire")]

    def t_at(km: float) -> float:
        return tc[min(range(len(xs)), key=lambda i: abs(xs[i] - km))]

    rows, prev_name, prev_km, prev_dep = [], "Montréal", 0.0, 0.0
    for name, km, is_stop in GARES:
        arr = t_at(km) if name != "Québec" else total_base
        base = arr - prev_dep
        auj = None
        if (prev_name, name) in via:
            auj, n = via[(prev_name, name)]
            src = f"VIA, médiane de {n} sillons GTFS"
        elif name == "Saint-Hilaire":
            auj = exo_min
            src = (f"exo ligne Mont-Saint-Hilaire, médiane de {exo_n} trains, "
                   "5 arrêts intermédiaires ; VIA passe sans arrêt")
        else:
            src = "aucun train direct aujourd'hui"
        rows.append({"sous_section": f"{prev_name} à {name}", "km_debut": prev_km, "km_fin": km,
                     "longueur_km": round(km - prev_km, 1),
                     "aujourd_hui_min": auj, "source_aujourd_hui": src,
                     "optimise_base_min": round(base, 1),
                     "optimise_avec_marge_min": round(base * MARGE, 1),
                     "note": ("temps de passage sans arrêt à Saint-Hilaire ; inclut l'arrêt à Saint-Lambert"
                              if name == "Saint-Hilaire" else "")})
        prev_name, prev_km = name, km
        prev_dep = arr + (m21.DWELL_MIN if is_stop else 0.0)
    # --- lignes cumulées depuis Montréal (table publiée : « gare par gare »)
    for name, km, _ in GARES:
        arr = t_at(km) if name != "Québec" else total_base
        if ("Montréal", name) in via:
            auj, n = via[("Montréal", name)]
            src = f"VIA, médiane de {n} sillons GTFS"
        else:
            auj, src = exo_min, f"exo ligne Mont-Saint-Hilaire, médiane de {exo_n} trains ; VIA passe sans arrêt"
        rows.append({"sous_section": f"Montréal à {name} (cumulé)", "km_debut": 0.0, "km_fin": km,
                     "longueur_km": round(km, 1), "aujourd_hui_min": auj, "source_aujourd_hui": src,
                     "optimise_base_min": round(arr, 1), "optimise_avec_marge_min": round(arr * MARGE, 1),
                     "note": "temps à l'arrivée, arrêts intermédiaires compris"})
    tot_auj, tot_n = via[("Montréal", "Québec")]
    rows.append({"sous_section": "Montréal à Québec, arrêts compris", "km_debut": 0.0, "km_fin": 269.85,
                 "longueur_km": 269.9, "aujourd_hui_min": tot_auj,
                 "source_aujourd_hui": f"VIA, médiane de {tot_n} sillons GTFS",
                 "optimise_base_min": round(total_base, 1),
                 "optimise_avec_marge_min": round(total_base * MARGE, 1),
                 "note": "les sous-sections + 2 × 2 min d'immobilisation (Saint-Hyacinthe, Drummondville) = ce total"})
    df = pd.DataFrame(rows)
    df.to_csv(OUT, sep=";", index=False, encoding="utf-8-sig")
    print(df[["sous_section", "longueur_km", "aujourd_hui_min", "optimise_avec_marge_min"]].to_string(index=False))
    print(f"\nÉcrit {OUT.name}. Total base {total_base:.1f} = référence {ref:.1f} ; "
          f"× {MARGE} = {total_base * MARGE:.1f} min.")


if __name__ == "__main__":
    main()

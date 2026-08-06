"""Étape 21 — Moteur T_base : temps de parcours par bande de vitesse × scénario.

Le modèle du rapport minimal (plan de match v3) :

    T(bande, scénario) = Σ blocs urbains figés (minutes actuelles GTFS)
                       + ∫ interurbain dx / V(x)   où V(x) = min(v_geo_scenario(x), bande)
                       + arrêts (NORMALISATION ~5 min/arrêt interurbain)
                       [+ marge — encadrée à l'étape 4, PAS ajoutée ici]

Décision structurante : les zones urbaines sont FIGÉES à l'horaire actuel. Aucun
gain pendulaire/dévers n'y est compté, quel que soit le scénario ou la bande.

Délimitation des blocs urbains (à documenter au rapport) :
  - Montréal (ouest, tronçons MTL-Ott / MTL-TO) : Central ↔ Dorval (17,8 km),
    minutes = médiane GTFS de la paire.
  - Montréal (est, tronçon MTL-QC via pont Victoria) : Central ↔ Saint-Lambert
    (6,1 km), minutes = médiane GTFS. NB : le plan v3 nommait « Central↔Dorval » ;
    MTL-QC sort par la rive sud, le bloc pertinent est Saint-Lambert.
  - Toronto : Union ↔ Guildwood (20,2 km), minutes = médiane GTFS. (Le plan v3
    évoquait « Guildwood/Oshawa » ; Guildwood retenu = borne courte, l'inclusion
    jusqu'à Oshawa est couverte par la sensibilité ±20 %.)
  - Québec : Sainte-Foy ↔ Québec (19,9 km, inclut le pont de Québec), médiane GTFS.
  - Ottawa : PAS de gare d'approche proche (Casselman à 47 km, Smiths Falls à
    65 km) → fenêtre kilométrique HYPOTHÈSE de ±10 km autour de la gare, traversée
    au plafond S1 borné par la bande (règle « aucun gain en urbain »), pas de
    minutes GTFS isolables. Couverte par la sensibilité ±20 %.

Arrêts : +5 min par arrêt intermédiaire HORS blocs urbains (normalisation ; borne
mesurée : pilote sans-arrêt 2025 = 30-40 min pour 4 arrêts sautés, soit 7,5-10 min
par arrêt en conditions réelles de cohabitation — le 5 min est donc une borne
basse volontairement favorable, documentée). Les arrêts situés dans un bloc urbain
sont déjà comptés dans les minutes GTFS figées du bloc.

Sensibilité : blocs urbains ±20 % (colonnes lo/hi).

Sorties : livrables/tbase_par_bande.csv (tronçon × scénario × bande) et
livrables/blocs_urbains.csv (délimitation + minutes GTFS mesurées).
La marge (étape 4) s'ajoutera par-dessus : T_base ici = SANS marge.
"""
from __future__ import annotations

import io
import json
import zipfile
from statistics import median

import pandas as pd

from utils import INTERMEDIATES, DELIVERABLES, RESOURCES

GTFS_ZIP = RESOURCES / "viarail_GTFS.zip"
SEGMENTS = INTERMEDIATES / "segments.geojson"
OUT_TBASE = DELIVERABLES / "tbase_par_bande.csv"
OUT_BLOCS = DELIVERABLES / "blocs_urbains.csv"

BANDES_KMH = [160, 200, 250, 300]
MIN_PER_STOP = 5.0            # normalisation, voir docstring
URBAN_SENS = 0.20             # sensibilité ±20 % sur les blocs urbains
OTTAWA_WINDOW_KM = 10.0       # HYPOTHÈSE : fenêtre urbaine ±10 km autour d'Ottawa

# Blocs urbains ancrés sur des paires de gares GTFS : (tronçon, stop_id A, stop_id B,
# nom, km_debut, km_fin). km relevés dans corridor_gtfs.geojson.
URBAN_GTFS_BLOCKS = [
    ("MTL-QC",  "226", "343", "Montréal Central ↔ Saint-Lambert (pont Victoria)", 0.0, 6.11),
    ("MTL-QC",  "629", "628", "Sainte-Foy ↔ Québec (pont de Québec)",             249.98, 269.85),
    ("MTL-Ott", "226", "332", "Montréal Central ↔ Dorval",                        0.0, 17.79),
    ("Ott-TO",  "450", "119", "Guildwood ↔ Toronto Union",                        423.93, 444.05),
    ("MTL-TO",  "226", "332", "Montréal Central ↔ Dorval",                        0.0, 17.79),
    ("MTL-TO",  "450", "119", "Guildwood ↔ Toronto Union",                        517.94, 538.06),
]
# Blocs urbains sans ancre GTFS : fenêtre km, traversée au plafond S1 ∧ bande.
URBAN_KM_BLOCKS = [
    ("MTL-Ott", "Ottawa (approche est, fenêtre ±10 km — HYPOTHÈSE)", 175.42, 185.42),
    ("Ott-TO",  "Ottawa (approche ouest, fenêtre ±10 km — HYPOTHÈSE)", 0.0, 10.0),
]

# Gares intermédiaires par tronçon (hors extrémités), avec leur km — pour compter
# les arrêts interurbains (hors blocs urbains). Relevé de corridor_gtfs.geojson ;
# l'Aéroport (555) est une desserte alternative de Dorval, non comptée en plus.
INTERMEDIATE_STOPS = {
    "MTL-QC":  [("Saint-Lambert", 6.11), ("Saint-Hyacinthe", 53.24), ("Drummondville", 100.01),
                ("Charny", 245.04), ("Sainte-Foy", 249.98)],
    "MTL-Ott": [("Dorval", 17.79), ("Coteau", 62.28), ("Alexandria", 99.43), ("Casselman", 138.78)],
    "Ott-TO":  [("Smiths Falls", 64.62), ("Brockville", 110.0), ("Gananoque", 155.83),
                ("Kingston", 191.99), ("Napanee", 227.49), ("Belleville", 262.44),
                ("Trenton Junction", 281.92), ("Cobourg", 332.06), ("Port Hope", 342.88),
                ("Oshawa", 393.31), ("Guildwood", 423.93)],
    "MTL-TO":  [("Dorval", 17.79), ("Brockville", 204.72), ("Gananoque", 249.75),
                ("Kingston", 285.97), ("Napanee", 321.47), ("Belleville", 356.42),
                ("Trenton Junction", 375.9), ("Cobourg", 426.05), ("Port Hope", 436.86),
                ("Oshawa", 487.24), ("Guildwood", 517.94)],
}

TRONCONS = ["MTL-QC", "MTL-Ott", "Ott-TO", "MTL-TO"]
# Extrémités (stop_id) pour le T_horaire actuel de référence.
ENDPOINTS = {"MTL-QC": ("226", "628"), "MTL-Ott": ("226", "617"),
             "Ott-TO": ("617", "119"), "MTL-TO": ("226", "119")}


# ----------------------------------------------------------------- GTFS
def _hms_to_min(s: str) -> float:
    h, m, sec = s.split(":")
    return int(h) * 60 + int(m) + int(sec) / 60.0


def load_gtfs_pair_minutes() -> tuple[dict, dict]:
    """Minutes médianes à l'horaire entre paires de gares, tous sillons confondus.

    Retourne (pair_minutes, endpoint_minutes) :
      pair_minutes[(A, B)] = médiane des (arrivée B − départ A) sur les voyages
      desservant A puis B (dans les deux sens : (A,B) et (B,A) agrégés, la
      géométrie étant la même).
    """
    with zipfile.ZipFile(GTFS_ZIP) as z:
        st = pd.read_csv(io.BytesIO(z.read("stop_times.txt")),
                         dtype={"trip_id": str, "stop_id": str})
    st = st.sort_values(["trip_id", "stop_sequence"])

    wanted_pairs = {(a, b) for _, a, b, *_ in URBAN_GTFS_BLOCKS} | set(ENDPOINTS.values())
    wanted_stops = {s for p in wanted_pairs for s in p}

    samples: dict[tuple[str, str], list[float]] = {p: [] for p in wanted_pairs}
    sub = st[st.stop_id.isin(wanted_stops)]
    for _, g in sub.groupby("trip_id"):
        seq = list(zip(g.stop_id, g.departure_time, g.arrival_time))
        pos = {sid: i for i, (sid, _, _) in enumerate(seq)}
        for (a, b) in wanted_pairs:
            lo, hi = (a, b) if pos.get(a, 9e9) < pos.get(b, -1) else (b, a)
            if a in pos and b in pos and pos[lo] < pos[hi]:
                dep = seq[pos[lo]][1]
                arr = seq[pos[hi]][2]
                if isinstance(dep, str) and isinstance(arr, str):
                    dt = _hms_to_min(arr) - _hms_to_min(dep)
                    if 0 < dt < 24 * 60:
                        samples[(a, b)].append(dt)

    pair_minutes = {p: (median(v) if v else None) for p, v in samples.items()}
    endpoint_minutes = {t: pair_minutes.get(ENDPOINTS[t]) for t in TRONCONS}
    return pair_minutes, endpoint_minutes


# ----------------------------------------------------------------- segments
def load_segments() -> dict[str, list[dict]]:
    gj = json.load(open(SEGMENTS, encoding="utf-8"))
    by_t: dict[str, list[dict]] = {t: [] for t in TRONCONS}
    for f in gj["features"]:
        p = f["properties"]
        by_t[p["troncon_id"]].append(p)
    for t in by_t:
        by_t[t].sort(key=lambda p: p["km_debut"])
    return by_t


def in_any_block(t: str, km0: float, km1: float, blocks) -> float:
    """Longueur (km) du recouvrement de [km0,km1] avec les blocs urbains du tronçon."""
    ov = 0.0
    for b in blocks:
        if b[0] != t:
            continue
        lo, hi = b[-2], b[-1]
        ov += max(0.0, min(km1, hi) - max(km0, lo))
    return ov


# ----------------------------------------------------------------- moteur
def integrate(t: str, segs: list[dict], scenario: str, bande: float) -> tuple[float, float]:
    """(minutes interurbain, minutes fenêtres Ottawa) pour un tronçon.

    Interurbain : dx / min(v_geo_scenario, bande).
    Fenêtres km urbaines (Ottawa) : dx / min(v_geo_S1, bande) — aucun gain de scénario.
    Les blocs urbains GTFS sont exclus (leurs minutes viennent de l'horaire).
    """
    urb_gtfs = [b for b in URBAN_GTFS_BLOCKS if b[0] == t]
    urb_km = [b for b in URBAN_KM_BLOCKS if b[0] == t]
    inter_min = 0.0
    ottawa_min = 0.0
    for p in segs:
        km0, km1 = p["km_debut"], p["km_fin"]
        length = km1 - km0
        if length <= 0:
            continue
        ov_gtfs = in_any_block(t, km0, km1, urb_gtfs)
        ov_km = in_any_block(t, km0, km1, urb_km)
        free = max(0.0, length - ov_gtfs - ov_km)
        v_scen = min(p[f"vmax_{scenario}_kmh"], bande)
        v_s1 = min(p["vmax_S1_kmh"], bande)
        if v_scen > 0:
            inter_min += free / v_scen * 60.0
        if ov_km > 0 and v_s1 > 0:
            ottawa_min += ov_km / v_s1 * 60.0
    return inter_min, ottawa_min


def main() -> None:
    pair_minutes, endpoint_minutes = load_gtfs_pair_minutes()
    by_t = load_segments()

    # --- blocs urbains : minutes GTFS figées
    bloc_rows = []
    urban_fixed: dict[str, float] = {t: 0.0 for t in TRONCONS}
    for (t, a, b, name, km0, km1) in URBAN_GTFS_BLOCKS:
        m = pair_minutes[(a, b)]
        urban_fixed[t] += m
        bloc_rows.append({"troncon": t, "bloc": name, "km_debut": km0, "km_fin": km1,
                          "longueur_km": round(km1 - km0, 1),
                          "minutes_gtfs_mediane": round(m, 1),
                          "source": "SOURCE : GTFS VIA (médiane des sillons)"})
    for (t, name, km0, km1) in URBAN_KM_BLOCKS:
        bloc_rows.append({"troncon": t, "bloc": name, "km_debut": km0, "km_fin": km1,
                          "longueur_km": round(km1 - km0, 1),
                          "minutes_gtfs_mediane": "",
                          "source": "HYPOTHÈSE : fenêtre km, traversée au plafond S1 ∧ bande"})

    # --- arrêts interurbains (hors blocs urbains)
    stops_inter: dict[str, int] = {}
    for t in TRONCONS:
        blocks = URBAN_GTFS_BLOCKS + URBAN_KM_BLOCKS
        n = 0
        for (_, km) in INTERMEDIATE_STOPS[t]:
            if in_any_block(t, km - 1e-6, km + 1e-6, [b for b in blocks if b[0] == t]) > 0:
                continue
            n += 1
        stops_inter[t] = n

    # --- table T_base
    rows = []
    for t in TRONCONS:
        for scen in ("S1", "S2", "S3"):
            for bande in BANDES_KMH:
                inter, ottawa = integrate(t, by_t[t], scen, float(bande))
                urb = urban_fixed[t]
                stops = stops_inter[t] * MIN_PER_STOP
                total = urb + ottawa + inter + stops
                rows.append({
                    "troncon": t, "scenario": scen, "bande_kmh": bande,
                    "urbain_gtfs_min": round(urb, 1),
                    "urbain_fenetre_min": round(ottawa, 1),
                    "interurbain_min": round(inter, 1),
                    "arrets_min": round(stops, 1),
                    "n_arrets_interurbains": stops_inter[t],
                    "tbase_sans_marge_min": round(total, 1),
                    "tbase_lo_min": round(total - URBAN_SENS * (urb + ottawa), 1),
                    "tbase_hi_min": round(total + URBAN_SENS * (urb + ottawa), 1),
                    "t_horaire_actuel_min": round(endpoint_minutes[t], 1),
                })

    pd.DataFrame(bloc_rows).to_csv(OUT_BLOCS, sep=";", index=False, encoding="utf-8-sig")
    pd.DataFrame(rows).to_csv(OUT_TBASE, sep=";", index=False, encoding="utf-8-sig")

    print("=== Étape 21 — T_base par bande × scénario (SANS marge) ===\n")
    print(f"{'tronçon':<8} {'scén':<4} {'bande':>5}  {'urbain':>6} {'fenêtre':>7} "
          f"{'inter':>6} {'arrêts':>6}  {'T_base':>6}  {'horaire actuel':>14}")
    for r in rows:
        print(f"{r['troncon']:<8} {r['scenario']:<4} {r['bande_kmh']:>5}  "
              f"{r['urbain_gtfs_min']:>6} {r['urbain_fenetre_min']:>7} "
              f"{r['interurbain_min']:>6} {r['arrets_min']:>6}  "
              f"{r['tbase_sans_marge_min']:>6}  {r['t_horaire_actuel_min']:>14}")
    print(f"\nÉcrit {OUT_TBASE.name} ({len(rows)} lignes) et {OUT_BLOCS.name}.")
    print("Rappel : T_base = SANS marge ; l'encadrement de la marge vient de l'étape 4.")


if __name__ == "__main__":
    main()

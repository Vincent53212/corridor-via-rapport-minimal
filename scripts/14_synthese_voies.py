#!/usr/bin/env python3
"""Étape 14 — Synthèse « voie simple vs double » : lissage, segmentation,
déduplication réseau-unique, agrégation et livrables.

Part de `voies_points.parquet` (signaux BRUTS par point, étape 13) et produit la
réponse Phase 2 : combien de km du corridor VIA existant sont en voie SIMPLE
(donc à doubler) vs déjà DOUBLE / MULTIPLE.

Décisions client (2026-06-15) : (1) inventaire infrastructure seul ; (2) chiffre
de tête = **km physiques UNIQUES** (voie partagée entre tronçons dédupliquée —
on ne double une voie qu'une fois), détail par tronçon en complément.

Chaîne :
  1. État par point = min(n_geom, 3) : 1=simple, 2=double, 3=multiple.
  2. Lissage « voie soutenue » : médiane glissante ±W (≈250 m) par tronçon —
     un aiguillage/crossover court ne fait plus basculer simple↔double.
  3. Règles pièges : abords de gare (pres_gare) isolés ; évitements (double
     court < EVIT_KM encadré de simple) flaggés ≠ double continu ; main vs branch.
  4. Segmentation : runs contigus de même état → segments homogènes par tronçon.
  5. Déduplication réseau-unique : grille spatiale (CELL_M) ; chaque cellule
     physique comptée une seule fois (1ʳᵉ occurrence dans l'ordre des tronçons
     les plus longs), état = MAX des états vus dans la cellule (si un tronçon la
     voit double, elle est double). Invariant : unique ≤ Σ tronçons.
  6. Validation : tags passenger_lines (corroboration) + zones-témoins.

Sorties :
  - livrables/voies_par_troncon.csv  (km simple/double/multiple + % par tronçon
    + ligne RÉSEAU UNIQUE)
  - livrables/km_a_doubler.csv        (sections voie simple à doubler)
  - intermediaires/segments_voies.geojson  (segments + géométrie, pour la carte)

Paramètres surchargables (sensibilité, étape 4) : WIN_PTS, CELL_M, EVIT_KM, IN_SUFFIX.

Entrées : voies_points[<IN_SUFFIX>].parquet, courbure_points.parquet, segments.geojson
"""
from __future__ import annotations
import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (INTERMEDIATES, DELIVERABLES, CURVATURE_PARQUET,
                   SEGMENTS_GEOJSON, ensure_dirs)
from alignments import CORRIDOR_SEGMENTS

# --------------------------------------------------------------- paramètres
WIN_PTS = int(os.environ.get("WIN_PTS", 25))     # fenêtre lissage (pts ; 25 ≈ 250 m)
CELL_M = float(os.environ.get("CELL_M", 20.0))   # taille cellule de déduplication
EVIT_KM = float(os.environ.get("EVIT_KM", 1.5))  # double court isolé = évitement
MIN_SEG_KM = float(os.environ.get("MIN_SEG_KM", 0.5))  # segment plus court = absorbé (pont/crossover)
IN_SUFFIX = os.environ.get("IN_SUFFIX", "")      # ex. "_s12a25"
STEP_KM = 0.01                                    # pas du référentiel (10 m)

ETAT_LABEL = {1: "simple", 2: "double", 3: "multiple"}
ETAT_COLOR = {1: "#d62728", 2: "#2ca02c", 3: "#7f7f7f"}  # rouge / vert / gris
TRONCON_ORDER = ["MTL-QC", "MTL-Ott", "Ott-TO", "MTL-TO"]


def load_points() -> pd.DataFrame:
    df = pd.read_parquet(INTERMEDIATES / f"voies_points{IN_SUFFIX}.parquet")
    xy = pd.read_parquet(CURVATURE_PARQUET)[
        ["alignment_id", "troncon_id", "point_idx", "x_utm", "y_utm"]]
    df = df.merge(xy, on=["alignment_id", "troncon_id", "point_idx"], how="left")
    df = df.sort_values(["troncon_id", "km_along_segment"]).reset_index(drop=True)
    # état brut géométrique par point
    df["etat_raw"] = np.clip(df["n_geom"].fillna(1).astype(int), 1, 3)
    # état brut RÉCONCILIÉ : géométrie corroborée par passenger_lines — on ne
    # fait que REVOIR À LA HAUSSE (tag dit ≥2 là où la géométrie lit simple),
    # jamais à la baisse → borne basse de la fourchette « à doubler ».
    # GARDE-FOU (red team RT-1, finding #1) : on n'admet la mise à niveau par le
    # tag QUE si la géométrie voit AUSSI au moins 2 *ways* à proximité (n_wide≥2).
    # Sinon un passenger_lines=2 ERRONÉ sur une voie mono-tracé (cas mesuré : sub.
    # Drummondville, voie simple notoire) reclasserait du simple en double à tort.
    pl = np.clip(df["n_pl"].fillna(0).astype(int), 0, 3)
    nwide = df["n_wide"].fillna(1).astype(int)
    pl_admis = np.where(nwide >= 2, pl, 0)
    df["etat_raw_reco"] = np.maximum(df["etat_raw"], pl_admis).clip(1, 3)
    return df


def despeckle(e: np.ndarray, min_pts: int) -> np.ndarray:
    """Absorbe les runs plus courts que min_pts dans le voisin le plus long
    (pont, crossover, aiguillage ponctuel ≠ changement réel d'état de voie).
    Applique le principe « voie soutenue » au niveau du segment."""
    e = e.copy()
    changed = True
    while changed:
        changed = False
        runs, i, n = [], 0, len(e)
        while i < n:
            j = i
            while j + 1 < n and e[j + 1] == e[i]:
                j += 1
            runs.append((i, j, e[i]))
            i = j + 1
        if len(runs) <= 1:
            break
        for k, (s, end, _val) in enumerate(runs):
            if end - s + 1 < min_pts:
                left = runs[k - 1] if k > 0 else None
                right = runs[k + 1] if k < len(runs) - 1 else None
                if left and right:
                    nb = left if (left[1] - left[0]) >= (right[1] - right[0]) else right
                else:
                    nb = left or right
                e[s:end + 1] = nb[2]
                changed = True
                break
    return e


def prepare_state(df: pd.DataFrame, rawcol: str, outcol: str) -> pd.DataFrame:
    """Médiane glissante ±WIN_PTS puis despeckle (< MIN_SEG_KM) par tronçon."""
    min_pts = max(1, int(round(MIN_SEG_KM / STEP_KM)))
    out = []
    for tid, g in df.groupby("troncon_id"):
        g = g.sort_values("km_along_segment").copy()
        med = g[rawcol].rolling(WIN_PTS, center=True, min_periods=1).median()
        e = med.round().clip(1, 3).astype(int).values
        g[outcol] = despeckle(e, min_pts)
        out.append(g)
    return pd.concat(out).sort_values(
        ["troncon_id", "km_along_segment"]).reset_index(drop=True)


def gare_lookup() -> dict:
    """{troncon_id: [(km_debut, km_fin, gare_amont, gare_aval), ...]} depuis
    segments.geojson, pour nommer les gares encadrant une section."""
    gj = json.loads(SEGMENTS_GEOJSON.read_text(encoding="utf-8"))
    by_tr = defaultdict(list)
    for f in gj["features"]:
        if f["properties"].get("kind") != "homog_segment":
            continue
        p = f["properties"]
        by_tr[p["troncon_id"]].append(
            (p["km_debut"], p["km_fin"], p["gare_amont"], p["gare_aval"]))
    for k in by_tr:
        by_tr[k].sort()
    return by_tr


def gares_for_span(glu: dict, tid: str, km_a: float, km_b: float):
    segs = glu.get(tid, [])
    amont = aval = ""
    for kd, kf, ga, gv in segs:
        if kd <= km_a < kf or (km_a <= kd and not amont):
            amont = amont or ga
        if kd < km_b <= kf:
            aval = gv
    if not amont and segs:
        amont = segs[0][2]
    if not aval and segs:
        aval = segs[-1][3]
    return amont, aval


def segment_troncon(g: pd.DataFrame, tid: str, glu: dict) -> list[dict]:
    """Runs contigus de même état → segments homogènes."""
    g = g.sort_values("km_along_segment").reset_index(drop=True)
    etat = g["etat"].values
    km = g["km_along_segment"].values
    usage = g["usage_primary"].values
    gare = g["pres_gare"].values
    segs = []
    i = 0
    n = len(g)
    while i < n:
        j = i
        while j + 1 < n and etat[j + 1] == etat[i]:
            j += 1
        km_a = float(km[i])
        km_b = float(km[j]) + STEP_KM        # fin = dernier point + un pas
        u_slice = [x for x in usage[i:j + 1] if x]
        u_mode = max(set(u_slice), key=u_slice.count) if u_slice else None
        ga, gv = gares_for_span(glu, tid, km_a, km_b)
        segs.append({
            "troncon_id": tid,
            "etat": int(etat[i]),
            "etat_label": ETAT_LABEL[int(etat[i])],
            "km_debut": round(km_a, 2),
            "km_fin": round(km_b, 2),
            "longueur_km": round(km_b - km_a, 2),
            "usage": u_mode,
            "pres_gare": bool(gare[i:j + 1].mean() >= 0.5),
            "gare_amont": ga,
            "gare_aval": gv,
            "i0": int(i), "i1": int(j),
        })
        i = j + 1
    # marquer les évitements : double court isolé entre deux simples
    for k, s in enumerate(segs):
        if s["etat"] == 2 and s["longueur_km"] < EVIT_KM:
            prev_simple = k > 0 and segs[k - 1]["etat"] == 1
            next_simple = k < len(segs) - 1 and segs[k + 1]["etat"] == 1
            s["evitement"] = bool(prev_simple and next_simple)
        else:
            s["evitement"] = False
    return segs


def dedup_unique(df: pd.DataFrame, statecol: str = "etat"):
    """Réseau physique unique : chaque cellule comptée une fois (1ʳᵉ occurrence
    dans l'ordre des tronçons les plus longs), état = MAX vu dans la cellule.

    Retourne (uniq, first_seen) : uniq = {(etat, usage, gare): km} ;
    first_seen = booléen par index de df (point dont la cellule est comptée ici,
    i.e. NON déjà couverte par un tronçon précédent → km physique additionnel)."""
    d = df.copy()
    d["cx"] = (d["x_utm"] / CELL_M).round().astype("Int64")
    d["cy"] = (d["y_utm"] / CELL_M).round().astype("Int64")
    d["cell"] = list(zip(d["cx"], d["cy"]))
    cellmax = d.groupby("cell")[statecol].max().to_dict()
    order = sorted(d["troncon_id"].unique(),
                   key=lambda t: -(d["troncon_id"] == t).sum())
    claimed: set = set()
    uniq = defaultdict(float)          # (etat, usage, pres_gare) -> km
    first_seen = pd.Series(False, index=d.index)
    for tid in order:
        sub = d[d["troncon_id"] == tid]
        before = claimed                 # ne PAS inclure les cellules de ce tronçon
        newcells = set()
        for idx, c, u, gr in zip(sub.index, sub["cell"], sub["usage_primary"],
                                 sub["pres_gare"]):
            if c in before:
                continue
            st = cellmax.get(c, 1)
            uniq[(st, u, bool(gr))] += STEP_KM
            first_seen.at[idx] = True
            newcells.add(c)
        claimed = before | newcells
    return uniq, first_seen


def unique_simple_main(uniq: dict) -> float:
    """km simple, ligne principale, hors abords de gare, depuis un dict dédup."""
    return sum(v for (st, u, gr), v in uniq.items()
               if st == 1 and u != "branch" and not gr)


def aggregate_troncon(segs_by_tr: dict) -> list[dict]:
    rows = []
    for tid in TRONCON_ORDER:
        segs = segs_by_tr.get(tid, [])
        tot = sum(s["longueur_km"] for s in segs)
        by_etat = defaultdict(float)
        main_simple = branch_simple = gare_simple = evit_double = 0.0
        for s in segs:
            by_etat[s["etat"]] += s["longueur_km"]
            if s["etat"] == 1:
                if s["pres_gare"]:
                    gare_simple += s["longueur_km"]
                elif s["usage"] == "branch":
                    branch_simple += s["longueur_km"]
                else:
                    main_simple += s["longueur_km"]
            if s["etat"] == 2 and s["evitement"]:
                evit_double += s["longueur_km"]
        rows.append({
            "troncon": tid,
            "longueur_km": round(tot, 1),
            "km_simple": round(by_etat[1], 1),
            "km_double": round(by_etat[2], 1),
            "km_multiple": round(by_etat[3], 1),
            "pct_simple": round(100 * by_etat[1] / tot, 1) if tot else 0,
            "pct_double": round(100 * by_etat[2] / tot, 1) if tot else 0,
            "pct_multiple": round(100 * by_etat[3] / tot, 1) if tot else 0,
            "km_a_doubler_ligne_principale": round(main_simple, 1),
            "km_simple_branch": round(branch_simple, 1),
            "km_simple_abords_gare": round(gare_simple, 1),
            "km_evitements_inclus_double": round(evit_double, 1),
        })
    return rows


def write_geojson(df: pd.DataFrame, segs_by_tr: dict, out: Path) -> None:
    feats = []
    for tid, segs in segs_by_tr.items():
        g = df[df["troncon_id"] == tid].sort_values(
            "km_along_segment").reset_index(drop=True)
        lat = g["lat"].values
        lon = g["lon"].values
        for s in segs:
            i0, i1 = s["i0"], s["i1"]
            # sous-échantillonne à ~30 m pour alléger
            idx = list(range(i0, i1 + 1, 3))
            if idx[-1] != i1:
                idx.append(i1)
            coords = [[round(float(lon[k]), 6), round(float(lat[k]), 6)]
                      for k in idx]
            if len(coords) < 2:
                continue
            props = {k: v for k, v in s.items() if k not in ("i0", "i1")}
            props["color"] = ETAT_COLOR[s["etat"]]
            feats.append({"type": "Feature",
                          "geometry": {"type": "LineString",
                                       "coordinates": coords},
                          "properties": props})
    out.write_text(json.dumps({"type": "FeatureCollection", "features": feats}),
                   encoding="utf-8")
    return len(feats)


def main() -> None:
    ensure_dirs()
    df = load_points()
    print(f"Points : {len(df):,}  | WIN={WIN_PTS}pts CELL={CELL_M:.0f}m "
          f"EVIT<{EVIT_KM}km MIN_SEG={MIN_SEG_KM}km")
    df = prepare_state(df, "etat_raw", "etat")          # géométrie (livrable)
    df = prepare_state(df, "etat_raw_reco", "etat_reco")  # réconcilié (borne basse)
    glu = gare_lookup()

    segs_by_tr = {}
    for tid, g in df.groupby("troncon_id"):
        segs_by_tr[tid] = segment_troncon(g, tid, glu)

    # --- agrégation par tronçon ---
    rows = aggregate_troncon(segs_by_tr)

    # --- réseau unique (géométrie = livrable) ---
    uniq, first_seen = dedup_unique(df, "etat")
    df["unique_pt"] = first_seen
    u_simple = sum(v for (st, u, gr), v in uniq.items() if st == 1)
    u_double = sum(v for (st, u, gr), v in uniq.items() if st == 2)
    u_multiple = sum(v for (st, u, gr), v in uniq.items() if st == 3)
    u_tot = u_simple + u_double + u_multiple
    u_simple_main = unique_simple_main(uniq)
    u_simple_branch = sum(v for (st, u, gr), v in uniq.items()
                          if st == 1 and u == "branch" and not gr)
    u_simple_gare = sum(v for (st, u, gr), v in uniq.items()
                        if st == 1 and gr)
    # --- borne basse « à doubler » : état réconcilié avec passenger_lines ---
    uniq_reco, _ = dedup_unique(df, "etat_reco")
    u_simple_reco = sum(v for (st, u, gr), v in uniq_reco.items() if st == 1)
    u_simple_main_reco = unique_simple_main(uniq_reco)
    # fourchette à doubler (ligne principale, hors gare) : [reco, géométrie]
    adbl_lo, adbl_hi = round(min(u_simple_main, u_simple_main_reco)), \
        round(max(u_simple_main, u_simple_main_reco))

    # --- écriture voies_par_troncon.csv ---
    # Bloc « réseau unique » écrit en lignes 2 colonnes (indicateur;valeur) via le
    # MÊME csv.writer → colonnes alignées + fins de ligne homogènes (red team RT-1
    # finding #8). La fourchette est préfixée d'une apostrophe pour qu'Excel FR ne
    # l'interprète pas comme une date.
    somme_tr = sum(r["longueur_km"] for r in rows)
    out_csv = DELIVERABLES / "voies_par_troncon.csv"
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(rows)
        ww = csv.writer(f, delimiter=";")
        ww.writerow([])
        ww.writerow(["RÉSEAU UNIQUE (km physiques dédupliqués — chiffre de tête)", "valeur", "pct"])
        ww.writerow(["longueur_totale_km", f"{u_tot:.1f}", ""])
        ww.writerow(["km_simple", f"{u_simple:.1f}", f"{100*u_simple/u_tot:.1f}"])
        ww.writerow(["km_double", f"{u_double:.1f}", f"{100*u_double/u_tot:.1f}"])
        ww.writerow(["km_multiple", f"{u_multiple:.1f}", f"{100*u_multiple/u_tot:.1f}"])
        ww.writerow(["km_a_doubler_ligne_principale (hors gare/branch)", f"{u_simple_main:.1f}", ""])
        ww.writerow(["km_a_doubler_borne_basse (réconcilié passenger_lines)", f"{u_simple_main_reco:.1f}", ""])
        ww.writerow(["km_a_doubler_fourchette", f"'{adbl_lo:.0f}-{adbl_hi:.0f}", ""])
        ww.writerow(["km_simple_branch", f"{u_simple_branch:.1f}", ""])
        ww.writerow(["km_simple_abords_gare", f"{u_simple_gare:.1f}", ""])
        ww.writerow([])
        ww.writerow(["somme_brute_troncons_km", f"{somme_tr:.1f}", ""])
        ww.writerow(["voie_partagee_dedupliquee_km", f"{somme_tr - u_tot:.1f}", ""])

    # --- km_a_doubler.csv (sections voie simple à doubler) ---
    # longueur_unique_km = part de la section NON déjà comptée via un autre
    # tronçon (déduplication) ; doublon=oui si la section recoupe surtout de la
    # voie partagée déjà listée ailleurs (ne pas additionner ces km).
    out_dbl = DELIVERABLES / "km_a_doubler.csv"
    adbl = []
    for tid in TRONCON_ORDER:
        g = df[df["troncon_id"] == tid].sort_values(
            "km_along_segment").reset_index(drop=True)
        upt = g["unique_pt"].values
        u_arr = g["usage_primary"].values
        gr_arr = g["pres_gare"].values
        for s in segs_by_tr.get(tid, []):
            if s["etat"] != 1 or s["pres_gare"]:
                continue
            sl = slice(s["i0"], s["i1"] + 1)
            luniq = float(upt[sl].sum()) * STEP_KM
            # à-doubler STRICTE = points uniques, ligne principale, hors gare
            # (même définition que le KPI réseau-unique → le total se réconcilie ;
            # red team RT-1 finding #2 : évite la contradiction tableau/KPI).
            strict_mask = (upt[sl]
                           & (u_arr[sl] != "branch")
                           & (~gr_arr[sl].astype(bool)))
            lstrict = float(strict_mask.sum()) * STEP_KM
            adbl.append({
                "troncon": tid,
                "km_debut": s["km_debut"],
                "km_fin": s["km_fin"],
                "longueur_km": s["longueur_km"],
                "longueur_unique_km": round(luniq, 2),
                "km_a_doubler": round(lstrict, 2),
                "doublon_physique": "oui" if luniq < 0.5 * s["longueur_km"] else "non",
                "ligne": s["usage"] or "?",
                "gare_amont": s["gare_amont"],
                "gare_aval": s["gare_aval"],
            })
    adbl.sort(key=lambda r: -r["km_a_doubler"])
    with out_dbl.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(adbl[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(adbl)

    # --- geojson ---
    out_gj = INTERMEDIATES / "segments_voies.geojson"
    nfeat = write_geojson(df, segs_by_tr, out_gj)

    # --- JSON chiffres-clés (source unique pour la note de synthèse) ---
    facts = {
        "params": {"WIN_PTS": WIN_PTS, "CELL_M": CELL_M, "EVIT_KM": EVIT_KM,
                   "MIN_SEG_KM": MIN_SEG_KM},
        "reseau_unique_km": round(u_tot, 1),
        "simple_km": round(u_simple, 1), "simple_pct": round(100 * u_simple / u_tot, 1),
        "double_km": round(u_double, 1), "double_pct": round(100 * u_double / u_tot, 1),
        "multiple_km": round(u_multiple, 1), "multiple_pct": round(100 * u_multiple / u_tot, 1),
        "deux_voies_plus_km": round(u_double + u_multiple, 1),
        "deux_voies_plus_pct": round(100 * (u_double + u_multiple) / u_tot, 1),
        "a_doubler_geom_km": round(u_simple_main, 1),
        "a_doubler_reco_km": round(u_simple_main_reco, 1),
        "a_doubler_fourchette": [adbl_lo, adbl_hi],
        "simple_branch_km": round(u_simple_branch, 1),
        "simple_abords_gare_km": round(u_simple_gare, 1),
        "somme_brute_troncons_km": round(somme_tr, 1),
        "voie_partagee_km": round(somme_tr - u_tot, 1),
        "troncons": rows,
        "corroboration_pl": None,
    }
    tagv = df[df["n_pl"].notna()].copy()
    if len(tagv):
        tagv["pl"] = np.clip(tagv["n_pl"].astype(int), 1, 3)
        facts["corroboration_pl"] = {
            "couverture_pct": round(100 * len(tagv) / len(df), 1),
            "accord_pct": round(100 * (tagv["pl"] == tagv["etat"]).mean(), 1),
            "geom_le_pl_pct": round(100 * (tagv["etat"] <= tagv["pl"]).mean(), 1),
        }
    (INTERMEDIATES / "voies_synthese.json").write_text(
        json.dumps(facts, ensure_ascii=False, indent=2), encoding="utf-8")

    # ------------------------------------------------------- console
    print(f"\n=== Par tronçon (lissé) ===")
    print(f"{'tronçon':9s} {'long':>6} {'simple':>14} {'double':>14} "
          f"{'multi':>12}")
    for r in rows:
        print(f"{r['troncon']:9s} {r['longueur_km']:>6.0f} "
              f"{r['km_simple']:>7.0f} ({r['pct_simple']:>4.0f}%) "
              f"{r['km_double']:>7.0f} ({r['pct_double']:>4.0f}%) "
              f"{r['km_multiple']:>5.0f} ({r['pct_multiple']:>4.0f}%)")
    print(f"\n=== RÉSEAU UNIQUE (dédupliqué) ===")
    print(f"  total           : {u_tot:7.0f} km")
    print(f"  simple          : {u_simple:7.0f} km ({100*u_simple/u_tot:4.0f}%)")
    print(f"  double          : {u_double:7.0f} km ({100*u_double/u_tot:4.0f}%)")
    print(f"  multiple        : {u_multiple:7.0f} km ({100*u_multiple/u_tot:4.0f}%)")
    print(f"  → à doubler (ligne principale, hors gare) : "
          f"{adbl_lo:.0f}–{adbl_hi:.0f} km (fourchette)")
    print(f"     géométrie {u_simple_main:.0f} km · "
          f"réconcilié passenger_lines {u_simple_main_reco:.0f} km")
    print(f"     dont simple branch : {u_simple_branch:.0f} km · "
          f"simple abords gare : {u_simple_gare:.0f} km")
    print(f"  somme brute tronçons : {somme_tr:.0f} km · "
          f"voie partagée dédupliquée : {somme_tr - u_tot:.0f} km")

    # invariants
    print(f"\n=== Invariants ===")
    ok = True
    for r in rows:
        ssum = r["km_simple"] + r["km_double"] + r["km_multiple"]
        flag = "OK" if abs(ssum - r["longueur_km"]) < 0.5 else "!!"
        if flag == "!!":
            ok = False
        print(f"  {r['troncon']:9s} simple+double+multi={ssum:.1f} vs "
              f"long={r['longueur_km']:.1f}  [{flag}]")
    print(f"  unique ({u_tot:.0f}) ≤ somme tronçons ({somme_tr:.0f}) : "
          f"{'OK' if u_tot <= somme_tr + 0.5 else '!!'}")

    # validation tags
    tag = df[df["n_pl"].notna()].copy()
    if len(tag):
        tag["pl"] = np.clip(tag["n_pl"].astype(int), 1, 3)
        agree = (tag["pl"] == tag["etat"]).mean()
        geq = (tag["etat"] <= tag["pl"]).mean()
        print(f"\n=== Corroboration passenger_lines (n={len(tag):,}, "
              f"{100*len(tag)/len(df):.0f}% des pts) ===")
        print(f"  géométrie == passenger_lines : {100*agree:.0f}%  | "
              f"géométrie ≤ passenger_lines : {100*geq:.0f}%")

    # zones-témoins (lissé)
    print(f"\n=== Zones-témoins (lissé) ===")
    for tid, name, k0, k1, exp in [
            ("MTL-QC", "Drummondville", 100, 190, "simple"),
            ("MTL-TO", "Kingston", 250, 330, "double")]:
        z = df[(df.troncon_id == tid) & (df.km_along_segment >= k0)
               & (df.km_along_segment <= k1)]
        if len(z):
            p1 = 100 * (z["etat"] == 1).mean()
            p2 = 100 * (z["etat"] == 2).mean()
            print(f"  [{tid}] {name}: {p1:.0f}% simple / {p2:.0f}% double "
                  f"(attendu {exp})")

    print(f"\nÉcrit :")
    print(f"  {out_csv.name}")
    print(f"  {out_dbl.name}  ({len(adbl)} sections simples à doubler)")
    print(f"  {out_gj.name}  ({nfeat} segments)")

    # ligne machine-parsable (analyse de sensibilité)
    print(f"RESULT;WIN={WIN_PTS};CELL={CELL_M:.0f};SUF={IN_SUFFIX or 'base'};"
          f"unique={u_tot:.0f};simple={u_simple:.0f};double={u_double:.0f};"
          f"multi={u_multiple:.0f};adbl_lo={adbl_lo:.0f};adbl_hi={adbl_hi:.0f}")


if __name__ == "__main__":
    main()

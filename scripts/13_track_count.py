#!/usr/bin/env python3
"""Étape 13 — Nombre de voies par point (pas 10 m) par détection géométrique
des *ways* OSM parallèles, corroborée par les tags `passenger_lines`/`tracks`.

Question Phase 2 : quelle part du corridor VIA existant est en voie SIMPLE
(donc à doubler) vs déjà en voie DOUBLE / MULTIPLE ?  Argument « améliorer
l'existant » contre le greenfield ALTO.

Faisabilité PROUVÉE par sonde (`intermediaires/_probe_tracks.py`, 2026-06-15) :
le tag OSM `tracks` est inexploitable ici (1,5 % des arêtes) ; en revanche la
voie double = **deux *ways* OSM parallèles espacées de ~4 m** (écartement
physique mesuré). La détection est donc GÉOMÉTRIQUE ; les tags ne servent que
de corroboration.

Ce script se contente de MESURER, point par point, sans rien réinterpréter :
le lissage « voie soutenue », les règles gare/évitement, la segmentation, la
déduplication et l'agrégation sont faits en aval par `14_synthese_voies.py`.
On stocke les signaux BRUTS (géométrie + tags) pour permettre l'analyse de
sensibilité et la red team.

Méthode (par point du référentiel courbure, tous les 10 m, déjà en UTM 18N) :
  1. Cap local θ du corridor = azimut sur une fenêtre ±HEAD_WIN_M (points
     consécutifs du même tronçon).
  2. Arêtes du graphe dans un buffer BUF_M ; on garde celles ALIGNÉES
     (|Δcap| ≤ ALIGN_DEG). Distance perpendiculaire point→arête, par *way*.
  3. La *way* la plus proche = way PRIMAIRE (clé de déduplication en aval).
     n_geom = nb de *ways* distinctes dont l'écart de distance à la primaire
     est ≤ SISTER_M (≈ une voie sœur, espacement mesuré ~4 m). 1 = simple,
     2 = double, ≥3 = multiple. Mesure RELATIVE à la voie la plus proche →
     robuste au décalage de la polyligne matchée par rapport au rail réel.
  4. Corroboration tags de la way primaire : passenger_lines (n_pl), tracks
     (n_tr). On STOCKE les trois signaux ; la réconciliation est faite en aval.
  5. Drapeaux : pres_gare (≤ GARE_M d'une gare snappée) et n_wide (nb de ways
     alignées dans tout le buffer BUF_M, pour repérer faisceaux/lignes voisines).

Paramètres surchargables par variables d'environnement (analyse de sensibilité,
étape 14/red team) : BUF_M, ALIGN_DEG, SISTER_M, HEAD_WIN_M, GARE_M, OUT_SUFFIX.

Entrées : courbure_points.parquet, osm_rails_graph.pkl, corridor_matched.geojson
Sortie  : intermediaires/voies_points[<OUT_SUFFIX>].parquet
"""
from __future__ import annotations
import json
import math
import os
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (CURVATURE_PARQUET, GRAPH_PKL, CORRIDOR_MATCHED_GEOJSON,
                   INTERMEDIATES)

# --------------------------------------------------------------- paramètres
# FIX extension SW (2026-08) : le parquet est en UTM PAR ZONE de tronçon
# (18N pour l'est, 17N pour Toronto-Windsor/Sarnia) alors que ce script
# projetait le graphe en 18N fixe → aucun rail trouvé hors zone 18 (d0=NaN,
# tout « simple »). On projette désormais TOUT (points recalculés depuis
# lat/lon, arêtes, gares) en Lambert conforme Canada (mètres, une seule zone).
UTM_EPSG = 3978
BUF_M = float(os.environ.get("BUF_M", 30.0))        # rayon de requête/large
ALIGN_DEG = float(os.environ.get("ALIGN_DEG", 25.0))  # tolérance d'alignement
SISTER_M = float(os.environ.get("SISTER_M", 7.0))   # écart max voie sœur (~4 m mesuré)
HEAD_WIN_M = float(os.environ.get("HEAD_WIN_M", 40.0))  # demi-fenêtre de cap
GARE_M = float(os.environ.get("GARE_M", 1500.0))    # rayon « abords de gare »
OUT_SUFFIX = os.environ.get("OUT_SUFFIX", "")       # ex. "_s12a25" pour sensibilité


def bdiff(a: float, b: float) -> float:
    """Écart d'azimut non orienté (mod 180°)."""
    d = abs(a - b) % 180.0
    return min(d, 180.0 - d)


def edge_bearing(ls: LineString, s: float) -> float:
    """Azimut local d'une arête autour de l'abscisse curviligne s (m)."""
    a = ls.interpolate(max(0.0, s - 6.0))
    b = ls.interpolate(min(ls.length, s + 6.0))
    return math.degrees(math.atan2(b.y - a.y, b.x - a.x))


def parse_tracks(v) -> float:
    """Tag `tracks` → nb de voies (corroboration). 'single'=1, 'multiple'=2
    (prudent : « au moins double »), entier sinon. NaN si absent/inconnu."""
    if v is None:
        return float("nan")
    s = str(v).strip().lower()
    if s in ("single",):
        return 1.0
    if s in ("multiple", "several"):
        return 2.0
    try:
        return float(int(s))
    except ValueError:
        return float("nan")


def parse_int_tag(v) -> float:
    if v is None:
        return float("nan")
    try:
        return float(int(str(v).strip()))
    except ValueError:
        return float("nan")


def load_edges():
    """Arêtes du graphe en UTM + attributs. Retourne (geoms, way_id, usage,
    n_pl, n_tracks) alignés par index."""
    G = pickle.load(open(GRAPH_PKL, "rb"))
    T = Transformer.from_crs(4326, UTM_EPSG, always_xy=True)
    geoms, wid, usage, npl, ntr = [], [], [], [], []
    for u, v, d in G.edges(data=True):
        c = np.asarray(d["coords"])  # (lat, lon)
        if len(c) < 2:
            continue
        xs, ys = T.transform(c[:, 1], c[:, 0])
        geoms.append(LineString(np.column_stack([xs, ys])))
        tg = d.get("tags", {})
        wid.append(int(d["way_id"]))
        usage.append(tg.get("usage"))
        npl.append(parse_int_tag(tg.get("passenger_lines")))
        ntr.append(parse_tracks(tg.get("tracks")))
    return (geoms, np.array(wid), usage,
            np.array(npl), np.array(ntr))


def load_station_tree():
    cm = json.load(open(CORRIDOR_MATCHED_GEOJSON, encoding="utf-8"))
    T = Transformer.from_crs(4326, UTM_EPSG, always_xy=True)
    pts = []
    for f in cm["features"]:
        if f["properties"].get("kind") == "station_snapped":
            lon, lat = f["geometry"]["coordinates"]
            pts.append(Point(T.transform(lon, lat)))
    return STRtree(pts) if pts else None


def headings_for_group(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Azimut (deg) par point sur une fenêtre ±HEAD_WIN_M, le long de la
    polyligne ordonnée (x, y) d'un tronçon."""
    n = len(x)
    # abscisse curviligne cumulée
    seg = np.hypot(np.diff(x), np.diff(y))
    s = np.concatenate([[0.0], np.cumsum(seg)])
    th = np.empty(n)
    lo = hi = 0
    for i in range(n):
        while lo < i and s[i] - s[lo] > HEAD_WIN_M:
            lo += 1
        while hi < n - 1 and s[hi] - s[i] < HEAD_WIN_M:
            hi += 1
        a, b = max(0, lo), min(n - 1, hi)
        if a == b:
            a, b = max(0, i - 1), min(n - 1, i + 1)
        th[i] = math.degrees(math.atan2(y[b] - y[a], x[b] - x[a]))
    return th


def main() -> None:
    t0 = time.time()
    df = pd.read_parquet(CURVATURE_PARQUET)
    print(f"Points : {len(df):,}")

    geoms, e_wid, e_usage, e_npl, e_ntr = load_edges()
    tree = STRtree(geoms)
    print(f"Arêtes indexées : {len(geoms):,}")
    station_tree = load_station_tree()

    # azimut par point (calcul par groupe ordonné) — coordonnées recalculées
    # depuis lat/lon dans le CRS unique (voir note UTM_EPSG).
    df = df.sort_values(["alignment_id", "troncon_id", "point_idx"]).reset_index(drop=True)
    Tp = Transformer.from_crs(4326, UTM_EPSG, always_xy=True)
    X, Y = Tp.transform(df["lon"].values, df["lat"].values)
    X = np.asarray(X)
    Y = np.asarray(Y)
    th = np.empty(len(df))
    for _, idx in df.groupby(["alignment_id", "troncon_id"]).groups.items():
        idx = np.asarray(idx)
        th[idx] = headings_for_group(X[idx], Y[idx])

    n_geom = np.ones(len(df), dtype=np.int16)
    n_wide = np.ones(len(df), dtype=np.int16)
    d0 = np.full(len(df), np.nan)
    d_sister = np.full(len(df), np.nan)
    way_prim = np.full(len(df), -1, dtype=np.int64)
    usage_prim = np.empty(len(df), dtype=object)
    n_pl = np.full(len(df), np.nan)
    n_tr = np.full(len(df), np.nan)
    pres_gare = np.zeros(len(df), dtype=bool)

    report_every = 20000
    for i in range(len(df)):
        P = Point(X[i], Y[i])
        thP = th[i]
        # ways alignées : way_id -> (dist_min, edge_idx)
        ways: dict[int, tuple[float, int]] = {}
        for j in tree.query(P.buffer(BUF_M)):
            ls = geoms[j]
            dist = ls.distance(P)
            if dist > BUF_M:
                continue
            sp = ls.project(P)
            if bdiff(edge_bearing(ls, sp), thP) > ALIGN_DEG:
                continue
            w = int(e_wid[j])
            if w not in ways or dist < ways[w][0]:
                ways[w] = (dist, j)
        if not ways:
            usage_prim[i] = None
            continue
        items = sorted(ways.values())          # par distance croissante
        d_prim, j_prim = items[0]
        # n_geom : ways dont l'écart à la primaire ≤ SISTER_M (mesure relative)
        ng = sum(1 for (dd, _) in items if (dd - d_prim) <= SISTER_M)
        n_geom[i] = ng
        n_wide[i] = len(items)
        d0[i] = d_prim
        if len(items) >= 2:
            d_sister[i] = items[1][0] - d_prim
        way_prim[i] = int(e_wid[j_prim])
        usage_prim[i] = e_usage[j_prim]
        n_pl[i] = e_npl[j_prim]
        n_tr[i] = e_ntr[j_prim]
        if station_tree is not None:
            pres_gare[i] = station_tree.query(P.buffer(GARE_M)).size > 0
        if (i + 1) % report_every == 0:
            el = time.time() - t0
            print(f"  {i+1:>7,}/{len(df):,}  ({el:5.0f}s, "
                  f"{(i+1)/el:,.0f} pts/s)")

    out = df[["alignment_id", "troncon_id", "point_idx",
              "km_along_segment", "lat", "lon"]].copy()
    out["n_geom"] = n_geom
    out["n_wide"] = n_wide
    out["d0_m"] = np.round(d0, 2)
    out["d_sister_m"] = np.round(d_sister, 2)
    out["way_primary"] = way_prim
    out["usage_primary"] = usage_prim
    out["n_pl"] = n_pl
    out["n_tracks"] = n_tr
    out["pres_gare"] = pres_gare

    out_path = INTERMEDIATES / f"voies_points{OUT_SUFFIX}.parquet"
    out.to_parquet(out_path, index=False)
    el = time.time() - t0
    print(f"\nÉcrit {out_path.name} ({len(out):,} points, {el:.0f}s)")

    # --- résumé console (BRUT, non lissé) ---
    print(f"\nParamètres : BUF={BUF_M:.0f} ALIGN=±{ALIGN_DEG:.0f}° "
          f"SISTER={SISTER_M:.0f}m HEAD_WIN=±{HEAD_WIN_M:.0f}m")
    print(f"\n{'tronçon':8s} {'n_pts':>7} {'%simple':>8} {'%double':>8} "
          f"{'%≥3':>6} {'méd_écart(m)':>12}")
    for tid, g in out.groupby("troncon_id"):
        n = len(g)
        p1 = 100 * (g["n_geom"] == 1).mean()
        p2 = 100 * (g["n_geom"] == 2).mean()
        p3 = 100 * (g["n_geom"] >= 3).mean()
        med = g["d_sister_m"].dropna()
        med = float(np.median(med)) if len(med) else float("nan")
        print(f"{tid:8s} {n:>7,} {p1:>7.0f}% {p2:>7.0f}% {p3:>5.0f}% "
              f"{med:>12.1f}")

    # zones-témoins
    print("\n=== Zones-témoins (BRUT) ===")
    zones = [("MTL-QC", "Drummondville", 100, 190, "≈ simple attendu"),
             ("MTL-TO", "Kingston", 250, 330, "≈ double attendu")]
    for tid, name, k0, k1, exp in zones:
        z = out[(out.troncon_id == tid) &
                (out.km_along_segment >= k0) & (out.km_along_segment <= k1)]
        if len(z):
            p1 = 100 * (z["n_geom"] == 1).mean()
            p2 = 100 * (z["n_geom"] == 2).mean()
            p3 = 100 * (z["n_geom"] >= 3).mean()
            print(f"  [{tid}] {name} {k0}-{k1} ({len(z):,} pts) : "
                  f"{p1:.0f}% simple / {p2:.0f}% double / {p3:.0f}% ≥3  "
                  f"→ {exp}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Étape 3 — Map-matching GTFS → OSM en mode "lock-on-edge".

L'algo précédent (snap-by-point indépendant) flippait entre voies parallèles
en zone double-track et créait du zigzag latéral à 4-6 m d'amplitude →
courbures fantômes (R apparent 500-4000 m). On remplace par une machine
à états qui verrouille l'arête OSM courante du graphe rail :

    1. **Bootstrap** : pour le 1er pt d'un tronçon (et après une perte de lock),
       snap KNN classique avec filtre bearing → identifie l'arête de départ.
    2. **Lock** : pour chaque pt suivant, projection perpendiculaire sur la
       polyligne de l'arête courante. Tant que la dist perp ≤ STAY_THRESHOLD_M
       et qu'on est dans les bornes de l'arête, on émet la projection.
    3. **Switch au junction** : si on dépasse la fin de l'arête, on choisit
       l'arête adjacente au junction OSM dont le bearing initial matche
       la direction GTFS. Continuité topologique, pas géométrique brute.
    4. **Forced switch** : si l'arête courante diverge brutalement (>30 m),
       on force un re-bootstrap. Marqué med-conf.
    5. **Fallback GTFS** : si même le bootstrap échoue (snap > 500 m), on
       revertit aux coordonnées GTFS d'origine (low conf).

Effet net : impossible de flipper voie A↔voie B sans franchir un junction.
Le zigzag artefact disparaît à la racine ; les vraies courbes (= géométrie
d'une seule way OSM) sont préservées intactes.

Sorties :
    - intermediaires/corridor_matched.geojson
    - intermediaires/controle_03_snapping.html
    - intermediaires/controle_03_matched.html
    - intermediaires/controle_03_snap_confidence.html
"""
from __future__ import annotations
import json
import pickle
import sys
import time
from collections import defaultdict
from pathlib import Path

import networkx as nx
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    GRAPH_PKL,
    CORRIDOR_GTFS_GEOJSON,
    CORRIDOR_MATCHED_GEOJSON,
    INTERMEDIATES,
    haversine_m,
    ensure_dirs,
)
from alignments import CORRIDOR_SEGMENTS

LAT0_DEG = 45.0  # méridien moyen pour projection equirectangulaire (KD-tree)

# Densification GTFS (inchangé)
DENSIFY_STEP_M = 50.0

# Bootstrap (snap KNN classique, utilisé pour le 1er pt + forced switches)
KNN_CANDIDATES = 10
BEARING_TOL_DEG = 35.0      # tolérance bearing pour candidat KNN valide
SNAP_DIST_REJECT_M = 500.0  # bootstrap > ce seuil → fallback GTFS
AMBIG_RATIO_LOWCONF = 1.20  # bootstrap : dist_2/dist_1 < ce ratio → med-conf

# Lock-on-edge (nouveau cœur de l'algo)
STAY_THRESHOLD_M = 30.0          # dist perp max pour rester locké sur l'arête
BACKTRACK_M = 5.0                # recul autorisé le long de l'arête (anti-bruit)
END_TOLERANCE_M = 5.0            # marge avant fin d'arête pour switch au junction
FORCED_SWITCH_THRESHOLD_M = 80.0 # divergence > seuil + bootstrap < seuil → med-conf
JUNCTION_BEARING_TOL_DEG = 60.0  # tolérance bearing au junction (plus permissif)
MAX_SWITCHES_PER_POINT = 5       # garde-fou anti-boucle infinie au junction

# Guidage par la référence GTFS (correctif RT-3 v4, upstream) : à un aiguillage
# / forced-switch, choisir l'arête qui SUIT le mieux l'itinéraire GTFS en aval
# (topologiquement juste) plutôt que le seul cap instantané — sinon on monte
# sur une branche divergente (aiguillage/évitement) → excursion fermée → faux-F.
GTFS_LOOKAHEAD_M = 200.0         # distance d'anticipation le long du GTFS
GTFS_GUIDE_MIN_PTS = 4           # pts GTFS mini pour un score fiable
GTFS_GUIDE_MARGIN_M = 6.0        # une candidate ne bat une autre QUE si elle
                                 # suit le GTFS au moins de ça en mieux (sinon
                                 # on garde le départage par cap → stabilité,
                                 # pas de nouvelle oscillation voie A↔B)


# ---------------------------------------------------------------- géo helpers

def latlon_array_to_xy(coords: np.ndarray) -> np.ndarray:
    """coords (N, 2) en lat/lon → (N, 2) en x/y mètres (équirectangulaire)."""
    cos0 = np.cos(np.radians(LAT0_DEG))
    R = 6_371_000.0
    x = np.radians(coords[:, 1]) * cos0 * R
    y = np.radians(coords[:, 0]) * R
    return np.column_stack([x, y])


def xy_to_latlon(xy: np.ndarray) -> np.ndarray:
    """Inverse de latlon_array_to_xy."""
    cos0 = np.cos(np.radians(LAT0_DEG))
    R = 6_371_000.0
    lon = np.degrees(xy[:, 0] / (cos0 * R))
    lat = np.degrees(xy[:, 1] / R)
    return np.column_stack([lat, lon])


def bearing_deg(a_xy: np.ndarray, b_xy: np.ndarray) -> float:
    """Angle (degrés, [0, 360)) du vecteur a→b dans le plan xy métrique."""
    dx, dy = b_xy[0] - a_xy[0], b_xy[1] - a_xy[1]
    return float((np.degrees(np.arctan2(dx, dy)) + 360.0) % 360.0)


def bearing_diff(b1: float, b2: float) -> float:
    """Différence d'angle dans [0, 90] (rails bidirectionnels → demi-cercle).

    Pour matcher des rails sans tenir compte du sens (deux rails parallèles
    de même axe, peu importe la direction de parcours).
    """
    d = abs(b1 - b2) % 360.0
    if d > 180.0:
        d = 360.0 - d
    if d > 90.0:
        d = 180.0 - d
    return d


def bearing_diff_signed(b1: float, b2: float) -> float:
    """Différence d'angle dans [0, 180] (orientations non pliées).

    Pour distinguer le sens de parcours d'un rail (savoir si on va u→v ou v→u
    selon que le bearing de l'edge est aligné ou opposé au bearing GTFS).
    """
    d = abs(b1 - b2) % 360.0
    return d if d <= 180.0 else 360.0 - d


# ---------------------------------------------------------------- densify

def densify_polyline(
    coords_latlon: list[tuple[float, float]], step_m: float
) -> list[tuple[float, float]]:
    """Re-échantillonne la polyligne lat/lon à pas constant en mètres."""
    if len(coords_latlon) < 2:
        return list(coords_latlon)
    arr = np.array(coords_latlon)
    xy = latlon_array_to_xy(arr)
    seg_lengths = np.linalg.norm(np.diff(xy, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg_lengths)])
    total = cum[-1]
    n = max(2, int(total / step_m) + 1)
    targets = np.linspace(0, total, n)
    new_x = np.interp(targets, cum, xy[:, 0])
    new_y = np.interp(targets, cum, xy[:, 1])
    cos0 = np.cos(np.radians(LAT0_DEG))
    R = 6_371_000.0
    new_lon = np.degrees(new_x / (cos0 * R))
    new_lat = np.degrees(new_y / R)
    return list(zip(new_lat.tolist(), new_lon.tolist()))


# ---------------------------------------------------------------- OSM index

def build_osm_edge_index(
    G: nx.MultiGraph,
) -> tuple[cKDTree, np.ndarray, np.ndarray, list[tuple], np.ndarray, dict]:
    """Indexe TOUS les points internes des arêtes OSM avec edge_id et offset.

    Retour :
        - kd : KD-tree sur les xy
        - latlon : (N, 2) lat/lon
        - bearings : (N,) bearing locale du rail au point
        - edge_ids : list[(u, v, key)] de longueur N
        - offsets_m : (N,) distance le long de l'arête depuis u (= coords[0])
        - edges_xy : dict{(u,v,k) → (xy_array, length_m, seg_bearings)}
    """
    points_latlon: list[tuple[float, float]] = []
    bearings: list[float] = []
    edge_ids: list[tuple] = []
    offsets: list[float] = []
    edges_xy: dict[tuple, tuple[np.ndarray, float, np.ndarray]] = {}

    for u, v, k, data in G.edges(keys=True, data=True):
        coords = data.get("coords")
        if not coords or len(coords) < 2:
            continue
        arr = np.array(coords)
        xy = latlon_array_to_xy(arr)
        seg_lengths = np.linalg.norm(np.diff(xy, axis=0), axis=1)
        cum = np.concatenate([[0.0], np.cumsum(seg_lengths)])
        total = float(cum[-1])
        seg_bearings = np.array(
            [bearing_deg(xy[i], xy[i + 1]) for i in range(len(xy) - 1)]
        )
        pt_bearings = np.empty(len(xy))
        pt_bearings[:-1] = seg_bearings
        pt_bearings[-1] = seg_bearings[-1]
        edges_xy[(u, v, k)] = (xy, total, seg_bearings)

        for i in range(len(coords)):
            points_latlon.append(coords[i])
            bearings.append(float(pt_bearings[i]))
            edge_ids.append((u, v, k))
            offsets.append(float(cum[i]))

    arr_latlon = np.array(points_latlon)
    arr_xy = latlon_array_to_xy(arr_latlon)
    return cKDTree(arr_xy), arr_latlon, np.array(bearings), edge_ids, np.array(offsets), edges_xy


# ---------------------------------------------------------------- projection

def project_point_on_polyline(
    p_xy: np.ndarray, polyline_xy: np.ndarray, seg_lengths: np.ndarray, cum: np.ndarray,
) -> tuple[np.ndarray, float, float]:
    """Projection perpendiculaire d'un point sur une polyligne.

    Retourne (proj_xy, dist_perp, offset_le_long).
    """
    N = len(polyline_xy)
    if N < 2:
        d = float(np.linalg.norm(p_xy - polyline_xy[0]))
        return polyline_xy[0].copy(), d, 0.0

    A = polyline_xy[:-1]
    B = polyline_xy[1:]
    AB = B - A
    L2 = np.maximum(seg_lengths ** 2, 1e-9)
    AP = p_xy - A
    t = (AP[:, 0] * AB[:, 0] + AP[:, 1] * AB[:, 1]) / L2
    t_clamped = np.clip(t, 0.0, 1.0)
    proj = A + t_clamped[:, None] * AB
    dists = np.linalg.norm(proj - p_xy, axis=1)
    i_best = int(np.argmin(dists))
    proj_xy = proj[i_best]
    dist_perp = float(dists[i_best])
    offset = float(cum[i_best] + t_clamped[i_best] * seg_lengths[i_best])
    return proj_xy, dist_perp, offset


def edge_oriented(
    edge_id: tuple, direction: int, edges_xy: dict
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Polyligne de l'arête dans le sens de parcours (direction +1 = u→v).

    Retourne (xy_oriented, seg_lengths, cum, total_length).
    """
    xy, total_len, _ = edges_xy[edge_id]
    if direction == -1:
        xy = xy[::-1].copy()
    seg_lengths = np.linalg.norm(np.diff(xy, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg_lengths)])
    return xy, seg_lengths, cum, float(cum[-1] if len(cum) else 0.0)


# -------------------------------------------------- native sub-polyline (M1)

def interp_xy_at(xy: np.ndarray, cum: np.ndarray, s: float) -> np.ndarray:
    """Point xy à l'abscisse curviligne s le long de la polyligne (cum croissant)."""
    if len(xy) == 0:
        return np.zeros(2)
    total = float(cum[-1]) if len(cum) else 0.0
    s = float(np.clip(s, 0.0, total))
    j = int(np.searchsorted(cum, s))
    if j <= 0:
        return xy[0].copy()
    if j >= len(xy):
        return xy[-1].copy()
    seg = cum[j] - cum[j - 1]
    t = 0.0 if seg <= 1e-9 else (s - cum[j - 1]) / seg
    return xy[j - 1] + t * (xy[j] - xy[j - 1])


def edge_subpolyline(xy_e: np.ndarray, cum_e: np.ndarray,
                     o_start: float, o_end: float) -> list[np.ndarray]:
    """Sous-polyligne NATIVE de l'arête entre o_start et o_end (M1).

    Émet le point interpolé à o_start, TOUS les sommets natifs OSM strictement
    entre o_start et o_end (= la vraie géométrie de courbe, ~25 m et plus fin
    en courbe), puis le point interpolé à o_end — dans le sens de parcours.
    """
    total = float(cum_e[-1]) if len(cum_e) else 0.0
    a = min(max(min(o_start, o_end), 0.0), total)
    b = min(max(max(o_start, o_end), 0.0), total)
    pts: list[np.ndarray] = [interp_xy_at(xy_e, cum_e, a)]
    for jdx in range(len(cum_e)):
        c = float(cum_e[jdx])
        if a + 1e-6 < c < b - 1e-6:
            pts.append(xy_e[jdx].copy())
    pts.append(interp_xy_at(xy_e, cum_e, b))
    if o_start > o_end:  # parcours à offset décroissant → suivre le sens réel
        pts = pts[::-1]
    return pts


# ---------------------------------------------------------------- junction

def edge_fit_to_gtfs(
    cand_id: tuple, cand_dir: int, edges_xy: dict, look_xy: np.ndarray | None,
) -> float:
    """Médiane des distances perpendiculaires des points GTFS d'anticipation
    à la polyligne orientée de la candidate.

    Faible = la candidate SUIT l'itinéraire GTFS (= voie principale, route
    topologiquement juste). Élevé = la candidate s'en écarte (branche
    divergente : aiguillage / voie d'évitement). np.inf si pas d'info fiable.
    """
    if look_xy is None or len(look_xy) < GTFS_GUIDE_MIN_PTS:
        return np.inf
    xy_or, seg_l, cum, total = edge_oriented(cand_id, cand_dir, edges_xy)
    if len(xy_or) < 2 or total <= 1.0:
        return np.inf
    d = [project_point_on_polyline(p, xy_or, seg_l, cum)[1] for p in look_xy]
    return float(np.median(d))


def pick_continuation_at_junction(
    current_edge: tuple, current_direction: int, gtfs_bearing: float,
    G: nx.MultiGraph, edges_xy: dict, look_xy: np.ndarray | None = None,
) -> tuple[tuple, int] | None:
    """Choisit l'arête de continuation au junction d'arrivée.

    Critère PRIMAIRE : fidélité à l'itinéraire GTFS en aval (la voie principale
    suit le GTFS, la branche divergente s'en écarte). Critère de DÉPART/secours :
    le cap (comme avant). Une candidate ne supplante la meilleure-au-cap QUE si
    elle suit le GTFS d'au moins GTFS_GUIDE_MARGIN_M en mieux → on n'introduit
    pas d'oscillation voie A↔B (départage stable par cap si quasi-égalité GTFS).

    Junction d'arrivée : v si current_direction == +1, u sinon.
    """
    u, v, k = current_edge
    junction = v if current_direction == +1 else u

    cands = []  # (bearing_diff, gtfs_fit, cand_id, cand_dir)
    for nu, nv, nk in G.edges(junction, keys=True):
        if {nu, nv} == {u, v} and nk == k:                  # exclut l'arrivée
            continue
        cand_id = (nu, nv, nk) if (nu, nv, nk) in edges_xy else (nv, nu, nk)
        if cand_id not in edges_xy:
            continue
        cu, cv, _ = cand_id
        if cu == junction:
            cand_dir = +1
        elif cv == junction:
            cand_dir = -1
        else:
            continue
        xy_or, _, _, _ = edge_oriented(cand_id, cand_dir, edges_xy)
        if len(xy_or) < 2:
            continue
        bdiff = bearing_diff(bearing_deg(xy_or[0], xy_or[1]), gtfs_bearing)
        if bdiff > JUNCTION_BEARING_TOL_DEG:                 # garde-fou sens
            continue
        gfit = edge_fit_to_gtfs(cand_id, cand_dir, edges_xy, look_xy)
        cands.append((bdiff, gfit, cand_id, cand_dir))

    if not cands:
        return None
    by_bearing = min(cands, key=lambda c: c[0])             # secours : cap
    scored = [c for c in cands if np.isfinite(c[1])]
    if not scored:                                          # pas d'info GTFS
        return (by_bearing[2], by_bearing[3])
    by_gtfs = min(scored, key=lambda c: c[1])               # primaire : GTFS
    bb_fit = by_bearing[1]
    # Supplanter le départage-cap seulement si le gain GTFS est FRANC
    # (bb_fit non fiable → on suit le GTFS ; sinon il faut battre d'une marge).
    franc = (not np.isfinite(bb_fit)) or (
        by_gtfs[1] + GTFS_GUIDE_MARGIN_M < bb_fit)
    chosen = by_gtfs if franc else by_bearing
    return (chosen[2], chosen[3])


# ---------------------------------------------------------------- bootstrap

def bootstrap_snap(
    p_xy: np.ndarray, gtfs_bearing: float,
    kd: cKDTree, osm_latlon: np.ndarray, osm_bearings: np.ndarray,
    edge_ids: list[tuple], offsets: np.ndarray, edges_xy: dict,
) -> dict:
    """Snap KNN classique (avec filtre bearing) pour bootstrap initial ou
    forced switch. Retourne un dict avec edge, direction, offset, dist, etc.
    """
    dists, idxs = kd.query(p_xy, k=KNN_CANDIDATES)
    bearing_diffs = np.array([bearing_diff(gtfs_bearing, osm_bearings[j]) for j in idxs])
    mask = bearing_diffs <= BEARING_TOL_DEG
    if mask.any():
        valid = np.where(mask)[0]
        best_local = valid[np.argmin(dists[valid])]
        chosen = int(idxs[best_local])
        chosen_dist = float(dists[best_local])
        chosen_bdiff = float(bearing_diffs[best_local])
    else:
        chosen = int(idxs[0])
        chosen_dist = float(dists[0])
        chosen_bdiff = float(bearing_diffs[0])

    sorted_dists = np.sort(dists)
    ratio = float(sorted_dists[1] / max(sorted_dists[0], 0.1)) if len(sorted_dists) > 1 else 99.0

    edge_id = edge_ids[chosen]
    offset_in_edge = float(offsets[chosen])
    _, total_len, _ = edges_xy[edge_id]
    osm_b_native = float(osm_bearings[chosen])
    # Direction signée : si edge bearing aligné GTFS bearing (<=90° non plié)
    # → +1 (parcours u→v) ; sinon → -1 (parcours v→u, orientation inverse)
    if bearing_diff_signed(osm_b_native, gtfs_bearing) <= 90.0:
        direction = +1
    else:
        direction = -1
        offset_in_edge = total_len - offset_in_edge

    return {
        "snap_lat": float(osm_latlon[chosen, 0]),
        "snap_lon": float(osm_latlon[chosen, 1]),
        "dist_m": chosen_dist,
        "bearing_diff_deg": chosen_bdiff,
        "ratio_2e_1er": ratio,
        "edge_id": edge_id,
        "direction": direction,
        "offset_m": offset_in_edge,
    }


def gtfs_guided_relock(
    p_xy: np.ndarray, gtfs_bearing: float, look_xy: np.ndarray | None,
    kd: cKDTree, osm_bearings: np.ndarray, edge_ids: list[tuple],
    offsets: np.ndarray, edges_xy: dict,
) -> dict | None:
    """Re-lock (forced-switch) GUIDÉ par l'itinéraire GTFS.

    Parmi les arêtes des KNN candidates (filtre bearing + reject distance),
    choisit celle qui SUIT le mieux le GTFS en aval (≠ la plus proche, qui
    peut être une branche divergente d'aiguillage). Retourne un dict au même
    format que bootstrap_snap, ou None si pas d'info GTFS fiable (→ l'appelant
    retombe sur bootstrap_snap).
    """
    if look_xy is None or len(look_xy) < GTFS_GUIDE_MIN_PTS:
        return None
    dists, idxs = kd.query(p_xy, k=KNN_CANDIDATES)
    best = None  # (gfit, dist, edge_id, direction, offset)
    seen: set = set()
    for d, j in zip(np.atleast_1d(dists), np.atleast_1d(idxs)):
        if d > SNAP_DIST_REJECT_M:
            continue
        eid = edge_ids[int(j)]
        if eid in seen:
            continue
        seen.add(eid)
        if bearing_diff(gtfs_bearing, float(osm_bearings[int(j)])) > BEARING_TOL_DEG:
            continue
        _, total_len, _ = edges_xy[eid]
        off = float(offsets[int(j)])
        if bearing_diff_signed(float(osm_bearings[int(j)]), gtfs_bearing) <= 90.0:
            direction = +1
        else:
            direction = -1
            off = total_len - off
        gfit = edge_fit_to_gtfs(eid, direction, edges_xy, look_xy)
        if not np.isfinite(gfit):
            continue
        if best is None or gfit < best[0]:
            best = (gfit, float(d), eid, direction, off)
    if best is None:
        return None
    return {
        "dist_m": best[1], "edge_id": best[2],
        "direction": best[3], "offset_m": best[4],
    }


# ---------------------------------------------------------------- snap loop

def snap_one_polyline(
    gtfs_dense_latlon: list[tuple[float, float]],
    G: nx.MultiGraph,
    kd: cKDTree, osm_latlon: np.ndarray, osm_bearings: np.ndarray,
    edge_ids: list[tuple], offsets: np.ndarray, edges_xy: dict,
) -> tuple[list[dict], dict]:
    """Map-matching d'une polyligne GTFS en mode lock-on-edge."""
    arr_gtfs = np.array(gtfs_dense_latlon)
    xy_gtfs = latlon_array_to_xy(arr_gtfs)

    gtfs_bearings = np.zeros(len(xy_gtfs))
    for i in range(len(xy_gtfs)):
        a = xy_gtfs[i - 1] if i > 0 else xy_gtfs[i]
        b = xy_gtfs[i + 1] if i < len(xy_gtfs) - 1 else xy_gtfs[i]
        gtfs_bearings[i] = bearing_deg(a, b)

    # records : une décision de lock par point GTFS (la LOGIQUE de décision est
    # identique à l'algo lock-on-edge validé ; seul le RENDU géométrique change,
    # déporté dans reconstruct_native — fix M1, résolution OSM native).
    records: list[dict] = []
    stats = {
        "high_locked": 0, "high_bootstrap": 0, "med_forced": 0, "low_fallback": 0,
        "switches_at_junction": 0, "forced_switches": 0, "bootstraps": 0,
    }

    state_edge: tuple | None = None
    state_direction: int = +1
    state_offset: float = 0.0

    def rec_fallback(idx: int) -> None:
        records.append({
            "src": "fallback_gtfs", "conf": "low", "edge": None, "dir": 0,
            "off": None, "snap_dist": 0.0,
            "glat": float(arr_gtfs[idx, 0]), "glon": float(arr_gtfs[idx, 1]),
        })

    def rec_edge(edge_id: tuple, direction: int, offset: float,
                 dist_perp: float, source: str, conf: str) -> None:
        records.append({
            "src": source, "conf": conf, "edge": edge_id, "dir": direction,
            "off": float(offset), "snap_dist": float(dist_perp),
            "glat": None, "glon": None,
        })

    look_k = int(GTFS_LOOKAHEAD_M / DENSIFY_STEP_M) + 1

    for i in range(len(xy_gtfs)):
        p_xy = xy_gtfs[i]
        gtfs_b = gtfs_bearings[i]
        look_xy = xy_gtfs[i:i + look_k]      # itinéraire GTFS en aval (guidage)

        # ---- Bootstrap si pas de lock
        if state_edge is None:
            snap = bootstrap_snap(p_xy, gtfs_b, kd, osm_latlon, osm_bearings,
                                  edge_ids, offsets, edges_xy)
            stats["bootstraps"] += 1
            if snap["dist_m"] > SNAP_DIST_REJECT_M:
                rec_fallback(i)
                stats["low_fallback"] += 1
                continue
            state_edge = snap["edge_id"]
            state_direction = snap["direction"]
            state_offset = snap["offset_m"]
            conf = "high"
            if (snap["ratio_2e_1er"] < AMBIG_RATIO_LOWCONF
                    or snap["bearing_diff_deg"] > BEARING_TOL_DEG / 2):
                conf = "med"
            rec_edge(state_edge, state_direction, state_offset,
                     snap["dist_m"], "bootstrap", conf)
            if conf == "high":
                stats["high_bootstrap"] += 1
            else:
                stats["med_forced"] += 1
            continue

        # ---- Lock continu (avec switches au junction)
        emitted = False
        for _switch in range(MAX_SWITCHES_PER_POINT):
            xy_e, seg_l, cum_e, total_l = edge_oriented(state_edge, state_direction, edges_xy)
            if total_l <= 0 or len(xy_e) < 2:
                break
            proj_xy, dist_perp, new_offset = project_point_on_polyline(p_xy, xy_e, seg_l, cum_e)

            in_bounds = (0.0 <= new_offset <= total_l - 0.01)
            close_enough = (dist_perp <= STAY_THRESHOLD_M)
            no_jump_back = (new_offset >= state_offset - BACKTRACK_M)
            if close_enough and in_bounds and no_jump_back:
                state_offset = new_offset
                rec_edge(state_edge, state_direction, new_offset,
                         dist_perp, "locked", "high")
                stats["high_locked"] += 1
                emitted = True
                break

            if new_offset > total_l - END_TOLERANCE_M:
                next_edge = pick_continuation_at_junction(
                    state_edge, state_direction, gtfs_b, G, edges_xy, look_xy
                )
                if next_edge is not None:
                    state_edge, state_direction = next_edge
                    state_offset = 0.0
                    stats["switches_at_junction"] += 1
                    continue
            break

        if emitted:
            continue

        # ---- Forced switch : re-lock GUIDÉ par le GTFS (≠ plus proche, qui
        # peut être une branche divergente d'aiguillage) ; sinon bootstrap KNN.
        snap = gtfs_guided_relock(p_xy, gtfs_b, look_xy, kd, osm_bearings,
                                  edge_ids, offsets, edges_xy)
        if snap is None:
            snap = bootstrap_snap(p_xy, gtfs_b, kd, osm_latlon, osm_bearings,
                                  edge_ids, offsets, edges_xy)
        stats["bootstraps"] += 1
        if snap["dist_m"] <= SNAP_DIST_REJECT_M:
            state_edge = snap["edge_id"]
            state_direction = snap["direction"]
            state_offset = snap["offset_m"]
            rec_edge(state_edge, state_direction, state_offset,
                     snap["dist_m"], "forced_switch", "med")
            stats["med_forced"] += 1
            stats["forced_switches"] += 1
        else:
            rec_fallback(i)
            stats["low_fallback"] += 1
            state_edge = None

    return records, stats


def reconstruct_native(records: list[dict], edges_xy: dict) -> list[dict]:
    """Reconstruit le tracé matché à la RÉSOLUTION OSM NATIVE (fix M1).

    Au lieu d'émettre la projection de chaque point GTFS (pas 50 m, courbure
    détruite), on parcourt les *records* de décision : pour chaque run
    consécutif sur une même (arête, sens), on émet la sous-polyligne native de
    l'arête entre l'offset d'entrée et l'offset de sortie (sommets OSM réels,
    ~25 m et plus fin en courbe). Les runs fallback émettent les coords GTFS.
    La logique de décision n'est pas touchée — seul le rendu géométrique change.
    """
    out: list[dict] = []

    def push(xy_pt: np.ndarray, src: str, conf: str, snap_dist: float,
             edge_label: str) -> None:
        x, y = float(xy_pt[0]), float(xy_pt[1])
        if out and abs(out[-1]["_x"] - x) < 1.0 and abs(out[-1]["_y"] - y) < 1.0:
            return  # dédoublonne les points coïncidents (couture au junction)
        ll = xy_to_latlon(np.array([[x, y]]))[0]
        out.append({
            "lat": float(ll[0]), "lon": float(ll[1]),
            "source": src, "confidence": conf,
            "snap_dist_m": round(float(snap_dist), 1),
            "edge_id": edge_label, "_x": x, "_y": y,
        })

    n = len(records)
    i = 0
    while i < n:
        r = records[i]
        if r["edge"] is None:  # run fallback GTFS
            xy = latlon_array_to_xy(np.array([(r["glat"], r["glon"])]))[0]
            push(xy, r["src"], r["conf"], r["snap_dist"], "")
            i += 1
            continue
        # Regroupe le run consécutif sur la même (arête, sens)
        j = i
        while (j + 1 < n and records[j + 1]["edge"] == r["edge"]
               and records[j + 1]["dir"] == r["dir"]):
            j += 1
        o_start = r["off"]
        o_end = records[j]["off"]
        xy_e, _seg_l, cum_e, _total_l = edge_oriented(r["edge"], r["dir"], edges_xy)
        label = f"{r['edge'][0]}_{r['edge'][1]}_{r['edge'][2]}"
        for xy_pt in edge_subpolyline(xy_e, cum_e, o_start, o_end):
            push(xy_pt, r["src"], r["conf"], r["snap_dist"], label)
        i = j + 1

    for d in out:
        d.pop("_x", None)
        d.pop("_y", None)
    return out


# ---------------------------------------------------------------- stations

def snap_stations_to_matched(
    stations: list[dict], matched_points: list[dict], troncon_id: str,
) -> list[dict]:
    """Pour chaque gare, trouve le point matched le plus proche."""
    arr = np.array([(p["lat"], p["lon"]) for p in matched_points])
    xy = latlon_array_to_xy(arr)
    out = []
    for s in stations:
        s_xy = latlon_array_to_xy(np.array([(s["lat"], s["lon"])]))[0]
        dists = np.linalg.norm(xy - s_xy, axis=1)
        i = int(np.argmin(dists))
        d_real = haversine_m(s["lat"], s["lon"], matched_points[i]["lat"], matched_points[i]["lon"])
        out.append({
            "stop_id": s["stop_id"],
            "stop_name": s["stop_name"],
            "lat_orig": s["lat"],
            "lon_orig": s["lon"],
            "snap_lat": matched_points[i]["lat"],
            "snap_lon": matched_points[i]["lon"],
            "snap_dist_m": d_real,
            "matched_point_idx": i,
            "troncon_id": troncon_id,
        })
    return out


# ---------------------------------------------------------------- HTML controles

def write_controle_snapping(stations_snapped: list[dict], out_html: Path) -> None:
    import folium
    m = folium.Map(location=[45.5, -75.5], zoom_start=6, tiles="cartodbpositron")
    for s in stations_snapped:
        color = "red" if s["snap_dist_m"] > 300 else ("orange" if s["snap_dist_m"] > 100 else "green")
        folium.CircleMarker(
            location=[s["lat_orig"], s["lon_orig"]],
            radius=4, color=color, fill=True, fill_color=color, fill_opacity=0.9,
            popup=f"<b>{s['stop_name']}</b><br>{s['stop_id']}<br>snap {s['snap_dist_m']:.0f}m",
        ).add_to(m)
        folium.PolyLine(
            locations=[(s["lat_orig"], s["lon_orig"]), (s["snap_lat"], s["snap_lon"])],
            color=color, weight=2, opacity=0.8,
        ).add_to(m)
    out_html.write_text(m.get_root().render(), encoding="utf-8")


def write_controle_matched(matched_segments: list[dict], gtfs_segments: list[dict],
                           stations_snapped: list[dict], out_html: Path) -> None:
    import folium
    m = folium.Map(location=[45.5, -75.5], zoom_start=6, tiles="cartodbpositron",
                   prefer_canvas=True)

    g = folium.FeatureGroup(name="GTFS basse-rés (référence)", show=True)
    for seg in gtfs_segments:
        folium.PolyLine(
            locations=seg["coords_latlon"], color="#0033cc", weight=3, opacity=0.5,
            dash_array="5,8", tooltip=f"GTFS {seg['troncon_id']} ({seg['length_km']:.0f} km)",
        ).add_to(g)
    g.add_to(m)

    matched_layer = folium.FeatureGroup(name="OSM matched (lock-on-edge)", show=True)
    for seg in matched_segments:
        coords = [(p["lat"], p["lon"]) for p in seg["matched_points"]]
        folium.PolyLine(
            locations=coords, color="#cc0000", weight=4, opacity=0.85,
            tooltip=f"Matched {seg['troncon_id']} ({seg['length_km']:.1f} km)",
        ).add_to(matched_layer)
    matched_layer.add_to(m)

    st_layer = folium.FeatureGroup(name="Gares VIA snappées", show=True)
    for s in stations_snapped:
        folium.CircleMarker(
            location=[s["snap_lat"], s["snap_lon"]],
            radius=5, color="black", fill=True, fill_color="white",
            fill_opacity=1.0, weight=2,
            popup=f"<b>{s['stop_name']}</b><br>{s['stop_id']}",
        ).add_to(st_layer)
    st_layer.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    out_html.write_text(m.get_root().render(), encoding="utf-8")


def write_controle_confidence(matched_segments: list[dict], out_html: Path) -> None:
    """Carte du tracé matched colorée par source/confiance.

    Couleurs :
      - vert foncé : locked (lock continu sur arête)
      - vert clair : bootstrap (lock initial via KNN)
      - jaune     : forced_switch (divergence détectée → re-bootstrap)
      - rouge     : fallback_gtfs (snap rejeté → coords GTFS schématiques)
    """
    import folium
    color_for_src = {
        "locked": "#0a6e0a",
        "bootstrap": "#4caf50",
        "forced_switch": "#ffaa00",
        "fallback_gtfs": "#cc0000",
    }
    m = folium.Map(location=[45.5, -75.5], zoom_start=6, tiles="cartodbpositron",
                   prefer_canvas=True)
    for seg in matched_segments:
        layer = folium.FeatureGroup(name=f"Tronçon {seg['troncon_id']}", show=True)
        pts = seg["matched_points"]
        if len(pts) < 2:
            continue
        cur_src = pts[0]["source"]
        run_start = 0
        for i in range(1, len(pts)):
            if pts[i]["source"] != cur_src:
                folium.PolyLine(
                    locations=[(p["lat"], p["lon"]) for p in pts[run_start:i + 1]],
                    color=color_for_src.get(cur_src, "#888"), weight=4, opacity=0.85,
                ).add_to(layer)
                run_start = i
                cur_src = pts[i]["source"]
        folium.PolyLine(
            locations=[(p["lat"], p["lon"]) for p in pts[run_start:]],
            color=color_for_src.get(cur_src, "#888"), weight=4, opacity=0.85,
        ).add_to(layer)
        layer.add_to(m)

    legend = (
        "<div style='background:white;padding:8px;border:1px solid #888;font-size:12px'>"
        "<b>Source du snap (lock-on-edge)</b><br>"
        "<span style='color:#0a6e0a'>■</span> locked — lock continu (haute conf)<br>"
        "<span style='color:#4caf50'>■</span> bootstrap — lock initial KNN (haute conf)<br>"
        "<span style='color:#ffaa00'>■</span> forced_switch — re-bootstrap (med)<br>"
        "<span style='color:#cc0000'>■</span> fallback_gtfs — coords GTFS (low)<br>"
        "</div>"
    )
    folium.Marker(location=[44.0, -77.0], icon=folium.DivIcon(html=legend)).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    out_html.write_text(m.get_root().render(), encoding="utf-8")


# ---------------------------------------------------------------- main

def polyline_length_km(coords: list[tuple[float, float]]) -> float:
    return sum(haversine_m(*coords[i - 1], *coords[i]) for i in range(1, len(coords))) / 1000


def main() -> None:
    ensure_dirs()
    if not GRAPH_PKL.exists():
        sys.exit(f"Graphe rail introuvable : {GRAPH_PKL}")
    if not CORRIDOR_GTFS_GEOJSON.exists():
        sys.exit(f"GTFS corridor introuvable : {CORRIDOR_GTFS_GEOJSON}")

    print("=== Étape 3 — Map-matching lock-on-edge ===", flush=True)
    print(f"Lecture du graphe rail : {GRAPH_PKL.name}", flush=True)
    t0 = time.time()
    with open(GRAPH_PKL, "rb") as f:
        G: nx.MultiGraph = pickle.load(f)
    print(f"  {G.number_of_nodes():,} nœuds, {G.number_of_edges():,} arêtes ({time.time()-t0:.1f}s)",
          flush=True)

    print(f"Lecture corridor GTFS : {CORRIDOR_GTFS_GEOJSON.name}", flush=True)
    geojson_in = json.loads(CORRIDOR_GTFS_GEOJSON.read_text(encoding="utf-8"))
    gtfs_segments = []
    stations_per_segment: dict[str, list[dict]] = defaultdict(list)
    for f in geojson_in["features"]:
        p = f["properties"]
        if p["kind"] == "corridor_segment":
            coords_latlon = [(c[1], c[0]) for c in f["geometry"]["coordinates"]]
            gtfs_segments.append({
                "troncon_id": p["troncon_id"],
                "coords_latlon": coords_latlon,
                "length_km": p["length_km_approx"],
            })
        elif p["kind"] == "station":
            lon, lat = f["geometry"]["coordinates"]
            stations_per_segment[p["troncon_id"]].append({
                "stop_id": p["stop_id"],
                "stop_name": p["stop_name"],
                "lat": lat, "lon": lon,
                "km_along_segment": p["km_along_segment"],
            })
    print(f"  {len(gtfs_segments)} tronçons GTFS", flush=True)

    print("\n[1/3] Construction de l'index OSM (KD-tree + edges + offsets) ...", flush=True)
    t0 = time.time()
    kd, osm_latlon, osm_bearings, edge_ids, offsets, edges_xy = build_osm_edge_index(G)
    print(f"  {len(osm_latlon):,} pts OSM indexés sur {len(edges_xy):,} arêtes ({time.time()-t0:.1f}s)",
          flush=True)

    print(f"\n[2/3] Map-matching lock-on-edge (densify {DENSIFY_STEP_M:.0f}m) ...", flush=True)
    matched_segments = []
    all_stations_snapped = []
    for tronc_id in CORRIDOR_SEGMENTS:
        gtfs_seg = next((g for g in gtfs_segments if g["troncon_id"] == tronc_id), None)
        if not gtfs_seg:
            print(f"  {tronc_id}: pas de polyligne GTFS, skip", flush=True)
            continue
        t0 = time.time()
        dense = densify_polyline(gtfs_seg["coords_latlon"], DENSIFY_STEP_M)
        records, stats = snap_one_polyline(dense, G, kd, osm_latlon, osm_bearings,
                                           edge_ids, offsets, edges_xy)
        # M1 : rendu à la résolution OSM native (sommets réels, pas pas-GTFS 50 m)
        snapped = reconstruct_native(records, edges_xy)
        n_total = len(snapped)
        coords_final = [(p["lat"], p["lon"]) for p in snapped]
        length = polyline_length_km(coords_final)
        delta_pct = 100 * (length - gtfs_seg["length_km"]) / gtfs_seg["length_km"]
        # La géométrie native est plus longue que le squelette en cordes 50 m
        # (vraie longueur d'arc) ; tolérance console élargie (informatif, non bloquant).
        marker = "✓" if abs(delta_pct) <= 12 else "⚠"
        matched_segments.append({
            "troncon_id": tronc_id,
            "matched_points": snapped,
            "length_km": length,
            "stats": stats,
        })
        print(f"  {tronc_id}: {n_total} pts | "
              f"locked {stats['high_locked']} | bootstrap {stats['high_bootstrap']} | "
              f"forced {stats['med_forced']} | fallback {stats['low_fallback']} | "
              f"switches_jct {stats['switches_at_junction']} | "
              f"{length:.1f} vs {gtfs_seg['length_km']:.1f} km Δ={delta_pct:+.1f}% {marker} "
              f"({time.time()-t0:.1f}s)", flush=True)

        st_snapped = snap_stations_to_matched(stations_per_segment[tronc_id], snapped, tronc_id)
        for s in st_snapped:
            d = s["snap_dist_m"]
            if d > 1500:
                print(f"    ⚠ gare {s['stop_name']} snap dist {d:.0f}m sur le matched", flush=True)
        all_stations_snapped.extend(st_snapped)

    seen = set()
    deduped_stations = []
    for s in all_stations_snapped:
        if s["stop_id"] in seen:
            continue
        seen.add(s["stop_id"])
        deduped_stations.append(s)

    print("\n[3/3] Écriture des sorties ...", flush=True)
    out_features = []
    for seg in matched_segments:
        out_features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[p["lon"], p["lat"]] for p in seg["matched_points"]],
            },
            "properties": {
                "kind": "matched_corridor_segment",
                "alignment_id": "via_existing",
                "troncon_id": seg["troncon_id"],
                "length_km": round(seg["length_km"], 2),
                "n_points": len(seg["matched_points"]),
                "n_locked": seg["stats"]["high_locked"],
                "n_bootstrap": seg["stats"]["high_bootstrap"],
                "n_forced_switch": seg["stats"]["med_forced"],
                "n_fallback": seg["stats"]["low_fallback"],
                "n_junction_switches": seg["stats"]["switches_at_junction"],
            },
        })
    for s in deduped_stations:
        out_features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [s["snap_lon"], s["snap_lat"]]},
            "properties": {
                "kind": "station_snapped",
                "stop_id": s["stop_id"],
                "stop_name": s["stop_name"],
                "snap_dist_m": round(s["snap_dist_m"], 1),
            },
        })
    out_geojson = {
        "type": "FeatureCollection",
        "meta": {
            "alignment_id": "via_existing",
            "method": "lock-on-edge with KNN bootstrap and topological junction continuation",
            "densify_step_m": DENSIFY_STEP_M,
            "stay_threshold_m": STAY_THRESHOLD_M,
            "snap_dist_reject_m": SNAP_DIST_REJECT_M,
            "junction_bearing_tol_deg": JUNCTION_BEARING_TOL_DEG,
            "n_matched_segments": len(matched_segments),
        },
        "features": out_features,
    }
    CORRIDOR_MATCHED_GEOJSON.write_text(json.dumps(out_geojson, ensure_ascii=False),
                                        encoding="utf-8")
    print(f"  Écrit {CORRIDOR_MATCHED_GEOJSON.name} "
          f"({CORRIDOR_MATCHED_GEOJSON.stat().st_size/1e6:.1f} MB)", flush=True)

    write_controle_snapping(deduped_stations, INTERMEDIATES / "controle_03_snapping.html")
    write_controle_matched(matched_segments, gtfs_segments, deduped_stations,
                           INTERMEDIATES / "controle_03_matched.html")
    write_controle_confidence(matched_segments, INTERMEDIATES / "controle_03_snap_confidence.html")
    print("  Contrôles : controle_03_snapping.html, controle_03_matched.html, "
          "controle_03_snap_confidence.html", flush=True)
    print("\nOK — étape 3 terminée.", flush=True)


if __name__ == "__main__":
    main()

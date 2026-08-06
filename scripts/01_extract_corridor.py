#!/usr/bin/env python3
"""Étape 1 — Extraction du corridor sémantique depuis GTFS.

Lit `ressources/viarail_GTFS.zip`, sélectionne pour chacun des 4 tronçons du
corridor (MTL-QC, MTL-Ott, Ott-TO, MTL-TO) un shape représentatif déduplicé,
détermine l'ordre des gares VIA traversées, et écrit le tout en GeoJSON
basse-résolution dans `intermediaires/corridor_gtfs.geojson`.

Sortie :
    - intermediaires/corridor_gtfs.geojson : FeatureCollection avec
        * Features LineString (1 par tronçon) avec propriétés tronçon, route, shape_id
        * Features Point (1 par gare VIA dans le corridor) avec stop_id, name
        * meta : version, source, date
"""
from __future__ import annotations
import zipfile
import csv
import io
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    GTFS_ZIP,
    CORRIDOR_GTFS_GEOJSON,
    haversine_m,
    ensure_dirs,
)
from alignments import CORRIDOR_SEGMENTS, SEGMENT_ENDPOINTS

# Bbox approximative du corridor pour filtrer les gares (ne sert qu'à
# l'identification — la géométrie haute-res viendra d'OSM, pas du bbox).
# Étendu (2026-08) jusqu'à Windsor/Sarnia pour l'extension sud-ouest.
CORRIDOR_BBOX = dict(lat_min=42.0, lat_max=47.5, lon_min=-83.5, lon_max=-71.0)


def read_gtfs_table(zf: zipfile.ZipFile, name: str) -> list[dict]:
    with zf.open(name) as f:
        return list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")))


def pick_representative_shape(
    trips: list[dict], shapes_by_id: dict[str, list[tuple[int, float, float]]], route_id: str
) -> tuple[str, list[tuple[float, float]]]:
    """Choisit le shape le plus long parmi ceux du route_id, dédupliqué.
    Retourne (shape_id, polyline lat/lon).
    """
    candidate_shape_ids = {t["shape_id"] for t in trips if t["route_id"] == route_id}
    best_id, best_pts = "", []
    for sid in candidate_shape_ids:
        pts_seq = shapes_by_id.get(sid, [])
        coords = [(lat, lon) for _, lat, lon in sorted(pts_seq)]
        # heuristique : on prend celui qui a le plus de points (couverture max)
        if len(coords) > len(best_pts):
            best_id, best_pts = sid, coords
    if not best_id:
        raise RuntimeError(f"Aucun shape trouvé pour route_id={route_id}")
    return best_id, best_pts


def enforce_troncon_orientation(
    seg_id: str,
    polyline: list[tuple[float, float]],
    stops_by_id: dict[str, dict],
) -> list[tuple[float, float]]:
    """Vérifie que polyline[0] est proche de l'origine (km=0) définie dans
    SEGMENT_ENDPOINTS et la renverse si nécessaire.

    Args:
        seg_id: identifiant du tronçon (ex. "Ott-TO")
        polyline: liste de (lat, lon) telle que retournée par pick_representative_shape
        stops_by_id: dict stop_id → stop_dict (chargé depuis stops.txt)

    Returns:
        polyline (éventuellement renversée) avec km0 = gare origine.
    """
    origin_id, dest_id = SEGMENT_ENDPOINTS[seg_id]

    origin_stop = stops_by_id.get(origin_id)
    dest_stop = stops_by_id.get(dest_id)
    if origin_stop is None or dest_stop is None:
        print(f"troncon {seg_id}: ⚠ stop_id {origin_id!r} ou {dest_id!r} introuvable — orientation non vérifiée")
        return polyline

    try:
        olat, olon = float(origin_stop["stop_lat"]), float(origin_stop["stop_lon"])
        dlat, dlon = float(dest_stop["stop_lat"]),   float(dest_stop["stop_lon"])
    except (KeyError, ValueError):
        print(f"troncon {seg_id}: ⚠ coordonnées manquantes pour les gares pivots — orientation non vérifiée")
        return polyline

    first_pt = polyline[0]
    d_first_to_origin = haversine_m(first_pt[0], first_pt[1], olat, olon)
    d_first_to_dest   = haversine_m(first_pt[0], first_pt[1], dlat, dlon)

    origin_name = origin_stop.get("stop_name", origin_id)
    dest_name   = dest_stop.get("stop_name",   dest_id)

    if d_first_to_dest < d_first_to_origin:
        # Le premier point est plus proche de la destination → sens inversé → on renverse
        polyline = list(reversed(polyline))
        print(f"troncon {seg_id}: inversée   (km0 -> {origin_name})")
    else:
        print(f"troncon {seg_id}: orientation conservée (km0 -> {origin_name})")
    return polyline


def stations_along_polyline(
    polyline: list[tuple[float, float]], stops: list[dict], max_dist_m: float = 2000.0
) -> list[tuple[float, dict]]:
    """Pour chaque gare du corridor, trouve sa distance minimale à la polyligne.
    Retourne la liste des (km_le_long_du_tracé, stop_dict) triée par km.
    """
    # Pré-calcul des distances cumulées le long de la polyligne
    cum = [0.0]
    for i in range(1, len(polyline)):
        cum.append(cum[-1] + haversine_m(*polyline[i - 1], *polyline[i]))

    result = []
    for stop in stops:
        try:
            slat, slon = float(stop["stop_lat"]), float(stop["stop_lon"])
        except ValueError:
            continue
        # Recherche du point de la polyligne le plus proche
        best_d, best_i = float("inf"), -1
        for i, (lat, lon) in enumerate(polyline):
            d = haversine_m(slat, slon, lat, lon)
            if d < best_d:
                best_d, best_i = d, i
        if best_d <= max_dist_m:
            result.append((cum[best_i] / 1000.0, best_d, stop))
    return sorted(result, key=lambda r: r[0])


def main() -> None:
    ensure_dirs()
    if not GTFS_ZIP.exists():
        sys.exit(f"GTFS introuvable : {GTFS_ZIP}")

    print(f"Lecture {GTFS_ZIP.name}")
    with zipfile.ZipFile(GTFS_ZIP) as zf:
        trips = read_gtfs_table(zf, "trips.txt")
        stops = read_gtfs_table(zf, "stops.txt")
        routes = {r["route_id"]: r for r in read_gtfs_table(zf, "routes.txt")}
        shapes_raw = read_gtfs_table(zf, "shapes.txt")

    # Regrouper les points par shape_id
    shapes_by_id: dict[str, list[tuple[int, float, float]]] = defaultdict(list)
    for row in shapes_raw:
        try:
            seq = int(row["shape_pt_sequence"])
            lat = float(row["shape_pt_lat"])
            lon = float(row["shape_pt_lon"])
            shapes_by_id[row["shape_id"]].append((seq, lat, lon))
        except (ValueError, KeyError):
            continue
    print(f"  {len(shapes_by_id)} shapes, {len(trips)} trips, {len(stops)} stops")

    # Index complet stop_id → stop_dict (utilisé pour vérifier l'orientation)
    stops_by_id: dict[str, dict] = {s["stop_id"]: s for s in stops}

    # Filtrer les gares dans le bbox du corridor
    bb = CORRIDOR_BBOX
    corridor_stops = []
    for s in stops:
        try:
            lat, lon = float(s["stop_lat"]), float(s["stop_lon"])
        except ValueError:
            continue
        if bb["lat_min"] <= lat <= bb["lat_max"] and bb["lon_min"] <= lon <= bb["lon_max"]:
            corridor_stops.append(s)
    print(f"  {len(corridor_stops)} gares dans le bbox corridor")

    features = []
    summary = []
    for seg_id, seg in CORRIDOR_SEGMENTS.items():
        route = routes.get(seg.via_route_id)
        if not route:
            print(f"  ⚠ route {seg.via_route_id} ({seg_id}) introuvable")
            continue
        shape_id, polyline = pick_representative_shape(trips, shapes_by_id, seg.via_route_id)
        polyline = enforce_troncon_orientation(seg_id, polyline, stops_by_id)
        total_km = sum(haversine_m(*polyline[i - 1], *polyline[i]) for i in range(1, len(polyline))) / 1000.0
        stops_along = stations_along_polyline(polyline, corridor_stops)
        summary.append((seg_id, shape_id, len(polyline), total_km, len(stops_along)))
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[lon, lat] for lat, lon in polyline],
            },
            "properties": {
                "kind": "corridor_segment",
                "troncon_id": seg_id,
                "troncon_label_fr": seg.label_fr,
                "troncon_label_en": seg.label_en,
                "route_id": seg.via_route_id,
                "route_long_name": route.get("route_long_name", ""),
                "shape_id": shape_id,
                "n_pts": len(polyline),
                "length_km_approx": round(total_km, 1),
                "n_stops": len(stops_along),
            },
        })
        # Inclure les gares positionnées sur ce tronçon
        for km, dist_m, st in stops_along:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(st["stop_lon"]), float(st["stop_lat"])],
                },
                "properties": {
                    "kind": "station",
                    "troncon_id": seg_id,
                    "stop_id": st["stop_id"],
                    "stop_name": st["stop_name"],
                    "km_along_segment": round(km, 2),
                    "snap_distance_m_gtfs": round(dist_m, 1),
                },
            })

    # Dédoublonner les gares (une même gare apparaît sur plusieurs tronçons)
    seen_stations: set[tuple[str, str]] = set()
    deduped_features = []
    for f in features:
        if f["properties"]["kind"] == "station":
            key = (f["properties"]["stop_id"], f["properties"]["troncon_id"])
            if key in seen_stations:
                continue
            seen_stations.add(key)
        deduped_features.append(f)

    geojson = {
        "type": "FeatureCollection",
        "meta": {
            "source": "VIA Rail GTFS (shapes.txt, basse-résolution)",
            "feed_publisher_name": "VIA Rail Canada inc.",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scenarios_supported": ["S1", "S2", "S3"],
            "alignment_id": "via_existing",
            "note": (
                "Cette polyligne est basse-résolution (pas médian ~200 m, max jusqu'à 32 km). "
                "À utiliser uniquement pour l'identification sémantique du corridor et l'ordre "
                "des gares. La géométrie haute-résolution pour le calcul de courbure est "
                "fournie par OSM (voir 03_match_gtfs_to_osm.py)."
            ),
        },
        "features": deduped_features,
    }
    CORRIDOR_GTFS_GEOJSON.write_text(json.dumps(geojson, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nÉcrit {CORRIDOR_GTFS_GEOJSON.relative_to(CORRIDOR_GTFS_GEOJSON.parent.parent)}")
    print(f"\n{'Tronçon':<8} {'shape_id':<10} {'n_pts':>6} {'km':>7} {'gares':>6}")
    print("-" * 48)
    total_km, total_stops = 0.0, 0
    for seg_id, shape_id, n_pts, km, n_stops in summary:
        print(f"{seg_id:<8} {shape_id:<10} {n_pts:>6} {km:>7.1f} {n_stops:>6}")
        total_km += km
        total_stops += n_stops
    print(f"{'TOTAL':<8} {'':<10} {'':<6} {total_km:>7.1f} {total_stops:>6} (avec doublons inter-tronçons)")
    print(f"Gares uniques retenues : {len({f['properties']['stop_id'] for f in deduped_features if f['properties']['kind']=='station'})}")


if __name__ == "__main__":
    main()

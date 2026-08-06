#!/usr/bin/env python3
"""Étape 5 — Classification des points par scénario et agglomération en segments.

Entrée : intermediaires/courbure_points.parquet (étape 4)
Sortie : intermediaires/segments.geojson + intermediaires/controle_05_classes.html

Pour chaque point, on calcule v_max(R) sous chacun des 3 scénarios S1/S2/S3
et on en déduit la classe (A..F). On agglomère ensuite les points consécutifs
pour lesquels le triplet (classe_S1, classe_S2, classe_S3) reste constant en
**segments homogènes**. Les segments très courts (< MIN_SEGMENT_LEN_M) sont
absorbés dans le segment voisin le plus long.

Pour chaque segment final on calcule :
    - longueur_m, R_min_m, R_moy_m
    - vmax_S1/S2/S3_kmh, classe_S1/S2/S3
    - gare amont/aval (par km le long du tronçon)
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    CURVATURE_PARQUET,
    SEGMENTS_GEOJSON,
    CORRIDOR_MATCHED_GEOJSON,
    INTERMEDIATES,
    haversine_m,
    ensure_dirs,
    robust_min_radius,
)
from scenarios import (SCENARIOS, classify, SPEED_CLASSES, capped_vmax,
                       guarded_class, published_vmax_class)

MIN_SEGMENT_LEN_M = 200.0

# Niveau de classe : A=0 (meilleur, ≥300 km/h) → F=5 (pire, <100 km/h)
CLASS_LEVEL = {sc.code: lvl for lvl, sc in enumerate(SPEED_CLASSES)}


def absorb_short_segments(
    seg_starts: list[int], keys_per_pt: list[tuple], n_points: int, min_len_pts: int,
) -> list[int]:
    """Fusionne les segments < min_len_pts, ASYMÉTRIQUE :

    - Si le segment court est PIRE (classe plus contraignante) que ses deux
      voisins → c'est un vrai goulot, on le préserve.
    - Sinon (= bruit dans une zone meilleure ou égale, ou transition naturelle)
      → absorbé dans le voisin le plus long.

    Le "niveau" d'un segment est le max des 3 niveaux de classes S1/S2/S3
    (= le plus contraignant des 3 scénarios).
    """
    def worst_level(idx: int) -> int:
        cS1, cS2, cS3 = keys_per_pt[idx]
        return max(CLASS_LEVEL[cS1], CLASS_LEVEL[cS2], CLASS_LEVEL[cS3])

    starts = list(seg_starts)
    starts.append(n_points)  # sentinelle
    changed = True
    while changed and len(starts) > 2:
        changed = False
        for i in range(1, len(starts) - 1):
            seg_len = starts[i + 1] - starts[i]
            if seg_len >= min_len_pts:
                continue
            # Préservation des goulots : segment pire que ses deux voisins
            w_seg = worst_level(starts[i])
            w_left = worst_level(starts[i - 1])
            has_right = (i + 1 < len(starts) - 1)
            w_right = worst_level(starts[i + 1]) if has_right else -1
            if w_seg > w_left and (not has_right or w_seg > w_right):
                continue  # vrai goulot → préserver
            # Sinon : absorber dans le voisin le plus long
            left_len = starts[i] - starts[i - 1]
            right_len = (starts[i + 1] - starts[i]) if has_right else 0
            if left_len >= right_len or not has_right:
                del starts[i]
            else:
                del starts[i + 1]
            changed = True
            break
    return starts[:-1]


def find_nearest_stations(stations_along: list[dict], km: float) -> tuple[str, str]:
    """Retourne (gare_amont_name, gare_aval_name) pour un km donné."""
    if not stations_along:
        return ("", "")
    upstream = max((s for s in stations_along if s["km"] <= km), default=None, key=lambda s: s["km"])
    downstream = min((s for s in stations_along if s["km"] >= km), default=None, key=lambda s: s["km"])
    return (
        upstream["name"] if upstream else "",
        downstream["name"] if downstream else "",
    )


def main() -> None:
    ensure_dirs()
    if not CURVATURE_PARQUET.exists():
        sys.exit(f"Parquet courbure introuvable : {CURVATURE_PARQUET} — lancer 04_compute_curvature.py d'abord.")

    print("=== Étape 5 — Segmentation et classification ===")
    df = pq.read_table(CURVATURE_PARQUET).to_pandas()
    print(f"  {len(df):,} points sur {df['troncon_id'].nunique()} tronçons")

    # Calcul des classes par scénario (cohérence vmax↔classe garantie ; au
    # niveau du point seul R_m existe → sert de R_p10 ET R_min pour le garde-fou.
    # Ne sert qu'à la segmentation interne, pas exporté tel quel.)
    for sid, sc in SCENARIOS.items():
        Rs = df["R_m"].to_numpy()
        cv = [published_vmax_class(sc, float(r), float(r)) for r in Rs]
        df[f"class_{sid}"] = [c for c, _ in cv]
        df[f"vmax_{sid}_kmh"] = [v for _, v in cv]

    min_len_pts = max(2, int(MIN_SEGMENT_LEN_M / 10.0))  # pas = 10 m

    # Charger les gares snappées par tronçon depuis corridor_matched.geojson
    matched = json.loads(CORRIDOR_MATCHED_GEOJSON.read_text(encoding="utf-8"))
    stations_per_tronc: dict[str, list[dict]] = defaultdict(list)
    for f in matched["features"]:
        if f["properties"]["kind"] != "station_snapped":
            continue
        # On a besoin de la position en km le long du tronçon. Pour
        # cela on cherchera ci-dessous le point de courbure le plus proche.
        pass  # gares calculées par tronçon ci-dessous via projection sur le parquet

    seg_features = []
    summary = []
    for tronc_id, sub in df.groupby("troncon_id", sort=False):
        sub = sub.sort_values("point_idx").reset_index(drop=True)
        # Stations along this tronçon : recompute by closest point in sub
        stations = []
        for f in matched["features"]:
            if f["properties"]["kind"] != "station_snapped":
                continue
            slat, slon = f["geometry"]["coordinates"][1], f["geometry"]["coordinates"][0]
            # Distance approximative (pas critique de précision)
            d = (sub["lat"].to_numpy() - slat) ** 2 + (sub["lon"].to_numpy() - slon) ** 2
            i_closest = int(np.argmin(d))
            d_m = haversine_m(slat, slon, sub.loc[i_closest, "lat"], sub.loc[i_closest, "lon"])
            if d_m <= 1500:  # gare considérée appartenant à ce tronçon si < 1.5 km
                stations.append({
                    "name": f["properties"]["stop_name"],
                    "stop_id": f["properties"]["stop_id"],
                    "km": float(sub.loc[i_closest, "km_along_segment"]),
                })
        stations.sort(key=lambda s: s["km"])

        # Segmentation par changement de tuple de classes
        keys = list(zip(sub["class_S1"], sub["class_S2"], sub["class_S3"]))
        seg_starts = [0]
        for i in range(1, len(keys)):
            if keys[i] != keys[i - 1]:
                seg_starts.append(i)
        seg_starts = absorb_short_segments(seg_starts, keys, len(sub), min_len_pts)

        for k, start in enumerate(seg_starts):
            end = seg_starts[k + 1] if k + 1 < len(seg_starts) else len(sub)
            seg = sub.iloc[start:end]
            if len(seg) < 2:
                continue
            longueur_m = (float(seg["km_along_segment"].iloc[-1]) - float(seg["km_along_segment"].iloc[0])) * 1000
            R_min = float(seg["R_m"].min())
            R_vals = seg["R_m"].to_numpy()
            # R_moy harmonique (plus représentatif pour la vitesse moyenne accessible)
            R_moy = float(len(R_vals) / np.sum(1.0 / np.maximum(R_vals, 1e-6)))
            # Vmax opérationnelle du segment = vitesse correspondant au R-percentile-10
            # (robuste aux artefacts numériques d'aiguillages : 1-2 points à R=100m
            # ne disent pas la classe d'un segment de 800m). Si une vraie courbe
            # contraignante existe, elle s'étend sur ≥10% des points du segment
            # (= ≥30m d'arc au pas 10m → critère "sustained curve").
            R_p10 = float(np.percentile(R_vals, 10)) if len(R_vals) >= 10 else R_min
            # R_p50 (médiane) : sert (a) au diagnostic d'hétérogénéité du
            # segment via l'écart R_p50−R_p10 et (b) au calcul de la FOURCHETTE
            # du chiffre-titre (incertitude transparente, idée Vincent / fix M2).
            R_p50 = float(np.percentile(R_vals, 50)) if len(R_vals) >= 2 else R_min
            # Base de classement = ROBUST-MIN : rayon le plus serré *soutenu*
            # (min d'une médiane glissante ~150 m). R_min seul était gouverné
            # par le PIRE artefact ponctuel de l'estimateur → faux-F vérifié
            # (red team : voie droite étiquetée F). R_p10 était l'inverse,
            # trop optimiste. Le robust-min = pire VRAIE courbe soutenue
            # (= règle physique d'une limite de vitesse) ET immunisé contre un
            # point parasite isolé. vmax borné dans la bande → classify==classe.
            R_classif = robust_min_radius(R_vals)
            classe_S1, vmax_S1 = published_vmax_class(SCENARIOS["S1"], R_classif, R_classif)
            classe_S2, vmax_S2 = published_vmax_class(SCENARIOS["S2"], R_classif, R_classif)
            classe_S3, vmax_S3 = published_vmax_class(SCENARIOS["S3"], R_classif, R_classif)
            km_mid = float(seg["km_along_segment"].mean())
            gare_amont, gare_aval = find_nearest_stations(stations, km_mid)
            # Géométrie : polyligne du segment
            coords = [[float(lon), float(lat)] for lat, lon in zip(seg["lat"], seg["lon"])]
            seg_features.append({
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coords},
                "properties": {
                    "kind": "homog_segment",
                    "alignment_id": "via_existing",
                    "troncon_id": tronc_id,
                    "seg_idx": k,
                    "km_debut": float(seg["km_along_segment"].iloc[0]),
                    "km_fin": float(seg["km_along_segment"].iloc[-1]),
                    "longueur_m": round(longueur_m, 1),
                    "R_min_m": round(R_min, 0) if np.isfinite(R_min) else None,
                    "R_moy_m": round(R_moy, 0) if np.isfinite(R_moy) else None,
                    "R_p10_m": round(R_p10, 0) if np.isfinite(R_p10) else None,
                    "R_p50_m": round(R_p50, 0) if np.isfinite(R_p50) else None,
                    "R_classif_m": round(R_classif, 0) if np.isfinite(R_classif) else None,
                    "vmax_S1_kmh": round(vmax_S1, 1),
                    "vmax_S2_kmh": round(vmax_S2, 1),
                    "vmax_S3_kmh": round(vmax_S3, 1),
                    "classe_S1": classe_S1,
                    "classe_S2": classe_S2,
                    "classe_S3": classe_S3,
                    "gare_amont": gare_amont,
                    "gare_aval": gare_aval,
                },
            })
        summary.append((tronc_id, len(seg_starts), sum(1 for f in seg_features if f["properties"]["troncon_id"] == tronc_id)))

    out_geojson = {
        "type": "FeatureCollection",
        "meta": {
            "alignment_id": "via_existing",
            "scenarios": [s.id for s in SCENARIOS.values()],
            "min_segment_len_m": MIN_SEGMENT_LEN_M,
            "n_segments": len(seg_features),
        },
        "features": seg_features,
    }
    SEGMENTS_GEOJSON.write_text(json.dumps(out_geojson, ensure_ascii=False), encoding="utf-8")
    print(f"\nÉcrit {SEGMENTS_GEOJSON.name} ({SEGMENTS_GEOJSON.stat().st_size/1e6:.1f} MB)")
    print(f"\n{'Tronçon':<8} {'segments':>10}")
    for t, _, n in summary:
        print(f"  {t:<6}  {n:>10}")
    print(f"  TOTAL   {len(seg_features):>10}")

    # Carte de contrôle : segments par scénario S2 (le scénario médian)
    write_controle_html(seg_features, INTERMEDIATES / "controle_05_classes.html")


def write_controle_html(seg_features: list[dict], out_html: Path) -> None:
    import folium
    sclass_color = {sc.code: sc.color for sc in SPEED_CLASSES}
    m = folium.Map(location=[45.5, -75.5], zoom_start=6, tiles="cartodbpositron")

    for sid in ("S1", "S2", "S3"):
        sc_obj = SCENARIOS[sid]
        layer = folium.FeatureGroup(name=f"{sid} — {sc_obj.name_fr}", show=(sid == "S2"))
        for feat in seg_features:
            classe = feat["properties"][f"classe_{sid}"]
            color = sclass_color.get(classe, "#888888")
            coords_latlon = [(c[1], c[0]) for c in feat["geometry"]["coordinates"]]
            popup = (
                f"<b>{feat['properties']['troncon_id']}</b> — segment {feat['properties']['seg_idx']}<br>"
                f"R_min: {feat['properties']['R_min_m']} m<br>"
                f"vmax {sid}: {feat['properties'][f'vmax_{sid}_kmh']:.0f} km/h ({classe})<br>"
                f"longueur: {feat['properties']['longueur_m']:.0f} m<br>"
                f"entre {feat['properties']['gare_amont']} et {feat['properties']['gare_aval']}"
            )
            folium.PolyLine(
                locations=coords_latlon, color=color, weight=4, opacity=0.85, popup=popup
            ).add_to(layer)
        layer.add_to(m)

    # Légende
    legend_rows = "".join(
        f"<div><span style='color:{sc.color}'>■</span> {sc.code} : {sc.name_fr} ({int(sc.vmin_kmh)}+ km/h)</div>"
        for sc in SPEED_CLASSES
    )
    folium.Marker(
        location=[44.0, -77.0],
        icon=folium.DivIcon(html=f"<div style='background:white;padding:6px;border:1px solid #888;font-size:11px'><b>Classes de vitesse</b><br>{legend_rows}</div>"),
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    out_html.write_text(m.get_root().render(), encoding="utf-8")


if __name__ == "__main__":
    main()

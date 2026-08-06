#!/usr/bin/env python3
"""Étape 2 — Construction du graphe rail à partir des PBF OSM Québec + Ontario.

Optimisations :
- Filtre `KeyFilter("railway")` appliqué côté C++ → évite d'inspecter en Python
  les ~10M ways non-rail.
- Sortie en flush=True pour suivre la progression.
- HTML de contrôle : limité au top-3 composantes pour rester léger.

Sortie : `intermediaires/osm_rails_graph.pkl` (pickle d'un MultiGraph) +
`intermediaires/controle_02_graphe.html`.
"""
from __future__ import annotations
import pickle
import sys
import time
from collections import Counter
from pathlib import Path

import osmium
import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    PBF_QUEBEC,
    PBF_ONTARIO,
    GRAPH_PKL,
    INTERMEDIATES,
    haversine_m,
    ensure_dirs,
)

KEEP_RAILWAY = {"rail", "main"}
EXCLUDE_SERVICE = {"yard", "spur", "siding", "crossover"}
EXCLUDE_USAGE = {"industrial", "tourism"}

# Bbox généreux pour limiter le rendu HTML uniquement (pas pour le calcul)
RENDER_BBOX = dict(lat_min=41.8, lat_max=48.0, lon_min=-83.5, lon_max=-70.0)


def collect_rail_ways(pbf_path: Path, label: str) -> list[dict]:
    """Itère le PBF avec filtre C++ KeyFilter("railway") pour skipper les non-rail."""
    print(f"  Lecture {label} ({pbf_path.stat().st_size/1e6:.0f} MB) ...", flush=True)
    t0 = time.time()
    fp = (osmium.FileProcessor(pbf_path)
          .with_filter(osmium.filter.KeyFilter("railway"))
          .with_locations())
    ways: list[dict] = []
    n_seen = n_skipped = 0
    last_log = t0
    for obj in fp:
        if not obj.is_way():
            continue
        n_seen += 1
        tags = {t.k: t.v for t in obj.tags}
        if tags.get("railway") not in KEEP_RAILWAY:
            continue
        if tags.get("service") in EXCLUDE_SERVICE:
            continue
        if tags.get("usage") in EXCLUDE_USAGE:
            continue
        try:
            node_refs = [n.ref for n in obj.nodes]
            coords = [(n.lat, n.lon) for n in obj.nodes if n.location.valid()]
        except (osmium.InvalidLocationError, RuntimeError):
            n_skipped += 1
            continue
        if len(coords) < 2 or len(coords) != len(node_refs):
            n_skipped += 1
            continue
        ways.append({
            "id": obj.id,
            "tags": tags,
            "node_refs": list(node_refs),
            "coords": coords,
        })
        # log de progression toutes les 5s
        now = time.time()
        if now - last_log > 5.0:
            print(f"    [{label}] {len(ways):>6} rail ways retenus, {n_seen:>6} ways scannés  t={now-t0:.0f}s", flush=True)
            last_log = now
    print(f"  {label} : {len(ways)} ways rail retenus sur {n_seen} ({n_skipped} skips), {time.time()-t0:.1f}s", flush=True)
    return ways


def way_length_m(coords: list[tuple[float, float]]) -> float:
    return sum(haversine_m(*coords[i - 1], *coords[i]) for i in range(1, len(coords)))


def build_graph(all_ways: list[dict]) -> nx.MultiGraph:
    print("  Détection des junctions ...", flush=True)
    node_use: Counter = Counter()
    for w in all_ways:
        for r in w["node_refs"]:
            node_use[r] += 1

    junction_set: set[int] = {r for r, c in node_use.items() if c >= 2}
    print(f"    {len(junction_set):,} junctions sur {len(node_use):,} nœuds rail uniques", flush=True)

    G: nx.MultiGraph = nx.MultiGraph()
    junction_coords: dict[int, tuple[float, float]] = {}

    print("  Construction des arêtes ...", flush=True)
    t0 = time.time()
    for idx, w in enumerate(all_ways):
        refs = w["node_refs"]
        coords = w["coords"]
        split_indices = sorted(set(
            i for i, r in enumerate(refs)
            if r in junction_set or i == 0 or i == len(refs) - 1
        ))
        for k in range(len(split_indices) - 1):
            i, j = split_indices[k], split_indices[k + 1]
            if i == j:
                continue
            seg_coords = coords[i:j + 1]
            length = way_length_m(seg_coords)
            if length <= 0:
                continue
            u, v = refs[i], refs[j]
            junction_coords[u] = seg_coords[0]
            junction_coords[v] = seg_coords[-1]
            G.add_edge(u, v, weight=length, coords=seg_coords, way_id=w["id"], tags=w["tags"])
        if (idx + 1) % 5000 == 0:
            print(f"    {idx+1}/{len(all_ways)} ways traités  t={time.time()-t0:.0f}s", flush=True)

    for node_id, (lat, lon) in junction_coords.items():
        G.add_node(node_id, lat=lat, lon=lon)
    print(f"  Arêtes construites en {time.time()-t0:.1f}s", flush=True)
    return G


def write_controle_html(G: nx.MultiGraph, out_html: Path) -> None:
    """Carte de contrôle : top-3 composantes filtrées au bbox du corridor."""
    import folium
    print("  Listage composantes connexes ...", flush=True)
    components = list(nx.connected_components(G))
    components.sort(key=len, reverse=True)
    print(f"    {len(components)} composantes (taille top-10 : {[len(c) for c in components[:10]]})", flush=True)
    palette = ["#e41a1c", "#377eb8", "#4daf4a"]
    bb = RENDER_BBOX

    m = folium.Map(location=[45.5, -75.5], zoom_start=6, tiles="cartodbpositron",
                   prefer_canvas=True)
    for idx, comp in enumerate(components[:3]):
        color = palette[idx]
        layer = folium.FeatureGroup(name=f"Composante #{idx+1} ({len(comp):,} nœuds)", show=True)
        n_drawn = 0
        for u, v, data in G.subgraph(comp).edges(data=True):
            # filtre bbox pour éviter de tracer des milliers de km hors corridor
            if not data["coords"]:
                continue
            avg_lat = sum(c[0] for c in data["coords"]) / len(data["coords"])
            avg_lon = sum(c[1] for c in data["coords"]) / len(data["coords"])
            if not (bb["lat_min"] <= avg_lat <= bb["lat_max"] and bb["lon_min"] <= avg_lon <= bb["lon_max"]):
                continue
            folium.PolyLine(
                locations=data["coords"], color=color, weight=2, opacity=0.7
            ).add_to(layer)
            n_drawn += 1
        layer.add_to(m)
        print(f"    Composante #{idx+1} : {n_drawn} arêtes dessinées (filtre bbox corridor)", flush=True)
    folium.LayerControl(collapsed=False).add_to(m)
    out_html.write_text(m.get_root().render(), encoding="utf-8")
    print(f"  Contrôle visuel : {out_html.name} ({out_html.stat().st_size/1024:.0f} KB)", flush=True)


def main() -> None:
    ensure_dirs()
    for p in (PBF_QUEBEC, PBF_ONTARIO):
        if not p.exists():
            sys.exit(f"PBF introuvable : {p}")

    print("=== Étape 2 — Construction du graphe rail OSM ===", flush=True)
    qc_ways = collect_rail_ways(PBF_QUEBEC, "Québec")
    on_ways = collect_rail_ways(PBF_ONTARIO, "Ontario")
    all_ways = qc_ways + on_ways
    print(f"  Total ways rail : {len(all_ways)} (QC: {len(qc_ways)}, ON: {len(on_ways)})", flush=True)

    print("\nConstruction du graphe ...", flush=True)
    t0 = time.time()
    G = build_graph(all_ways)
    print(f"  Graphe : {G.number_of_nodes():,} nœuds, {G.number_of_edges():,} arêtes ({time.time()-t0:.1f}s)", flush=True)
    total_km = sum(d["weight"] for _, _, d in G.edges(data=True)) / 1000
    print(f"  Longueur totale : {total_km:,.0f} km", flush=True)

    print(f"\nÉcriture du graphe → {GRAPH_PKL.name}", flush=True)
    with open(GRAPH_PKL, "wb") as f:
        pickle.dump(G, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"  ({GRAPH_PKL.stat().st_size/1e6:.1f} MB)", flush=True)

    print("\nGénération de la carte de contrôle ...", flush=True)
    write_controle_html(G, INTERMEDIATES / "controle_02_graphe.html")

    print("\nOK — étape 2 terminée.", flush=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Étape 15 — Carte des voies simple / double / multiple (Phase 2).

Rend `intermediaires/segments_voies.geojson` (produit par 14_synthese_voies.py)
en carte interactive Folium + KMZ Google Earth, dans le style des livrables
Phase 1 (07_render_outputs.py). Couleurs : simple = rouge, double = vert,
multiple = gris. Les sections « à doubler » (simple, ligne principale, hors
gare) sont mises en évidence (trait plus épais).

Entrées : intermediaires/segments_voies.geojson, intermediaires/corridor_matched.geojson
Sorties : livrables/corridor_voies.html, livrables/corridor_voies.kmz
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import folium
import simplekml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (INTERMEDIATES, DELIVERABLES, CORRIDOR_MATCHED_GEOJSON,
                   ensure_dirs)

SEGMENTS_VOIES = INTERMEDIATES / "segments_voies.geojson"

ETAT_COLOR = {"simple": "#d62728", "double": "#2ca02c", "multiple": "#7f7f7f"}
ETAT_LABEL_FR = {"simple": "Voie simple (1)", "double": "Voie double (2)",
                 "multiple": "Voie multiple (≥3)"}

CAVEAT_FR = (
    "Inventaire du NOMBRE DE VOIES seulement : n'évalue ni génie civil, "
    "signalisation, électrification, foncier, ni emprise pour une 2ᵉ voie. "
    "Détection géométrique (voies parallèles OSM ~4 m) corroborée par le tag "
    "passenger_lines ; dépend de la complétude d'OpenStreetMap (un tronçon "
    "double mal cartographié ressort « simple » → biais prudent). « À doubler » "
    "suppose une cible de double-voie continue."
)
CAVEAT_EN = (
    "Track-COUNT inventory only: does NOT assess civil works, signalling, "
    "electrification, land/right-of-way for a 2nd track. Geometric detection "
    "(parallel OSM ways ~4 m) corroborated by the passenger_lines tag; depends "
    "on OpenStreetMap completeness (a mis-mapped double section reads as "
    "'single' → conservative bias). 'To double' assumes a continuous "
    "double-track target."
)


def is_a_doubler(p: dict) -> bool:
    return (p.get("etat_label") == "simple"
            and (p.get("usage") or "") != "branch"
            and not p.get("pres_gare", False))


def load_stations() -> list[dict]:
    matched = json.loads(CORRIDOR_MATCHED_GEOJSON.read_text(encoding="utf-8"))
    out, seen = [], set()
    for f in matched["features"]:
        if f["properties"].get("kind") != "station_snapped":
            continue
        sid = f["properties"]["stop_id"]
        if sid in seen:
            continue
        seen.add(sid)
        lon, lat = f["geometry"]["coordinates"]
        out.append({"stop_id": sid, "name": f["properties"]["stop_name"],
                    "lat": lat, "lon": lon})
    return out


def build_html(feats: list[dict], stations: list[dict], out: Path) -> None:
    m = folium.Map(location=[44.8, -76.5], zoom_start=6, tiles=None,
                   prefer_canvas=True)
    folium.TileLayer("cartodbpositron", control=False).add_to(m)

    layers = {e: folium.FeatureGroup(name=ETAT_LABEL_FR[e], show=True)
              for e in ("double", "multiple", "simple")}
    all_lats, all_lons = [], []
    for feat in feats:
        p = feat["properties"]
        e = p["etat_label"]
        coords = [(c[1], c[0]) for c in feat["geometry"]["coordinates"]]
        all_lats.extend(c[0] for c in coords)
        all_lons.extend(c[1] for c in coords)
        doubler = is_a_doubler(p)
        popup = (
            f"<b>{p['troncon_id']} — {ETAT_LABEL_FR[e]}</b><br>"
            f"km {p['km_debut']:.1f} → {p['km_fin']:.1f} "
            f"({p['longueur_km']:.1f} km)<br>"
            f"Ligne : {p.get('usage') or '?'}"
            f"{' · abords de gare' if p.get('pres_gare') else ''}"
            f"{' · <i>évitement</i>' if p.get('evitement') else ''}<br>"
            f"Entre : {p.get('gare_amont','')} → {p.get('gare_aval','')}"
            + ("<br><b style='color:#b00'>→ à doubler</b>" if doubler else ""))
        folium.PolyLine(
            locations=coords, color=ETAT_COLOR[e],
            weight=7 if doubler else 4,
            opacity=0.9, dash_array="8,6" if doubler else None,
            popup=folium.Popup(popup, max_width=300),
        ).add_to(layers[e])
    for e in ("double", "multiple", "simple"):
        layers[e].add_to(m)

    layer_st = folium.FeatureGroup(name="Gares VIA", show=True)
    for st in stations:
        folium.CircleMarker(
            location=[st["lat"], st["lon"]], radius=4, color="black",
            fill=True, fill_color="white", fill_opacity=1.0, weight=2,
            tooltip=st["name"],
            popup=f"<b>{st['name']}</b>").add_to(layer_st)
    layer_st.add_to(m)

    if all_lats:
        m.fit_bounds([[min(all_lats), min(all_lons)],
                      [max(all_lats), max(all_lons)]])

    legend = f"""
    <div style="position: fixed; bottom: 20px; left: 20px; background: white;
        padding: 10px 12px; border: 1px solid #888; border-radius: 4px;
        font: 11px/1.45 sans-serif; max-width: 430px; z-index: 9999;">
      <div style='font-weight:bold;font-size:13px'>Nombre de voies — corridor VIA existant</div>
      <div style='color:#666;font-size:10px;margin-bottom:4px'>Track count — existing VIA corridor</div>
      <table style='font-size:11px;border-collapse:collapse'>
        <tr><td><span style='display:inline-block;width:20px;height:10px;background:{ETAT_COLOR['simple']}'></span></td>
            <td style='padding:2px 6px'><b>Simple</b> — à doubler (trait épais pointillé sur ligne principale)</td></tr>
        <tr><td><span style='display:inline-block;width:20px;height:10px;background:{ETAT_COLOR['double']}'></span></td>
            <td style='padding:2px 6px'><b>Double</b> — déjà 2 voies</td></tr>
        <tr><td><span style='display:inline-block;width:20px;height:10px;background:{ETAT_COLOR['multiple']}'></span></td>
            <td style='padding:2px 6px'><b>Multiple</b> — 3 voies et + (abords/jonctions)</td></tr>
      </table>
      <div style='margin-top:6px;padding:6px 8px;background:#fff8e1;
        border:1px solid #f0a500;border-radius:3px;font-size:10px;color:#5a3e00'>
        <b>&#9888; Portée / Scope</b><br><b>FR :</b> {CAVEAT_FR}<br>
        <b>EN :</b> {CAVEAT_EN}</div>
    </div>"""
    m.get_root().html.add_child(folium.Element(legend))
    folium.LayerControl(collapsed=False).add_to(m)
    out.write_text(m.get_root().render(), encoding="utf-8")
    print(f"  Carte HTML : {out.name}")


def build_kmz(feats: list[dict], stations: list[dict], out: Path) -> None:
    kml = simplekml.Kml(name="TGV Canada — Voies du corridor VIA (simple/double)")
    kml.document.description = (
        "Phase 2 — inventaire du nombre de voies (simple/double/multiple) du "
        "corridor VIA existant. Détection géométrique (voies parallèles OSM "
        "~4 m) + corroboration passenger_lines.\n\n"
        f"PORTÉE / SCOPE\nFR : {CAVEAT_FR}\nEN : {CAVEAT_EN}")
    folders = {}
    for e in ("simple", "double", "multiple"):
        folders[e] = kml.newfolder(name=ETAT_LABEL_FR[e])
    for feat in feats:
        p = feat["properties"]
        e = p["etat_label"]
        ch = ETAT_COLOR[e]
        col = simplekml.Color.rgb(int(ch[1:3], 16), int(ch[3:5], 16),
                                  int(ch[5:7], 16), a=230)
        ls = folders[e].newlinestring(
            name=f"{p['troncon_id']} km {p['km_debut']:.1f}-{p['km_fin']:.1f} — {e}")
        ls.coords = feat["geometry"]["coordinates"]
        ls.style.linestyle.color = col
        ls.style.linestyle.width = 5 if is_a_doubler(p) else 3
        ls.description = (
            f"{e} · {p['longueur_km']:.1f} km · ligne {p.get('usage') or '?'}\n"
            f"Entre {p.get('gare_amont','')} et {p.get('gare_aval','')}"
            + ("\n→ à doubler" if is_a_doubler(p) else ""))
    fst = kml.newfolder(name="Gares VIA")
    for st in stations:
        pt = fst.newpoint(name=st["name"], coords=[(st["lon"], st["lat"])])
        pt.style.iconstyle.icon.href = "http://maps.google.com/mapfiles/kml/shapes/rail.png"
    kml.savekmz(str(out))
    print(f"  KMZ : {out.name} ({out.stat().st_size/1e6:.1f} MB)")


def main() -> None:
    ensure_dirs()
    if not SEGMENTS_VOIES.exists():
        sys.exit("segments_voies.geojson introuvable — lancer 14_synthese_voies.py.")
    feats = json.loads(SEGMENTS_VOIES.read_text(encoding="utf-8"))["features"]
    stations = load_stations()
    print(f"=== Étape 15 — Carte des voies ===\n  {len(feats)} segments, "
          f"{len(stations)} gares")
    build_html(feats, stations, DELIVERABLES / "corridor_voies.html")
    build_kmz(feats, stations, DELIVERABLES / "corridor_voies.kmz")
    print(f"\nLivrables carte prêts dans livrables/")


if __name__ == "__main__":
    main()

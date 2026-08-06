#!/usr/bin/env python3
"""Étape 7 — Génération des livrables finaux.

Entrées :
    - intermediaires/segments.geojson  (segments avec classes S1/S2/S3)
    - intermediaires/corridor_matched.geojson  (gares snappées)

Sorties (dans livrables/) :
    - corridor_courbatures.html      Carte Folium principale (3 calques scénarios + gares)
    - corridor_courbatures.kmz       Google Earth, structure dossier-par-scénario
    - segments_courbature.csv        Données brutes triables, en-têtes bilingues FR/EN
"""
from __future__ import annotations
import json
import csv
import sys
import tempfile
import zipfile
from pathlib import Path

import folium
import simplekml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    SEGMENTS_GEOJSON,
    CORRIDOR_MATCHED_GEOJSON,
    DELIVERABLES,
    ensure_dirs,
    degre_courbure,
    fmt_dc,
    kmh_to_mph,
    km_to_mile,
)


def _mph(v_kmh, dec: int = 1):
    """Arrondi mph depuis km/h (vide si None)."""
    m = kmh_to_mph(v_kmh)
    return round(m, dec) if m is not None else ""
from scenarios import SCENARIOS, SPEED_CLASSES
from alignments import ALIGNMENTS, CORRIDOR_SEGMENTS


CLASS_COLOR = {sc.code: sc.color for sc in SPEED_CLASSES}

# ----------------------------------------------------------------- Caveats
# Textes VERBATIM — ne pas modifier sans mettre à jour inject_synthese_into_methodo.py
CAVEAT_FR1 = (
    "Le scénario S1 est un plafond physique légal (règlement Transport Canada), "
    "PAS la vitesse réellement exploitée par VIA."
)
CAVEAT_EN1 = (
    "Scenario S1 is a legal physical ceiling (Transport Canada rules), "
    "NOT VIA's actual operating speed."
)
CAVEAT_FR2 = (
    "Analyse de courbure seulement : ponts, tunnels, signalisation, électrification, "
    "état de la voie NON pris en compte. La précision visée est la classe de vitesse, pas le km/h."
)
CAVEAT_EN2 = (
    "Curvature analysis only: bridges, tunnels, signalling, electrification, "
    "track condition NOT considered. Target precision is the speed class, not exact km/h."
)
CAVEAT_FR3 = (
    "Le dévers réellement en voie n'a PAS été relevé : S1 suppose 100 mm (≈ 4 po) ; S2 et S3 sont des dévers de conception (127 mm = 5 po). "
    "v_max est un plafond géométrique au dévers normatif, pas une vitesse relevée."
)
CAVEAT_EN3 = (
    "Actual in-track cant was NOT surveyed: S1 assumes 100 mm (~4 in); S2 and S3 use design cant (127 mm = 5 in). "
    "v_max is a geometric ceiling at the normative cant, not a surveyed speed."
)

# Ancres du gradient continu, alignées sur les frontières des classes A-F.
# Interpolation linéaire RGB entre ces ancres → couleur continue par vmax,
# mais qui passe par les couleurs canoniques aux frontières (cohérence légende).
GRADIENT_ANCHORS = [
    (0,    "#660000"),  # rouge très foncé (vmax minimal)
    (100,  "#8b0000"),  # frontière E/F : rouge foncé
    (160,  "#ff4500"),  # frontière D/E : rouge-orange
    (200,  "#ffa500"),  # frontière C/D : orange
    (250,  "#ffd700"),  # frontière B/C : jaune
    (300,  "#32cd32"),  # frontière A/B : vert clair
    (350,  "#006400"),  # vert foncé (HSR pleine vitesse)
    (450,  "#003d00"),  # plafond visuel
]


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def vmax_to_color(vmax_kmh: float) -> str:
    """Couleur continue interpolée sur GRADIENT_ANCHORS."""
    if vmax_kmh <= GRADIENT_ANCHORS[0][0]:
        return GRADIENT_ANCHORS[0][1]
    if vmax_kmh >= GRADIENT_ANCHORS[-1][0]:
        return GRADIENT_ANCHORS[-1][1]
    for i in range(len(GRADIENT_ANCHORS) - 1):
        v0, c0 = GRADIENT_ANCHORS[i]
        v1, c1 = GRADIENT_ANCHORS[i + 1]
        if v0 <= vmax_kmh <= v1:
            t = (vmax_kmh - v0) / (v1 - v0)
            r0, g0, b0 = _hex_to_rgb(c0)
            r1, g1, b1 = _hex_to_rgb(c1)
            r = round(r0 + t * (r1 - r0))
            g = round(g0 + t * (g1 - g0))
            b = round(b0 + t * (b1 - b0))
            return _rgb_to_hex(r, g, b)
    return GRADIENT_ANCHORS[-1][1]


# ----------------------------------------------------------------- HTML map

def build_main_html(seg_features: list[dict], stations: list[dict], out_html: Path) -> None:
    m = folium.Map(location=[45.5, -75.5], zoom_start=6, tiles=None,
                   prefer_canvas=True)
    # Fond de carte ajouté hors sélecteur (control=False) : il ne doit pas
    # apparaître comme une entrée « cartodbpositron » dans le panneau de calques.
    folium.TileLayer("cartodbpositron", control=False).add_to(m)

    # Calques par scénario — segments colorés par leur classe sous ce scénario.
    # overlay=False → calque « de base » : le sélecteur affiche des boutons
    # radio, une seule option (S1 / S2 / S3) sélectionnable à la fois.
    for sid in ("S1", "S2", "S3"):
        sc_obj = SCENARIOS[sid]
        layer = folium.FeatureGroup(
            name=f"{sid} · {sc_obj.name_fr} / {sc_obj.name_en}",
            overlay=False,
            show=(sid == "S2"),  # S2 sélectionné par défaut
        )
        for feat in seg_features:
            p = feat["properties"]
            classe = p[f"classe_{sid}"]
            vmax = float(p[f"vmax_{sid}_kmh"])
            color = CLASS_COLOR.get(classe, "#888888")
            coords_latlon = [(c[1], c[0]) for c in feat["geometry"]["coordinates"]]
            popup_html = (
                f"<b>{p['troncon_id']} — segment {p['seg_idx']}</b><br>"
                f"<b>Longueur / Length:</b> {p['longueur_m']:.0f} m<br>"
                f"<b>Degré de courbure / Degree of curve "
                f"(gouvernant, max):</b> {fmt_dc(p['R_classif_m'])}"
                f" &nbsp;<small>(rayon {p['R_classif_m']} m · R_p50 "
                f"{p['R_p50_m']} m · R_moy {p['R_moy_m']} m)</small><br>"
                f"<hr style='margin:4px 0'>"
                f"<b>{sid} — {sc_obj.name_fr}</b><br>"
                f"Plafond de courbure / curvature ceiling &asymp; "
                f"<b>{vmax:.0f} km/h / {kmh_to_mph(vmax):.0f} mph</b> &nbsp;(classe {classe})<br>"
                f"<small>S1: {p['vmax_S1_kmh']:.0f} km/h ({kmh_to_mph(p['vmax_S1_kmh']):.0f} mph, {p['classe_S1']}) | "
                f"S3: {p['vmax_S3_kmh']:.0f} km/h ({kmh_to_mph(p['vmax_S3_kmh']):.0f} mph, {p['classe_S3']})</small><br>"
                f"<small style='color:#a00'>Plafond géométrique — PAS la vitesse "
                f"opérationnelle / Geometric ceiling — NOT operating speed</small><br>"
                f"<small>Entre / Between: {p['gare_amont']} → {p['gare_aval']}</small>"
            )
            folium.PolyLine(
                locations=coords_latlon, color=color, weight=4, opacity=0.85,
                popup=folium.Popup(popup_html, max_width=320),
            ).add_to(layer)
        layer.add_to(m)

    # Calque gares — toggleable
    layer_st = folium.FeatureGroup(name="Gares VIA / VIA stations", show=True)
    for st in stations:
        folium.CircleMarker(
            location=[st["lat"], st["lon"]],
            radius=4, color="black", fill=True, fill_color="white", fill_opacity=1.0, weight=2,
            popup=f"<b>{st['name']}</b><br>stop_id: {st['stop_id']}",
            tooltip=st["name"],
        ).add_to(layer_st)
    layer_st.add_to(m)

    # Légende bilingue avec couleurs canoniques par classe
    classes_table = "<table style='font-size:11px;border-collapse:collapse;width:100%'>"
    for sc in SPEED_CLASSES:
        classes_table += (
            f"<tr>"
            f"<td style='padding:2px 4px'>"
            f"<span style='display:inline-block;width:18px;height:12px;"
            f"background:{sc.color};border:1px solid #555;vertical-align:middle'></span>"
            f"</td>"
            f"<td style='padding:2px 4px'><b>{sc.code}</b></td>"
            f"<td style='padding:2px 4px'>{sc.name_fr} / {sc.name_en}</td>"
            f"<td style='padding:2px 4px;color:#666'>≥{int(sc.vmin_kmh)} km/h</td>"
            f"</tr>"
        )
    classes_table += "</table>"

    scenario_rows = "".join(
        f"<div style='margin-top:4px'><b>{sid}</b> {SCENARIOS[sid].name_fr}<br>"
        f"<small style='color:#444'>dévers {SCENARIOS[sid].cant_mm} mm "
        f"({SCENARIOS[sid].cant_in:.1f}&Prime;) · insuff. {SCENARIOS[sid].cant_def_mm} mm "
        f"({SCENARIOS[sid].cant_def_in:.1f}&Prime;) · v&asymp;{SCENARIOS[sid].coeff:.2f}&middot;&radic;R</small><br>"
        f"<small style='color:#777'>{SCENARIOS[sid].fret_fr}</small><br>"
        f"<small style='color:#999'>{SCENARIOS[sid].source}</small></div>"
        for sid in ("S1", "S2", "S3")
    )
    caveat_html = (
        f"<div style='margin-top:6px;padding:6px 8px;"
        f"background:#fff8e1;border:1px solid #f0a500;border-radius:3px;"
        f"font-size:10px;line-height:1.4;color:#5a3e00'>"
        f"<b>&#9888; Avertissements / Warnings</b><br>"
        f"<b>FR&nbsp;1&nbsp;:</b> {CAVEAT_FR1}<br>"
        f"<b>EN&nbsp;1&nbsp;:</b> {CAVEAT_EN1}<br>"
        f"<b>FR&nbsp;2&nbsp;:</b> {CAVEAT_FR2}<br>"
        f"<b>EN&nbsp;2&nbsp;:</b> {CAVEAT_EN2}<br>"
        f"<b>FR&nbsp;3&nbsp;:</b> {CAVEAT_FR3}<br>"
        f"<b>EN&nbsp;3&nbsp;:</b> {CAVEAT_EN3}"
        f"</div>"
    )
    legend_html = f"""
    <div style="position: fixed; bottom: 20px; left: 20px; background: white;
        padding: 10px 12px; border: 1px solid #888; border-radius: 4px;
        font: 11px/1.4 sans-serif; max-width: 400px; z-index: 9999;">
      <div style='font-weight:bold;font-size:13px'>Classes de vitesse / Speed classes</div>
      {classes_table}
      <hr style='margin:6px 0'>
      <div style='font-weight:bold;font-size:12px'>Scénarios / Scenarios</div>
      {scenario_rows}
      <hr style='margin:6px 0'>
      <div style='color:#888;font-size:10px'>
        v<sub>max</sub> exact (km/h) disponible dans le popup de chaque segment.<br>
        Alignement : VIA existant. Calque ALTO à venir en Phase ultérieure.
      </div>
      {caveat_html}
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    folium.LayerControl(collapsed=False).add_to(m)
    out_html.write_text(m.get_root().render(), encoding="utf-8")
    print(f"  Carte HTML : {out_html.name}")


# ----------------------------------------------------------------- KMZ

def _simplify_coords(coords_lonlat: list[list[float]], tol_deg: float) -> list[list[float]]:
    """Douglas-Peucker via shapely. coords format [lon, lat]."""
    if len(coords_lonlat) < 3:
        return coords_lonlat
    from shapely.geometry import LineString
    ls = LineString(coords_lonlat)
    simp = ls.simplify(tol_deg, preserve_topology=False)
    return [list(c) for c in simp.coords]


# Tolérance ~7m à lat 45° (1 deg ≈ 111km, donc 7m ≈ 6.3e-5 deg).
# Ratio typique observé : ~5-10x compression sans dégradation visible à zoom corridor.
KMZ_SIMPLIFY_TOL_DEG = 6.3e-5


def build_kmz(seg_features: list[dict], stations: list[dict], out_kmz: Path) -> None:
    kml = simplekml.Kml(name="TGV Canada — Courbatures du corridor VIA")
    kml.document.description = (
        "Phase 1 — analyse stratégique. Alignement VIA existant, 3 scénarios "
        "(S1 voie actuelle, S2 pendulaire LRC + dévers max standard CN 5 po, S3 pendulaire moderne insuffisance 270 mm). "
        "Sources : viarail GTFS + OSM PBF QC+ON. Géométries simplifiées (Douglas-Peucker, "
        "tol ~7m) pour rester sous la limite de 5 MB de Google My Maps.\n\n"
        "AVERTISSEMENTS / WARNINGS\n"
        f"FR 1 : {CAVEAT_FR1}\n"
        f"EN 1 : {CAVEAT_EN1}\n"
        f"FR 2 : {CAVEAT_FR2}\n"
        f"EN 2 : {CAVEAT_EN2}\n"
        f"FR 3 : {CAVEAT_FR3}\n"
        f"EN 3 : {CAVEAT_EN3}"
    )

    # Dossier par scénario, avec sous-dossiers ou styling par classe
    for sid in ("S1", "S2", "S3"):
        sc_obj = SCENARIOS[sid]
        folder = kml.newfolder(
            name=f"{sid} — {sc_obj.name_fr} / {sc_obj.name_en}",
            description=sc_obj.source,
        )
        folder.visibility = 1 if sid == "S2" else 0
        for feat in seg_features:
            p = feat["properties"]
            classe = p[f"classe_{sid}"]
            vmax = float(p[f"vmax_{sid}_kmh"])
            # KMZ : couleurs canoniques par classe A-F (Google Earth ne blend pas
            # comme un navigateur, des couleurs discrètes sont plus lisibles).
            # La carte HTML interactive garde le gradient continu pour l'analyse fine.
            color_hex = CLASS_COLOR.get(classe, "#888888")
            # KML utilise AABBGGRR
            color_kml = simplekml.Color.rgb(
                int(color_hex[1:3], 16), int(color_hex[3:5], 16), int(color_hex[5:7], 16),
                a=220,
            )
            line = folder.newlinestring(name=f"{p['troncon_id']} #{p['seg_idx']} — {classe}")
            line.coords = _simplify_coords(feat["geometry"]["coordinates"], KMZ_SIMPLIFY_TOL_DEG)
            line.style.linestyle.color = color_kml
            line.style.linestyle.width = 4
            line.description = (
                f"Degré de courbure (gouvernant, max): {fmt_dc(p['R_classif_m'])} "
                f"(rayon {p['R_classif_m']} m | R_p50 {p['R_p50_m']} m "
                f"| R_moy {p['R_moy_m']} m)\n"
                f"Longueur: {p['longueur_m']:.0f} m\n"
                f"Plafond de courbure {sid} ≈ {p[f'vmax_{sid}_kmh']:.0f} km/h "
                f"({kmh_to_mph(p[f'vmax_{sid}_kmh']):.0f} mph) "
                f"(classe {classe}) — GÉOMÉTRIQUE, PAS opérationnel\n"
                f"Autres scénarios: S1 {p['vmax_S1_kmh']:.0f} km/h / "
                f"{kmh_to_mph(p['vmax_S1_kmh']):.0f} mph ({p['classe_S1']}), "
                f"S3 {p['vmax_S3_kmh']:.0f} km/h / "
                f"{kmh_to_mph(p['vmax_S3_kmh']):.0f} mph ({p['classe_S3']})\n"
                f"Entre {p['gare_amont']} et {p['gare_aval']}"
            )

    # Dossier gares
    folder_st = kml.newfolder(name="Gares VIA / VIA stations")
    for st in stations:
        pt = folder_st.newpoint(name=st["name"], coords=[(st["lon"], st["lat"])])
        pt.description = f"stop_id: {st['stop_id']}"
        pt.style.iconstyle.icon.href = "http://maps.google.com/mapfiles/kml/shapes/rail.png"

    kml.savekmz(str(out_kmz))
    print(f"  KMZ : {out_kmz.name} ({out_kmz.stat().st_size/1e6:.1f} MB)")


# ----------------------------------------------------------------- CSV

def build_segments_csv(seg_features: list[dict], out_csv: Path) -> None:
    """En-têtes bilingues sur 2 lignes : ligne 1 = FR, ligne 2 = EN."""
    headers_fr = [
        "alignement_id", "id_segment", "tronçon", "km_début", "km_fin",
        "mille_début", "mille_fin",
        "longueur_m", "longueur_mille",
        "degré_courbure_gouvernant_deg",
        "R_min_m", "R_classant_min_m", "R_p10_m", "R_p50_m", "R_moy_m",
        "vmax_S1_kmh_plafond_courbure", "vmax_S1_mph_plafond_courbure",
        "vmax_S2_kmh_plafond_courbure", "vmax_S2_mph_plafond_courbure",
        "vmax_S3_kmh_plafond_courbure", "vmax_S3_mph_plafond_courbure",
        "classe_S1", "classe_S2", "classe_S3",
        "gare_amont", "gare_aval",
    ]
    headers_en = [
        "alignment_id", "segment_id", "section", "km_start", "km_end",
        "mile_start", "mile_end",
        "length_m", "length_mile",
        "degree_of_curve_governing_deg",
        "R_min_m", "R_governing_min_m", "R_p10_m", "R_p50_m", "R_mean_m",
        "vmax_S1_kmh_curv_ceiling", "vmax_S1_mph_curv_ceiling",
        "vmax_S2_kmh_curv_ceiling", "vmax_S2_mph_curv_ceiling",
        "vmax_S3_kmh_curv_ceiling", "vmax_S3_mph_curv_ceiling",
        "class_S1", "class_S2", "class_S3",
        "station_upstream", "station_downstream",
    ]
    # encoding utf-8-sig (BOM) + delimiter ; pour Excel Windows FR (sinon
    # tout se retrouve dans une seule colonne car la locale attend ;)
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers_fr)
        writer.writerow(headers_en)
        for feat in seg_features:
            p = feat["properties"]
            dc_gouv = degre_courbure(p["R_classif_m"])
            writer.writerow([
                p["alignment_id"],
                f"{p['troncon_id']}-{p['seg_idx']:04d}",
                p["troncon_id"],
                round(p["km_debut"], 3),
                round(p["km_fin"], 3),
                round(km_to_mile(p["km_debut"]), 3),
                round(km_to_mile(p["km_fin"]), 3),
                round(p["longueur_m"], 1),
                round(km_to_mile(p["longueur_m"] / 1000.0), 3),
                round(dc_gouv, 2) if dc_gouv is not None else "",
                p["R_min_m"],
                p["R_classif_m"],
                p["R_p10_m"],
                p["R_p50_m"],
                p["R_moy_m"],
                round(p["vmax_S1_kmh"], 1), _mph(p["vmax_S1_kmh"]),
                round(p["vmax_S2_kmh"], 1), _mph(p["vmax_S2_kmh"]),
                round(p["vmax_S3_kmh"], 1), _mph(p["vmax_S3_kmh"]),
                p["classe_S1"],
                p["classe_S2"],
                p["classe_S3"],
                p["gare_amont"],
                p["gare_aval"],
            ])
    print(f"  CSV : {out_csv.name} ({len(seg_features)} segments)")


# ----------------------------------------------------------------- Avertissements TXT

def build_avertissements_txt(out_txt: Path) -> None:
    """Écrit livrables/LISEZ-MOI_AVERTISSEMENTS.txt (UTF-8, FR puis EN)."""
    content = (
        "AVERTISSEMENTS — TGV Canada Phase 1 — Analyse de courbures du corridor VIA\n"
        "=============================================================================\n\n"
        "FRANÇAIS\n"
        "--------\n\n"
        f"1. {CAVEAT_FR1}\n\n"
        f"2. {CAVEAT_FR2}\n\n"
        f"3. {CAVEAT_FR3}\n\n"
        "ENGLISH\n"
        "-------\n\n"
        f"1. {CAVEAT_EN1}\n\n"
        f"2. {CAVEAT_EN2}\n\n"
        f"3. {CAVEAT_EN3}\n"
    )
    out_txt.write_text(content, encoding="utf-8")
    print(f"  LISEZ-MOI : {out_txt.name}")


# ----------------------------------------------------------------- main

def load_stations() -> list[dict]:
    matched = json.loads(CORRIDOR_MATCHED_GEOJSON.read_text(encoding="utf-8"))
    out = []
    seen = set()
    for f in matched["features"]:
        if f["properties"]["kind"] != "station_snapped":
            continue
        sid = f["properties"]["stop_id"]
        if sid in seen:
            continue
        seen.add(sid)
        lon, lat = f["geometry"]["coordinates"]
        out.append({
            "stop_id": sid,
            "name": f["properties"]["stop_name"],
            "lat": lat, "lon": lon,
        })
    return out


def main() -> None:
    ensure_dirs()
    if not SEGMENTS_GEOJSON.exists():
        sys.exit(f"segments.geojson introuvable — lancer 05_segment_and_classify.py.")
    if not CORRIDOR_MATCHED_GEOJSON.exists():
        sys.exit(f"corridor_matched.geojson introuvable — lancer 03_match_gtfs_to_osm.py.")

    print("=== Étape 7 — Production des livrables ===")
    segments = json.loads(SEGMENTS_GEOJSON.read_text(encoding="utf-8"))
    seg_features = [f for f in segments["features"] if f["properties"]["kind"] == "homog_segment"]
    stations = load_stations()
    print(f"  {len(seg_features)} segments, {len(stations)} gares")

    build_main_html(seg_features, stations, DELIVERABLES / "corridor_courbatures.html")
    build_kmz(seg_features, stations, DELIVERABLES / "corridor_courbatures.kmz")
    build_segments_csv(seg_features, DELIVERABLES / "segments_courbature.csv")
    build_avertissements_txt(DELIVERABLES / "LISEZ-MOI_AVERTISSEMENTS.txt")

    print(f"\nLivrables prêts dans {DELIVERABLES.relative_to(DELIVERABLES.parent.parent)}/")


if __name__ == "__main__":
    main()

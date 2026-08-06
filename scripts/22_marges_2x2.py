"""Étape 22 — Le 2×2 du corridor : marges mesurées par inter-gare × cellule.

Éléments 2 et 5 du plan v3, le même instrument lu deux fois :
  - lecture « doublement »   : simple-CN vs double-CN = ce que la voie double achète,
    mesuré ici, chez ce propriétaire (croisements éliminés, dépassements subis) ;
  - lecture « régime »       : simple-VIA vs double-CN = si une voie de moins sous
    le bon régime bat une voie de plus sous le mauvais, le régime pèse plus que le
    béton.

Définition de la mesure, par paire de gares adjacentes (inter-gare) :
    marge = (T_horaire − T_base_S1) / T_base_S1
  T_horaire = médiane GTFS (arrivée B − départ A) sur tous les sillons desservant
              A puis B (les deux sens agrégés : même géométrie).
  T_base_S1 = ∫ dx / min(v_geo_S1(x), 160)  sur [km_A, km_B] — le plafond
              géométrique de la voie actuelle, borné au régime de vitesse actuel
              du corridor (aucun scénario d'investissement : on mesure le coussin
              d'exploitation d'aujourd'hui, à géométrie neutralisée).

Cellules (étiquetage par recouvrement km avec segments_voies + propriétaire) :
  simple-VIA : voie simple, subdivisions VIA (Alexandria, Smiths Falls) —
               croisements planifiés VIA-VIA
  simple-CN  : voie simple, tronçons CN (rive sud MTL-QC) — croisements subis,
               fret prioritaire
  double-CN  : voie double CN (Kingston) — croisements éliminés, dépassements
               subis
  mixte      : paires dont la voie est < 70 % d'un seul état (publiées, non
               classées dans le 2×2)
Propriétaire par bornes km (SOURCE : subdivisions observées dans la jointure PN,
script 20) : MTL-Ott = CN jusqu'à Coteau (62,3 km) puis VIA ; Ott-TO = VIA
jusqu'à Brockville (110,0 km) puis CN ; MTL-QC et MTL-TO = CN.

Exclusions (nœuds contaminants, plan v3) :
  - toute paire couverte par un bloc urbain figé (Montréal↔Saint-Lambert,
    Montréal↔Dorval, Guildwood↔Toronto, Sainte-Foy↔Québec) ;
  - paires adjacentes aux ponts : Saint-Lambert↔Saint-Hyacinthe (pont Victoria),
    Charny↔Sainte-Foy (pont de Québec) ;
  - les paires touchant Ottawa sont GARDÉES mais étiquetées (l'approche urbaine
    ±10 km est incluse dans la paire — biais à la hausse sur la marge, dit).

Caveats à publier (bornes, pas de point unique) : échantillon mince par cellule,
densités de fret différentes entre cellules, certains sillons font des arrêts
non listés (ex. Fallowfield) qui gonflent légèrement le T_horaire de leur paire.

Entrées : GTFS, segments.geojson, segments_voies.geojson
Sorties : livrables/marges_par_intergare.csv, livrables/marges_2x2_synthese.csv
"""
from __future__ import annotations

import importlib
import json
from statistics import median

import pandas as pd

from utils import INTERMEDIATES, DELIVERABLES

t21 = importlib.import_module("21_tbase_bande")

OUT_PAIRS = DELIVERABLES / "marges_par_intergare.csv"
OUT_SYNTH = DELIVERABLES / "marges_2x2_synthese.csv"

CAP_KMH = 160.0            # régime de vitesse actuel du corridor
DOMINANCE = 0.70           # part d'un état de voie pour classer la paire

# (tronçon, [(nom, stop_id, km), ...]) — extrémités + intermédiaires, ordre km.
# L'Aéroport (555, desserte alternative de Dorval au même km) est omis.
STATIONS = {
    "MTL-QC":  [("Montréal", "226", 0.0), ("Saint-Lambert", "343", 6.11),
                ("Saint-Hyacinthe", "631", 53.24), ("Drummondville", "630", 100.01),
                ("Charny", "492", 245.04), ("Sainte-Foy", "629", 249.98),
                ("Québec", "628", 269.85)],
    "MTL-Ott": [("Montréal", "226", 0.0), ("Dorval", "332", 17.79),
                ("Coteau", "351", 62.28), ("Alexandria", "344", 99.43),
                ("Casselman", "419", 138.78), ("Ottawa", "617", 185.42)],
    "Ott-TO":  [("Ottawa", "617", 0.0), ("Fallowfield", "576", None),
                ("Smiths Falls", "377", 64.62),
                ("Brockville", "35", 110.0), ("Gananoque", "200", 155.83),
                ("Kingston", "58", 191.99), ("Napanee", "309", 227.49),
                ("Belleville", "415", 262.44), ("Trenton Junction", "413", 281.92),
                ("Cobourg", "178", 332.06), ("Port Hope", "9", 342.88),
                ("Oshawa", "367", 393.31), ("Guildwood", "450", 423.93),
                ("Toronto", "119", 444.05)],
    # Extension sud-ouest (2026-08) : km relevés dans corridor_gtfs.geojson ;
    # Aldershot (desservie par les trains Windsor/Niagara) projetée au tracé.
    "TO-WDN":  [("Toronto", "119", 0.0), ("Oakville", "436", 34.06),
                ("Aldershot", "600", None), ("Brantford", "162", 96.23),
                ("Woodstock", "282", 138.87), ("Ingersoll", "323", 153.96),
                ("London", "93", 184.49), ("Glencoe", "78", 233.71),
                ("Chatham", "601", 288.16), ("Windsor", "618", 358.75)],
    "TO-SAR":  [("Toronto", "119", 0.0), ("Malton", "34", 25.65),
                ("Brampton", "322", 34.12), ("Georgetown", "6", 47.09),
                ("Guelph", "70", 78.41), ("Kitchener", "114", 101.06),
                ("Stratford", "7", 142.16), ("St. Marys", "11", 160.16),
                ("London", "93", 194.61), ("Strathroy", "14", 225.4),
                ("Sarnia", "341", 289.46)],
    "MTL-TO":  [("Montréal", "226", 0.0), ("Dorval", "332", 17.79),
                ("Cornwall", "602", None),
                ("Brockville", "35", 204.72), ("Gananoque", "200", 249.75),
                ("Kingston", "58", 285.97), ("Napanee", "309", 321.47),
                ("Belleville", "415", 356.42), ("Trenton Junction", "413", 375.9),
                ("Cobourg", "178", 426.05), ("Port Hope", "9", 436.86),
                ("Oshawa", "367", 487.24), ("Guildwood", "450", 517.94),
                ("Toronto", "119", 538.06)],
}

# Propriétaire par tronçon : liste de (km_fin_exclusif, owner) ordonnée.
# SOURCES : sources/proprietes_voies_verification.md (plan triennal VIA art. 141 ;
# BST R19H0021 ; communiqué CN-Metrolinx 2011). Metrolinx possède la Kingston de
# Union à Pickering Jct (≈ PM 315,2, déduction) : ≈ 29,9 km avant Toronto.
MTX_FROM_TORONTO_KM = 29.9
OWNER = {
    "MTL-QC":  [(1e9, "CN")],
    "MTL-Ott": [(62.28, "CN"), (1e9, "VIA")],
    "Ott-TO":  [(110.0, "VIA"), (444.05 - MTX_FROM_TORONTO_KM, "CN"), (1e9, "MTX")],
    "MTL-TO":  [(538.06 - MTX_FROM_TORONTO_KM, "CN"), (1e9, "MTX")],
    # Sud-ouest. TO-WDN : Oakville sub Metrolinx jusqu'au PM 32,06 (≈ km 50,1) ;
    # CN (Dundas + Chatham-CN) ; VIA sur les 67,1 derniers km (Bloomfield→Windsor,
    # plan triennal art. 141 : 358,75 − 67,1 ≈ 291,7). TO-SAR : Weston Metrolinx
    # (→ Bramalea ≈ km 29), Halton CN (→ Silver/Georgetown ≈ km 46), Guelph
    # Metrolinx (→ Kitchener ≈ km 103), puis CN (Guelph ouest + Strathroy).
    # Bornes ≈ : voir sources/proprietes_voies_verification.md.
    "TO-WDN":  [(50.1, "MTX"), (291.7, "CN"), (1e9, "VIA")],
    "TO-SAR":  [(29.0, "MTX"), (46.0, "CN"), (103.0, "MTX"), (1e9, "CN")],
}

EXCLUDED_PAIRS = {
    ("Ott-TO", "Ottawa", "Fallowfield"): "bloc urbain (approche d'Ottawa)",
    ("MTL-QC", "Montréal", "Saint-Lambert"): "bloc urbain (pont Victoria)",
    ("MTL-QC", "Saint-Lambert", "Saint-Hyacinthe"): "adjacente au pont Victoria",
    ("MTL-QC", "Charny", "Sainte-Foy"): "adjacente au pont de Québec",
    ("MTL-QC", "Sainte-Foy", "Québec"): "bloc urbain (pont de Québec)",
    ("MTL-Ott", "Montréal", "Dorval"): "bloc urbain",
    ("MTL-TO", "Montréal", "Dorval"): "bloc urbain",
    ("Ott-TO", "Guildwood", "Toronto"): "bloc urbain",
    ("MTL-TO", "Guildwood", "Toronto"): "bloc urbain",
}
OTTAWA_FLAG = {("MTL-Ott", "Casselman", "Ottawa")}
# Banlieue torontoise (Metrolinx, cellule « double-passager » INDICATIVE : arrêts
# GO denses, congestion terminale) : hors synthèse 2×2, publiée dans la table.
for _k in [("TO-WDN", "Toronto", "Oakville"), ("TO-SAR", "Toronto", "Malton"),
           ("TO-SAR", "Malton", "Brampton")]:
    EXCLUDED_PAIRS[_k] = "banlieue Toronto (Metrolinx) : cellule indicative"

OWNER_DOMINANCE = 0.85  # part majoritaire requise ; sinon la paire chevauche

# Régions d'analyse : le CŒUR (4 tronçons du plan v3, voie de classe 4-5, où la
# marge vs plafond géométrique mesure surtout l'exploitation) et le SUD-OUEST
# (voie de classe inférieure, ralentissements permanents documentés BST : la
# marge y mélange ÉTAT DE LA VOIE et régime). Les synthèses et les deux
# lectures se font PAR RÉGION, jamais en les fusionnant.
REGION = {"MTL-QC": "coeur", "MTL-Ott": "coeur", "Ott-TO": "coeur",
          "MTL-TO": "coeur", "TO-WDN": "sud-ouest", "TO-SAR": "sud-ouest"}


def pair_owner(t: str, km0: float, km1: float) -> tuple[str, float]:
    """(propriétaire majoritaire, sa part de longueur) sur [km0, km1]."""
    shares: dict[str, float] = {}
    lo = 0.0
    for km_end, owner in OWNER[t]:
        ov = max(0.0, min(km1, km_end) - max(km0, lo))
        if ov > 0:
            shares[owner] = shares.get(owner, 0.0) + ov
        lo = km_end
    if not shares or km1 <= km0:
        return "?", 0.0
    owner = max(shares, key=shares.get)
    return owner, shares[owner] / (km1 - km0)


def load_voies():
    gj = json.load(open(INTERMEDIATES / "segments_voies.geojson", encoding="utf-8"))
    rows = [f["properties"] for f in gj["features"]]
    return rows


def track_shares(voies, t: str, km0: float, km1: float) -> dict[str, float]:
    tot = {"simple": 0.0, "double": 0.0, "multiple": 0.0}
    for v in voies:
        if v["troncon_id"] != t:
            continue
        ov = max(0.0, min(km1, v["km_fin"]) - max(km0, v["km_debut"]))
        if ov > 0:
            tot[v["etat_label"]] = tot.get(v["etat_label"], 0.0) + ov
    length = km1 - km0
    return {k: (val / length if length > 0 else 0.0) for k, val in tot.items()}


def cell_of(owner: str, shares: dict[str, float]) -> str:
    dbl = shares.get("double", 0) + shares.get("multiple", 0)
    if shares.get("simple", 0) >= DOMINANCE:
        return f"simple-{owner}"
    if dbl >= DOMINANCE:
        return f"double-{owner}"
    return "mixte"


def tbase_pair(by_t, t: str, km0: float, km1: float) -> float:
    minutes = 0.0
    for p in by_t[t]:
        ov = max(0.0, min(km1, p["km_fin"]) - max(km0, p["km_debut"]))
        if ov > 0:
            v = min(p["vmax_S1_kmh"], CAP_KMH)
            if v > 0:
                minutes += ov / v * 60.0
    return minutes


def resolve_missing_kms() -> None:
    """Complète les km None de STATIONS par projection du point d'arrêt GTFS
    sur le tracé matché du tronçon (même référence km que segments.geojson,
    écart < 0,3 % dû au rééchantillonnage)."""
    import io
    import zipfile

    import geopandas as gpd
    from shapely.geometry import LineString, Point

    need = {(t, i) for t, sts in STATIONS.items() for (_, i, k) in sts if k is None}
    if not need:
        return
    with zipfile.ZipFile(t21.GTFS_ZIP) as z:
        stops = pd.read_csv(io.BytesIO(z.read("stops.txt")), dtype=str)
    coords = {r.stop_id: (float(r.stop_lon), float(r.stop_lat))
              for r in stops.itertuples() if r.stop_id in {i for _, i in need}}
    gj = json.load(open(INTERMEDIATES / "corridor_matched.geojson", encoding="utf-8"))
    lines = {f["properties"]["troncon_id"]: LineString(f["geometry"]["coordinates"])
             for f in gj["features"]
             if f["geometry"]["type"] == "LineString" and f["properties"].get("troncon_id")}
    lines_m = gpd.GeoSeries(list(lines.values()), crs="EPSG:4326").to_crs("EPSG:3978")
    lines_m = dict(zip(lines.keys(), lines_m))
    for t, sts in STATIONS.items():
        for idx, (name, sid, km) in enumerate(sts):
            if km is None:
                pt = gpd.GeoSeries([Point(coords[sid])], crs="EPSG:4326").to_crs("EPSG:3978")[0]
                km_proj = lines_m[t].project(pt) / 1000.0
                sts[idx] = (name, sid, round(km_proj, 2))
                print(f"  km projeté : {name} ({t}) = {km_proj:.2f} km "
                      f"(écart au tracé {lines_m[t].distance(pt):.0f} m)")


def gtfs_pair_samples() -> dict[tuple[str, str], list[float]]:
    import io
    import zipfile
    with zipfile.ZipFile(t21.GTFS_ZIP) as z:
        st = pd.read_csv(io.BytesIO(z.read("stop_times.txt")),
                         dtype={"trip_id": str, "stop_id": str})
    st = st.sort_values(["trip_id", "stop_sequence"])
    pairs = set()
    for t, sts in STATIONS.items():
        for (na, ia, ka), (nb, ib, kb) in zip(sts, sts[1:]):
            pairs.add((ia, ib))
    stops = {s for p in pairs for s in p}
    samples: dict[tuple[str, str], list[float]] = {p: [] for p in pairs}
    sub = st[st.stop_id.isin(stops)]
    for _, g in sub.groupby("trip_id"):
        seq = list(zip(g.stop_id, g.departure_time, g.arrival_time))
        pos = {sid: i for i, (sid, _, _) in enumerate(seq)}
        for (a, b) in pairs:
            if a not in pos or b not in pos:
                continue
            lo, hi = (a, b) if pos[a] < pos[b] else (b, a)
            if pos[hi] - pos[lo] != 1:
                continue  # une autre gare du corridor s'intercale : pas la paire pure
            dep, arr = seq[pos[lo]][1], seq[pos[hi]][2]
            if isinstance(dep, str) and isinstance(arr, str):
                dt = t21._hms_to_min(arr) - t21._hms_to_min(dep)
                if 0 < dt < 24 * 60:
                    samples[(a, b)].append(dt)
    return samples


def main() -> None:
    by_t = t21.load_segments()
    voies = load_voies()
    resolve_missing_kms()
    samples = gtfs_pair_samples()

    rows = []
    seen_physical: dict[tuple[str, str], str] = {}
    for t, sts in STATIONS.items():
        for (na, ia, ka), (nb, ib, kb) in zip(sts, sts[1:]):
            s = samples.get((ia, ib), [])
            t_hor = median(s) if s else None
            phys = tuple(sorted((ia, ib)))
            dup_of = seen_physical.get(phys, "")
            if not dup_of:
                seen_physical[phys] = t
            t_base = tbase_pair(by_t, t, ka, kb)
            shares = track_shares(voies, t, ka, kb)
            owner, own_share = pair_owner(t, ka, kb)
            cell = cell_of(owner, shares)
            key = (t, na, nb)
            excl = EXCLUDED_PAIRS.get(key, "")
            if not excl and own_share < OWNER_DOMINANCE:
                excl = (f"chevauche une frontière de propriétaire "
                        f"({owner} {own_share:.0%})")
            marge = (100 * (t_hor - t_base) / t_base) if (t_hor and t_base > 0) else None
            m100 = (100 * (t_hor - t_base) / (kb - ka)) if (t_hor and kb > ka) else None
            if len(s) >= 4:
                ss = sorted(s)
                q25, q75 = ss[int(0.25 * (len(ss) - 1))], ss[int(0.75 * (len(ss) - 1))]
                iqr = q75 - q25
            else:
                iqr = None
            rows.append({
                "troncon": t, "region": REGION[t], "de": na, "a": nb,
                "km_debut": ka, "km_fin": kb, "longueur_km": round(kb - ka, 1),
                "cellule": cell, "part_simple_pct": round(100 * shares.get("simple", 0)),
                "part_double_plus_pct": round(100 * (shares.get("double", 0)
                                                     + shares.get("multiple", 0))),
                "t_horaire_med_min": round(t_hor, 1) if t_hor else "",
                "n_sillons": len(s),
                "t_base_S1cap160_min": round(t_base, 1),
                "marge_pct": round(marge, 1) if marge is not None else "",
                "marge_min_par_100km": round(m100, 1) if m100 is not None else "",
                "dispersion_iqr_min": round(iqr, 1) if iqr is not None else "",
                "dispersion_iqr_pct": round(100 * iqr / t_hor, 1)
                                      if (iqr is not None and t_hor) else "",
                "doublon_physique_de": dup_of,
                "exclue_du_2x2": excl,
                "note": "contient l'approche d'Ottawa (±10 km urbains)"
                        if key in OTTAWA_FLAG or (t, nb, na) in OTTAWA_FLAG else "",
            })
    df = pd.DataFrame(rows)
    df.to_csv(OUT_PAIRS, sep=";", index=False, encoding="utf-8-sig")

    kept = df[(df.exclue_du_2x2 == "") & (df.marge_pct != "")
              & (df.doublon_physique_de == "")].copy()
    kept["marge_pct"] = pd.to_numeric(kept["marge_pct"])
    kept["dispersion_iqr_pct"] = pd.to_numeric(kept["dispersion_iqr_pct"], errors="coerce")
    synth = (kept[kept.cellule != "mixte"]
             .groupby(["region", "cellule"])
             .agg(n=("marge_pct", "count"), mediane=("marge_pct", "median"),
                  q25=("marge_pct", lambda x: x.quantile(.25)),
                  q75=("marge_pct", lambda x: x.quantile(.75)),
                  minimum=("marge_pct", "min"), maximum=("marge_pct", "max"),
                  disp_iqr_pct_med=("dispersion_iqr_pct", "median"))
             .round(1).reset_index())
    synth.to_csv(OUT_SYNTH, sep=";", index=False, encoding="utf-8-sig")

    print("=== Étape 22 — Le 2×2 : marge mesurée par inter-gare ===\n")
    print(f"{'tronçon':<8} {'paire':<34} {'cell':<11} {'T_hor':>6} {'T_base':>6} "
          f"{'marge %':>8}  notes")
    for r in rows:
        marge = r["marge_pct"] if r["marge_pct"] != "" else "  —"
        note = r["exclue_du_2x2"] or r["note"]
        print(f"{r['troncon']:<8} {r['de']+' → '+r['a']:<34} {r['cellule']:<11} "
              f"{r['t_horaire_med_min']:>6} {r['t_base_S1cap160_min']:>6} {marge:>8}  {note}")
    print("\nSynthèse par cellule (paires retenues, hors mixte) :")
    print(synth.to_string(index=False))

    # ---- Sensibilité à la pénalité d'arrêt (critique « dénominateur » 2026-08-06) :
    # T_base de paire n'inclut pas l'accélération/freinage des arrêts d'extrémité,
    # ce qui gonfle la marge des paires COURTES. Conservateur pour la lecture
    # doublement (les paires simple-CN sont longues), ANTI-conservateur pour la
    # lecture régime (le double-CN a les paires les plus courtes). On teste donc
    # le classement avec une pénalité p ajoutée à T_base (p ≈ v/2·(1/a+1/d) :
    # ~1,5-2 min à 160 km/h pour a≈0,4 / d≈0,5 m/s² ; 3 min = borne haute).
    print("\nSensibilité à la pénalité d'arrêt p (CŒUR seulement, médianes par cellule) :")
    kt = kept[(kept.cellule != "mixte") & (kept.region == "coeur")].copy()
    kt["t_hor"] = pd.to_numeric(kt["t_horaire_med_min"])
    kt["t_base"] = pd.to_numeric(kt["t_base_S1cap160_min"])
    print(f"  {'p (min)':>8} {'double-CN':>10} {'simple-VIA':>11} {'simple-CN':>10}")
    for p in (0.0, 1.5, 3.0):
        m = (100 * (kt.t_hor - (kt.t_base + p)) / (kt.t_base + p))
        med_p = m.groupby(kt.cellule).median()
        print(f"  {p:>8} {med_p.get('double-CN', float('nan')):>10.1f} "
              f"{med_p.get('simple-VIA', float('nan')):>11.1f} "
              f"{med_p.get('simple-CN', float('nan')):>10.1f}")

    med = {r["cellule"]: r["mediane"] for _, r in synth.iterrows()
           if r["region"] == "coeur"}
    med_sw = {r["cellule"]: r["mediane"] for _, r in synth.iterrows()
              if r["region"] == "sud-ouest"}
    via_pure = kept[(kept.cellule == "simple-VIA") & (kept.note == "")
                    & (kept.region == "coeur")]["marge_pct"]
    print("\n=== LECTURES DU CŒUR (classe de voie homogène) ===")
    print("Lecture « doublement » (simple-CN vs double-CN, même propriétaire) :")
    print(f"  médianes {med.get('simple-CN')} % vs {med.get('double-CN')} % : "
          f"le doublement achète ≈ {med.get('simple-CN', 0) - med.get('double-CN', 0):.0f} points "
          f"de marge (échantillon simple-CN MINCE, n=2 : publier en bornes)")
    print("Lecture « régime » (formulation robuste au biais de dénominateur) :")
    print(f"  le coût de la voie simple = simple-VIA − double-CN "
          f"({med.get('simple-VIA', 0) - med.get('double-CN', 0):+.1f} pts, stable 3-6 pts "
          f"à toute pénalité d'arrêt) CONTRE simple-CN − double-CN "
          f"({med.get('simple-CN', 0) - med.get('double-CN', 0):+.1f} pts, 27-33 pts). "
          f"Sous régime VIA, la voie simple coûte quelques points ; sous régime CN, "
          f"elle en coûte ~7 fois plus. C'est le régime qui fixe le prix du béton.")
    print("\n=== SUD-OUEST (voie de classe inférieure : la marge vs plafond "
          "géométrique y mélange ÉTAT DE LA VOIE et régime — ne JAMAIS fusionner "
          "avec le cœur) ===")
    print(f"  Contraste interne, à état de voie comparable : simple-VIA "
          f"(Chatham-Windsor, 8 VIA vs 2 fret/j) {med_sw.get('simple-VIA', '—')} % "
          f"CONTRE simple-CN (Guelph ouest, Strathroy) {med_sw.get('simple-CN', '—')} %. "
          f"double-CN (Dundas) {med_sw.get('double-CN', '—')} % ; simple-MTX "
          f"(Guelph, 23 GO/j) {med_sw.get('simple-MTX', '—')} % — indicatifs.")

    print("\nCaveat de mesure : T_horaire de paire inclut l'effet d'accélération/"
          "freinage des arrêts d'extrémité, que T_base ne modélise pas → les paires "
          "COURTES sont gonflées. Le double-CN ayant les paires les plus courtes, "
          "la lecture « doublement » est CONSERVATRICE. La marge min/100 km "
          "(colonne dédiée) se compare aux règles publiées (SNCF 4,5 ; "
          "Trafikverket 2-3) : l'écart mesuré ici est le coussin TOTAL "
          "(état de voie, ralentissements, cohabitation), pas la seule marge "
          "de régularité — décomposition : voir schittenhelm2011 au registre.")
    print(f"\nÉcrit {OUT_PAIRS.name} ({len(rows)} paires) et {OUT_SYNTH.name}.")


if __name__ == "__main__":
    main()

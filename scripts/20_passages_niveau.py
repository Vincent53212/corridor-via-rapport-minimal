"""Étape 20 — Passages à niveau : jointure inventaire TC × segments du corridor.

Élément 4 du plan v3 : un escalier + un compte + un tri.

Escalier réglementaire (bandes de vitesse GÉOMÉTRIQUE du segment porteur) :
  ≤153 km/h   : régime actuel (précédent domestique : plafond du Turbo — seuil,
                jamais un temps de parcours)
  154-177     : corridor scellé (traiter ou fermer chaque passage)
  178-201     : classe 7 FRA — système barrière/avertissement complet approuvé
                et fonctionnel (49 CFR 213.347(b), SOURCE ecfr213-347)
  >201        : zéro passage à niveau (49 CFR 213.347(a), classes 8-9)

Compte : N passages par bande × scénario × tronçon, plus un total corridor
DÉDOUBLONNÉ (un même passage physique — même TC Number — rattaché à deux
trajets, p.ex. le tronc commun Montréal↔Dorval de MTL-Ott et MTL-TO, ne compte
qu'une fois ; il est classé selon le trajet le plus rapide qui l'emprunte).

Tri en trois classes d'intervention (règles sur données ouvertes, documentées) :
  fermeture      : Access = Private (HYPOTHÈSE : l'alternative routière < 2 km
                   n'est pas vérifiée ici — réseau routier hors périmètre)
  standard       : Public, autorité routière municipale, ≤ 2 voies, non urbain
  complexe       : Public urbain (IsUrban=Y) OU ≥ 3 voies OU autorité
                   provinciale/fédérale (MTQ, MTO, etc.)

Ancrage opposable : 304 passages à prédicteurs (requête VIA, Cour fédérale,
12 nov. 2024, SOURCE via2024requete). L'inventaire TC ne code pas « prédicteur » :
on compare l'ordre de grandeur avec les passages publics à protection active
joints ici, et on documente l'écart de périmètre.

Entrées : ressources/en-grade-crossing-inventory-2023-update.csv (TC, 2023),
          intermediaires/segments.geojson
Sorties : livrables/passages_niveau_par_bande.csv
          livrables/passages_niveau_tri.csv
          livrables/passages_niveau_LISEZMOI.txt
"""
from __future__ import annotations

import geopandas as gpd
import pandas as pd

from utils import INTERMEDIATES, DELIVERABLES, RESOURCES, kmh_to_mph

INV = RESOURCES / "en-grade-crossing-inventory-2023-update.csv"
SEGMENTS = INTERMEDIATES / "segments.geojson"
OUT_BANDE = DELIVERABLES / "passages_niveau_par_bande.csv"
OUT_TRI = DELIVERABLES / "passages_niveau_tri.csv"
OUT_LISEZMOI = DELIVERABLES / "passages_niveau_LISEZMOI.txt"

CRS_M = "EPSG:3978"          # Canada Atlas Lambert (mètres, couvre tout le corridor)
BUFFER_M = 75.0              # rattachement passage → tracé ; sensibilité ±50 m documentée
SENS_M = (25.0, 125.0)

BANDES = [("≤153", 0.0, 153.0), ("154-177", 153.0, 177.0),
          ("178-201", 177.0, 201.0), (">201", 201.0, float("inf"))]
TRONCONS = ["MTL-QC", "MTL-Ott", "Ott-TO", "MTL-TO"]

# Autorités routières provinciales/fédérales → classe « complexe »
PROVINCIAL_HINTS = ("MTQ", "MTO", "Ministry", "Ministère", "Québec (gouv", "Ontario (gov")

# Liste blanche des subdivisions du corridor (observées à la jointure, validées).
# Les passages d'autres subdivisions tombés dans le buffer appartiennent à des
# lignes qui CROISENT ou LONGENT le corridor (ex. Sherbrooke-CN à Saint-Lambert,
# Vaudreuil-CP parallèle près de Dorval, Rouses Point, St-Guillaume,
# Beachburg-VIA au nord d'Ottawa) : exclus, avec compte rendu dans le LISEZMOI.
SUBDIV_CORRIDOR = {
    "Kingston - CN", "Kingston - GO", "Drummondville", "Alexandria - VIA",
    "St-Hyacinthe", "Brockville - VIA", "Belleville", "Smiths Falls",
    "Bridge", "Montréal",
}


def bande_of(v_kmh: float) -> str:
    for name, lo, hi in BANDES:
        if lo < v_kmh <= hi or (name == "≤153" and v_kmh <= 153):
            return name
    return ">201"


def load_inventory() -> gpd.GeoDataFrame:
    df = pd.read_csv(INV, encoding="utf-8-sig", low_memory=False)
    df.columns = [" ".join(c.split()) for c in df.columns]  # « Road  Authority » → « Road Authority »
    df = df[df["Province"].isin(["ON", "QC"])].copy()
    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
    df = df.dropna(subset=["Latitude", "Longitude"])
    # Embranchements (spur) : rattachés à un point milliaire d'embranchement,
    # pas à la voie principale → exclus du compte corridor.
    spur = df["Spur Mile Point"].astype(str).str.strip().replace("nan", "-") != "-"
    df = df[~spur]
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude),
                           crs="EPSG:4326").to_crs(CRS_M)
    return gdf


def load_segments() -> gpd.GeoDataFrame:
    segs = gpd.read_file(SEGMENTS)[
        ["troncon_id", "seg_idx", "km_debut", "km_fin",
         "vmax_S1_kmh", "vmax_S2_kmh", "vmax_S3_kmh", "gare_amont", "gare_aval",
         "geometry"]
    ].to_crs(CRS_M)
    return segs


def join(gdf: gpd.GeoDataFrame, segs: gpd.GeoDataFrame, buffer_m: float) -> pd.DataFrame:
    """Rattache chaque passage au segment le plus proche (par tronçon) ≤ buffer."""
    out = []
    for t in TRONCONS:
        st = segs[segs.troncon_id == t]
        j = gpd.sjoin_nearest(gdf, st, how="inner", max_distance=buffer_m,
                              distance_col="dist_m")
        # un passage ne se rattache qu'une fois par tronçon (au plus proche)
        j = j.sort_values("dist_m").drop_duplicates(subset=["TC Number"])
        j["troncon"] = t
        out.append(pd.DataFrame(j.drop(columns="geometry")))
    return pd.concat(out, ignore_index=True)


def classify_intervention(r: pd.Series) -> str:
    if str(r["Access"]).strip().lower() == "private":
        return "fermeture (HYPOTHÈSE : alternative routière non vérifiée)"
    ra = str(r["Road Authority"])
    lanes = pd.to_numeric(r.get("Lanes"), errors="coerce")
    urban = str(r.get("IsUrban", "")).strip().upper() == "Y"
    if urban or (pd.notna(lanes) and lanes >= 3) or any(h in ra for h in PROVINCIAL_HINTS):
        return "complexe (urbain / multi-voies / autorité provinciale)"
    return "standard (municipal, ≤2 voies, non urbain)"


def main() -> None:
    gdf = load_inventory()
    segs = load_segments()
    print(f"Inventaire TC (ON+QC, hors embranchements, géolocalisés) : {len(gdf)} passages")

    matched = join(gdf, segs, BUFFER_M)
    # sensibilité au buffer
    sens = {b: len(join(gdf, segs, b)["TC Number"].unique()) for b in SENS_M}
    excl = matched[~matched["Subdivision"].isin(SUBDIV_CORRIDOR)]
    n_excl = excl["TC Number"].nunique()
    print(f"Exclus (subdivisions hors corridor — lignes croisantes/parallèles) : "
          f"{n_excl} : {sorted(excl['Subdivision'].unique())}")
    matched = matched[matched["Subdivision"].isin(SUBDIV_CORRIDOR)].copy()
    n_unique = matched["TC Number"].nunique()
    print(f"Joints au corridor (buffer {BUFFER_M:.0f} m) : {n_unique} passages physiques "
          f"(sensibilité : {sens[SENS_M[0]]} à {SENS_M[0]:.0f} m, "
          f"{sens[SENS_M[1]]} à {SENS_M[1]:.0f} m)")

    subdivs = matched.groupby("Subdivision")["TC Number"].nunique().sort_values(ascending=False)
    print("\nSubdivisions observées (n passages) :")
    for s, n in subdivs.items():
        print(f"   {s:<28} {n}")

    # bandes par scénario
    for sid in ("S1", "S2", "S3"):
        matched[f"bande_{sid}"] = matched[f"vmax_{sid}_kmh"].map(bande_of)
    matched["intervention"] = matched.apply(classify_intervention, axis=1)

    # ---- comptes par bande × scénario × tronçon + total corridor dédoublonné
    rows = []
    for sid in ("S1", "S2", "S3"):
        for t in TRONCONS:
            sub = matched[matched.troncon == t]
            for name, *_ in BANDES:
                rows.append({"scenario": sid, "troncon": t, "bande_kmh": name,
                             "n_passages": int((sub[f"bande_{sid}"] == name).sum())})
        # corridor dédoublonné : classer chaque TC Number selon la vmax MAX des
        # trajets qui l'empruntent (bande la plus exigeante qu'il devra suivre)
        dedup = (matched.groupby("TC Number")[f"vmax_{sid}_kmh"].max().map(bande_of))
        for name, *_ in BANDES:
            rows.append({"scenario": sid, "troncon": "CORRIDOR (dédoublonné)",
                         "bande_kmh": name, "n_passages": int((dedup == name).sum())})
    pd.DataFrame(rows).to_csv(OUT_BANDE, sep=";", index=False, encoding="utf-8-sig")

    # ---- tri par passage (dédoublonné, une ligne par passage physique)
    first = matched.sort_values("dist_m").drop_duplicates(subset=["TC Number"]).copy()
    tri_cols = {
        "TC Number": "tc_number", "troncon": "troncon_principal",
        "km_debut": "km_segment", "Subdivision": "subdivision", "Mile": "mille",
        "Location": "localisation", "Access": "acces", "Jurisdiction": "juridiction",
        "Road Authority": "autorite_routiere", "Protection": "protection",
        "Trains Daily": "trains_jour", "Vehicles Daily": "vehicules_jour",
        "Lanes": "voies_route", "IsUrban": "urbain",
        "vmax_S1_kmh": "vmax_S1_kmh", "vmax_S2_kmh": "vmax_S2_kmh",
        "vmax_S3_kmh": "vmax_S3_kmh", "bande_S1": "bande_S1", "bande_S2": "bande_S2",
        "bande_S3": "bande_S3", "intervention": "intervention", "dist_m": "dist_trace_m",
    }
    tri = first[list(tri_cols)].rename(columns=tri_cols)
    tri["dist_trace_m"] = tri["dist_trace_m"].round(1)
    tri.to_csv(OUT_TRI, sep=";", index=False, encoding="utf-8-sig")

    # ---- comparaison à l'ancrage 304 (public + protection active)
    pub_actifs = first[(first["Access"].str.strip() == "Public")
                       & first["Protection"].str.contains("Active", na=False)]
    n_pub_actifs = len(pub_actifs)
    tri_counts = first["intervention"].value_counts()

    resume = (
        f"corridor dédoublonné : {first['TC Number'].nunique()} passages physiques ; "
        f"publics à protection active : {n_pub_actifs} (ancrage VIA nov. 2024 : 304 à prédicteurs)"
    )
    print(f"\n{resume}")
    print("\nTri d'intervention (corridor dédoublonné) :")
    for k, v in tri_counts.items():
        print(f"   {k:<55} {v}")

    OUT_LISEZMOI.write_text(f"""PASSAGES À NIVEAU — MÉTHODE ET AVERTISSEMENTS (2026-08)

Source : Inventaire des passages à niveau, Transports Canada, mise à jour 2023
(données ouvertes, SOURCE tc2023inventairepn au registre). {len(gdf)} passages
ON+QC géolocalisés hors embranchements ; {n_unique} rattachés au corridor
(buffer {BUFFER_M:.0f} m au tracé matché ; sensibilité avant filtre de subdivision :
{sens[SENS_M[0]]} passages à {SENS_M[0]:.0f} m, {sens[SENS_M[1]]} à {SENS_M[1]:.0f} m —
l'écart provient de voies parallèles proches et de la précision des coordonnées).
{n_excl} passages exclus car leur subdivision n'est pas une subdivision du corridor
(lignes croisantes ou parallèles tombées dans le buffer) ; subdivisions retenues :
{", ".join(sorted(SUBDIV_CORRIDOR))}.

Chaque passage hérite de la vitesse géométrique (plafond, PAS une vitesse
d'exploitation) du segment porteur, par scénario. Bandes de l'escalier
réglementaire : ≤153 (régime actuel, précédent Turbo cité comme seuil) ;
154-177 (corridor scellé : traiter ou fermer) ; 178-201 (49 CFR 213.347(b),
classe 7 : système approuvé FRA fonctionnel) ; >201 (213.347(a) : zéro passage).
Le 49 CFR est cité comme PRÉCÉDENT réglementaire nord-américain ; il ne
s'applique pas de plein droit au Canada.

Total corridor DÉDOUBLONNÉ : un même passage physique (TC Number) emprunté par
deux trajets ne compte qu'une fois, classé à la vmax maximale des trajets.

Tri d'intervention (règles sur données ouvertes) :
  fermeture  = accès privé (HYPOTHÈSE : l'existence d'une alternative < 2 km
               n'est pas vérifiée — réseau routier hors périmètre)
  standard   = public, municipal, ≤2 voies, hors zone urbaine
  complexe   = public urbain, ou ≥3 voies, ou autorité provinciale
Le lecteur applique ses propres coûts unitaires à ces trois classes.

Ancrage opposable : {resume}.
L'écart avec 304 s'explique par le périmètre : le chiffre de la requête VIA vise
les passages à PRÉDICTEURS (un équipement précis, non codé dans l'inventaire
ouvert) sur les subdivisions du CN concernées par le supplément d'octobre 2024 ;
notre compte couvre tous les passages publics à protection active du corridor
(toutes subdivisions, y compris VIA Alexandria/Smiths Falls).

AVERTISSEMENT : compte et tri = données ouvertes, sans visite de site ; les
vitesses sont des plafonds géométriques par scénario, jamais des promesses.
""", encoding="utf-8")
    print(f"\nÉcrit {OUT_BANDE.name}, {OUT_TRI.name}, {OUT_LISEZMOI.name}")


if __name__ == "__main__":
    main()

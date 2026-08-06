"""Fonctions partagées et constantes globales du pipeline."""
from __future__ import annotations
from pathlib import Path
import math

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESOURCES = PROJECT_ROOT / "ressources"
INTERMEDIATES = PROJECT_ROOT / "intermediaires"
DELIVERABLES = PROJECT_ROOT / "livrables"

GTFS_ZIP = RESOURCES / "viarail_GTFS.zip"
PBF_QUEBEC = RESOURCES / "quebec-260510.osm.pbf"
PBF_ONTARIO = RESOURCES / "ontario-260510.osm.pbf"

GRAPH_PKL = INTERMEDIATES / "osm_rails_graph.pkl"
CORRIDOR_GTFS_GEOJSON = INTERMEDIATES / "corridor_gtfs.geojson"
CORRIDOR_MATCHED_GEOJSON = INTERMEDIATES / "corridor_matched.geojson"
CURVATURE_PARQUET = INTERMEDIATES / "courbure_points.parquet"
SEGMENTS_GEOJSON = INTERMEDIATES / "segments.geojson"

EARTH_RADIUS_M = 6_371_000.0
G_ACCEL = 9.81           # m/s²
EFFECTIVE_GAUGE_MM = 1524  # écartement effectif = 60 po : reproduit EXACTEMENT la
                           # constante 0,0007 de la formule CN/AREMA (MR 1305-0)
                           # D = 0,0007·C·V² − Dd  ⟺  v = k·√R avec ce G


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance grand-cercle entre deux points (degrés décimaux) en mètres."""
    la1, lo1, la2, lo2 = map(math.radians, (lat1, lon1, lat2, lon2))
    dlat, dlon = la2 - la1, lo2 - lo1
    h = math.sin(dlat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))


def utm_epsg_for_lon(lon: float) -> int:
    """EPSG code de la zone UTM nord pour une longitude donnée. 18N = 32618, 19N = 32619."""
    zone = int((lon + 180) // 6) + 1
    return 32600 + zone


def pick_utm_for_corridor(lons: list[float]) -> int:
    """Choisit la zone UTM dominante pour un corridor (vote majoritaire)."""
    counts: dict[int, int] = {}
    for lon in lons:
        epsg = utm_epsg_for_lon(lon)
        counts[epsg] = counts.get(epsg, 0) + 1
    return max(counts, key=counts.get)


# --------------------------------------------- rayon « plus serré soutenu »

# Longueur sur laquelle une courbe doit être SOUTENUE pour gouverner la classe.
# Un coude parasite isolé (1-2 points : aiguillage clippé, sommet OSM véreux)
# ne survit pas à une médiane glissante de cette largeur ; une vraie courbe
# ferroviaire, oui (elle s'étend bien au-delà de 150 m).
ROBUST_MIN_SUPPORT_M = 150.0


def robust_min_radius(R_series, step_m: float = 10.0,
                      support_m: float = ROBUST_MIN_SUPPORT_M) -> float:
    """Rayon le plus serré *soutenu* d'un segment = min d'une médiane glissante.

    Remplace R_min comme base de classement : R_min est gouverné par le PIRE
    artefact ponctuel de l'estimateur (→ faux-F vérifié), alors que ce
    robust-min exige que la contrainte soit soutenue sur ~support_m pour
    compter — ce qui est aussi la règle physique d'une limite de vitesse
    (pour une vraie courbe, pas un défaut de relevé).
    """
    import numpy as np
    from scipy.ndimage import median_filter
    R = np.asarray(R_series, dtype=float)
    if R.size == 0:
        return float("inf")
    w = max(3, int(round(support_m / step_m)))
    if w % 2 == 0:
        w += 1
    if R.size <= w:
        return float(np.median(R))  # segment < fenêtre : médiane globale
    return float(median_filter(R, size=w, mode="nearest").min())


# --------------------------------------------- degré de courbure (norme NA)

# Standard ferroviaire nord-américain (AREMA) : la netteté d'une courbe se
# mesure en DEGRÉ DE COURBURE — l'angle au centre sous-tendu par une CORDE de
# 100 pieds (déf. « corde », celle du rail NA ; la déf. « arc » est routière).
#   R[pi] = 50 / sin(Dc/2)   ⇔   Dc[°] = 2·asin(50 / R[pi])
# En mètres (1 pi = 0,3048 m, demi-corde = 50 pi = 15,24 m) :
#   Dc[°] = 2·asin(15,24 / R[m])
# Relation INVERSE du rayon : grand rayon (courbe ample, rapide) → petit Dc ;
# courbe serrée (lente) → grand Dc. Vérif : R = 1746 m → Dc = 1,00°.
HALF_CHORD_FT = 50.0               # demi-corde de la corde de 100 pieds
FEET_PER_M = 1.0 / 0.3048          # 3,28084 pi/m
HALF_CHORD_M = HALF_CHORD_FT / FEET_PER_M   # 15,24 m


def degre_courbure(radius_m: float | None) -> float | None:
    """Degré de courbure (°, déf. corde de 100 pi — standard ferroviaire NA).

    Argument : rayon en mètres. Retourne :
      - None si le rayon est None/non numérique (préserve les trous d'affichage) ;
      - 0.0 pour un rayon infini, ≤ 0 ou non fini (tangente = courbure nulle) ;
      - sinon 2·asin(15,24 / R) en degrés.
    Un rayon < 15,24 m (jamais atteint sur voie réelle, plancher physique 100 m)
    sature à 180°.
    """
    if radius_m is None:
        return None
    try:
        R = float(radius_m)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(R) or R <= 0:
        return 0.0
    ratio = HALF_CHORD_M / R
    if ratio >= 1.0:
        return 180.0
    return 2.0 * math.degrees(math.asin(ratio))


def fmt_dc(radius_m: float | None, dec: int = 2, suffix: str = "°") -> str:
    """Degré de courbure formaté FR ('4,79°'), '—' si non défini.

    Décimale française (virgule). `suffix` permet de retirer le ° si besoin.
    """
    dc = degre_courbure(radius_m)
    if dc is None:
        return "—"
    return f"{dc:.{dec}f}".replace(".", ",") + suffix


# ----------------------------------------- conversions d'unités (conventions NA)

# Le collaborateur ferroviaire raisonne en conventions nord-américaines : vitesses
# en mph, dévers et insuffisance de dévers en pouces, jalons en milles. On expose
# systématiquement les DEUX unités dans les livrables (colonnes séparées) pour qu'il
# n'ait jamais à convertir à la main et que rien ne se perde à la traduction.
MPH_PER_KMH = 0.621371          # 1 km/h = 0,621371 mph
MM_PER_INCH = 25.4              # 1 pouce = 25,4 mm
M_PER_MILE = 1609.344          # 1 mille = 1609,344 m

# Facteur géo/commercial (vitesse commerciale ≈ plafond géométrique × ce facteur).
# Borne médiane de la fourchette 0,70–0,80 mesurée sur HSR réels (Annexe E).
COMMERCIAL_FACTOR = 0.75


def kmh_to_mph(v_kmh: float | None) -> float | None:
    """km/h → mph. None reste None."""
    return None if v_kmh is None else v_kmh * MPH_PER_KMH


def mph_to_kmh(v_mph: float | None) -> float | None:
    """mph → km/h. None reste None."""
    return None if v_mph is None else v_mph / MPH_PER_KMH


def mm_to_inch(x_mm: float | None) -> float | None:
    """mm → pouces. None reste None."""
    return None if x_mm is None else x_mm / MM_PER_INCH


def inch_to_mm(x_in: float | None) -> float | None:
    """pouces → mm. None reste None."""
    return None if x_in is None else x_in * MM_PER_INCH


def m_to_mile(x_m: float | None) -> float | None:
    """mètres → milles. None reste None."""
    return None if x_m is None else x_m / M_PER_MILE


def km_to_mile(x_km: float | None) -> float | None:
    """km → milles. None reste None."""
    return None if x_km is None else x_km * 1000.0 / M_PER_MILE


def fmt_num(x: float | None, dec: int = 1, suffix: str = "") -> str:
    """Nombre formaté FR (virgule décimale), '—' si None. Ex : fmt_num(124.27)='124,3'."""
    if x is None:
        return "—"
    return f"{x:.{dec}f}".replace(".", ",") + suffix


# ------------------------------------------------------------------ i18n

TRANSLATIONS = {
    "corridor": {"fr": "Corridor TGV Canada", "en": "Canada HSR Corridor"},
    "via_existing": {"fr": "Alignement VIA existant", "en": "Existing VIA alignment"},
    "stations": {"fr": "Gares VIA", "en": "VIA stations"},
    "scenario": {"fr": "Scénario", "en": "Scenario"},
    "speed_class": {"fr": "Classe de vitesse", "en": "Speed class"},
    "vmax": {"fr": "Vitesse max", "en": "Max speed"},
    "radius_min": {"fr": "Rayon min", "en": "Min radius"},
    "radius_mean": {"fr": "Rayon moyen", "en": "Mean radius"},
    "length": {"fr": "Longueur", "en": "Length"},
    "troncon": {"fr": "Tronçon", "en": "Section"},
    "station_upstream": {"fr": "Gare amont", "en": "Upstream station"},
    "station_downstream": {"fr": "Gare aval", "en": "Downstream station"},
    "bottleneck": {"fr": "Goulot d'étranglement", "en": "Bottleneck"},
    "source": {"fr": "Source", "en": "Source"},
}


def t(key: str, lang: str = "fr") -> str:
    return TRANSLATIONS.get(key, {}).get(lang, key)


def bilingual(key: str) -> str:
    """Retourne 'FR / EN' pour les popups bilingues."""
    fr = TRANSLATIONS.get(key, {}).get("fr", key)
    en = TRANSLATIONS.get(key, {}).get("en", key)
    return f"{fr} / {en}"


# ------------------------------------------------------------------ setup

def ensure_dirs() -> None:
    for d in (INTERMEDIATES, DELIVERABLES):
        d.mkdir(parents=True, exist_ok=True)

"""Schéma multi-alignement.

Un *alignement* = une polyligne ferroviaire nommée avec attributs uniformes,
prête à être analysée et comparée. Phase 1 ne produit qu'un alignement
(`via_existing`), mais la structure est conçue pour ingérer d'autres alignements
plus tard (ALTO greenfield, hybrides VIA+ALTO).
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Alignment:
    id: str                     # "via_existing", "alto_proposed", "hybrid_v1", ...
    label_fr: str
    label_en: str
    source: str                 # origine des données géo
    color_primary: str          # couleur de base pour les rendus
    description_fr: str = ""
    description_en: str = ""


ALIGNMENTS: dict[str, Alignment] = {
    "via_existing": Alignment(
        id="via_existing",
        label_fr="Tracé VIA existant",
        label_en="Existing VIA route",
        source="VIA Rail GTFS (corridor sémantique) + OSM PBF QC+ON (géométrie haute-résolution)",
        color_primary="#0072B2",
        description_fr=(
            "Tracé ferroviaire existant utilisé par VIA Rail le long du corridor "
            "Québec–Montréal–Ottawa–Toronto. Géométrie reconstituée par map-matching "
            "topologique des données GTFS sur le graphe OSM des rails."
        ),
        description_en=(
            "Existing railway alignment used by VIA Rail along the Québec–Montréal–"
            "Ottawa–Toronto corridor. Geometry reconstructed by topological "
            "map-matching of GTFS data onto the OSM railway graph."
        ),
    ),
    # Slots préparés pour Phase ultérieure :
    # "alto_proposed": Alignment(id="alto_proposed", label_fr="Tracé ALTO proposé", ...),
    # "hybrid_v1":     Alignment(id="hybrid_v1",     label_fr="Hybride VIA + ALTO v1", ...),
}


@dataclass
class CorridorSegment:
    """Sous-tronçon administratif du corridor (entre deux villes-pivot)."""
    id: str            # "QC-MTL", "MTL-Ott", "Ott-TO", "MTL-TO"
    label_fr: str
    label_en: str
    via_route_id: str  # route_id GTFS de référence pour ce tronçon


CORRIDOR_SEGMENTS: dict[str, CorridorSegment] = {
    # Note : les noms reflètent le SENS du shape GTFS (origine→destination).
    # km_along_segment = 0 au 1er endpoint, croît vers le 2nd.
    "MTL-QC":  CorridorSegment("MTL-QC",  "Montréal → Québec",  "Montréal → Québec City",  "628-226"),
    "MTL-Ott": CorridorSegment("MTL-Ott", "Montréal → Ottawa",  "Montréal → Ottawa",       "617-226"),
    "Ott-TO":  CorridorSegment("Ott-TO",  "Ottawa → Toronto",   "Ottawa → Toronto",        "617-119"),
    "MTL-TO":  CorridorSegment("MTL-TO",  "Montréal → Toronto", "Montréal → Toronto",      "226-119"),
}

# Gares-pivot des tronçons : (stop_id origine km=0, stop_id destination km=max)
SEGMENT_ENDPOINTS: dict[str, tuple[str, str]] = {
    "MTL-QC":  ("226", "628"),
    "MTL-Ott": ("226", "617"),
    "Ott-TO":  ("617", "119"),
    "MTL-TO":  ("226", "119"),
}

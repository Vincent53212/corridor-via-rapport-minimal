"""Étape 33 — Sensibilité : les courbes des sections à doubler sont rectifiées.

Idée (Vincent, 2026-08-17) : reconstruire une plateforme pour y poser une
seconde voie est le seul moment où rouvrir un rayon ne coûte presque rien de
plus. La sensibilité chiffre donc le scénario recommandé OÙ les courbes situées
sur le programme de doublement sont rectifiées.

Définition d'un segment « rectifiable » (déclarée, pas de recalcul géométrique) :
  (i)  au moins RECOUVREMENT_MIN (70 %) de sa longueur recoupe une section de
       voie SIMPLE stricte du programme de doublement (segments_voies.geojson :
       etat == 1, usage == main, hors abords de gare et hors évitements — la
       définition « à doubler » de l'étape 14), même tronçon, axe km commun ;
  (ii) son plafond géométrique S2 est < 177 km/h (sinon rien à rectifier au
       plafond retenu).
Sur ces segments, vmax_S2 est porté à 177 (rectification au plafond retenu,
PAS à l'infini). vmax_S1 et vmax_S3 restent INTACTS : le moteur 21 lit vmax_S1
pour la fenêtre d'Ottawa, et la sensibilité ne doit isoler qu'un seul effet.

Sortie : intermediaires/segments_rectifies.geojson, puis relancer :
    SEGMENTS_OVERRIDE=intermediaires/segments_rectifies.geojson python scripts/21_tbase_bande.py
→ livrables/tbase_par_bande_rectifies.csv (jamais d'écrasement de la référence).
"""
from __future__ import annotations
import json

from utils import INTERMEDIATES, SEGMENTS_PUBLIES_GEOJSON

RECOUVREMENT_MIN = 0.70
PLAFOND = 177.0
# Périmètre du rapport : les quatre trajets du cœur. Le sud-ouest ontarien a
# aussi de la voie simple, mais il est hors des tables publiées ; l'inclure
# gonflerait le kilométrage annoncé de la sensibilité (audit 2026-08-17).
TRONCONS_COEUR = {"MTL-QC", "MTL-Ott", "Ott-TO", "MTL-TO"}

# Entrée = segments PUBLIÉS (correction des courbes courtes de l'étape 34
# incluse) : la rectification au doublement part de la géométrie publiée.
# ORDRE : 34 avant 33.
SEGMENTS = SEGMENTS_PUBLIES_GEOJSON
VOIES = INTERMEDIATES / "segments_voies.geojson"
OUT = INTERMEDIATES / "segments_rectifies.geojson"


def main() -> None:
    gj = json.loads(SEGMENTS.read_text(encoding="utf-8"))
    voies = json.loads(VOIES.read_text(encoding="utf-8"))

    # intervalles km de voie simple stricte (la définition « à doubler » de 14)
    simple: dict[str, list[tuple[float, float]]] = {}
    for f in voies["features"]:
        p = f["properties"]
        if (p["troncon_id"] in TRONCONS_COEUR
                and p["etat"] == 1 and p["usage"] == "main"
                and not p["pres_gare"] and not p["evitement"]):
            simple.setdefault(p["troncon_id"], []).append(
                (p["km_debut"], p["km_fin"]))

    n_rect, km_rect = 0, 0.0
    for f in gj["features"]:
        p = f["properties"]
        iv = simple.get(p["troncon_id"], [])
        a, b = p["km_debut"], p["km_fin"]
        if b <= a:
            continue
        recouvre = sum(max(0.0, min(b, hi) - max(a, lo)) for lo, hi in iv)
        if (recouvre / (b - a) >= RECOUVREMENT_MIN
                and p["vmax_S2_kmh"] < PLAFOND):
            p["vmax_S2_kmh"] = PLAFOND
            p["rectifie"] = True
            n_rect += 1
            km_rect += p["longueur_m"] / 1000.0

    OUT.write_text(json.dumps(gj, ensure_ascii=False), encoding="utf-8")
    print(f"Segments rectifiés (recouvrement ≥ {RECOUVREMENT_MIN:.0%} de voie "
          f"simple à doubler, vmax_S2 < {PLAFOND:.0f}) : {n_rect} segments, "
          f"{km_rect:.1f} km → vmax_S2 = {PLAFOND:.0f}")
    print(f"Écrit {OUT.name}. Relancer ensuite :\n"
          f"  SEGMENTS_OVERRIDE={OUT} python scripts/21_tbase_bande.py")


if __name__ == "__main__":
    main()

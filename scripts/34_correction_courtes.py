"""Étape 34 — Correction empirique des courbes courtes → segments PUBLIÉS.

L'estimateur de courbure ajuste un cercle sur une fenêtre glissante de 900 m.
Une courbe dont le corps est plus court que la fenêtre est lue plus AMPLE
qu'elle n'est : l'audit de terrain de La Tuque (2026-08-15) a mesuré des rayons
publiés valant environ deux fois le rayon du corps sur des courbes de 310 et
370 m. Le biais est à sens unique (la fenêtre lit toujours plus ample) et
optimiste (il fait annoncer une voie plus droite qu'elle n'est).

Décision client (remodelage du 24 août) : les chiffres publiés incluent une
correction forfaitaire, volontairement conservatrice :

    R' = FACTEUR_CORRECTION_R × R_classif   (0,5 sur le rayon, soit −30 % sur
                                             la vitesse, v = k·√R)

appliquée à tout segment qui remplit les DEUX conditions :
  (i)  longueur_m < FENETRE_BIAIS_M (900 m) : plus court que la fenêtre ;
  (ii) limité par une courbe : R_classif fini et inférieur au rayon qui
       donnerait 250 km/h au moteur pendulaire (≈ 2 685 m) — un bout droit
       court n'est pas une courbe sous-estimée, on ne le corrige pas.

vmax et classe sont recalculées pour les trois scénarios internes via
published_vmax_class (même patron que l'étape 05). Les rayons descriptifs
(R_min, R_p10…) restent les valeurs mesurées ; seule la ligne de classification
change, et le segment porte facteur_applique = true.

Entrée  : intermediaires/segments.geojson          (brut, sortie du 05 — intact)
Sortie  : intermediaires/segments_publies.geojson  (lu par 06/07/11/20/21/33)

ORDRE : lancer 34 AVANT 33 (la rectification au doublement part des segments
publiés). Le 31 continue de mesurer le biais sur le brut : ne pas le rebrancher.

    python scripts/34_correction_courtes.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scenarios import (FACTEUR_CORRECTION_R, FENETRE_BIAIS_M,  # noqa: E402
                       SCENARIOS, published_vmax_class)
from utils import SEGMENTS_GEOJSON, SEGMENTS_PUBLIES_GEOJSON  # noqa: E402

# Seuil « limité par une courbe » : rayon donnant 250 km/h au moteur pendulaire.
R_SEUIL_COURBE_M = SCENARIOS["S2"].r_for_vmax(250.0)


def main() -> None:
    gj = json.loads(SEGMENTS_GEOJSON.read_text(encoding="utf-8"))
    n_corr, km_corr = 0, 0.0
    for f in gj["features"]:
        p = f["properties"]
        R = p.get("R_classif_m")
        est_courbe = (R is not None and math.isfinite(R)
                      and 0 < R < R_SEUIL_COURBE_M)
        if p["longueur_m"] < FENETRE_BIAIS_M and est_courbe:
            R_corr = FACTEUR_CORRECTION_R * R
            for sid in ("S1", "S2", "S3"):
                c, v = published_vmax_class(SCENARIOS[sid], R_corr, R_corr)
                p[f"vmax_{sid}_kmh"] = v
                p[f"classe_{sid}"] = c
            p["R_classif_m"] = round(R_corr, 0)
            p["facteur_applique"] = True
            n_corr += 1
            km_corr += p["longueur_m"] / 1000.0
        else:
            p["facteur_applique"] = False

    gj.setdefault("meta", {})["correction_courtes"] = {
        "facteur_R": FACTEUR_CORRECTION_R,
        "fenetre_m": FENETRE_BIAIS_M,
        "seuil_courbe_R_m": round(R_SEUIL_COURBE_M, 0),
        "source": "audit de terrain La Tuque 2026-08-15 (rayons publiés ~2× le corps sur courbes < 900 m)",
        "n_segments_corriges": n_corr,
        "km_corriges": round(km_corr, 1),
    }
    SEGMENTS_PUBLIES_GEOJSON.write_text(
        json.dumps(gj, ensure_ascii=False), encoding="utf-8")
    print(f"=== Étape 34 — Correction des courbes courtes (R' = "
          f"{FACTEUR_CORRECTION_R} × R sur segments < {FENETRE_BIAIS_M:.0f} m "
          f"courbes, R < {R_SEUIL_COURBE_M:.0f} m) ===")
    print(f"Corrigés : {n_corr} segments, {km_corr:.1f} km "
          f"(sur {len(gj['features'])} segments)")
    print(f"Écrit {SEGMENTS_PUBLIES_GEOJSON.name}. "
          f"Enchaîner : 33 (rectification au doublement) puis la chaîne 21+.")


if __name__ == "__main__":
    main()

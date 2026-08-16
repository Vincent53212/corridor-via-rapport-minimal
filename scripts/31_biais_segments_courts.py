#!/usr/bin/env python3
"""Étape 31 — Mesure du biais de fenêtre sur les segments courts du corridor.

CE QUE ÇA MESURE, ET POURQUOI. L'estimateur ajuste un cercle sur une fenêtre
glissante de 900 m. Sur un segment plus court que sa fenêtre, il mélange la
courbe et ses tangentes d'approche et rend un rayon plus AMPLE que la courbe :
l'audit de méthode l'a montré sur des courbes de 310 et 370 m, où le degré
publié valait moins de la moitié du degré réel. Le biais est à sens unique, donc
il ne se compense pas en agrégeant, et il est optimiste : il fait annoncer une
voie plus droite qu'elle n'est.

Ce script chiffre ce biais SUR LE CORRIDOR, au lieu de le supposer. Pour chaque
segment publié, il refait la mesure de la façon dont un relevé de terrain la
ferait : il localise le corps de la courbe avec un estimateur fin (fenêtre de
300 m), y ajuste UN cercle, et compare ce rayon à celui que le rapport publie.

Le rapport de ces deux rayons est le FACTEUR de biais. Sa distribution en
fonction de la longueur de segment est la sortie principale : elle dit à partir
de quelle longueur la fenêtre de 900 m cesse de fausser la mesure.

CE QUE ÇA N'EST PAS. L'estimateur fin de 300 m n'est pas publiable : sur le bruit
d'OpenStreetMap (5 à 10 m), une fenêtre de 300 m ne dépasse le bruit qu'au-dessus
d'environ 1 000 m de rayon. Il sert ici de RÉFÉRENCE LOCALE sur des courbes
serrées, où il est légitime, et jamais de remplaçant. C'est le même usage que
dans l'audit de méthode.

Sorties : livrables/biais_segments_courts.csv (un segment par ligne) et
intermediaires/segments_corriges.geojson (les mêmes segments avec la vitesse
recalculée sur le rayon de corps là où celui-ci est mesurable), que l'étape 21
peut consommer par la variable d'environnement SEGMENTS_OVERRIDE pour donner
l'effet sur les temps de parcours.

    python scripts/31_biais_segments_courts.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scenarios import SCENARIOS, published_vmax_class  # noqa: E402
from utils import (CURVATURE_PARQUET, DELIVERABLES, INTERMEDIATES,  # noqa: E402
                   SEGMENTS_GEOJSON, degre_courbure)

_spec = importlib.util.spec_from_file_location(
    "curv04", Path(__file__).resolve().parent / "04_compute_curvature.py")
curv04 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(curv04)

STEP_M = curv04.RESAMPLE_STEP_M          # 10 m
FENETRE_FINE_M = 300.0                   # référence locale, jamais publiée
MARGE_M = 300.0                          # de quoi laisser la fenêtre fine s'établir
BODY_FRAC = 0.30                         # même définition de corps que l'audit
MIN_PTS_CORPS = 5
CORE = ["MTL-QC", "MTL-Ott", "Ott-TO", "MTL-TO"]

SORTIE_CSV = DELIVERABLES / "biais_segments_courts.csv"
SORTIE_GEO = INTERMEDIATES / "segments_corriges.geojson"


def mesurer(sub: pd.DataFrame, km0: float, km1: float) -> tuple[float, float]:
    """(rayon du corps, longueur du corps en m) pour un segment.

    `sub` porte le segment ET sa marge : la fenêtre fine a besoin de matière de
    part et d'autre pour ne pas s'appuyer sur un bord."""
    xy = np.column_stack([sub["x_utm"].to_numpy(), sub["y_utm"].to_numpy()])
    if len(xy) < MIN_PTS_CORPS + 4:
        return float("nan"), 0.0
    R_fin = curv04.postfilter_R(
        curv04.curvature_lsq_segmented(xy, STEP_M, FENETRE_FINE_M))
    dedans = ((sub["km_along_segment"].to_numpy() >= km0)
              & (sub["km_along_segment"].to_numpy() <= km1))
    if dedans.sum() < MIN_PTS_CORPS:
        return float("nan"), 0.0
    kappa = np.where(dedans, 1.0 / np.maximum(R_fin, 1.0), 0.0)
    if kappa.max() <= 0:
        return float("nan"), 0.0
    idx = np.where(kappa >= kappa.max() * (1.0 - BODY_FRAC))[0]
    a, b = int(idx.min()), int(idx.max())
    if b - a + 1 < MIN_PTS_CORPS:
        return float("nan"), 0.0
    return curv04.lsq_circle_radius(xy[a:b + 1]), (b - a) * STEP_M


def main() -> None:
    df = pq.read_table(CURVATURE_PARQUET).to_pandas()
    gj = json.loads(SEGMENTS_GEOJSON.read_text(encoding="utf-8"))
    feats = [f for f in gj["features"]
             if f["properties"].get("troncon_id") in CORE]
    print(f"=== Étape 31 — Biais de fenêtre sur {len(feats)} segments du cœur ===")

    par_tronc = {t: s.sort_values("km_along_segment").reset_index(drop=True)
                 for t, s in df.groupby("troncon_id")}

    lignes = []
    for n, f in enumerate(feats, 1):
        p = f["properties"]
        t = p["troncon_id"]
        s = par_tronc[t]
        km0, km1 = p["km_debut"], p["km_fin"]
        m = ((s["km_along_segment"] >= km0 - MARGE_M / 1000)
             & (s["km_along_segment"] <= km1 + MARGE_M / 1000))
        R_corps, L_corps = mesurer(s[m], km0, km1)
        R_pub = p["R_classif_m"]
        ligne = {
            "troncon": t, "seg_idx": p["seg_idx"],
            "km_debut": km0, "km_fin": km1, "longueur_m": p["longueur_m"],
            "R_publie_m": R_pub, "R_corps_m": R_corps, "corps_m": L_corps,
            "facteur": (R_pub / R_corps) if (R_corps and np.isfinite(R_corps)
                                             and R_corps > 0 and R_pub) else np.nan,
            "Dc_publie_deg": degre_courbure(R_pub) if R_pub else np.nan,
            "Dc_corps_deg": degre_courbure(R_corps) if np.isfinite(R_corps) else np.nan,
        }
        for sid in ("S1", "S2", "S3"):
            ligne[f"vmax_{sid}_publie"] = p[f"vmax_{sid}_kmh"]
            if np.isfinite(R_corps) and R_corps > 0:
                _, v = published_vmax_class(SCENARIOS[sid], R_corps, R_corps)
                ligne[f"vmax_{sid}_corrige"] = v
            else:
                ligne[f"vmax_{sid}_corrige"] = p[f"vmax_{sid}_kmh"]
        lignes.append(ligne)
        if n % 200 == 0:
            print(f"  {n}/{len(feats)}…", flush=True)

    b = pd.DataFrame(lignes)
    b.to_csv(SORTIE_CSV, sep=";", index=False, encoding="utf-8-sig")

    # --- distribution du facteur par longueur de segment ------------------
    print("\n=== FACTEUR DE BIAIS (rayon publié / rayon du corps) ===")
    print(f"{'longueur':>14} {'n':>5} {'km':>8} {'médiane':>9} {'q75':>7} {'q90':>7}")
    bandes = [(0, 300), (300, 450), (450, 600), (600, 900), (900, 1e9)]
    for lo, hi in bandes:
        sel = b[(b.longueur_m >= lo) & (b.longueur_m < hi) & b.facteur.notna()]
        if not len(sel):
            continue
        lib = f"{lo}-{hi:.0f} m" if hi < 1e9 else f"{lo} m et plus"
        print(f"{lib:>14} {len(sel):>5} {sel.longueur_m.sum()/1000:>7.1f} "
              f"{sel.facteur.median():>9.2f} {sel.facteur.quantile(.75):>7.2f} "
              f"{sel.facteur.quantile(.90):>7.2f}")

    # --- où la correction s'applique --------------------------------------
    #
    # PAS PARTOUT, et c'est le point délicat de cette étape. Le biais démontré
    # est celui d'une fenêtre PLUS LONGUE que la courbe : il ne concerne que les
    # segments plus courts que la fenêtre d'ajustement. Sur les segments longs,
    # la valeur publiée est déjà bonne, et lui substituer la mesure de
    # l'estimateur fin ne ferait qu'importer le bruit de celui-ci. Le premier
    # jet corrigeait tout : il rendait le résidu S1 plus FAIBLE de 35 km, ce qui
    # n'est pas un effet du biais mais un artefact de la référence.
    #
    # Deuxième restriction : sur un segment court, le biais de fenêtre est à
    # SENS UNIQUE, la fenêtre lit toujours plus ample. Un facteur inférieur à 1
    # n'est donc pas un biais de fenêtre mais du bruit de la référence. On
    # publie les deux lectures, qui bornent l'effet :
    #   « adverse » ne retient que les écarts défavorables (facteur > 1) et
    #   majore l'effet ; « neutre » retient les deux sens et le minore.
    court = b.longueur_m < curv04.FIT_WINDOW_M
    adverse = court & (b.facteur > 1.0) & b.R_corps_m.notna()
    neutre = court & b.R_corps_m.notna()
    print(f"\nSegments concernés : {court.sum()} plus courts que la fenêtre de "
          f"{curv04.FIT_WINDOW_M:.0f} m ({b.longueur_m[court].sum()/1000:.0f} km), "
          f"dont {adverse.sum()} au facteur > 1")

    print("\n=== EFFET SUR LE RÉSIDU SOUS 200 km/h (cœur) ===")
    print(f"{'':>4} {'publié':>9} {'neutre':>9} {'adverse':>9}")
    for sid in ("S1", "S2", "S3"):
        pub = b[f"vmax_{sid}_publie"]
        av = b.loc[pub < 200, "longueur_m"].sum() / 1000
        out = [av]
        for masque in (neutre, adverse):
            v = pub.copy()
            v[masque] = b.loc[masque, f"vmax_{sid}_corrige"]
            out.append(b.loc[v < 200, "longueur_m"].sum() / 1000)
        print(f"  {sid} {out[0]:>8.0f} km {out[1]:>7.0f} km {out[2]:>7.0f} km")

    # --- geojson corrigé, pour l'étape 21 ---------------------------------
    # Le geojson porte la lecture ADVERSE : c'est celle dont on veut connaître
    # l'effet sur les temps, puisqu'elle borne le risque du côté défavorable.
    a_corriger = {(r.troncon, int(r.seg_idx)): r
                  for _, r in b[adverse].iterrows()}
    sortie = {"type": "FeatureCollection",
              "meta": {**gj.get("meta", {}),
                       "correction": "rayon de corps, lecture adverse, sur les "
                       "segments plus courts que la fenêtre (étape 31)"},
              "features": []}
    n_corr = 0
    for f in gj["features"]:
        g = json.loads(json.dumps(f))
        p = g["properties"]
        if p.get("troncon_id") in CORE:
            r = a_corriger.get((p["troncon_id"], p["seg_idx"]))
            if r is not None:
                for sid in ("S1", "S2", "S3"):
                    p[f"vmax_{sid}_kmh"] = float(r[f"vmax_{sid}_corrige"])
                    c, _ = published_vmax_class(SCENARIOS[sid],
                                                r["R_corps_m"], r["R_corps_m"])
                    p[f"classe_{sid}"] = c
                p["R_classif_m"] = float(r["R_corps_m"])
                n_corr += 1
        sortie["features"].append(g)
    SORTIE_GEO.write_text(json.dumps(sortie, ensure_ascii=False), encoding="utf-8")
    print(f"\nÉcrit {SORTIE_CSV.name} ({len(b)} segments) et "
          f"{SORTIE_GEO.name} ({n_corr} segments corrigés)")
    print("Pour l'effet sur les temps : "
          "SEGMENTS_OVERRIDE=intermediaires/segments_corriges.geojson "
          "python scripts/21_tbase_bande.py")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Étape 11 — « Vitesse cible → km de tracé à rectifier ».

Le livrable décisionnel : on fixe une ambition de vitesse, on sort combien de
km de voie devraient être rectifiés (et où) pour l'atteindre, par scénario.

DEUX volets, de fiabilité TRÈS différente — affichés comme tels :

  #1 SOLIDE — cible de POINTE (vitesse géométrique).
     Pour une vitesse-cible V et un scénario, un segment est « à rectifier »
     ssi son plafond géométrique publié (vmax_{scénario}, déjà borné 360 et
     cohérent-classe) < V. C'est un simple balayage de seuil sur des données
     déjà validées : AUCUNE hypothèse nouvelle. Sortie : km + sites contigus
     + rayon-cible (de combien la pire courbe doit s'ouvrir).

  #2 INDICATIF — cible de TEMPS / vitesse MOYENNE.
     Convertit une vitesse moyenne-cible en pointe requise via le rapport
     moyenne/pointe **mesuré sur des HSR réels = 0,70–0,80** (Annexe E,
     sourcé), scénario modernisé S3. Donne une ENVELOPPE [bas, haut], jamais
     un chiffre ferme. Accél/décél/arrêts non modélisés finement → indicatif.

Entrée : intermediaires/segments.geojson
Sorties : livrables/cible_km_a_rectifier.csv (#1 agrégé)
          livrables/cible_sites_a_rectifier.csv (#1 détail par site)
          + résumé console (#1 matrice, #2 enveloppe)
"""
from __future__ import annotations
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scenarios import SCENARIOS, VMAX_PHYSICAL_CEILING_KMH
from utils import (SEGMENTS_GEOJSON, DELIVERABLES, degre_courbure,
                   kmh_to_mph, km_to_mile)

TARGET_PEAKS = [160, 200, 250, 300]          # #1 : vitesses de pointe cibles
TARGET_AVGS = [150, 180, 200]                # #2 : vitesses moyennes cibles
RATIO_BAND = (0.70, 0.80)                    # Annexe E (HSR réels sourcés)
TRONCONS = ["MTL-QC", "MTL-Ott", "Ott-TO", "MTL-TO"]


def load_segments():
    gj = json.loads(SEGMENTS_GEOJSON.read_text(encoding="utf-8"))
    by_tr = defaultdict(list)
    for f in gj["features"]:
        by_tr[f["properties"]["troncon_id"]].append(f["properties"])
    for k in by_tr:
        by_tr[k].sort(key=lambda p: p["km_debut"])
    return by_tr


def contiguous_sites(segs: list[dict]) -> list[list[dict]]:
    """Runs maximaux de segments consécutifs marqués 'à rectifier'."""
    sites, cur = [], []
    for p in segs:
        if p.get("_rect"):
            cur.append(p)
        elif cur:
            sites.append(cur); cur = []
    if cur:
        sites.append(cur)
    return sites


def main() -> None:
    by_tr = load_segments()

    # ---------- #1 SOLIDE : cible de pointe → km à rectifier ----------
    agg_rows, site_rows = [], []
    print("=== #1 SOLIDE — Vitesse de POINTE cible → km à rectifier "
          "(par scénario) ===")
    print("  (un segment compte si son plafond géométrique publié < cible ;"
          " données déjà validées, aucune hypothèse nouvelle)\n")
    for sid in ("S1", "S2", "S3"):
        sc = SCENARIOS[sid]
        print(f"  ── Scénario {sid} ({sc.name_fr}) ──")
        print(f"  {'cible':>6} | " + " | ".join(f"{t:>8}" for t in TRONCONS)
              + " |   TOTAL")
        for V in TARGET_PEAKS:
            R_target = sc.r_for_vmax(V)
            line = []
            tot_km = tot_len = 0.0
            for tr in TRONCONS:
                segs = by_tr.get(tr, [])
                for p in segs:
                    p["_rect"] = p[f"vmax_{sid}_kmh"] < V - 1e-6
                km_r = sum(p["longueur_m"] for p in segs if p["_rect"]) / 1000.0
                len_tr = sum(p["longueur_m"] for p in segs) / 1000.0
                tot_km += km_r; tot_len += len_tr
                line.append(f"{km_r:6.0f}km")
                sites = contiguous_sites(segs)
                dc_cible = degre_courbure(R_target)
                agg_rows.append({
                    "scenario": sid, "vitesse_cible_kmh": V,
                    "vitesse_cible_mph": round(kmh_to_mph(V), 1),
                    "troncon": tr,
                    "km_a_rectifier": round(km_r, 1),
                    "mille_a_rectifier": round(km_to_mile(km_r), 1),
                    "pct_troncon": round(100 * km_r / len_tr, 1) if len_tr else 0,
                    "n_sites": len(sites),
                    "degre_courbure_cible_max_deg": round(dc_cible, 2) if dc_cible is not None else "",
                    "rayon_cible_m": round(R_target),
                })
                for s in sites:
                    rmins = [x["R_classif_m"] for x in s
                             if x.get("R_classif_m") is not None]
                    r_act = min(rmins) if rmins else None
                    dc_act = degre_courbure(r_act) if r_act is not None else None
                    site_rows.append({
                        "scenario": sid, "vitesse_cible_kmh": V,
                        "vitesse_cible_mph": round(kmh_to_mph(V), 1),
                        "troncon": tr,
                        "km_debut": round(s[0]["km_debut"], 2),
                        "km_fin": round(s[-1]["km_fin"], 2),
                        "mille_debut": round(km_to_mile(s[0]["km_debut"]), 2),
                        "mille_fin": round(km_to_mile(s[-1]["km_fin"]), 2),
                        "longueur_km": round(
                            sum(x["longueur_m"] for x in s) / 1000.0, 2),
                        "longueur_mille": round(
                            km_to_mile(sum(x["longueur_m"] for x in s) / 1000.0), 2),
                        "degre_courbure_actuel_max_deg": round(dc_act, 2) if dc_act is not None else "",
                        "R_actuel_min_m": round(r_act) if r_act is not None else "",
                        "degre_courbure_cible_max_deg": round(dc_cible, 2) if dc_cible is not None else "",
                        "rayon_cible_m": round(R_target),
                        "gare_amont": s[0].get("gare_amont", ""),
                        "gare_aval": s[-1].get("gare_aval", ""),
                    })
            print(f"  {V:>4}km | " + " | ".join(f"{c:>8}" for c in line)
                  + f" | {tot_km:6.0f}km ({100*tot_km/tot_len:4.1f}%)"
                  f"  Dc≤{degre_courbure(R_target):.2f}° (R≥{R_target:,.0f}m)")
        print()
    # garde-fou de cohérence avec le récit. NB (2026-08-06, nomenclature rapport
    # minimal) : S3 = pendulaire 127/270 (k=5,75). Attendu ≈ 187 km (estimation du
    # plan de match v3 ; l'ancien S3 127/152, devenu S2, donnait ≈ 271 km / 18,9 %).
    s3_200 = sum(r["km_a_rectifier"] for r in agg_rows
                 if r["scenario"] == "S3" and r["vitesse_cible_kmh"] == 200)
    print(f"  Contrôle cohérence : S3 (127/270) cible 200 km/h → {s3_200:.0f} km "
          f"(attendu ≈ 187 km ; ancien S3 127/152, devenu S2 : ≈ 271 km). "
          f"{'OK ✓' if 165 <= s3_200 <= 210 else 'ÉCART À VÉRIFIER ✗'}\n")

    # ---------- #2 INDICATIF : vitesse moyenne cible → enveloppe ----------
    print("=== #2 INDICATIF — Vitesse MOYENNE cible → km à rectifier "
          "(enveloppe, scénario modernisé S3) ===")
    print("  Conversion moyenne→pointe via rapport HSR réel "
          f"{RATIO_BAND[0]:.2f}–{RATIO_BAND[1]:.2f} (Annexe E, sourcé). "
          "ENVELOPPE, pas un chiffre ferme ; accél/décél/arrêts non "
          "modélisés finement.\n")
    sc3 = SCENARIOS["S3"]
    print(f"  {'v_moy':>6} {'pointe requise':>16} {'km à rectifier (S3)':>22}")
    for Vavg in TARGET_AVGS:
        peak_hi = Vavg / RATIO_BAND[0]      # ratio bas → pointe haute
        peak_lo = Vavg / RATIO_BAND[1]      # ratio haut → pointe basse
        kms = []
        for peak in (peak_lo, peak_hi):
            peak_c = min(peak, VMAX_PHYSICAL_CEILING_KMH)
            km = 0.0
            for tr in TRONCONS:
                for p in by_tr.get(tr, []):
                    if p["vmax_S3_kmh"] < peak_c - 1e-6:
                        km += p["longueur_m"] / 1000.0
            kms.append(km)
        print(f"  {Vavg:>4}   {peak_lo:6.0f}–{peak_hi:<6.0f} km/h   "
              f"{min(kms):6.0f} – {max(kms):<6.0f} km   "
              f"(indicatif)")
    print("\n  ⚠ INDICATIF : enveloppe issue d'un rapport empirique HSR, "
          "scénario S3 ; ne remplace pas une étude de marche de train.")

    # ---------- écritures ----------
    a = DELIVERABLES / "cible_km_a_rectifier.csv"
    with open(a, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(agg_rows[0].keys()),
                           delimiter=";")
        w.writeheader(); w.writerows(agg_rows)
    b = DELIVERABLES / "cible_sites_a_rectifier.csv"
    with open(b, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(site_rows[0].keys()),
                           delimiter=";")
        w.writeheader(); w.writerows(site_rows)
    print(f"\nÉcrit {a.name} ({len(agg_rows)} lignes) et {b.name} "
          f"({len(site_rows)} sites).")
    print("NB : #1 ne dépend QUE de la géométrie validée ; #2 est une "
          "enveloppe indicative (rapport Annexe E). Aucun reclassement.")


if __name__ == "__main__":
    main()

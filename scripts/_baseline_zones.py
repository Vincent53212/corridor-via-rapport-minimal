#!/usr/bin/env python3
"""Acceptation de la distribution de courbure sur 3 zones témoins.

Lit le parquet de courbure régénéré (étape 4) et vérifie, par critères
PASS/FAIL explicites, que l'estimateur LSQ recalibré ne sur-corrige PAS
(courbes réelles aplaties → faux droits) ni ne sous-corrige (bruit OSM
résiduel → faux serrés). Écrit _baseline_zones.json et sort 1 si FAIL.

Sémantique des classes (cf. scenarios.py) : A = HSR pleine vitesse (R le
plus grand), F = sévèrement contraint (R le plus petit). « classe ≥ X »
désigne X et toutes les classes plus rapides ; « classe ≤ X » désigne X et
toutes les classes plus lentes.

NB : l'ancienne sémantique « rayon quasi-infini = bon » a été retirée — un
rayon démesuré sur une zone à vraies courbes est désormais un ÉCHEC
(sur-correction), pas un succès.
"""
from __future__ import annotations
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import CURVATURE_PARQUET, INTERMEDIATES, CORRIDOR_GTFS_GEOJSON
from scenarios import SCENARIOS, classify

# Le seuil de déviation vient de l'étape 04 : même grandeur, même valeur, une
# seule définition (le nom de module commence par un chiffre → import par
# spec, comme ailleurs dans le projet).
_spec_c4 = importlib.util.spec_from_file_location(
    "_curv04", Path(__file__).resolve().parent / "04_compute_curvature.py")
_c4 = importlib.util.module_from_spec(_spec_c4)
_spec_c4.loader.exec_module(_c4)
DEFLECTION_MIN_DEG = _c4.DEFLECTION_MIN_DEG


def _station_km(troncon: str, name_contains: str) -> float:
    """km d'une gare (corridor_gtfs.geojson régénéré) pour ancrer une zone.

    On ancre les zones-témoins sur des GARES RÉELLES, pas des km en dur :
    robuste à la convention d'origine km (corrigée pour Ott-TO/MTL-TO) et
    auto-documenté. (Le km GTFS ≈ km matched à <1,5 % — négligeable pour des
    zones de caractère larges de ~250 km.)
    """
    g = json.loads(CORRIDOR_GTFS_GEOJSON.read_text(encoding="utf-8"))
    for f in g["features"]:
        p = f["properties"]
        if (p.get("kind") == "station" and p["troncon_id"] == troncon
                and name_contains.lower() in p["stop_name"].lower()):
            return float(p["km_along_segment"])
    raise SystemExit(
        f"Zone-témoin : gare '{name_contains}' introuvable sur {troncon} "
        f"(ancrage impossible — vérifier corridor_gtfs.geojson).")


def build_zones() -> list:
    """Zones-témoins ancrées sur gares (convention km corrigée).

    type ∈ {'courbe', 'droite'} → critères selon le mode d'échec testé :
      - 'courbe' : zone à courbes réelles connues → garde anti-SUR-correction
        (les courbes doivent survivre, sinon on a aplati la réalité) ;
      - 'droite' : tangente rapide connue → garde anti-SOUS-correction
        (pas de faux-F injectés sur du tangent).
    """
    k_lo = _station_km("MTL-TO", "Dorval")        # exclut le terminus Montréal
    k_hi = _station_km("MTL-TO", "Kingston")      # fin de la sub « droite »
    o_lo = _station_km("Ott-TO", "Ottawa")        # = 0 (Ottawa en tête)
    d_lo = _station_km("MTL-QC", "Drummondville")
    m_lo = _station_km("MTL-QC", "Montréal")      # = 0 (terminus Montréal)
    return [
        # (label, key, type, troncon_id, km_min, km_max, attendu)
        ("Dorval→Kingston (réf rapide, sub Kingston)", "kingston", "droite",
         "MTL-TO", k_lo, k_hi,
         "tangente rapide : ≥D(S1)≥90%, F(S1)≤1.5%, méd. R finis ≥2000"),
        ("Drummondville→+100km (réf rapide rive-nord)", "drummondville", "droite",
         "MTL-QC", d_lo, d_lo + 100.0,
         "tangente rapide (sub Drummondville, VIA 160 limité signalisation)"),
        ("Ottawa centre→~Fallowfield (vraies courbes)", "ottawa", "courbe",
         "Ott-TO", o_lo, o_lo + 15.0,
         "courbes réelles préservées : F+E(S1)≥8%, R_p10≤1700, R_med≤8000"),
        ("Approche terminale Montréal (courbes de gare)", "montreal", "courbe",
         "MTL-QC", m_lo, m_lo + 8.0,
         "courbes terminales sévères préservées (anti-sur-correction renforcé)"),
    ]

# Seuils d'acceptation RE-SPÉCIFIÉS (testent les vrais modes d'échec ; le
# critère R_median∈[1500,25000] a été retiré car il confondait « vraiment
# tangent » et « sur-corrigé » sur du tangent réel post-C4).
G_FRAC_TINY_MAX = 0.01        # global : frac(R<100 m) < 1% (plancher numérique)
# Zone COURBE — anti-SUR-correction (les vraies courbes doivent survivre)
C_FE_MIN = 8.0                # % classe F+E en S1 ≥ 8
C_RP10_MAX = 1700.0           # R_p10 ≤ 1700 m
C_RMED_MAX = 8000.0           # R_median ≤ 8000 m (zone courbe ≠ tangente)
C_SENTINEL_MAX = 0.50         # frac(R au plafond 50 km) < 50%
# Zone DROITE/RAPIDE — anti-SOUS-correction (pas de faux-F sur du tangent)
S_F_MAX = 1.5                 # % classe F en S1 ≤ 1.5
# Zones « droite » : le test est la DÉVIATION, plage par plage (cf.
# deflection_audit). Une plage classée sous D dont le cap ne tourne pas est
# une courbe fantôme. Les deux seuils ci-dessous bornent ce qu'on tolère :
# une plage isolée à une transition de classe est inévitable, une plage
# soutenue ne l'est pas.
#
# Ils REMPLACENT l'ancien couple (classe ≥ D ≥ 90 %, médiane des R finis
# ≥ 2 000 m). Motif : ces deux critères étaient des agrégats calés sur la
# sortie de l'estimateur d'alors, et aucun des deux ne distingue une vraie
# courbe d'un rayon inventé. Vérification à l'appui : sur la zone
# Drummondville, 15 des 17 plages sous D dévient de 17 à 69°, et les rayons
# déduits de ces déviations concordent avec les rayons ajustés ; seuls 30 m
# sur 10,2 km ne tournent pas. La médiane des R finis, elle, mesure
# désormais autre chose qu'avant : les points sans déviation étant portés au
# plafond, ils sortent du calcul et la médiane du reste baisse mécaniquement.
S_RUN_FANTOME_MAX_M = 100.0   # plus longue plage sous D sans déviation réelle
S_FRAC_FANTOME_MAX = 0.5      # % de la zone en plages fantômes
SENTINEL = 49999.0            # seuil « au plafond droite » (R_MAX_DISPLAY=50000)


def dist_kmpercls(R_vals: np.ndarray, sc) -> dict:
    """Pour un array de R, retourne {classe: km}."""
    v = sc.coeff * np.sqrt(np.maximum(R_vals, 0))
    out = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0}
    for vi in v:
        c = classify(vi).code
        out[c] += 1
    # 1 point = 10 m de pas
    return {k: val * 0.01 for k, val in out.items()}


def runs_sous_classe_D(R: np.ndarray, sc) -> list[tuple[int, int]]:
    """Plages contiguës de points classés sous D dans le scénario sc."""
    v = sc.coeff * np.sqrt(np.maximum(R, 0))
    sous = np.array([classify(vi).code not in ("A", "B", "C", "D") for vi in v])
    runs, i, n = [], 0, len(sous)
    while i < n:
        if not sous[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and sous[j + 1]:
            j += 1
        runs.append((i, j))
        i = j + 1
    return runs


def deflection_audit(sub, R: np.ndarray, sc,
                     min_deg: float = DEFLECTION_MIN_DEG,
                     base_m: float = 150.0,
                     step_m: float = 10.0) -> tuple[float, float, list]:
    """Vérifie que chaque plage sous la classe D TOURNE réellement.

    Une voie qui ne tourne pas ne peut pas porter un rayon fini : si le cap
    ne varie pas de plus de min_deg d'un bout à l'autre d'une plage classée
    sous D, cette plage est une courbe fantôme, quel que soit le rayon rendu
    par l'ajustement. Test direct, par plage, sur la géométrie UTM du parquet.

    Retourne (km suspects au total, plus longue plage suspecte en m, détail).
    """
    x = sub["x_utm"].to_numpy()
    y = sub["y_utm"].to_numpy()
    xy = np.column_stack([x, y])
    N = len(xy)
    b = max(1, int(round(base_m / step_m / 2.0)))
    if N < 2 * b + 2:
        return 0.0, 0.0, []
    idx = np.arange(b, N - b)
    dxy = xy[idx + b] - xy[idx - b]
    th = np.unwrap(np.arctan2(dxy[:, 1], dxy[:, 0]))
    theta = np.empty(N, dtype=float)
    theta[b:N - b] = th
    theta[:b] = th[0]
    theta[N - b:] = th[-1]

    km_suspect, plus_longue, detail = 0.0, 0.0, []
    for a, z in runs_sous_classe_D(R, sc):
        L_m = (z - a + 1) * step_m
        t0 = theta[max(0, a - b)]
        t1 = theta[min(N - 1, z + b)]
        dth = abs(math.atan2(math.sin(t1 - t0), math.cos(t1 - t0)))
        deg = math.degrees(dth)
        if deg < min_deg:
            km_suspect += L_m / 1000.0
            plus_longue = max(plus_longue, L_m)
            detail.append({"i_debut": int(a), "longueur_m": L_m,
                           "deviation_deg": round(deg, 2),
                           "R_median_m": round(float(np.median(R[a:z + 1])), 0)})
    return km_suspect, plus_longue, detail


def main() -> None:
    ZONES = build_zones()
    df = pq.read_table(CURVATURE_PARQUET).to_pandas()
    summary = {}
    failures: list[str] = []

    for label, key, ztype, tronc, km_min, km_max, attendu in ZONES:
        sub = df[(df["troncon_id"] == tronc) &
                 (df["km_along_segment"] >= km_min) &
                 (df["km_along_segment"] <= km_max)]
        R = sub["R_m"].to_numpy()
        if len(R) == 0:
            print(f"{label}: AUCUN POINT")
            failures.append(f"[{label}] AUCUN POINT dans la zone")
            continue
        n_km = len(R) * 0.01
        R_p10 = float(np.percentile(R, 10))
        R_med = float(np.median(R))
        frac_tiny = float(np.mean(R < 100.0))
        frac_sentinel = float(np.mean(R >= SENTINEL))
        R_fini = R[R < SENTINEL]
        R_med_fini = float(np.median(R_fini)) if len(R_fini) else float("inf")

        zone = {
            "tronçon": tronc,
            "type": ztype,
            "km_min": km_min,
            "km_max": km_max,
            "n_points": int(len(R)),
            "km_total": round(n_km, 2),
            "R_p10_m": round(R_p10, 0),
            "R_median_m": round(R_med, 0),
            "R_median_fini_m": round(R_med_fini, 0) if np.isfinite(R_med_fini) else None,
            "frac_au_plafond": round(frac_sentinel, 4),
            "frac_R_lt_100m": round(frac_tiny, 4),
            "attendu": attendu,
        }

        cls_km = {}
        for sid in ("S1", "S2", "S3"):
            d = dist_kmpercls(R, SCENARIOS[sid])
            zone[sid] = {k: round(v, 2) for k, v in d.items()}
            cls_km[sid] = d
            geD = sum(d[c] for c in "ABCD")          # classe >= D
            zone[f"{sid}_pct_geD"] = round(100 * geD / n_km, 1) if n_km else 0
            geE = sum(d[c] for c in "ABCDE")
            zone[f"{sid}_pct_geE"] = round(100 * geE / n_km, 1) if n_km else 0

        # ---- Garde-fou global : plancher numérique (toutes zones) ----
        if frac_tiny >= G_FRAC_TINY_MAX:
            failures.append(
                f"[{label}] frac(R<100m)={frac_tiny:.2%} >= {G_FRAC_TINY_MAX:.0%}")

        # ---- Critères par TYPE de zone ----
        s1 = cls_km["S1"]
        if ztype == "courbe":
            # Anti-SUR-correction : zone à courbes réelles connues → les
            # courbes DOIVENT survivre (sinon on a aplati la réalité).
            pctFE = 100 * (s1["F"] + s1["E"]) / n_km if n_km else 0
            if pctFE < C_FE_MIN:
                failures.append(
                    f"[{label}] F+E(S1)={pctFE:.1f}% < {C_FE_MIN:.0f}% "
                    f"(SUR-correction : vraies courbes effacées)")
            if R_p10 > C_RP10_MAX:
                failures.append(
                    f"[{label}] R_p10={R_p10:.0f} m > {C_RP10_MAX:.0f} "
                    f"(courbes serrées non détectées)")
            if R_med > C_RMED_MAX:
                failures.append(
                    f"[{label}] R_median={R_med:.0f} m > {C_RMED_MAX:.0f} "
                    f"(zone courbe devenue ~tangente = sur-correction)")
            if frac_sentinel >= C_SENTINEL_MAX:
                failures.append(
                    f"[{label}] frac_au_plafond={frac_sentinel:.0%} >= "
                    f"{C_SENTINEL_MAX:.0%} (courbes → faux droit)")
            zone["check_courbe"] = {
                "F+E_S1>=8": pctFE >= C_FE_MIN,
                "R_p10<=1700": R_p10 <= C_RP10_MAX,
                "R_med<=8000": R_med <= C_RMED_MAX,
                "frac_plafond<50%": frac_sentinel < C_SENTINEL_MAX,
                "pct_FE_S1": round(pctFE, 1),
            }
        else:  # ztype == "droite"
            # Anti-SOUS-correction : tangente rapide connue → pas de courbes
            # fantômes. Le test porte sur CHAQUE plage classée sous D, et non
            # sur un pourcentage agrégé : une plage n'est légitime que si le
            # cap y tourne réellement, ce qui est la définition d'une courbe.
            # Un pourcentage agrégé ne distingue pas une vraie courbe d'un
            # rayon inventé sur du tangent ; la déviation, si.
            pctD = 100 * sum(s1[c] for c in "ABCD") / n_km if n_km else 0
            pctF = 100 * s1["F"] / n_km if n_km else 0
            km_susp, plus_longue, detail = deflection_audit(
                sub, R, SCENARIOS["S1"])
            frac_susp = 100 * km_susp / n_km if n_km else 0
            if plus_longue > S_RUN_FANTOME_MAX_M:
                failures.append(
                    f"[{label}] plage de {plus_longue:.0f} m classée sous D "
                    f"avec une déviation < {DEFLECTION_MIN_DEG:.0f}° "
                    f"(> {S_RUN_FANTOME_MAX_M:.0f} m : courbe fantôme sur "
                    f"du tangent rapide)")
            if frac_susp > S_FRAC_FANTOME_MAX:
                failures.append(
                    f"[{label}] {km_susp:.2f} km sous D sans déviation réelle "
                    f"= {frac_susp:.2f}% de la zone > {S_FRAC_FANTOME_MAX}%")
            if pctF > S_F_MAX:
                failures.append(
                    f"[{label}] classe F(S1)={pctF:.1f}% > {S_F_MAX:.1f}% "
                    f"(faux-F injectés)")
            zone["check_droite"] = {
                "plage_fantome_max_m": round(plus_longue, 0),
                "km_sous_D_sans_deviation": round(km_susp, 3),
                "pct_zone_fantome": round(frac_susp, 3),
                "F_S1<=1.5": pctF <= S_F_MAX,
                "pct_geD_S1": round(pctD, 1),
                "pct_F_S1": round(pctF, 1),
                "detail_plages_fantomes": detail,
            }

        summary[label] = zone

        print(f"\n=== {label} ===")
        print(f"  Tronçon {tronc} km {km_min:.0f}-{km_max:.0f} ({n_km:.1f} km)")
        print(f"  [{ztype}] R_p10={R_p10:.0f}m  R_med={R_med:.0f}m  "
              f"R_med_fini={R_med_fini:.0f}m  frac@plafond={frac_sentinel:.1%}  "
              f"frac(R<100m)={frac_tiny:.2%}")
        for sid in ("S1", "S2", "S3"):
            d = zone[sid]
            tot = sum(d.values())
            pcts = " | ".join(
                f"{c}={100*d[c]/tot:.1f}%" if tot else f"{c}=0.0%"
                for c in "ABCDEF")
            print(f"  {sid}: {pcts}    "
                  f"[>=D: {zone[f'{sid}_pct_geD']:.1f}% | "
                  f">=E: {zone[f'{sid}_pct_geE']:.1f}%]")
            print(f"        km: " +
                  " | ".join(f"{c}={d[c]:.1f}" for c in "ABCDEF"))

    out_path = INTERMEDIATES / "_baseline_zones.json"
    summary["_acceptation"] = {
        "PASS": len(failures) == 0,
        "echecs": failures,
    }
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    print(f"\nÉcrit {out_path}")

    print()
    if failures:
        print("BASELINE: FAIL")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("BASELINE: PASS")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Étape 4 — Calcul du rayon de courbure local le long du tracé matché.

Entrée : intermediaires/corridor_matched.geojson (étape 3, polylignes haute-res)
Sortie : intermediaires/courbure_points.parquet
       + intermediaires/controle_04_courbure.html

Algorithme (par tronçon) :
    1) Reprojection lat/lon → UTM (zone 18N pour TO/Ott/MTL, 19N pour QC).
       NB : le rejet des faux-F (excursions sur aiguillage / voie
       d'évitement) est traité EN AMONT — étape 03, map-matching guidé par
       l'itinéraire GTFS. La géométrie reçue ici est déjà propre : aucun
       post-hoc géométrique dans cette étape.
    2) Ré-échantillonnage uniforme de la polyligne à pas de RESAMPLE_STEP_M (10 m).
    3) Lissage léger des coordonnées par moyenne glissante (SMOOTH_WINDOW_M / step
       points) pour absorber le bruit de numérisation OSM.
    4) Pour chaque point, ajustement par moindres carrés (cercle algébrique de
       Kåsa, centré sur la moyenne) sur une fenêtre de FIT_WINDOW_M mètres
       d'arc ; le rayon de ce cercle est le rayon de courbure local. Cet
       estimateur intègre ~80 points et est donc robuste au bruit de
       numérisation OSM (~5-10 m), contrairement au cercle circonscrit à 3
       points qui en était dominé.
    5) Post-filtre minimal : un seul médian glissant (5 pts) puis clip sur
       [R_MIN_PHYSICAL, 5e6].
    6) Stockage dans un parquet avec colonnes : alignment_id, troncon_id,
       point_idx, km_along_segment, lat, lon, x_utm, y_utm, R_m.

Auto-calibration : `python3 04_compute_curvature.py --calibrate` exécute
run_synthetic_calibration() qui valide l'estimateur sur des arcs de rayon
connu bruités, en appelant les MÊMES fonctions de production.
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pyproj import Transformer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    CORRIDOR_MATCHED_GEOJSON,
    CURVATURE_PARQUET,
    INTERMEDIATES,
    pick_utm_for_corridor,
    ensure_dirs,
)

RESAMPLE_STEP_M = 10.0    # pas constant le long du tracé
SMOOTH_WINDOW_M = 30.0    # fenêtre lissage XY légère : retire le jitter
                          # haute-fréquence sans aplatir les courbes réelles
                          # (l'estimateur LSQ fait le gros du débruitage)
FIT_WINDOW_M = 900.0      # fenêtre d'ajustement du cercle LSQ (m d'arc).
                          # Calibrée : voir run_synthetic_calibration(). Le
                          # balayage {600,700,800,900} a montré que 800 m
                          # échoue la bande R=7000 → médiane≥3000 à σ=8
                          # (médiane 2722 m) ; 900 m est la PLUS PETITE valeur
                          # passant TOUTES les bandes + hard-fails.
R_MAX_DISPLAY = 50_000    # rayon affiché max (au-delà = "ligne droite")
R_MIN_PHYSICAL = 100.0    # rayon minimal physiquement plausible pour rail
R_MEDIAN_WINDOW_M = 50.0  # fenêtre du médian post-filtre (→ taille en points
                          # dérivée dans postfilter_R, pas de constante morte)


def transformer_from_lonlat(epsg_target: int) -> Transformer:
    return Transformer.from_crs("EPSG:4326", f"EPSG:{epsg_target}", always_xy=True)


def resample_uniform(xy: np.ndarray, step: float) -> tuple[np.ndarray, np.ndarray]:
    """Ré-échantillonne une polyligne à pas constant.

    xy : array (N, 2) en mètres
    step : pas en mètres
    Retourne (xy_resampled, cum_length)
    """
    diffs = np.diff(xy, axis=0)
    seg_lengths = np.linalg.norm(diffs, axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg_lengths)])
    total = cum[-1]
    n_pts = int(np.floor(total / step)) + 1
    targets = np.arange(n_pts) * step
    new_x = np.interp(targets, cum, xy[:, 0])
    new_y = np.interp(targets, cum, xy[:, 1])
    return np.column_stack([new_x, new_y]), targets


def smooth_xy(xy: np.ndarray, window: int) -> np.ndarray:
    """Moyenne glissante centrée sur chaque coordonnée."""
    if window <= 1:
        return xy
    kernel = np.ones(window) / window
    pad = window // 2
    x_pad = np.pad(xy[:, 0], pad, mode="edge")
    y_pad = np.pad(xy[:, 1], pad, mode="edge")
    sx = np.convolve(x_pad, kernel, mode="same")[pad:pad + len(xy)]
    sy = np.convolve(y_pad, kernel, mode="same")[pad:pad + len(xy)]
    # Si convolve renvoie une longueur différente (bordures), tronquer
    sx = sx[:len(xy)]
    sy = sy[:len(xy)]
    return np.column_stack([sx, sy])


def lsq_circle_radius(xy: np.ndarray) -> float:
    """Rayon du cercle ajusté par moindres carrés (cercle algébrique de Kåsa).

    Conditionnement OBLIGATOIRE : centrage sur la moyenne avant résolution.
    On résout, pour le nuage (u, v) = (x - x̄, y - ȳ) :
        A·u + B·v + C = u² + v²
    par moindres carrés. Le centre du cercle est (uc, vc) = (A/2, B/2) et
    R = sqrt(C + uc² + vc²). La forme non centrée est mal conditionnée — ne
    pas l'utiliser.

    Retourne np.inf si lstsq est de rang déficient, ou si R non fini ou <= 0
    (cas dégénéré / quasi-aligné = courbure nulle = rayon infini).
    """
    xy = np.asarray(xy, dtype=float)
    if len(xy) < 3:
        return np.inf
    x = xy[:, 0]
    y = xy[:, 1]
    u = x - x.mean()
    v = y - y.mean()
    M = np.column_stack([u, v, np.ones_like(u)])
    rhs = u ** 2 + v ** 2
    sol, _res, rank, _sv = np.linalg.lstsq(M, rhs, rcond=None)
    if rank < 3:
        return np.inf
    A, B, C = sol
    uc = A / 2.0
    vc = B / 2.0
    disc = C + uc ** 2 + vc ** 2
    if not np.isfinite(disc) or disc <= 0:
        return np.inf
    R = float(np.sqrt(disc))
    if not np.isfinite(R) or R <= 0:
        return np.inf
    return R


def curvature_lsq_window(xy: np.ndarray, step_m: float,
                         fit_window_m: float) -> np.ndarray:
    """Rayon de courbure local par ajustement LSQ glissant.

    Pour chaque centre intérieur i ∈ [W//2, N-1-W//2], ajuste un cercle sur la
    fenêtre xy[i-W//2 : i+W//2+1] (W = round(fit_window_m/step_m)+1 points).
    Les points de bord recopient la valeur intérieure la plus proche.

    Retourne un array float de longueur N (R en mètres ; np.inf si droit).
    """
    N = len(xy)
    R = np.full(N, np.inf, dtype=float)
    if N < 3:
        return R
    W = int(round(fit_window_m / step_m)) + 1
    W = max(3, W)
    half = W // 2
    lo = half
    hi = N - 1 - half
    if hi < lo:
        # Tronçon plus court que la fenêtre : un seul ajustement global.
        R[:] = lsq_circle_radius(xy)
        return R
    for i in range(lo, hi + 1):
        R[i] = lsq_circle_radius(xy[i - half:i + half + 1])
    # Bords : valeur intérieure la plus proche.
    R[:lo] = R[lo]
    R[hi + 1:] = R[hi]
    return R


# C4 (fix red team) : le plafond R injecté dans la physique EST le plafond
# d'affichage R_MAX_DISPLAY (50 000 m), PAS 5 000 000 m. Au-delà de ~9 000 m
# aucun scénario n'a de contrainte de courbure (r_for_vmax(360) ≈ 8 690 m en
# S1) ; 50 000 m = « droite, hors contrainte » est physiquement neutre et ne
# génère plus de v_max absurde (combiné au plafond v_max ≤ 360 du scénario).
R_CLAMP_MAX = float(R_MAX_DISPLAY)  # 50 000 m


def postfilter_R(R: np.ndarray) -> np.ndarray:
    """Post-filtre R : un seul médian glissant puis clip physique.

    UNIQUE post-traitement appliqué au rayon brut, partagé entre la production
    et la calibration synthétique pour garantir qu'elles testent le même code.
    Taille du médian dérivée de R_MEDIAN_WINDOW_M (aucune constante morte).
    """
    from scipy.ndimage import median_filter
    R = np.asarray(R, dtype=float)
    msize = max(3, int(round(R_MEDIAN_WINDOW_M / RESAMPLE_STEP_M)))
    if msize % 2 == 0:
        msize += 1
    # Les valeurs non finies (droit) sont remplacées par le plafond avant
    # filtrage médian (un voisinage majoritairement droit reste "droit").
    R = np.where(np.isfinite(R), R, R_CLAMP_MAX)
    R = median_filter(R, size=msize, mode="nearest")
    R = np.clip(R, R_MIN_PHYSICAL, R_CLAMP_MAX)
    return R


R_BINS = [(7000, "#006400"), (4000, "#32cd32"), (2000, "#ffd700"),
          (1000, "#ffa500"), (500, "#ff4500"), (0, "#8b0000")]


def color_for_R(R: float) -> str:
    for thr, col in R_BINS:
        if R >= thr:
            return col
    return R_BINS[-1][1]


def write_controle_html(df: pd.DataFrame, out_html: Path) -> None:
    """Carte de contrôle : tracé coloré par classe de rayon, segments fusionnés."""
    import folium

    m = folium.Map(location=[45.5, -75.5], zoom_start=6, tiles="cartodbpositron")

    legend = (
        "<b>Rayon de courbure (m)</b><br>"
        "<span style='color:#006400'>■</span> ≥ 7000 (très ample, HSR ok)<br>"
        "<span style='color:#32cd32'>■</span> 4000–7000<br>"
        "<span style='color:#ffd700'>■</span> 2000–4000<br>"
        "<span style='color:#ffa500'>■</span> 1000–2000<br>"
        "<span style='color:#ff4500'>■</span> 500–1000<br>"
        "<span style='color:#8b0000'>■</span> &lt; 500 (très serré)<br>"
    )

    # Pour économiser : batcher les points consécutifs de même couleur en une seule PolyLine
    for tronc_id, sub in df.groupby("troncon_id"):
        layer = folium.FeatureGroup(name=f"Tronçon {tronc_id}", show=True)
        lats = sub["lat"].to_numpy()
        lons = sub["lon"].to_numpy()
        Rs = sub["R_m"].to_numpy()
        if len(lats) < 2:
            continue
        cur_color = color_for_R(Rs[0])
        run_start = 0
        for i in range(1, len(lats)):
            c = color_for_R(Rs[i])
            if c != cur_color:
                folium.PolyLine(
                    locations=list(zip(lats[run_start:i + 1], lons[run_start:i + 1])),
                    color=cur_color, weight=4, opacity=0.85,
                ).add_to(layer)
                run_start = i
                cur_color = c
        # Dernier run
        folium.PolyLine(
            locations=list(zip(lats[run_start:], lons[run_start:])),
            color=cur_color, weight=4, opacity=0.85,
        ).add_to(layer)
        layer.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    folium.Marker(
        location=[44.0, -77.0],
        icon=folium.DivIcon(html=f"<div style='background:white;padding:6px;border:1px solid #888;font-size:11px'>{legend}</div>"),
    ).add_to(m)
    out_html.write_text(m.get_root().render(), encoding="utf-8")


# ---------------------------------------------------------------------------
# Calibration synthétique
# ---------------------------------------------------------------------------
# Bandes de PASS (asymétriques, délibérées) : on NE veut PAS exiger une
# récupération serrée des grands rayons — au-delà de ~3 km la signature
# géométrique d'une courbe est noyée dans le bruit OSM, et exiger 7000 m
# ré-instituerait le défaut « faux-A » (sous-estimation de courbure → fausse
# classe A) que ce correctif élimine. On garantit donc seulement que les
# rayons serrés (vraies contraintes) NE sont PAS surestimés.
CALIB_BANDS = {
    400:  (320, 560),
    800:  (560, 1200),
    1500: (1000, 2400),
    3000: (1900, 9000),
    7000: (3000, None),   # plancher seul, AUCUNE borne haute
}
CALIB_RADII = [400, 800, 1500, 3000, 7000]
CALIB_SIGMAS = [5, 8]
CALIB_TRIALS = 200


def _synthetic_arc(R: float, step_m: float = RESAMPLE_STEP_M) -> np.ndarray:
    """Arc de cercle de rayon R, échantillonné tous les step_m mètres d'arc.

    Longueur d'arc = max(0.6*R, 1000) m. Retourne (M, 2).
    """
    arc_len = max(0.6 * R, 1000.0)
    n = int(round(arc_len / step_m)) + 1
    s = np.arange(n) * step_m            # abscisse curviligne
    theta = s / R                        # angle (rad)
    x = R * np.sin(theta)
    y = R * (1.0 - np.cos(theta))
    return np.column_stack([x, y])


def _recover_median_R(R_true: float, sigma: float, rng: np.random.Generator,
                      fit_window_m: float) -> float:
    """Un essai : arc bruité → mêmes fonctions de prod → médiane R intérieur."""
    arc = _synthetic_arc(R_true)
    noisy = arc + rng.normal(0.0, sigma, size=arc.shape)
    # Estimateur de PROD pur (le rejet d'excursions est désormais traité EN
    # AMONT, étape 03 map-matching guidé GTFS — pas de post-hoc géométrie ici).
    smooth_window_pts = max(1, int(SMOOTH_WINDOW_M / RESAMPLE_STEP_M))
    xy_sm = smooth_xy(noisy, smooth_window_pts)
    R_raw = curvature_lsq_window(xy_sm, RESAMPLE_STEP_M, fit_window_m)
    R_filt = postfilter_R(R_raw)
    # Médiane sur la partie intérieure (exclut les bords recopiés).
    W = max(3, int(round(fit_window_m / RESAMPLE_STEP_M)) + 1)
    half = W // 2
    interior = R_filt[half:len(R_filt) - half]
    if len(interior) == 0:
        interior = R_filt
    return float(np.median(interior))


def _run_calibration_for_window(fit_window_m: float, seed: int = 12345):
    """Exécute la grille (R × σ × trials) pour une fenêtre donnée.

    Retourne (table, reasons) : table = liste de dicts par (R, σ) ;
    reasons = liste de chaînes décrivant chaque échec (vide si tout passe).
    """
    rng = np.random.default_rng(seed)
    table = []
    reasons = []
    for R_true in CALIB_RADII:
        lo, hi = CALIB_BANDS[R_true]
        for sigma in CALIB_SIGMAS:
            recs = np.array([
                _recover_median_R(R_true, sigma, rng, fit_window_m)
                for _ in range(CALIB_TRIALS)
            ])
            med = float(np.median(recs))
            rel_std = float(np.std(recs) / med) if med > 0 else float("inf")
            row = {"R": R_true, "sigma": sigma, "median": med,
                   "rel_std": rel_std, "band_lo": lo, "band_hi": hi}
            table.append(row)
            # Bande de PASS (asymétrique).
            if med < lo:
                reasons.append(
                    f"R={R_true} σ={sigma}: médiane {med:.0f} < borne basse {lo}")
            if hi is not None and med > hi:
                reasons.append(
                    f"R={R_true} σ={sigma}: médiane {med:.0f} > borne haute {hi}")
            # HARD FAIL 1 : explosion de R (faux droit).
            if med > 50000:
                reasons.append(
                    f"HARD: R={R_true} σ={sigma}: médiane {med:.0f} > 50000 m")
            # HARD FAIL 2 : R=400 & σ=8 surestimé ≥ 2682 m.
            if R_true == 400 and sigma == 8 and med >= 2682:
                reasons.append(
                    f"HARD: R=400 σ=8: médiane {med:.0f} >= 2682 m "
                    f"(surestimation des courbes serrées)")
            # HARD FAIL 3 : std relative > 25 % pour tout R ≤ 3000.
            if R_true <= 3000 and rel_std > 0.25:
                reasons.append(
                    f"HARD: R={R_true} σ={sigma}: std rel {rel_std:.1%} > 25%")
    return table, reasons


def _print_calibration_table(fit_window_m: float, table: list) -> None:
    print(f"\n  --- FIT_WINDOW_M = {fit_window_m:.0f} m ---")
    print(f"  {'R_true':>7} {'sigma':>6} {'med_rec':>9} {'rel_std':>8} "
          f"{'band':>15} {'ok':>4}")
    for row in table:
        lo, hi = row["band_lo"], row["band_hi"]
        hi_s = "inf" if hi is None else f"{hi}"
        in_band = (row["median"] >= lo) and (hi is None or row["median"] <= hi)
        band = f"[{lo},{hi_s}]"
        print(f"  {row['R']:>7} {row['sigma']:>6} {row['median']:>9.0f} "
              f"{row['rel_std']:>7.1%} {band:>15} {'OK' if in_band else 'XX':>4}")


def _finalize_pass(fit_window_m: float) -> bool:
    """Gate FINAL de l'estimateur LSQ.

    Le rejet des excursions fermées (faux-F) est désormais traité EN AMONT
    (étape 03, map-matching guidé GTFS) — il n'y a plus de filtre post-hoc
    géométrie ici, donc plus de test adverse « excursion » à ce stade. Les
    bandes-arcs synthétiques (déjà validées par l'appelant avant cet appel)
    suffisent à valider que l'estimateur LSQ ne sur-/sous-estime pas un arc
    de rayon connu. Conservé comme point d'extension explicite."""
    print(f"CALIBRATION: PASS  (FIT_WINDOW_M = {fit_window_m:.0f} m ; "
          f"bandes-arcs OK ; rejet faux-F = upstream étape 03, pas de "
          f"post-hoc géométrie 04)")
    return True


def run_synthetic_calibration() -> bool:
    """Valide l'estimateur sur arcs synthétiques bruités.

    Stratégie : tester FIT_WINDOW_M courant ; s'il échoue, balayer
    {600,700,800,900} et choisir la PLUS PETITE valeur qui passe toutes les
    bandes + hard-fails. Met à jour la constante globale FIT_WINDOW_M si une
    valeur différente est retenue. Retourne True si une config passe.
    """
    global FIT_WINDOW_M
    print("=== Calibration synthétique de l'estimateur de courbure ===")
    print(f"  {CALIB_TRIALS} essais/case, σ ∈ {CALIB_SIGMAS} m, "
          f"R ∈ {CALIB_RADII} m")
    print("  Bandes asymétriques délibérées : pas de borne haute sur R=7000 "
          "(éviter le défaut faux-A)")

    # 1) Tenter la valeur courante.
    table0, reasons0 = _run_calibration_for_window(FIT_WINDOW_M)
    _print_calibration_table(FIT_WINDOW_M, table0)
    if not reasons0:
        print(f"\n  Bandes-arcs : PASS (FIT_WINDOW_M = {FIT_WINDOW_M:.0f} m)")
        return _finalize_pass(FIT_WINDOW_M)

    print(f"\n  FIT_WINDOW_M = {FIT_WINDOW_M:.0f} m échoue :")
    for r in reasons0:
        print(f"    - {r}")
    print("  → balayage de FIT_WINDOW_M ∈ {600,700,800,900} ...")

    sweep = [600, 700, 800, 900]
    passing = []
    for fw in sweep:
        tbl, rs = _run_calibration_for_window(float(fw))
        _print_calibration_table(float(fw), tbl)
        if not rs:
            print(f"  → FIT_WINDOW_M={fw} m : PASS toutes bandes+hard-fails")
            passing.append(fw)
        else:
            print(f"  → FIT_WINDOW_M={fw} m : FAIL")
            for r in rs:
                print(f"      - {r}")

    if passing:
        chosen = min(passing)            # plus petite valeur qui passe
        FIT_WINDOW_M = float(chosen)
        print(f"\n  Bandes-arcs : PASS (FIT_WINDOW_M retenu = {chosen} m)")
        return _finalize_pass(FIT_WINDOW_M)

    print("\nCALIBRATION: FAIL (aucune valeur de FIT_WINDOW_M ∈ "
          "{600,700,800,900} ne passe toutes les bandes + hard-fails)")
    return False


def main() -> None:
    ensure_dirs()
    if not CORRIDOR_MATCHED_GEOJSON.exists():
        sys.exit(f"Tracé matché introuvable : {CORRIDOR_MATCHED_GEOJSON} — lancer 03_match_gtfs_to_osm.py d'abord.")

    print("=== Étape 4 — Calcul du rayon de courbure ===")
    geojson = json.loads(CORRIDOR_MATCHED_GEOJSON.read_text(encoding="utf-8"))
    matched_features = [f for f in geojson["features"] if f["properties"]["kind"] == "matched_corridor_segment"]
    print(f"  {len(matched_features)} tronçons matchés à analyser")

    smooth_window_pts = max(1, int(SMOOTH_WINDOW_M / RESAMPLE_STEP_M))
    rows = []
    for feat in matched_features:
        tronc_id = feat["properties"]["troncon_id"]
        coords_lonlat = np.array(feat["geometry"]["coordinates"])  # (N, 2) : lon, lat
        lats = coords_lonlat[:, 1]
        lons = coords_lonlat[:, 0]
        epsg = pick_utm_for_corridor(lons.tolist())
        print(f"\n  {tronc_id}: {len(lats)} pts → UTM EPSG:{epsg}")
        t0 = time.time()
        tr = transformer_from_lonlat(epsg)
        x, y = tr.transform(lons, lats)
        xy = np.column_stack([x, y])
        # Élimine doublons consécutifs (artefact de concaténation)
        keep = np.concatenate([[True], np.linalg.norm(np.diff(xy, axis=0), axis=1) > 0.01])
        xy = xy[keep]
        print(f"    Reprojeté en {time.time()-t0:.2f}s ; {len(xy)} pts uniques")
        # NB : le rejet des faux-F (excursions sur aiguillage/évitement) est
        # traité EN AMONT — étape 03, map-matching guidé par l'itinéraire GTFS
        # (cf. 03_match_gtfs_to_osm.py : pick_continuation_at_junction /
        # gtfs_guided_relock). Plus aucun filtre post-hoc géométrie ici :
        # l'estimateur LSQ travaille sur une géométrie déjà propre.
        # Resample
        t0 = time.time()
        xy_rs, km_along = resample_uniform(xy, RESAMPLE_STEP_M)
        print(f"    Ré-échantillonné à pas {RESAMPLE_STEP_M:.0f} m → {len(xy_rs)} pts ({time.time()-t0:.2f}s)")
        # Smooth
        xy_sm = smooth_xy(xy_rs, smooth_window_pts)
        # Re-projeter en lat/lon pour le rendu
        inv = Transformer.from_crs(f"EPSG:{epsg}", "EPSG:4326", always_xy=True)
        lon_rs, lat_rs = inv.transform(xy_sm[:, 0], xy_sm[:, 1])
        # Curvature : ajustement LSQ glissant (robuste au bruit OSM)
        t0 = time.time()
        R_raw = curvature_lsq_window(xy_sm, RESAMPLE_STEP_M, FIT_WINDOW_M)
        # UNIQUE post-filtre : médian(5) + clip physique (cf. postfilter_R)
        R_capped = postfilter_R(R_raw)
        n_floor = int(np.sum(R_capped <= R_MIN_PHYSICAL + 1e-6))
        frac_straight = float(np.mean(R_capped >= R_MAX_DISPLAY - 1.0))
        median_R = float(np.median(R_capped))
        physical = R_capped[(R_capped >= R_MIN_PHYSICAL) & (R_capped < R_MAX_DISPLAY)]
        median_phys = np.median(physical) if len(physical) > 0 else 0
        print(f"    Courbure : R_min={R_capped.min():.0f} m, "
              f"médiane R={median_R:.0f} m, médiane physique={median_phys:.0f} m, "
              f"frac(droite@{R_MAX_DISPLAY/1000:.0f}km)={frac_straight:.1%}, "
              f"{n_floor} pts au plancher ({R_MIN_PHYSICAL:.0f}m) "
              f"({time.time()-t0:.2f}s)")
        for i in range(len(xy_sm)):
            rows.append({
                "alignment_id": "via_existing",
                "troncon_id": tronc_id,
                "point_idx": i,
                "km_along_segment": float(km_along[i] / 1000.0),
                "lat": float(lat_rs[i]),
                "lon": float(lon_rs[i]),
                "x_utm": float(xy_sm[i, 0]),
                "y_utm": float(xy_sm[i, 1]),
                "epsg": int(epsg),
                "R_m": float(R_capped[i]),
            })

    df = pd.DataFrame(rows)
    print(f"\nTotal : {len(df):,} points calculés")
    pq.write_table(pa.Table.from_pandas(df), CURVATURE_PARQUET, compression="snappy")
    print(f"Écrit {CURVATURE_PARQUET.name} ({CURVATURE_PARQUET.stat().st_size/1e6:.1f} MB)")

    print("\nGénération de la carte de contrôle ...")
    write_controle_html(df, INTERMEDIATES / "controle_04_courbure.html")
    print("Contrôle : controle_04_courbure.html")
    print("\nOK — étape 4 terminée.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Étape 4 — rayon de courbure local + calibration.")
    parser.add_argument(
        "--calibrate", action="store_true",
        help="Exécute la calibration synthétique (auto-contenue, sans "
             "dépendance amont) et sort 0/1 selon PASS/FAIL.")
    args = parser.parse_args()
    if args.calibrate:
        ok = run_synthetic_calibration()
        sys.exit(0 if ok else 1)
    main()

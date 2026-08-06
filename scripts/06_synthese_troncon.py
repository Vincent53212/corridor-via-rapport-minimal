#!/usr/bin/env python3
"""Étape 6 — Synthèse statistique par tronçon × scénario + détection des goulots.

Entrée : intermediaires/segments.geojson
Sortie : - livrables/synthese_troncon.csv  (distribution km par tronçon × scénario × classe)
        - livrables/goulots_detranglement.csv  (goulots structurels)
        - livrables/synthese_par_troncon.html  (vue exec : tableau + barres)
"""
from __future__ import annotations
import json
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    SEGMENTS_GEOJSON,
    DELIVERABLES,
    ensure_dirs,
    degre_courbure,
    fmt_dc,
    kmh_to_mph,
)
from scenarios import SCENARIOS, SPEED_CLASSES, published_vmax_class
from alignments import CORRIDOR_SEGMENTS


CLASS_RANK = {sc.code: i for i, sc in enumerate(SPEED_CLASSES)}  # A=0 (best) … F=5 (worst)
# Cible HSR-utile = classes A, B, C (≥ 200 km/h)
HSR_CLASSES = {"A", "B", "C"}
BOTTLENECK_DROP = 2  # nb de classes en-dessous de la classe dominante locale


def compute_distribution(segments: list[dict]) -> dict:
    """dist[troncon][scenario][classe] = km cumulés."""
    dist: dict[str, dict[str, dict[str, float]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(float))
    )
    for s in segments:
        p = s["properties"]
        t = p["troncon_id"]
        lm = p["longueur_m"] / 1000.0
        for sid in ("S1", "S2", "S3"):
            dist[t][sid][p[f"classe_{sid}"]] += lm
    return dist


def compute_extra_metrics(segments: list[dict]) -> tuple[dict, dict, dict]:
    """Métriques M2 + fourchette, par tronçon × scénario :

      - dist_p50[t][sid][classe] : km par classe recalculée sur R_p50 (médiane)
        = BORNE HAUTE de la fourchette (moins pessimiste que R_p10 publié) ;
      - segcount[t][sid] = {'tot', 'hsr'} : dénominateur PAR SEGMENT (fix M2) ;
      - geom[t][sid] = {plafond_kmh, vmax_medL_kmh} :
          * plafond_kmh = ΣL/Σ(L/vmax) — **plafond GÉOMÉTRIQUE moyen, HORS
            EXPLOITATION** : il suppose chaque segment parcouru à son plafond
            de courbure (jusqu'à 360 km/h sur les tangentes). N'inclut PAS
            signalisation / passages à niveau / partage fret / électrification
            / accél.-décél. → la vitesse opérationnelle réelle est INFÉRIEURE.
            Fortement tiré vers le haut par la fraction de linéaire au plafond
            360 (tangentes). À présenter comme borne supérieure, jamais comme
            « vitesse réalisable » (cf. caveat S1).
          * vmax_medL_kmh = médiane de vmax pondérée par la longueur :
            indicateur central ROBUSTE, peu déformé par la queue à 360.
    """
    dist_p50: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    segcount: dict = defaultdict(lambda: defaultdict(lambda: {"tot": 0, "hsr": 0}))
    pairs: dict = defaultdict(lambda: defaultdict(list))  # (t,sid) → [(L_km, vmax)]
    for s in segments:
        p = s["properties"]
        t = p["troncon_id"]
        lm = p["longueur_m"] / 1000.0
        Rp50 = p.get("R_p50_m")
        Rmin = p.get("R_min_m")
        for sid in ("S1", "S2", "S3"):
            if Rp50 is not None and Rmin is not None:
                code_opt, _ = published_vmax_class(
                    SCENARIOS[sid], float(Rp50), float(Rmin))
            else:
                code_opt = p[f"classe_{sid}"]
            dist_p50[t][sid][code_opt] += lm
            sc = segcount[t][sid]
            sc["tot"] += 1
            if p[f"classe_{sid}"] in HSR_CLASSES:
                sc["hsr"] += 1
            v = p.get(f"vmax_{sid}_kmh") or 0.0
            if v > 0:
                pairs[t][sid].append((lm, float(v)))
    geom: dict = defaultdict(lambda: defaultdict(dict))
    for t in pairs:
        for sid in pairs[t]:
            pr = sorted(pairs[t][sid], key=lambda x: x[1])
            Ltot = sum(L for L, _ in pr)
            tsum = sum(L / v for L, v in pr if v > 0)
            harm = Ltot / tsum if tsum > 0 else 0.0
            half = Ltot / 2.0
            acc = 0.0
            medL = pr[-1][1] if pr else 0.0
            for L, v in pr:
                acc += L
                if acc >= half:
                    medL = v
                    break
            geom[t][sid] = {"plafond_kmh": round(harm, 1),
                            "vmax_medL_kmh": round(medL, 1)}
    return dist_p50, segcount, geom


def detect_bottlenecks(segments: list[dict], scenario: str = "S3") -> list[dict]:
    """Goulot structurel = section courte (≤5 km) qui, MÊME dans le scénario
    le plus permissif (S3 pendulaire), reste **classe F** (< 100 km/h) ET
    descend ≥2 classes sous son voisinage ET est **soutenue ≥ 150 m**.

    Définition resserrée (correctif RT-4) : seul **F-en-S3** compte comme
    « goulot à rectifier en tracé », car c'est la seule classe qu'AUCUN
    scénario (même pendulaire) ne sauve. Les classes D (160–199) et E
    (100–159) en S3 sont une **dégradation relative**, pas un goulot
    greenfield : à 160–199 km/h on est très au-dessus de la pratique VIA
    actuelle — les ranger « à reconstruire » contredirait la thèse même de
    l'étude (moderniser > reconstruire). Le seuil de longueur (≥150 m) évite
    de compter un pic ponctuel de relevé comme un goulot. Le total complet
    par classe (dont D/E « dégradé, à moderniser ») est rapporté séparément
    dans la synthèse, sans être étiqueté « à reconstruire ».
    """
    # Trier par tronçon, puis par km_debut
    by_tronc: dict[str, list[dict]] = defaultdict(list)
    for s in segments:
        by_tronc[s["properties"]["troncon_id"]].append(s)
    for k in by_tronc:
        by_tronc[k].sort(key=lambda f: f["properties"]["km_debut"])

    goulots = []
    for troncon_id, segs in by_tronc.items():
        for i, s in enumerate(segs):
            p = s["properties"]
            classe = p[f"classe_{scenario}"]
            longueur_km = p["longueur_m"] / 1000.0
            # Classe dominante du voisinage (10 segments avant et après)
            window = segs[max(0, i - 10):i] + segs[i + 1:i + 11]
            if not window:
                continue
            wc = [w["properties"][f"classe_{scenario}"] for w in window]
            # Médiane des rangs
            sorted_ranks = sorted(CLASS_RANK[c] for c in wc)
            dominant_rank = sorted_ranks[len(sorted_ranks) // 2]
            this_rank = CLASS_RANK[classe]
            drop = this_rank - dominant_rank
            if (drop >= BOTTLENECK_DROP and longueur_km <= 5.0
                    and classe == "F"               # RT-4 : seul F-en-S3 = à rectifier
                    and p["longueur_m"] >= 150.0):   # RT-4 : soutenu, pas un pic
                dominant_classe = SPEED_CLASSES[dominant_rank].code
                _dc_g = degre_courbure(p["R_min_m"])
                goulots.append({
                    "troncon_id": troncon_id,
                    "seg_idx": p["seg_idx"],
                    "km_debut": p["km_debut"],
                    "km_fin": p["km_fin"],
                    "longueur_m": p["longueur_m"],
                    "degre_courbure_max_deg": round(_dc_g, 2) if _dc_g is not None else None,
                    "R_min_m": p["R_min_m"],
                    "vmax_S3_kmh": p[f"vmax_{scenario}_kmh"],
                    "classe_S3": classe,
                    "classe_dominante_voisinage": dominant_classe,
                    "drop_classes": drop,
                    "gare_amont": p["gare_amont"],
                    "gare_aval": p["gare_aval"],
                })
    # Trier par drop décroissant
    goulots.sort(key=lambda g: (g["drop_classes"], -g["R_min_m"] if g["R_min_m"] else 0), reverse=True)
    return goulots


def write_synthese_csv(dist: dict, dist_p50: dict, segcount: dict,
                       geom: dict, out_path: Path) -> None:
    rows = []
    for troncon in CORRIDOR_SEGMENTS:
        for sid in ("S1", "S2", "S3"):
            tot = sum(dist[troncon][sid].values())
            sc_obj = SCENARIOS[sid]
            row = {
                "troncon_id / section_id": troncon,
                "scenario": sid,
                "scenario_label": sc_obj.name_fr + " | " + sc_obj.name_en,
                "devers_mm": sc_obj.cant_mm,
                "devers_pouces": round(sc_obj.cant_in, 2),
                "insuff_devers_mm": sc_obj.cant_def_mm,
                "insuff_devers_pouces": round(sc_obj.cant_def_in, 2),
                "coeff_k_vmax": round(sc_obj.coeff, 3),
                "longueur_totale_km / total_length_km": round(tot, 2),
            }
            for sc in SPEED_CLASSES:
                km = dist[troncon][sid].get(sc.code, 0.0)
                pct = 100 * km / tot if tot > 0 else 0
                row[f"km_{sc.code} ({sc.name_fr})"] = round(km, 2)
                row[f"pct_{sc.code} ({sc.name_en})"] = round(pct, 1)
            # km HSR-utile — pct_HSR_utile = borne BASSE (R_p10, prudent, publié)
            km_hsr = sum(dist[troncon][sid].get(c, 0.0) for c in HSR_CLASSES)
            pct_hsr = 100 * km_hsr / tot if tot > 0 else 0
            row["km_HSR_utile (A+B+C, ≥200km/h)"] = round(km_hsr, 2)
            row["pct_HSR_utile"] = round(pct_hsr, 1)
            # Fourchette : borne HAUTE = classes recalculées sur R_p50 (médiane)
            km_hsr_hi = sum(dist_p50[troncon][sid].get(c, 0.0) for c in HSR_CLASSES)
            pct_hsr_hi = 100 * km_hsr_hi / tot if tot > 0 else 0
            row["pct_HSR_utile_borne_haute_R_p50"] = round(pct_hsr_hi, 1)
            # M2 : dénominateur PAR SEGMENT (pas dilué par les longues droites)
            scn = segcount[troncon][sid]
            row["pct_HSR_utile_par_segment_M2"] = (
                round(100 * scn["hsr"] / scn["tot"], 1) if scn["tot"] else 0)
            # M2/M6 : plafond GÉOMÉTRIQUE moyen (HORS exploitation — borne
            # supérieure, n'inclut PAS signalisation/passages/fret/accél.) +
            # médiane vmax pondérée-longueur (indicateur central robuste).
            g = geom[troncon][sid]
            row["DIAG_NON_OP_plafond_geom_kmh"] = g["plafond_kmh"]
            row["DIAG_NON_OP_plafond_geom_mph"] = round(kmh_to_mph(g["plafond_kmh"]), 1)
            row["DIAG_NON_OP_vmax_med_pondL_kmh"] = g["vmax_medL_kmh"]
            row["DIAG_NON_OP_vmax_med_pondL_mph"] = round(kmh_to_mph(g["vmax_medL_kmh"]), 1)
            rows.append(row)
    fieldnames = list(rows[0].keys()) if rows else []
    # encoding utf-8-sig (BOM) + delimiter ; pour qu'Excel Windows FR ouvre
    # le CSV en colonnes correctement et préserve les accents
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def write_goulots_csv(goulots: list[dict], out_path: Path) -> None:
    if not goulots:
        out_path.write_text("Aucun goulot d'étranglement détecté.\n", encoding="utf-8-sig")
        return
    fieldnames = list(goulots[0].keys())
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(goulots)


def write_scenarios_params_csv(out_path: Path) -> None:
    """Tableau de référence des 3 scénarios — « expliciter les mesures de dévers et
    d'insuffisance » (mm ET pouces), coefficient de vitesse, impact fret et drapeau
    « dévers supposé, non relevé ». Source unique : scenarios.py."""
    rows = []
    for sid in ("S1", "S2", "S3"):
        s = SCENARIOS[sid]
        rows.append({
            "scenario": sid,
            "libelle_fr": s.name_fr,
            "libelle_en": s.name_en,
            "devers_mm": s.cant_mm,
            "devers_pouces": round(s.cant_in, 2),
            "insuff_devers_mm": s.cant_def_mm,
            "insuff_devers_pouces": round(s.cant_def_in, 2),
            "accel_laterale_m_s2": round(s.a_total, 3),
            "coeff_k_vmax_kmh_par_racine_R": round(s.coeff, 3),
            "devers_suppose_non_releve": "oui" if s.cant_assumed else "non",
            "impact_fret_fr": s.fret_fr,
            "impact_fret_en": s.fret_en,
            "source": s.source,
        })
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(rows)


def write_synthese_html(dist: dict, dist_p50: dict, segcount: dict,
                        geom: dict, goulots: list[dict],
                        out_html: Path) -> None:
    """Page HTML autonome : tableau récapitulatif + barres + top-10 goulots."""
    # Pas de folium ici, juste du HTML statique bilingue
    classes_codes = [sc.code for sc in SPEED_CLASSES]

    def bar(km_by_class: dict[str, float], total: float) -> str:
        # Conteneur flex : les bandes se partagent la largeur proportionnellement
        # (flex-grow = % de la classe, flex-basis 0) et restent TOUJOURS sur une
        # seule ligne, même si l'écran est étroit (flex ne renvoie pas à la ligne).
        if total <= 0:
            return ""
        parts = []
        for sc in SPEED_CLASSES:
            km = km_by_class.get(sc.code, 0.0)
            pct = 100 * km / total
            if pct > 0:
                parts.append(
                    f"<span title='{sc.code} {km:.1f} km ({pct:.1f}%)' "
                    f"style='flex:{pct:.4f} 0 0;background:{sc.color}'></span>")
        return ("<span style='display:flex;width:100%;height:18px;"
                "border-radius:2px;overflow:hidden'>" + "".join(parts) + "</span>")

    html_rows = []
    for tronc_id, tronc_obj in CORRIDOR_SEGMENTS.items():
        html_rows.append(f"<h3>{tronc_obj.label_fr} <span style='color:#888;font-weight:normal'>/ {tronc_obj.label_en}</span></h3>")
        html_rows.append("<table style='border-collapse:collapse;width:100%;margin-bottom:1em'>")
        html_rows.append(
            "<tr style='background:#eee'><th style='padding:4px;text-align:left'>Scénario</th>"
            "<th>Total km</th><th style='width:50%'>Répartition par classe</th>"
            + "".join(f"<th>{c}</th>" for c in classes_codes)
            + "<th>HSR-utile ≥ 200 km/h<br>"
              "<span style='font-weight:normal;color:#666'>km (fourchette) · "
              "% du tronçon</span></th>"
            + "<th>Part des segments ≥ 200 km/h<br>"
              "<span style='font-weight:normal;color:#666'>en nombre de "
              "segments, non pondérée par la longueur</span></th></tr>"
        )
        for sid in ("S1", "S2", "S3"):
            tot = sum(dist[tronc_id][sid].values())
            km_hsr = sum(dist[tronc_id][sid].get(c, 0.0) for c in HSR_CLASSES)
            pct_hsr = 100 * km_hsr / tot if tot > 0 else 0
            km_hsr_hi = sum(dist_p50[tronc_id][sid].get(c, 0.0) for c in HSR_CLASSES)
            pct_hsr_hi = 100 * km_hsr_hi / tot if tot > 0 else 0
            scn = segcount[tronc_id][sid]
            pct_seg = 100 * scn["hsr"] / scn["tot"] if scn["tot"] else 0
            html_rows.append("<tr style='border-bottom:1px solid #ddd'>")
            _s = SCENARIOS[sid]
            html_rows.append(
                f"<td style='padding:4px'><b>{sid}</b> — {_s.name_fr}<br>"
                f"<small style='color:#777'>dévers {_s.cant_mm} mm "
                f"({_s.cant_in:.1f}″) · insuff. {_s.cant_def_mm} mm "
                f"({_s.cant_def_in:.1f}″)</small></td>")
            html_rows.append(f"<td style='text-align:right'>{tot:.1f}</td>")
            html_rows.append(f"<td>{bar(dist[tronc_id][sid], tot)}</td>")
            for c in classes_codes:
                km = dist[tronc_id][sid].get(c, 0.0)
                html_rows.append(f"<td style='text-align:right'>{km:.1f}</td>")
            html_rows.append(
                f"<td style='text-align:right;font-weight:bold;color:#006400'>"
                f"{km_hsr:.0f}–{km_hsr_hi:.0f} km<br>{pct_hsr:.0f}–{pct_hsr_hi:.0f}%</td>")
            html_rows.append(f"<td style='text-align:right'>{pct_seg:.0f}%</td>")
            html_rows.append("</tr>")
        html_rows.append("</table>")

    # --- Annexe diagnostic géométrique (NON opérationnel) ---
    html_rows.append(
        "<h2>Annexe — diagnostic géométrique "
        "<span style='color:#b00'>(NE PAS citer comme vitesse opérationnelle)</span></h2>")
    html_rows.append(
        "<p style='background:#fff3cd;border:1px solid #e0c060;padding:8px;"
        "font-size:0.9em'>Ces km/h sont des <b>plafonds de courbure</b> : ils "
        "supposent chaque segment parcouru à sa limite géométrique (jusqu'à "
        "360 sur les tangentes) et <b>n'incluent pas</b> signalisation, "
        "passages à niveau, partage fret, électrification, accél./décél. → la "
        "vitesse opérationnelle réelle est <b>inférieure</b>. L'écart entre ce "
        "plafond et la vitesse réelle de VIA mesure précisément que la "
        "contrainte mordante n'est PAS la courbure, mais les "
        "systèmes/passages.</p>")
    html_rows.append("<table style='border-collapse:collapse;font-size:12px'>")
    html_rows.append(
        "<tr style='background:#eee'><th style='padding:4px'>Tronçon</th>"
        "<th>Scén.</th><th>plafond géom.<br>km/h (mph)</th>"
        "<th>vmax méd. (pond. L)<br>km/h (mph)</th></tr>")
    for tid in CORRIDOR_SEGMENTS:
        for sid in ("S1", "S2", "S3"):
            gg = geom[tid][sid]
            html_rows.append(
                f"<tr><td style='padding:4px'>{tid}</td><td>{sid}</td>"
                f"<td style='text-align:right'>{gg['plafond_kmh']:.0f} "
                f"({kmh_to_mph(gg['plafond_kmh']):.0f})</td>"
                f"<td style='text-align:right'>{gg['vmax_medL_kmh']:.0f} "
                f"({kmh_to_mph(gg['vmax_medL_kmh']):.0f})</td></tr>")
    html_rows.append("</table>")
    # Goulots top-10
    html_rows.append(f"<h2>Goulots structurels ({len(goulots)} site(s), scénario S3) / Structural bottlenecks</h2>")
    html_rows.append("<p style='color:#555;font-size:0.9em'>Un goulot structurel est une section courte (≤ 5 km), soutenue sur ≥ 150 m, qui reste en classe F (&lt; 100 km/h) même dans le scénario le plus permissif (S3, HSR pendulaire) et descend d'au moins deux classes sous son voisinage : c'est la seule catégorie qu'aucun scénario ne récupère, donc le seul candidat à une rectification de tracé. Les sections classées D ou E en S3 (100–199 km/h) ne sont pas des goulots à reconstruire mais des cibles de modernisation ; leur volume figure dans le tableau de répartition ci-dessus.</p>")
    if not goulots:
        html_rows.append("<p>Aucun goulot structurel (classe F soutenue en S3) détecté.</p>")
    else:
        html_rows.append("<table style='border-collapse:collapse;width:100%'>")
        html_rows.append("<tr style='background:#eee'><th>#</th><th>Tronçon</th><th>km début</th><th>Longueur (m)</th><th>Degré de courbure (max)</th><th>R min (m)</th><th>vmax S3</th><th>Classe S3</th><th>Classe voisinage</th><th>Entre gares</th></tr>")
        for i, g in enumerate(goulots):   # liste COMPLÈTE (déf resserrée → peu nombreux)
            html_rows.append(
                f"<tr style='border-bottom:1px solid #ddd'>"
                f"<td>{i+1}</td><td>{g['troncon_id']}</td><td>{g['km_debut']:.1f}</td>"
                f"<td>{g['longueur_m']:.0f}</td>"
                f"<td style='text-align:right'>{fmt_dc(g['R_min_m'])}</td>"
                f"<td style='text-align:right'>{g['R_min_m']}</td>"
                f"<td>{g['vmax_S3_kmh']:.0f}</td><td>{g['classe_S3']}</td>"
                f"<td>{g['classe_dominante_voisinage']}</td>"
                f"<td>{g['gare_amont']} → {g['gare_aval']}</td></tr>"
            )
        html_rows.append("</table>")

    # Classes legend
    legend = "<h2>Classes de vitesse / Speed classes</h2><ul>"
    for sc in SPEED_CLASSES:
        legend += f"<li><span style='display:inline-block;width:16px;height:16px;background:{sc.color};vertical-align:middle'></span> <b>{sc.code}</b> : {sc.name_fr} / {sc.name_en} ({int(sc.vmin_kmh)}+ km/h)</li>"
    legend += "</ul>"

    html = f"""<!DOCTYPE html>
<html lang='fr'><head><meta charset='utf-8'>
<title>Synthèse courbatures par tronçon — TGV Canada</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Helvetica, sans-serif; padding: 20px; max-width: 1100px; margin: auto; }}
  h1 {{ color: #003366; }}
  table {{ font-size: 13px; }}
  th, td {{ padding: 4px 6px; }}
  th {{ font-weight: 600; text-align: center; }}
</style>
</head><body>
<h1>Synthèse courbatures — Corridor VIA existant</h1>
<h1 style='font-weight:normal;color:#666;font-size:1em'>Curvature synthesis — Existing VIA corridor</h1>
<p>Phase 1 — analyse stratégique préliminaire. Quantification km par classe de vitesse, par tronçon et par scénario.</p>
<p style='font-size:0.85em;color:#666'>La <b>fourchette</b> HSR-utile va de la borne basse (classement prudent retenu pour la publication) à la borne haute (recalcul sur le rayon médian de chaque section) : elle rend visible la sensibilité du résultat aux courbes d'entrée de gare, sans la masquer derrière un chiffre unique.</p>
{''.join(html_rows)}
{legend}
<hr>
<p style='font-size:0.85em;color:#888'>Généré automatiquement depuis <code>segments.geojson</code> par <code>06_synthese_troncon.py</code>. Sources normatives : Transport Canada / CN MR 1305-0 (S1), CN MR 1305-0 (S2 LRC + dévers max 5 po) ; S3 = insuffisance 270 mm hors précédent NA (réf. EN 13803). Voir le rapport pour le détail.</p>
</body></html>"""
    out_html.write_text(html, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    if not SEGMENTS_GEOJSON.exists():
        sys.exit(f"Segments introuvable : {SEGMENTS_GEOJSON} — lancer 05_segment_and_classify.py d'abord.")

    print("=== Étape 6 — Synthèse par tronçon + goulots ===")
    geojson = json.loads(SEGMENTS_GEOJSON.read_text(encoding="utf-8"))
    segments = [f for f in geojson["features"] if f["properties"]["kind"] == "homog_segment"]
    print(f"  {len(segments)} segments à agréger")

    dist = compute_distribution(segments)
    dist_p50, segcount, geom = compute_extra_metrics(segments)
    goulots = detect_bottlenecks(segments)

    out_csv = DELIVERABLES / "synthese_troncon.csv"
    write_synthese_csv(dist, dist_p50, segcount, geom, out_csv)
    out_goul = DELIVERABLES / "goulots_detranglement.csv"
    write_goulots_csv(goulots, out_goul)
    out_html = DELIVERABLES / "synthese_par_troncon.html"
    write_synthese_html(dist, dist_p50, segcount, geom, goulots, out_html)
    out_params = DELIVERABLES / "scenarios_parametres.csv"
    write_scenarios_params_csv(out_params)

    print(f"\nÉcrit :")
    print(f"  {out_csv.name}")
    print(f"  {out_goul.name}  ({len(goulots)} goulots détectés)")
    print(f"  {out_html.name}")
    print(f"  {out_params.name}")

    # Quick summary à l'écran
    print(f"\nRépartition par tronçon × scénario (km à chaque classe) :")
    print(f"{'Tronçon':<8} {'Scén':<4}  ", end="")
    for sc in SPEED_CLASSES:
        print(f"{sc.code:>8}", end="")
    print(f"  {'HSR ≥200':>10}")
    for tronc in CORRIDOR_SEGMENTS:
        for sid in ("S1", "S2", "S3"):
            print(f"  {tronc:<6} {sid}    ", end="")
            tot = sum(dist[tronc][sid].values())
            for sc in SPEED_CLASSES:
                km = dist[tronc][sid].get(sc.code, 0.0)
                print(f"{km:>7.1f} ", end="")
            km_hsr = sum(dist[tronc][sid].get(c, 0.0) for c in HSR_CLASSES)
            pct = 100 * km_hsr / tot if tot > 0 else 0
            print(f"  {km_hsr:>5.0f} ({pct:>3.0f}%)")
        print()


if __name__ == "__main__":
    main()

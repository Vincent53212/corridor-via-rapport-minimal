#!/usr/bin/env python3
"""Sous-livrable (variante) — « Sections à vitesse commerciale estimée < 160 km/h en S3 ».

Même esprit que `12_sections_a_rectifier_pdf.py` (tracé inchangé ; vitesse
géométrique + commerciale estimée), mais le CRITÈRE est la VITESSE COMMERCIALE :
on liste les sections dont la vitesse commerciale estimée (0,75 × géométrique)
reste sous 160 km/h en S3 — équivaut à un plafond géométrique < 160/0,75 ≈ 213 km/h.

Ce seuil (213 géom.) n'existe pas dans les CSV pré-agrégés (160/200/250/300) :
on reconstruit donc les sections contiguës DIRECTEMENT depuis `segments.geojson`
(même règle de regroupement que l'étape 11), filtrées sur la vitesse commerciale.

Sortie : livrables/sections_vcom_sous_160kmh_S3.html (+ PDF via Chrome headless).
"""
from __future__ import annotations
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEGMENTS = ROOT / "intermediaires" / "segments.geojson"
OUT = ROOT / "livrables" / "liste_résumé_cutoff_160kmhCOM_S3.html"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import degre_courbure, kmh_to_mph
from scenarios import SCENARIOS

DATE = "2026-07"
COEFF_S3 = SCENARIOS["S3"].coeff                          # source unique scenarios.py
FACTEUR_COM = 0.75                                         # médiane 0,70–0,80 (Annexe E)
VCOM_CUTOFF = 160.0                                        # critère : vitesse commerciale
GEO_EQUIV = VCOM_CUTOFF / FACTEUR_COM                      # ≈ 213,3 km/h géométrique
R_CUTOFF = (GEO_EQUIV / COEFF_S3) ** 2                     # ≈ 1491 m
R_SEVERE = (100 / COEFF_S3) ** 2                           # 328 m → géom. < 100 km/h

TRONCONS = [
    ("MTL-QC", "Montréal → Québec", 269.42),
    ("MTL-Ott", "Montréal → Ottawa", 184.69),
    ("Ott-TO", "Ottawa → Toronto", 442.27),
    ("MTL-TO", "Montréal → Toronto", 535.86),
]
TRACE_TOTAL = sum(t[2] for t in TRONCONS)


def fr(x, dec=0):
    return f"{x:,.{dec}f}".replace(",", " ").replace(".", ",")


def vgeo(R):
    return COEFF_S3 * math.sqrt(R)


def build_sections():
    """Reconstruit les sections contiguës V.commerciale < 160 depuis segments.geojson.

    Un segment qualifie si 0,75 × (5,52·√R_classif) < 160, i.e. R_classif < R_CUTOFF.
    Retourne {troncon: [section, ...]} avec section = dict (km_debut, km_fin,
    longueur_km, R_min, gare_amont, gare_aval).
    """
    gj = json.loads(SEGMENTS.read_text(encoding="utf-8"))
    by_tr = defaultdict(list)
    for f in gj["features"]:
        by_tr[f["properties"]["troncon_id"]].append(f["properties"])
    out = defaultdict(list)
    for tr, segs in by_tr.items():
        segs.sort(key=lambda p: p["km_debut"])
        run = []
        def flush():
            if not run:
                return
            rmin = min(p["R_classif_m"] for p in run)
            out[tr].append({
                "km_debut": run[0]["km_debut"],
                "km_fin": run[-1]["km_fin"],
                "longueur_km": sum(p["longueur_m"] for p in run) / 1000.0,
                "R_min": rmin,
                "gare_amont": run[0].get("gare_amont", ""),
                "gare_aval": run[-1].get("gare_aval", ""),
            })
        for p in segs:
            R = p.get("R_classif_m")
            qualifie = R is not None and R < R_CUTOFF
            if qualifie:
                run.append(p)
            else:
                flush()
                run = []
        flush()
    return out


def table_for(tr_id, by):
    rows = by.get(tr_id, [])
    tot_km = sum(r["longueur_km"] for r in rows)
    body = []
    for i, r in enumerate(rows, 1):
        R = r["R_min"]
        vg = vgeo(R)
        vc = FACTEUR_COM * vg
        severe = R < R_SEVERE
        tr_style = " style='background:#fbeaea'" if severe else ""
        gares = f"{r['gare_amont']} → {r['gare_aval']}".strip(" →")
        flag = (" <span style='color:#8b0000;font-size:0.85em'>⚠ section la plus "
                "contrainte</span>") if severe else ""
        vg_txt = f"{fr(vg)} ({fr(kmh_to_mph(vg))} mph)"
        vg_cell = f"<b style='color:#8b0000'>{vg_txt}</b>" if severe else vg_txt
        vc_txt = f"{fr(vc)} ({fr(kmh_to_mph(vc))} mph)"
        dc_txt = fr(degre_courbure(R), 2) + "°"
        dc_cell = f"<b style='color:#8b0000'>{dc_txt}</b>" if severe else dc_txt
        body.append(
            f"<tr{tr_style}>"
            f"<td style='text-align:right;color:#888'>{i}</td>"
            f"<td style='text-align:right'>{fr(r['km_debut'],2)}</td>"
            f"<td style='text-align:right'>{fr(r['km_fin'],2)}</td>"
            f"<td style='text-align:right'>{fr(r['longueur_km'],2)}</td>"
            f"<td style='text-align:right'>{dc_cell}</td>"
            f"<td style='text-align:right'>{fr(R)}</td>"
            f"<td style='text-align:right'>{vg_cell}</td>"
            f"<td style='text-align:right'>{vc_txt}</td>"
            f"<td>{gares}{flag}</td>"
            f"</tr>"
        )
    pct = 100 * tot_km / next(t[2] for t in TRONCONS if t[0] == tr_id)
    nom = next(t[1] for t in TRONCONS if t[0] == tr_id)
    head = (
        "<thead><tr style='background:#003366;color:#fff'>"
        "<th style='text-align:right'>#</th>"
        "<th style='text-align:right'>km début</th>"
        "<th style='text-align:right'>km fin</th>"
        "<th style='text-align:right'>Longueur<br>(km)</th>"
        "<th style='text-align:right'>Degré de courbure<br>(max, °/100 pi)</th>"
        "<th style='text-align:right'>Rayon courbe<br>la plus serrée (m)</th>"
        "<th style='text-align:right'>Vitesse<br>géométrique (km/h · mph)</th>"
        "<th style='text-align:right'>Vitesse commerciale<br>estimée (km/h · mph)</th>"
        "<th style='text-align:left'>Entre gares</th>"
        "</tr></thead>"
    )
    return (
        f"<section class='troncon'>"
        f"<h3>{tr_id} <span style='color:#888;font-weight:normal'>· {nom}</span></h3>"
        f"<p class='soustitre'>{len(rows)} sections · <b>{fr(tot_km,1)} km</b> · "
        f"{fr(pct,1)} % du tronçon · vitesse commerciale estimée &lt; 160 km/h en S3</p>"
        f"<table>{head}<tbody>{''.join(body)}</tbody></table>"
        f"</section>"
    ), len(rows), tot_km


def main():
    by = build_sections()
    tables, n_tot, km_tot, recap = [], 0, 0.0, []
    for tr_id, nom, L in TRONCONS:
        h, n, km = table_for(tr_id, by)
        tables.append(h)
        n_tot += n
        km_tot += km
        recap.append((tr_id, nom, n, km, 100 * km / L))
    pct_tot = 100 * km_tot / TRACE_TOTAL

    recap_rows = "".join(
        f"<tr><td>{tid}</td><td style='color:#666'>{nom}</td>"
        f"<td style='text-align:right'>{n}</td>"
        f"<td style='text-align:right'>{fr(km,1)}</td>"
        f"<td style='text-align:right'>{fr(p,1)} %</td></tr>"
        for tid, nom, n, km, p in recap
    )
    recap_table = (
        "<table class='recap'><thead><tr style='background:#003366;color:#fff'>"
        "<th style='text-align:left'>Tronçon</th><th style='text-align:left'></th>"
        "<th style='text-align:right'>Sections</th>"
        "<th style='text-align:right'>km (V.com &lt; 160)</th>"
        "<th style='text-align:right'>% du tronçon</th></tr></thead><tbody>"
        f"{recap_rows}"
        f"<tr style='font-weight:bold;border-top:2px solid #003366'>"
        f"<td>Corridor</td><td style='color:#666'>somme par trajet</td>"
        f"<td style='text-align:right'>{n_tot}</td>"
        f"<td style='text-align:right'>{fr(km_tot,1)}</td>"
        f"<td style='text-align:right'>{fr(pct_tot,1)} %</td></tr>"
        "</tbody></table>"
    )

    css = """
    @page { size: A4 landscape; margin: 14mm 14mm 15mm 14mm; }
    :root { --bleu:#003366; --encre:#1a1a2e; --gris:#5a6472; }
    * { box-sizing: border-box; }
    body { font-family:'Segoe UI',Helvetica,Arial,sans-serif; color:var(--encre);
           margin:0; font-size:12px; line-height:1.5;
           -webkit-print-color-adjust:exact; print-color-adjust:exact; }
    h1 { color:var(--bleu); font-size:1.7em; margin:0 0 2px; }
    h1.sub { font-weight:normal; color:#777; font-size:.98em; margin:0 0 12px; }
    h2 { color:var(--bleu); font-size:1.12em; border-bottom:2px solid var(--bleu);
         padding-bottom:3px; margin:16px 0 8px; }
    h3 { color:var(--bleu); font-size:1.03em; margin:13px 0 2px; }
    p { margin:6px 0; }
    .soustitre { color:var(--gris); font-size:.9em; margin:0 0 6px; }
    .resume { background:#eef3fa; border:1px solid #b9cae3; border-left:5px solid var(--bleu);
              border-radius:4px; padding:10px 14px; margin:10px 0; font-size:1.02em; }
    .resume b.big { color:var(--bleu); font-size:1.25em; }
    .intro { background:#f4f7fb; border:1px solid #d7e0ec; border-radius:4px;
             padding:9px 14px; margin:10px 0; }
    .intro p { margin:7px 0; }
    .avert { background:#fff3cd; border:1px solid #e0c060; border-radius:4px;
             padding:8px 12px; font-size:.9em; margin:10px 0; }
    table { border-collapse:collapse; width:100%; font-size:11px; margin:4px 0 2px; }
    table.recap { width:auto; min-width:62%; font-size:12px; }
    th, td { padding:3px 8px; border-bottom:1px solid #e2e2e2; }
    th { font-weight:600; vertical-align:bottom; }
    tbody tr:nth-child(even) { background:#f7f9fc; }
    .legende { font-size:.86em; color:var(--gris); margin:2px 0 4px; }
    @media print {
      thead { display:table-header-group; }
      tr { page-break-inside:avoid; }
      h2, h3 { page-break-after:avoid; }
      .troncon { page-break-inside:auto; }
      .intro, .avert, .resume, .recap { page-break-inside:avoid; }
    }
    """

    resume = f"""
    <div class='resume'><b class='big'>{n_tot} sections · {fr(km_tot,0)} km ·
    {fr(pct_tot,1)} % du corridor</b> ont une <b>vitesse commerciale estimée
    inférieure à 160 km/h</b> dans le scénario S3 (modernisation maximale). Ces
    sections <b>conservent le tracé existant</b> ; le tableau donne, pour chacune,
    sa <b>vitesse géométrique</b> (plafond imposé par la courbe) et sa <b>vitesse
    commerciale estimée</b> — base pour l'estimation des temps de parcours en S3
    sans modification du tracé.</div>
    """

    intro = f"""
    <div class='intro'>
      <p><b>Scénario S3.</b> Modernisation maximale de la voie existante, <b>sans
      refaire le tracé</b> : dévers relevé au maximum standard CN (5 po = 127 mm,
      MR 1305-0) + train <b>pendulaire type LRC</b>. C'est l'hypothèse la plus
      permissive de l'étude.</p>

      <p><b>Vitesse géométrique vs vitesse commerciale.</b> La <b>vitesse
      géométrique</b> est le plafond physique d'une courbe (équilibre dévers /
      accélération latérale) — pas la vitesse réellement tenue. La <b>vitesse
      commerciale</b> est <b>inférieure</b> (accélérations, freinages, arrêts,
      marges). On l'estime par un <b>facteur de transposition documenté</b> : le
      rapport moyenne/pointe de lignes à grande vitesse réellement modernisées —
      <b>0,70–0,80</b> (médiane <b>0,75</b> retenue ; sources Annexe E :
      Paris–Lyon, Nozomi, Madrid–Barcelone). Donc <b>V. commerciale ≈ 0,75 ×
      V. géométrique</b> ; <b>estimation indicative</b>, pas une simulation de
      marche de train.</p>

      <p><b>Lecture.</b> Chaque ligne est une <b>section continue</b> dont la
      <b>vitesse commerciale estimée reste &lt; 160 km/h</b> en S3 (soit un
      plafond géométrique &lt; {fr(GEO_EQUIV,0)} km/h), tracé inchangé. Total :
      <b>{fr(km_tot,0)} km ({fr(pct_tot,1)} % du corridor)</b>. Les sections en
      <b>rouge</b> sont les plus contraintes (vitesse géométrique &lt; 100 km/h).</p>
    </div>

    <p class='legende'><b>Degré de courbure (max) :</b> netteté de la courbe la
    plus contraignante de la section, exprimée selon le <b>standard ferroviaire
    nord-américain</b> — angle au centre sous-tendu par une corde de 100 pieds
    (D = 2·arcsin(15,24 / R), AREMA). C'est une mesure <b>inverse du rayon</b> :
    plus le degré est élevé, plus la courbe est serrée. Le <b>rayon (m)</b>
    correspondant (mesuré de façon robuste, minimum d'une médiane glissante
    ~150 m) est donné en regard ; il fixe la vitesse géométrique
    (V<sub>géo</sub> = {COEFF_S3:.2f} × √R, scénario S3). <i>Autres mesures de
    rayon disponibles sur demande.</i> &nbsp;·&nbsp; <b>Vitesse commerciale
    estimée</b> = 0,75 × vitesse géométrique (facteur 0,70–0,80, Annexe E).</p>

    <div class='avert'><b>Périmètre.</b> Étude de <b>courbure uniquement</b>
    (Phase 1), préliminaire / stratégique. La <b>vitesse géométrique</b> est un
    plafond — <b>à ne pas citer comme vitesse opérationnelle</b>. La <b>vitesse
    commerciale</b> est une <b>estimation indicative</b> par facteur de
    transposition (rapport moyenne/pointe de HSR modernisés), pas une simulation
    de marche de train. Ne sont pas évalués : ponts, tunnels, passages à niveau,
    électrification, signalisation, génie civil. Tronçons analysés comme
    <b>4 trajets origine–destination</b> partageant par endroits la même voie
    (le total km est la somme par trajet). Document destiné à alimenter
    l'estimation ultérieure des <b>temps de parcours en S3</b> (tracé inchangé).</div>
    """

    html = f"""<!DOCTYPE html>
<html lang='fr'><head><meta charset='utf-8'>
<title>Sections à vitesse commerciale estimée &lt; 160 km/h en S3 — TGV Canada Phase 1</title>
<style>{css}</style></head><body>
<h1>Sections à vitesse commerciale estimée inférieure à 160 km/h en S3</h1>
<h1 class='sub'>Corridor VIA existant · scénario S3 (modernisation maximale :
voie ré-inclinée + train pendulaire) · tracé inchangé ·
vitesse géométrique et vitesse commerciale estimée</h1>
{resume}
{intro}
<h2>Synthèse par tronçon</h2>
{recap_table}
<h2>Détail des sections, par tronçon</h2>
{''.join(tables)}
<hr style='margin-top:18px;border:none;border-top:1px solid #ddd'>
<p style='font-size:0.82em;color:#888'>Source : sections dont la vitesse
commerciale estimée &lt; 160 km/h en S3 (= plafond géométrique &lt; {fr(GEO_EQUIV,0)}
km/h), reconstruites depuis la géométrie classée <code>segments.geojson</code>.
Vitesse géométrique : V = {COEFF_S3:.2f}·√R (CN MR 1305-0, pendulaire type LRC).
Vitesse commerciale : facteur de transposition 0,70–0,80 (Annexe E). Détail
méthodologique : le rapport du projet.</p>
</body></html>"""

    OUT.write_text(html, encoding="utf-8")
    print(f"Écrit {OUT}")
    print(f"  {n_tot} sections · {km_tot:.1f} km · {pct_tot:.1f} % du corridor "
          f"· critère V.com < {VCOM_CUTOFF:.0f} (géom < {GEO_EQUIV:.0f}, R < {R_CUTOFF:.0f} m)")


if __name__ == "__main__":
    main()

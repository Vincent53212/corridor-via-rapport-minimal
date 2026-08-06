#!/usr/bin/env python3
"""Sous-livrable — « Sections à plafond géométrique < 200 km/h en S3 ».

Reframe (2026-06-15) : ce n'est PLUS un document « km à rectifier ». Le tracé
est CONSERVÉ tel quel ; on documente, pour chaque section qui reste sous
200 km/h en S3, sa vitesse géométrique (plafond imposé par la courbe). But :
alimenter le moteur T_base (script 21) sans modification du tracé.
NB audit 2026-08-06 : la colonne « vitesse commerciale estimée » (facteur de
transposition 0,75) est RETIRÉE — interdit du plan v3, remplacée par T_base.

Lit le CSV DÉJÀ VALIDÉ `livrables/cible_sites_a_rectifier.csv` (étape 11), filtré
scénario S3 × seuil 200 km/h (= sections dont le plafond géométrique S3 < 200).
AUCUN recalcul de géométrie ; vitesses dérivées par la formule documentée.

Sortie : livrables/sections_a_rectifier_200kmh_S3.html (+ PDF via Chrome headless).
"""
from __future__ import annotations
import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "livrables" / "cible_sites_a_rectifier.csv"
OUT = ROOT / "livrables" / "liste_résumé_cutoff_200kmhGEO_S3.html"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import degre_courbure, kmh_to_mph
from scenarios import SCENARIOS

SCENARIO = "S3"
SEUIL = "200"
DATE = "2026-07"

# Coefficient S3 — source unique scenarios.py (nomenclature 2026-08 : h=127, CD=270)
COEFF_S3 = SCENARIOS["S3"].coeff
R_SEVERE = (100 / COEFF_S3) ** 2              # sous ce rayon, < 100 km/h en S3

TRONCONS = [
    ("MTL-QC", "Montréal → Québec", 269.42),
    ("MTL-Ott", "Montréal → Ottawa", 184.69),
    ("Ott-TO", "Ottawa → Toronto", 442.27),
    ("MTL-TO", "Montréal → Toronto", 535.86),
]
TRACE_TOTAL = sum(t[2] for t in TRONCONS)     # 1432.24 km (somme par trajet)


def fr(x, dec=0):
    return f"{x:,.{dec}f}".replace(",", " ").replace(".", ",")


def vgeo(R):
    return COEFF_S3 * math.sqrt(R)


def load():
    by = defaultdict(list)
    with open(SRC, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r["scenario"] == SCENARIO and r["vitesse_cible_kmh"] == SEUIL:
                by[r["troncon"]].append(r)
    for k in by:
        by[k].sort(key=lambda r: float(r["km_debut"]))
    return by


def table_for(tr_id, by):
    rows = by.get(tr_id, [])
    tot_km = sum(float(r["longueur_km"]) for r in rows)
    body = []
    for i, r in enumerate(rows, 1):
        R = float(r["R_actuel_min_m"]) if r["R_actuel_min_m"] else None
        vg = vgeo(R) if R else None
        severe = R is not None and R < R_SEVERE
        tr_style = " style='background:#fbeaea'" if severe else ""
        gares = f"{r['gare_amont']} → {r['gare_aval']}".strip(" →")
        flag = (" <span style='color:#8b0000;font-size:0.85em'>⚠ section la plus "
                "contrainte</span>") if severe else ""
        vg_txt = f"{fr(vg)} ({fr(kmh_to_mph(vg))} mph)" if vg else "—"
        vg_cell = f"<b style='color:#8b0000'>{vg_txt}</b>" if (severe and vg) else vg_txt
        dc_txt = (fr(degre_courbure(R), 2) + "°") if R else "—"
        dc_cell = f"<b style='color:#8b0000'>{dc_txt}</b>" if (severe and R) else dc_txt
        body.append(
            f"<tr{tr_style}>"
            f"<td style='text-align:right;color:#888'>{i}</td>"
            f"<td style='text-align:right'>{fr(float(r['km_debut']),2)}</td>"
            f"<td style='text-align:right'>{fr(float(r['km_fin']),2)}</td>"
            f"<td style='text-align:right'>{fr(float(r['longueur_km']),2)}</td>"
            f"<td style='text-align:right'>{dc_cell}</td>"
            f"<td style='text-align:right'>{fr(R) if R else '—'}</td>"
            f"<td style='text-align:right'>{vg_cell}</td>"
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
        "<th style='text-align:left'>Entre gares</th>"
        "</tr></thead>"
    )
    return (
        f"<section class='troncon'>"
        f"<h3>{tr_id} <span style='color:#888;font-weight:normal'>· {nom}</span></h3>"
        f"<p class='soustitre'>{len(rows)} sections · <b>{fr(tot_km,1)} km</b> · "
        f"{fr(pct,1)} % du tronçon · plafond géométrique &lt; 200 km/h en S3</p>"
        f"<table>{head}<tbody>{''.join(body)}</tbody></table>"
        f"</section>"
    ), len(rows), tot_km


def main():
    by = load()
    tables, n_tot, km_tot = [], 0, 0.0
    recap = []
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
        "<th style='text-align:right'>km &lt; 200 km/h</th>"
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
    {fr(pct_tot,1)} % du corridor</b> ont un <b>plafond géométrique inférieur à
    200 km/h</b> dans le scénario S3 (modernisation maximale). Ces sections
    <b>conservent le tracé existant</b> ; le tableau donne, pour chacune, sa
    <b>vitesse géométrique</b> (plafond imposé par la courbe). Les temps de
    parcours sont calculés par le moteur d'intégration du projet
    (<code>tbase_par_bande.csv</code>), sans facteur de transposition.</div>
    """

    intro = f"""
    <div class='intro'>
      <p><b>Scénario S3.</b> Le plus permissif de l'étude : dévers au maximum
      standard CN (5 po = 127 mm, MR 1305-0) + matériel <b>pendulaire moderne</b>
      (insuffisance de dévers 270 mm, hors précédent nord-américain, voie
      d'approbation par équipement RRTS Subpart C 4.3), <b>sans refaire le
      tracé</b>. Les sections ci-dessous restent sous 200 km/h <b>même en S3</b> :
      c'est la <b>géométrie du tracé</b> (le rayon de courbure) qui fixe leur
      plafond.</p>

      <p><b>Vitesse géométrique vs vitesse commerciale.</b> La <b>vitesse
      géométrique</b> est le plafond physique d'une courbe (équilibre dévers /
      accélération latérale), pas la vitesse réellement tenue. La <b>vitesse
      commerciale</b> (inférieure : plafonds réglementaires, blocs urbains,
      arrêts, marge) est calculée ailleurs dans le projet par un <b>moteur
      d'intégration</b> segment par segment (<code>tbase_par_bande.csv</code>),
      jamais par un facteur uniforme.</p>

      <p><b>Lecture.</b> Chaque ligne est une <b>section continue</b> dont le
      plafond géométrique reste &lt; 200 km/h en S3, tracé inchangé.
      Total : <b>{fr(km_tot,0)} km ({fr(pct_tot,1)} % du corridor)</b>. Les
      sections en <b>rouge</b> sont les plus contraintes (vitesse géométrique
      &lt; 100 km/h).</p>
    </div>

    <p class='legende'><b>Degré de courbure (max) :</b> netteté de la courbe la
    plus contraignante de la section, exprimée selon le <b>standard ferroviaire
    nord-américain</b> — angle au centre sous-tendu par une corde de 100 pieds
    (D = 2·arcsin(15,24 / R), AREMA). C'est une mesure <b>inverse du rayon</b> :
    plus le degré est élevé, plus la courbe est serrée. Le <b>rayon (m)</b>
    correspondant (mesuré de façon robuste, minimum d'une médiane glissante
    ~150 m) est donné en regard ; il fixe la vitesse géométrique
    (V<sub>géo</sub> = {COEFF_S3:.2f} × √R, scénario S3). <i>Autres mesures de
    rayon disponibles sur demande.</i></p>

    <div class='avert'><b>Périmètre.</b> Étude de <b>courbure uniquement</b>
    (Phase 1), préliminaire / stratégique. La <b>vitesse géométrique</b> est un
    plafond — <b>à ne pas citer comme vitesse opérationnelle</b>. Les temps de
    parcours et vitesses commerciales relèvent du moteur d'intégration du projet,
    pas d'un facteur uniforme. Ne sont pas évalués ici : ponts, tunnels, passages à niveau,
    électrification, signalisation, génie civil. Tronçons analysés comme
    <b>4 trajets origine–destination</b> partageant par endroits la même voie
    (le total km est la somme par trajet). Document destiné à alimenter
    l'estimation ultérieure des <b>temps de parcours en S3</b> (tracé inchangé).</div>
    """

    html = f"""<!DOCTYPE html>
<html lang='fr'><head><meta charset='utf-8'>
<title>Sections à plafond géométrique &lt; 200 km/h en S3 — TGV Canada Phase 1</title>
<style>{css}</style></head><body>
<h1>Sections à plafond géométrique inférieur à 200 km/h en S3</h1>
<h1 class='sub'>Corridor VIA existant · scénario S3 (voie ré-inclinée +
pendulaire moderne, insuffisance 270 mm) · tracé inchangé ·
vitesse géométrique (plafond)</h1>
{resume}
{intro}
<h2>Synthèse par tronçon</h2>
{recap_table}
<h2>Détail des sections, par tronçon</h2>
{''.join(tables)}
<hr style='margin-top:18px;border:none;border-top:1px solid #ddd'>
<p style='font-size:0.82em;color:#888'>Source : sections à plafond géométrique
&lt; 200 km/h en S3, dérivées de la géométrie classée <code>segments.geojson</code>
(<code>cible_sites_a_rectifier.csv</code>, S3). Vitesse géométrique :
V = {COEFF_S3:.2f}·√R (dévers CN MR 1305-0, insuffisance 270 mm). Détail
méthodologique : le rapport du projet.</p>
</body></html>"""

    OUT.write_text(html, encoding="utf-8")
    print(f"Écrit {OUT}")
    print(f"  {n_tot} sections · {km_tot:.1f} km · {pct_tot:.1f} % du corridor")


if __name__ == "__main__":
    main()

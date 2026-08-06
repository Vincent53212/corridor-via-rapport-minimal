#!/usr/bin/env python3
"""Étape 19 — Visualiseur HTML standalone des livrables.

Produit `livrables/visualiseur.html` : un SEUL fichier autonome (hors-ligne,
ouvrable par double-clic, sans CDN ni serveur) qui embarque toutes les tables
de livrables en JSON et offre tri + filtres par colonne + filtres-presets
(p.ex. « toutes les courbes < 150 km/h de vitesse commerciale en S3 »).

« Se met à jour quand on rechange les scripts » : c'est un ÉTAGE DE PIPELINE.
Relancer ce script ré-embarque les données courantes des CSV. (Un fichier
file:// ne peut pas lire les CSV voisins pour des raisons de sécurité
navigateur → on embarque les données à la génération.)

Dépendances : stdlib `csv`/`json`/`datetime` (indépendant du venv géo).
"""
from __future__ import annotations
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import DELIVERABLES, COMMERCIAL_FACTOR
from scenarios import SCENARIOS

DUAL_HEADER = {"segments_courbature.csv"}
NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")

# Libellés conviviaux + ordre d'affichage.
LABELS = {
    "scenarios_parametres.csv": "Paramètres des scénarios",
    "segments_courbature.csv": "Segments (courbure)",
    "synthese_troncon.csv": "Synthèse par tronçon",
    "cible_km_a_rectifier.csv": "Cibles — km à rectifier",
    "cible_sites_a_rectifier.csv": "Cibles — sites détaillés",
    "goulots_detranglement.csv": "Goulots structurels",
    "facteur_transposition.csv": "Facteur de transposition",
    "voies_par_troncon.csv": "Voies (doublement) par tronçon",
    "km_a_doubler.csv": "Voies — km à doubler",
}
ORDER = list(LABELS.keys())

# Filtres-presets par dataset : chaque preset = {label, conds:[{col, op, val}]}.
# `col` = sous-chaîne cherchée dans l'en-tête (insensible à la casse) ;
# `op` ∈ {<, <=, >, >=, ==, contains}.
PRESETS = {
    "segments_courbature.csv": [
        {"label": "Commercial S3 < 150 km/h", "conds": [{"col": "vcom_s3", "op": "<", "val": 150}]},
        {"label": "Commercial S2 < 150 km/h", "conds": [{"col": "vcom_s2", "op": "<", "val": 150}]},
        {"label": "Plafond S3 < 200 km/h", "conds": [{"col": "vmax_s3_kmh", "op": "<", "val": 200}]},
        {"label": "Plafond S3 ≥ 300 km/h", "conds": [{"col": "vmax_s3_kmh", "op": ">=", "val": 300}]},
        {"label": "Classe S3 = F (sévère)", "conds": [{"col": "classe_s3", "op": "==", "val": "F"}]},
    ],
    "cible_km_a_rectifier.csv": [
        {"label": "S3 seulement", "conds": [{"col": "scenario", "op": "==", "val": "S3"}]},
        {"label": "Cible 200 km/h", "conds": [{"col": "vitesse_cible_kmh", "op": "==", "val": 200}]},
        {"label": "S3 · cible 200 km/h", "conds": [
            {"col": "scenario", "op": "==", "val": "S3"},
            {"col": "vitesse_cible_kmh", "op": "==", "val": 200}]},
    ],
    "cible_sites_a_rectifier.csv": [
        {"label": "S3 · cible 200 km/h", "conds": [
            {"col": "scenario", "op": "==", "val": "S3"},
            {"col": "vitesse_cible_kmh", "op": "==", "val": 200}]},
    ],
}


def read_table(path: Path) -> tuple[list[str], list[list]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f, delimiter=";"))
    if not rows:
        return [], []
    if path.name in DUAL_HEADER and len(rows) >= 2:
        header = [f"{fr} / {en}" for fr, en in zip(rows[0], rows[1])]
        data = rows[2:]
    else:
        header, data = rows[0], rows[1:]
    return header, data


def coerce(v):
    if v is None or v == "":
        return None
    if NUM_RE.match(v):
        f = float(v)
        return int(f) if ("." not in v and -2**53 < f < 2**53) else f
    return v


def add_commercial_columns(header: list[str], data: list[list]) -> None:
    """Ajoute vcom_S{n} = vmax_S{n}_kmh × facteur commercial (in place)."""
    for n in (1, 2, 3):
        idx = next((i for i, h in enumerate(header)
                    if f"vmax_s{n}_kmh" in h.lower()), None)
        if idx is None:
            continue
        header.append(f"vcom_S{n}_kmh_×{str(COMMERCIAL_FACTOR).replace('.', ',')} (commercial)")
        for row in data:
            raw = row[idx] if idx < len(row) else ""
            row.append(str(round(float(raw) * COMMERCIAL_FACTOR, 1))
                       if NUM_RE.match(str(raw)) else "")


def build_dataset(path: Path) -> dict | None:
    header, data = read_table(path)
    if not header or (len(header) <= 1 and len(data) <= 1):
        return None
    if path.name == "segments_courbature.csv":
        add_commercial_columns(header, data)
    numeric = []
    for c in range(len(header)):
        nonempty = [row[c] for row in data if c < len(row) and row[c] not in (None, "")]
        numeric.append(bool(nonempty) and all(NUM_RE.match(str(v)) for v in nonempty))
    rows = [[coerce(v) for v in row] + [None] * (len(header) - len(row)) for row in data]
    return {
        "file": path.name,
        "label": LABELS.get(path.name, path.name),
        "columns": header,
        "numeric": numeric,
        "rows": rows,
        "presets": PRESETS.get(path.name, []),
    }


def build_meta() -> dict:
    return {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "factor": COMMERCIAL_FACTOR,
        "scenarios": [{
            "id": s.id, "name_fr": s.name_fr,
            "cant_mm": s.cant_mm, "cant_in": round(s.cant_in, 2),
            "cant_def_mm": s.cant_def_mm, "cant_def_in": round(s.cant_def_in, 2),
            "coeff": round(s.coeff, 3), "fret_fr": s.fret_fr,
            "cant_assumed": s.cant_assumed,
        } for s in SCENARIOS.values()],
    }


def main() -> None:
    datasets = []
    for name in ORDER:
        p = DELIVERABLES / name
        if p.exists():
            ds = build_dataset(p)
            if ds:
                datasets.append(ds)
    # Tout autre CSV non listé dans ORDER (robustesse future).
    for p in sorted(DELIVERABLES.glob("*.csv")):
        if p.name not in ORDER:
            ds = build_dataset(p)
            if ds:
                datasets.append(ds)
    if not datasets:
        sys.exit(f"Aucune table exploitable dans {DELIVERABLES}")

    payload = {"datasets": datasets, "meta": build_meta()}
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    html = HTML_TEMPLATE.replace("__PAYLOAD__", blob)
    out = DELIVERABLES / "visualiseur.html"
    out.write_text(html, encoding="utf-8")
    print(f"=== Étape 19 — Visualiseur ===")
    print(f"  {out.name}  ({len(datasets)} tables, {out.stat().st_size/1024:.0f} KB)")
    for d in datasets:
        print(f"    · {d['label']}: {len(d['rows'])} lignes × {len(d['columns'])} col.")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="fr"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Visualiseur — TGV Canada Phase 1 (courbure)</title>
<style>
  :root{--bleu:#003366;--encre:#1a1a2e;--gris:#5a6472;--bord:#d7dee8;--surb:#eef3fa;}
  *{box-sizing:border-box}
  body{font-family:'Segoe UI',Helvetica,Arial,sans-serif;color:var(--encre);margin:0;
       font-size:13px;line-height:1.45;background:#f4f6f9}
  header{background:var(--bleu);color:#fff;padding:14px 20px}
  header h1{margin:0 0 2px;font-size:1.35em}
  header .sub{opacity:.85;font-size:.86em}
  .wrap{padding:14px 20px}
  .cards{display:flex;flex-wrap:wrap;gap:10px;margin:10px 0}
  .card{background:#fff;border:1px solid var(--bord);border-left:5px solid var(--bleu);
        border-radius:4px;padding:8px 11px;min-width:230px;flex:1}
  .card b{color:var(--bleu)}
  .card small{color:var(--gris)}
  .card.assumed{border-left-color:#e08a00}
  .avert{background:#fff3cd;border:1px solid #e0c060;border-radius:4px;padding:8px 12px;
         font-size:.9em;margin:8px 0}
  .bar{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:10px 0 4px}
  button{font:inherit;cursor:pointer;border:1px solid var(--bord);background:#fff;
         border-radius:4px;padding:4px 10px;color:var(--encre)}
  button:hover{background:var(--surb)}
  button.active{background:var(--bleu);color:#fff;border-color:var(--bleu)}
  .preset{border-color:#9bb4d4}
  .preset.on{background:#1f77b4;color:#fff;border-color:#1f77b4}
  .count{color:var(--gris);font-size:.9em;margin-left:auto}
  .tablewrap{overflow:auto;max-height:72vh;border:1px solid var(--bord);border-radius:4px;background:#fff}
  table{border-collapse:separate;border-spacing:0;width:100%;font-size:12px}
  th,td{padding:4px 8px;border-bottom:1px solid #eceff3;white-space:nowrap;text-align:right}
  th.txt,td.txt{text-align:left}
  thead th{position:sticky;top:0;background:var(--bleu);color:#fff;cursor:pointer;z-index:2;
           border-bottom:2px solid #00264d}
  thead th .ar{opacity:.6;font-size:.85em}
  thead tr.filters th{position:sticky;top:28px;background:#eaf0f8;z-index:1;padding:3px 5px}
  thead tr.filters input{width:100%;min-width:54px;font:inherit;font-size:11px;
        border:1px solid #c3cfe0;border-radius:3px;padding:2px 4px}
  thead tr.filters .mm{display:flex;gap:3px}
  tbody tr:nth-child(even){background:#f7f9fc}
  tbody tr:hover{background:#fdf6e3}
  .vcom{color:#1f77b4}
  footer{padding:10px 20px;color:var(--gris);font-size:.82em}
  code{background:#eef;padding:1px 4px;border-radius:2px}
</style></head>
<body>
<header>
  <h1>Visualiseur des livrables — TGV Canada Phase 1 (courbure)</h1>
  <div class="sub">Tri et filtre par colonne · vitesses en km/h ET mph · dévers/insuffisance en mm ET pouces · <span id="gen"></span></div>
</header>
<div class="wrap">
  <div class="cards" id="cards"></div>
  <div class="avert" id="caveat"></div>

  <div class="bar" id="datasetBar"></div>
  <div class="bar" id="presetBar"></div>
  <div class="bar">
    <button id="reset">Réinitialiser les filtres</button>
    <span class="count" id="count"></span>
  </div>

  <div class="tablewrap">
    <table id="tbl"><thead></thead><tbody></tbody></table>
  </div>
</div>
<footer>
  Fichier autonome (hors-ligne). « Vitesse commerciale » = plafond géométrique × <span id="fac"></span>
  (<i>indicatif</i>, Annexe E), non opérationnel. Régénéré par <code>scripts/19_build_viewer.py</code>
  à partir des CSV de <code>livrables/</code>.
</footer>

<script>
const DB = __PAYLOAD__;
const $ = s => document.querySelector(s);

let curIdx = 0, sortCol = -1, sortDir = 1, filters = {}, activePreset = -1;

function ds(){ return DB.datasets[curIdx]; }
function isNum(c){ return ds().numeric[c]; }
function fnum(v){ return (typeof v === 'number' && !Number.isInteger(v)) ? String(v).replace('.', ',') : (v===null?'':v); }

function findCol(sub){
  const cols = ds().columns; sub = sub.toLowerCase();
  for(let i=0;i<cols.length;i++){ if(cols[i].toLowerCase().includes(sub)) return i; }
  return -1;
}

function banner(){
  $('#gen').textContent = 'généré le ' + DB.meta.generated;
  $('#fac').textContent = String(DB.meta.factor).replace('.', ',');
  $('#cards').innerHTML = DB.meta.scenarios.map(s =>
    `<div class="card${s.cant_assumed?' assumed':''}">
       <b>${s.id}</b> ${s.name_fr}<br>
       <small>dévers ${s.cant_mm} mm (${String(s.cant_in).replace('.',',')}″) ·
       insuff. ${s.cant_def_mm} mm (${String(s.cant_def_in).replace('.',',')}″) ·
       v≈${String(s.coeff).replace('.',',')}·√R</small><br>
       <small>${s.fret_fr}${s.cant_assumed?' · <i>dévers supposé</i>':''}</small>
     </div>`).join('');
  $('#caveat').innerHTML = '<b>⚠ Dévers supposé :</b> le dévers réellement en voie n\'a pas été relevé ; '
    + 'S1 suppose 100 mm (≈ 4 po) ; S2 et S3 = dévers de conception 127 mm (5 po). Les vitesses sont des <b>plafonds géométriques</b> au dévers '
    + 'normatif, pas des vitesses relevées ni opérationnelles.';
}

function datasetBar(){
  $('#datasetBar').innerHTML = DB.datasets.map((d,i) =>
    `<button class="dsbtn${i===curIdx?' active':''}" data-i="${i}">${d.label} <small>(${d.rows.length})</small></button>`).join('');
  document.querySelectorAll('.dsbtn').forEach(b => b.onclick = () => {
    curIdx = +b.dataset.i; sortCol = -1; filters = {}; activePreset = -1; renderAll();
  });
}

function presetBar(){
  const ps = ds().presets || [];
  $('#presetBar').innerHTML = ps.length
    ? '<span style="color:#5a6472;font-size:.9em">Filtres rapides :</span> ' + ps.map((p,i) =>
        `<button class="preset${i===activePreset?' on':''}" data-p="${i}">${p.label}</button>`).join('')
    : '';
  document.querySelectorAll('[data-p]').forEach(b => b.onclick = () => {
    const i = +b.dataset.p; activePreset = (activePreset===i)? -1 : i; renderBody(); presetBar();
  });
}

function header(){
  const cols = ds().columns;
  const head = $('#tbl thead');
  const ar = c => c===sortCol ? `<span class="ar">${sortDir>0?'▲':'▼'}</span>` : '';
  let h1 = '<tr>' + cols.map((c,i) =>
    `<th class="${isNum(i)?'':'txt'}" data-c="${i}" title="${c}">${c} ${ar(i)}</th>`).join('') + '</tr>';
  let h2 = '<tr class="filters">' + cols.map((c,i) => {
    if(isNum(i)){
      const f = filters[i]||{};
      return `<th><div class="mm"><input type="number" data-c="${i}" data-k="min" placeholder="min" value="${f.min??''}">`
           + `<input type="number" data-c="${i}" data-k="max" placeholder="max" value="${f.max??''}"></div></th>`;
    }
    const f = filters[i]||{};
    return `<th><input data-c="${i}" data-k="q" placeholder="⌕" value="${f.q??''}"></th>`;
  }).join('') + '</tr>';
  head.innerHTML = h1 + h2;
  head.querySelectorAll('th[data-c]').forEach(th => th.onclick = () => {
    const c = +th.dataset.c;
    if(sortCol===c) sortDir = -sortDir; else { sortCol = c; sortDir = 1; }
    header(); renderBody();
  });
  head.querySelectorAll('input').forEach(inp => inp.oninput = () => {
    const c = +inp.dataset.c; filters[c] = filters[c]||{};
    filters[c][inp.dataset.k] = inp.value; renderBody();
  });
}

function passUI(row){
  for(const c in filters){
    const f = filters[c], v = row[c];
    if(isNum(+c)){
      if(f.min!=='' && f.min!=null && !(v!=null && v>=parseFloat(f.min))) return false;
      if(f.max!=='' && f.max!=null && !(v!=null && v<=parseFloat(f.max))) return false;
    } else if(f.q){
      if(!String(v??'').toLowerCase().includes(f.q.toLowerCase())) return false;
    }
  }
  return true;
}

function evalCond(row, cond){
  const i = findCol(cond.col); if(i<0) return true;
  let v = row[i]; const target = cond.val;
  if(cond.op==='contains') return String(v??'').toLowerCase().includes(String(target).toLowerCase());
  if(cond.op==='==') return (typeof target==='number') ? (parseFloat(v)===target) : (String(v)===String(target));
  const x = parseFloat(v); if(isNaN(x)) return false;
  if(cond.op==='<') return x<target;
  if(cond.op==='<=') return x<=target;
  if(cond.op==='>') return x>target;
  if(cond.op==='>=') return x>=target;
  return true;
}

function passPreset(row){
  if(activePreset<0) return true;
  return (ds().presets[activePreset].conds||[]).every(c => evalCond(row, c));
}

function renderBody(){
  let rows = ds().rows.filter(r => passUI(r) && passPreset(r));
  if(sortCol>=0){
    const num = isNum(sortCol);
    rows = rows.slice().sort((a,b) => {
      let x=a[sortCol], y=b[sortCol];
      if(x==null) return 1; if(y==null) return -1;
      if(num) return (x-y)*sortDir;
      return String(x).localeCompare(String(y),'fr')*sortDir;
    });
  }
  const cols = ds().columns;
  const vcomCols = cols.map(c => c.toLowerCase().startsWith('vcom'));
  const tb = $('#tbl tbody');
  const frag = rows.map(r => '<tr>' + r.map((v,i) =>
    `<td class="${isNum(i)?'':'txt'}${vcomCols[i]?' vcom':''}">${fnum(v)}</td>`).join('') + '</tr>').join('');
  tb.innerHTML = frag;
  $('#count').textContent = rows.length + ' / ' + ds().rows.length + ' lignes';
}

function renderAll(){ datasetBar(); presetBar(); header(); renderBody(); }

$('#reset').onclick = () => { filters = {}; activePreset = -1; sortCol = -1; renderAll(); };

banner(); renderAll();
</script>
</body></html>
"""


if __name__ == "__main__":
    main()

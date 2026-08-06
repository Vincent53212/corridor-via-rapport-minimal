# Corridor VIA : rapport minimal (temps de parcours par scénario)

Projet d'analyse du corridor VIA Rail Québec-Windsor : ce que la géométrie, les passages
à niveau, la signalisation, le doublement et le régime de cohabitation permettent comme
temps de parcours, par scénario de matériel et de voie. Livrable : un rapport (~15-20 p)
documentant cinq éléments clés, plus un visualiseur autonome hors-ligne.

Ce projet est un fork autonome du pipeline « TGV Canada, courbatures et doublement des
voies » (phases 1-2, mai-juillet 2026, validé par 4 passes red team). L'ancien projet et
ses livrables restent l'archive ; tout ce qui vit ici utilise la nomenclature ci-dessous.

## Nomenclature des scénarios (2026-08)

| ID | Description | Dévers | Insuffisance | k (v=k·√R) |
|----|-------------|--------|--------------|------------|
| S1 | Voie actuelle (VIA / Transports Canada) | 100 mm (supposé) | 76 mm | 3,83 |
| S2 | Pendulaire LRC, dévers max standard CN (5 po) | 127 mm | 152 mm | 4,82 |
| S3 | Pendulaire moderne (insuffisance 270 mm) | 127 mm | 270 mm | 5,75 |

S1 et S2 sont 100 % précédent CN (MR 1305-0). S3 sort du précédent nord-américain
(référence de conception EN 13803, approbation par équipement requise, RRTS Subpart C 4.3) ;
une sensibilité Ed=225 mm est disponible comme position de repli.

⚠ L'ancien pipeline numérotait autrement (son S2 = LRC sur dévers actuel 100 mm, abandonné ;
son S3 = le S2 d'ici). Ne jamais mélanger les deux nomenclatures.

## Structure

- `scripts/` : pipeline Python (segmentation 05 → synthèses 06/11/12/12b/14 → cartes 07/15 → exports 18/19). Source unique des scénarios : `scripts/scenarios.py`.
- `intermediaires/` : données dérivées (parquet de courbure, tracés matchés GTFS/OSM) héritées du pipeline amont (étapes 01-04 du projet parent, non refaites ici).
- `ressources/` : sources de données (GTFS VIA, CN MR 1305-0, rapports). Les extraits OSM (.pbf, ~2 Go) ne sont pas versionnés : voir `sources/registre_sources.md`.
- `livrables/` : sorties générées (CSV, xlsx, cartes HTML/KMZ, visualiseur, listes PDF).
- `sources/` : **registre des sources** (`registre_sources.md`, statuts VÉRIFIÉE / À TROUVER) + `refs.bib` + `apa.csl`. Règle : chaque affirmation sourçable du rapport est référencée APA (7e éd.) au fil de l'eau ; une clé n'entre dans `refs.bib` qu'une fois vérifiée.

## Reproduire

```bash
# venv Python 3.12 avec : geopandas shapely pyarrow folium scipy pandas openpyxl simplekml
python scripts/05_segment_and_classify.py   # segmentation + classes par scénario
python scripts/06_synthese_troncon.py       # synthèse par tronçon
python scripts/07_render_outputs.py         # carte, KMZ, CSV
python scripts/11_target_speed_to_km.py     # vitesse cible → km à rectifier
python scripts/12_sections_a_rectifier_pdf.py
python scripts/12b_sections_vcom160_S3.py
python scripts/14_synthese_voies.py         # doublement (voies simples/doubles)
python scripts/15_carte_voies.py
python scripts/18_export_xlsx.py
python scripts/19_build_viewer.py           # visualiseur autonome
python scripts/_baseline_zones.py           # garde-fou : doit afficher BASELINE: PASS
```

Sous Windows, préfixer `PYTHONUTF8=1` (sorties console UTF-8).

## Garde-fous

- Invariant par construction : `classify(vmax) == classe` et vmax ≤ 360 km/h sur chaque segment × scénario (vérifié : 0/3666).
- `_baseline_zones.py` : les zones de référence (Ottawa, Montréal, Kingston) gardent leurs vraies courbes.
- Les vitesses publiées sont des plafonds géométriques, pas des promesses d'horaire.

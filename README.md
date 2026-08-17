# Corridor VIA : rapport minimal (temps de parcours par scénario)

Projet d'analyse du corridor VIA Rail Québec-Windsor : ce que la géométrie, les passages
à niveau, la signalisation, le doublement et le régime de cohabitation permettent comme
temps de parcours, par scénario de matériel et de voie. Livrable : un rapport (~15-20 p)
documentant cinq éléments clés, plus un visualiseur autonome hors-ligne.

Ce projet est un fork autonome du pipeline « TGV Canada, courbatures et doublement des
voies » (phases 1-2, mai-juillet 2026, validé par 4 passes red team). L'ancien projet et
ses livrables restent l'archive ; tout ce qui vit ici utilise la nomenclature ci-dessous.

## Nomenclature des scénarios (2026-08)

| ID interne | Nom publié | Dévers | Insuffisance | k (v=k·√R) |
|----|-------------|--------|--------------|------------|
| S1 | Scénario de base (voie et train actuels) | 100 mm (supposé) | 76 mm | 3,83 |
| S2 | Scénario recommandé (pendulaire LRC, plafond 177 km/h) | 127 mm | 152 mm | 4,82 |
| S3 | (interne seulement, retiré du rapport 2026-08-17) | 127 mm | 270 mm | 5,75 |

Le RAPPORT ne publie que deux scénarios, nommés par leur fonction : « scénario de
base » (l'horaire d'aujourd'hui ; le moteur S1 plafonné à 160 sert de contrôle
interne) et « scénario recommandé » (pendulaire LRC, 100 % précédent CN MR 1305-0,
plafonné à 177 km/h = 110 mi/h, la limite du contrôle en cabine incrémental type
ITCS). S3 (270 mm, hors précédent NA) reste calculé dans le pipeline et les annexes
numériques, mais n'apparaît plus dans le rapport ni ses figures.

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
python scripts/11_target_speed_to_km.py     # vitesse cible → km restants sous grande vitesse
python scripts/12_sections_a_rectifier_pdf.py  # sections restantes < 177, scénario recommandé
python scripts/14_synthese_voies.py         # doublement (voies simples/doubles)
python scripts/15_carte_voies.py
python scripts/18_export_xlsx.py
python scripts/_baseline_zones.py           # garde-fou : doit afficher BASELINE: PASS

# --- identité graphique, rapport et visualiseur ---
python identite/fonts/_installer_polices.py # une fois : .ttf des figures
python scripts/27_verif_identite.py         # garde-fou : doit afficher PASS
python scripts/20_passages_niveau.py        # passages à niveau (bandes d'exploitation)
python scripts/21_tbase_bande.py            # moteur T_base (bandes 160/177/200/250/300)
python scripts/33_courbes_doublees.py       # sensibilité : courbes des sections à doubler
SEGMENTS_OVERRIDE=intermediaires/segments_rectifies.geojson python scripts/21_tbase_bande.py
BLOCS_URBAINS=libres python scripts/21_tbase_bande.py   # sensibilité : blocs réintégrés
python scripts/22_marges_2x2.py             # médianes du 2×2 (lues par la figure 23)
python scripts/23_figure_cellules.py        # figure : le 2×2 du corridor
python scripts/24_figure_vs_auto.py         # figure : le train contre l'auto (4 trajets)
python scripts/32_figure_gains.py           # figure : d'où viennent les minutes
python scripts/28_couverture.py             # couverture + vignette du visualiseur
python scripts/29_rapport_html.py           # rapport.md → HTML à l'identité
node   scripts/30_rapport_pdf.mjs           # HTML → PDF paginé (sommaire à folios réels)
python scripts/25_build_rapport.py          # version Word, pour annotation client
python scripts/19_build_viewer.py           # visualiseur autonome (APRÈS 28 et le rapport)
```

L'ordre des trois dernières lignes compte : l'étape 19 incorpore la vignette
produite par 28, et elle RELÈVE dans `rapport.md` les chiffres que ses
vérifications comparent. Lancée avant une correction du rapport, elle publierait
la comparaison d'hier.

Sous Windows, préfixer `PYTHONUTF8=1` (sorties console UTF-8).

## Identité graphique

`identite/identite.json` est la source unique : palette, typographie, réglages de
page. Le gabarit HTML, les figures matplotlib et la couverture la lisent toutes
par `scripts/identite.py` ; aucune couleur n'est écrite ailleurs. `rapport.md`
reste du markdown ordinaire, relu et versionné comme tel : la mise en page est
entièrement appliquée après pandoc.

Deux règles de lecture que le document tient partout : Fraunces porte le propos,
IBM Plex Mono porte la mesure ; l'acier dit le réseau, le chaud dit la
contrainte. La rampe des bandes de vitesse est divergente et s'articule sur
200 km/h (la grille physique des classes A-F) ; le plafond d'exploitation retenu
par l'étude est 177 km/h (limite ITCS), marqué d'un repère sur la couverture.

## Garde-fous

- Invariant par construction : `classify(vmax) == classe` et vmax ≤ 360 km/h sur chaque segment × scénario (vérifié : 0/3666).
- `_baseline_zones.py` : les zones de référence (Ottawa, Montréal, Kingston) gardent leurs vraies courbes.
- `27_verif_identite.py` : la palette tient ses promesses. Distinction dE2000 des figurés en vision normale ET sous protanopie, deutéranopie et tritanopie ; clarté monotone des rampes ordonnées, pour qu'elles survivent au noir et blanc ; contraste WCAG AA des couples texte/fond employés.
- Les vitesses publiées sont des plafonds géométriques, pas des promesses d'horaire.

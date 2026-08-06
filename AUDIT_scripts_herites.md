# Audit des scripts hérités de l'ancien projet (2026-08-06)

Règle (décision Vincent) : tout script importé de l'ancien pipeline est SUSPECT de ne pas
respecter le nouveau cadre (plan de match v3). Interdits du cadre : facteur de transposition
(remplacé par le moteur d'intégration T_base), benchmark Rapido/Metropolis, vitesse publiée
comme promesse, ancienne nomenclature de scénarios, renvois à la methodologie.docx (archivée).

Verdicts après passage au crible :

| Script | Verdict | Détail |
|---|---|---|
| `scenarios.py` | MIGRÉ | Nouvelle nomenclature S1/S2/S3 (127/270 en S3), sensibilité 225 hors dict, note de migration dans la docstring |
| `utils.py` | NETTOYÉ | `COMMERCIAL_FACTOR = 0.75` RETIRÉ (facteur de transposition) |
| `alignments.py` | OK | Définition des tronçons, neutre aux scénarios |
| `05_segment_and_classify.py` | OK (caveat) | Suit la source unique scenarios.py. Caveat connu : la grille de segmentation groupe par triplet de classes S1/S2/S3, donc les frontières bougent quand les scénarios changent (re-découpage, pas un bug) |
| `06_synthese_troncon.py` | NETTOYÉ (décision ouverte) | Textes de sources mis à jour. ATTENTION : la définition de « goulot structurel » (F-en-S3 soutenu) se VIDE sous le nouveau S3 (0 goulot, la classe F disparaît). Sous S2 (= ancien S3 exactement) on retrouve les 2 goulots historiques. À trancher au rapport : publier goulots-S2 (précédent CN) et goulots-S3 (0) côte à côte, ou retirer le livrable |
| `07_render_outputs.py` | NETTOYÉ | Caveat dévers corrigé (S1 seul supposé 100 mm), description des scénarios recalée |
| `11_target_speed_to_km.py` | NETTOYÉ | Volet « #2 INDICATIF » (conversion moyenne→pointe 0,70-0,80) RETIRÉ ; contrôle de cohérence recalé sur la nouvelle nomenclature. Le volet #1 (balayage de seuil géométrique) est conservé : aucune hypothèse |
| `12_sections_a_rectifier_pdf.py` | NETTOYÉ | Colonne et panneaux « vitesse commerciale estimée = 0,75 × » RETIRÉS ; renvoi au moteur T_base ; description S3 recalée |
| `12b_sections_vcom160_S3.py` | RETIRÉ | Entièrement bâti sur le facteur 0,75 (critère vcom<160 ⇔ géo<213). Son besoin légitime (où la vitesse commerciale reste basse) sera recalculé PROPREMENT via T_base à l'étape 5 si le rapport en a besoin |
| `13_track_count.py` | OK | Compte de voies OSM, indépendant des scénarios. Non exécutable ici (exige les .pbf, non versionnés) ; ses sorties sont dans `intermediaires/` |
| `14_synthese_voies.py` | OK | Doublement (voies simples/doubles), indépendant des scénarios |
| `15_carte_voies.py` | OK | Carte des voies, indépendant des scénarios |
| `18_export_xlsx.py` | OK | Miroir xlsx des CSV, sans logique propre |
| `19_build_viewer.py` | NETTOYÉ | Colonnes « vcom × 0,75 », presets « Commercial < 150 » et facteur du pied de page RETIRÉS ; le visualiseur embarque maintenant tbase_par_bande.csv et blocs_urbains.csv |
| `_baseline_zones.py` | OK | Garde-fou de zones de référence, PASS re-vérifié après migration |
| `21_tbase_bande.py` | NEUF | Moteur d'intégration T_base (étape 2), écrit pour le nouveau cadre |

Vérifications post-nettoyage : `grep` de « 0,75 / commerciale estimée / transposition »
dans les livrables régénérés = 0 occurrence ; pipeline 11 → 12 → 19 relancé ; PDF 12
régénéré (Chrome headless) ; invariant classe/vmax et BASELINE inchangés.

Dettes restantes connues :
- Décision goulots S2 vs S3 (ci-dessus), à trancher à l'étape 5.
- `12` porte encore le sous-titre « TGV Canada Phase 1 » dans son `<title>` (cosmétique).
- `05` : option future de segmenter sur un scénario fixe pour stabiliser les frontières.

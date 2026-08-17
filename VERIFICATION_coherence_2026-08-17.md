# Test de cohérence complet — rapport minimal, 17 août 2026

Vérificateur indépendant. Périmètre : `rapport.md`, `livrables/*.csv`,
`intermediaires/*.geojson`, `livrables/figure_*.png`, `livrables/visualiseur.html`,
`livrables/rapport_corridor.pdf` (25 p.), `sources/refs.bib`.

Méthode : recalcul intégral des chiffres à partir des CSV et des GeoJSON (scripts Python
ad hoc), lecture des trois figures, extraction du payload JSON du visualiseur, extraction
du texte du PDF page par page.

---

## 1. Ce qui est vérifié et juste

### Temps (section 7, prose de la synthèse, figure vs auto)

Source : `tbase_par_bande.csv`, scénario interne S2, bande 177.

| Tronçon | tbase CSV | Rapport | Horaire CSV | Rapport |
|---|---|---|---|---|
| MTL-QC | 138,5 | 2 h 18 ✓ | 202,5 | 3 h 22 ✓ |
| MTL-Ott | 98,0 | 1 h 38 ✓ | 122,0 | 2 h 02 ✓ |
| Ott-TO | 202,5 | 3 h 22 ✓ | 275,0 | 4 h 35 ✓ |
| MTL-TO | 247,3 | 4 h 07 ✓ | 318,0 | 5 h 18 ✓ |

Marges hautes recalculées (`t_horaire / tbase(S1,160) − 1`) : MTL-Ott 11,0 % ; MTL-TO
18,1 % ; Ott-TO 23,8 % ; MTL-QC 32,2 % → **11 / 18 / 24 / 32 publiés : exact.**

Fourchettes (×1,08 et ×(1+marge)) :

| Tronçon | Recalcul | Publié |
|---|---|---|
| MTL-QC | 149,6 – 183,1 | 2 h 30 à 3 h 03 ✓ |
| MTL-Ott | 105,8 – 108,8 | 1 h 46 à 1 h 49 ✓ |
| Ott-TO | 218,7 – 250,7 | 3 h 39 à 4 h 11 ✓ |
| MTL-TO | 267,1 – 292,2 | 4 h 27 à 4 h 52 ✓ |

Pourcentages face à l'auto (170 / 330 / 140 / 260 min) : 88–108, 81–89, 76–78, 84–96 —
**tous exacts**, y compris les repères VIA de la figure (119 / 96 / 87 / 106 %).
« 26 à 51 minutes calculées sur Montréal-Toronto » (§1, comparaison WCML) : 318 − 292,2 =
25,8 et 318 − 267,1 = 50,9 ✓.

### Kilomètres restants

Recalcul sur `km_restants_sous_grande_vitesse.csv` et `intermediaires/segments*.geojson`
(cœur = 4 trajets, 1 432,9 km) :

| Cible | Base publié / recalcul | Recommandé publié / recalcul |
|---|---|---|
| < 177 | 494 / **494,4** ✓ | 234 / **233,7** ✓ |
| < 160 | 358 / **358,1** ✓ | 94 / **94,5** (arrondi bas) |
| < 100 | 28 / **27,8** ✓ | 7 / **7,4** ✓ |
| < 177 corrigé | 530 / **530,1** ✓ | 265 / **265,2** ✓ |

« 16 pour cent du réseau parcouru » = 233,7/1 432,9 = 16,3 % ✓ ; « 84 pour cent du tracé
atteint 177 » ✓ ; « résidu corrigé 13 pour cent plus long » = 265,2/233,7 = +13,5 % ✓ ;
« environ un huitième » ✓.

### Passages à niveau

Recalcul sur `passages_niveau_tri.csv` (924 lignes) : bande recommandée 154-177 = **891**,
≤153 = **33** (891+33 = 924 ✓) ; `flbg_present` vrai dans la zone rapide = **328**, donc
**563** à équiper ✓ ; intervention **782** standards + **109** complexes = 891 ✓ ;
accès Public × protection Active = **352** ✓. Les huit chiffres publiés sont exacts.

### Marges 2×2

Recalcul sur `marges_par_intergare.csv` avec le filtre du script 22 (non exclue, marge
non vide, pas de doublon physique, cellule ≠ mixte, région cœur) :

| Cellule | n | km | médiane | dispersion | trains/j (covariables) | classe (mi/h) |
|---|---|---|---|---|---|---|
| double-CN | **11** ✓ | **514,7** ✓ | **36,6 → 37** ✓ | 5,0 ✓ | 40 ✓ | 95–100 ✓ |
| simple-VIA | **5** ✓ | **217,7** ✓ | **33,8 → 34** ✓ | 10,0 ✓ | 12–14 ✓ | 80–95 ✓ |
| simple-CN | **2** ✓ | **191,8** ✓ | **67,8 → 68** ✓ | 21,4 → 21 ✓ | 27 ✓ | 95 ✓ |

Dérivés : 67,8 − 36,6 = **31,2 points** ✓ ; 36,6 − 33,8 = **2,8 → 3 points** ✓ ;
temps de base simple-CN = **77,4 min** ✓ (« 77 minutes ») ; simple-VIA = **91,6 min** ✓
(« 92 minutes ») ; 0,312 × 77,4 = **24,1 min** ✓ ; 0,30–0,33 × 77,4 = **23,2–25,5 →
23 à 26 min** ✓ ; 0,03–0,07 × 91,6 = **2,7–6,4 → 3 à 6 min** ✓. Écarts interquartiles
simple-CN = 8 et 16 min ✓ (« varie de 8 à 16 minutes »). Sud-ouest : 8 trains/jour,
42,5–70 mi/h, VIA à 100 mi/h — tous corroborés par `covariables_paires.csv`.

### Décomposition des gains

`decomposition_gains.csv` ↔ figure ↔ texte, tout ferme :

| Trajet | H | C | G | plafond+pendul. | doublement | cohabitation |
|---|---|---|---|---|---|---|
| Québec-Toronto | 530,5 | 426,7 | 103,8 | 20,1+19,4 = 39,5 (fig. −40) | 24,1 (−24) | 40,2 (−40) |
| Québec-Montréal | 202,5 | 149,6 | 52,9 | 5,1+10,7 = 15,8 (−16) | 24,1 (−24) | 12,9 (−13) |
| Montréal-Ottawa | 122,0 | 105,8 | 16,2 | 2,0+10,9 = 12,9 (−13) | 0,0 | 3,3 (−3) |

Somme des parts = G dans les trois cas ✓. Écart max entre les deux ordres de Shapley =
5,7 min → « ne dépasse pas 6 minutes » ✓. Le total Québec-Toronto s'explique par
149,6 + 267,1 + 10 min d'arrêt à Montréal = 426,7 ✓ (et 202,5 + 318 + 10 = 530,5 ✓).

### Sensibilités

Blocs réintégrés (`tbase_par_bande_blocs_libres.csv`, S2/177) : 138,5−118,5 = **20,0** ;
98,0−83,3 = **14,7 → 15** ; 202,5−193,3 = **9,2 → 9** ; 247,3−225,4 = **21,9 → 22**.
→ **−20 / −15 / −9 / −22 : exact.**

Courbes rectifiées (`tbase_par_bande_rectifies.csv`) : **3,8 → 4** (MTL-QC), **3,1 → 3**
(MTL-Ott), **0,7** (Ott-TO), **0,0** (MTL-TO) → « 4 et 3, moins d'une minute ailleurs » ✓.

Biais corrigé (`tbase_par_bande_corriges.csv`) : **+2,9 → 3** (MTL-QC), **+1,9 → 2**
(Ott-TO), +0,5 et +0,7 ailleurs ✓ ; toutes configurations : min 0,0, **max 7,8 → 8**,
médiane **2,25 → 2** ✓.

Immobilisation : « 3 à 10 minutes par tronçon » = n_arrets 3/3/10/9 ✓.

### Divers vérifiés

- Blocs urbains : 17,8 / 6,1 / 19,9 / 20,1 km et fenêtre Ottawa ±10 km — conformes à
  `blocs_urbains.csv` ; sommes GTFS 38 / 23,5 / 18 / 41,5 min ✓.
- Paramètres : k = 3,83 et 4,82, dévers 100/127 mm, insuffisance 76/152 mm — conformes à
  `scenarios_parametres.csv` ✓.
- **Toutes les conversions km/h ↔ mi/h sont justes** : 177=110, 160=99, 200=124, 153=95,
  100=62, 201=125, 226=140,6, 127=79, 72=45, 68-113=42-70, 129-153=80-95, 24/72/80=15/45/50,
  161=100, 95 km/h = 59 mi/h. Aucune erreur trouvée.
- « environ 1 090 km de voies physiques » : **traçable** — somme des inter-gares du cœur
  hors doublons physiques = **1 086,1 km** (`marges_par_intergare.csv`) ✓.
- « 1 433 km de trajets » = 1 432,9 km (`segments.geojson`, cœur) ✓.
- **Bibliographie : aucune clé manquante.** 34 clés citées, toutes présentes dans
  `refs.bib` (39 clés ; 5 non utilisées : boyd1982, fra2001sealed, uic2004c406,
  wiki2025lrc, wiki2025turbo).
- **Aucun reste de l'ancienne version** dans `rapport.md` : pas de « trois scénarios »,
  pas de « bande 200 » comme scénario, pas de S1/S2/S3, pas de « km à rectifier », pas de
  4 h 12 / 2 h 25 / 199 km / 301 km / 569 / 754. La seule occurrence de « fermeture » est
  la phrase voulue.
- **Renvois de section** : tous justes sauf un (voir écart n° 2). Sections : 1 Synthèse,
  2 Méthode, 3 Pendulaire, 4 Doublement, 5 Passages à niveau, 6 Signalisation,
  7 Résultats, 8 Limites.

### Figures

- `figure_vs_auto.png` : les 12 valeurs affichées (temps auto, temps VIA, fourchettes,
  pourcentages) sont **identiques au texte**. Légende conforme.
- `figure_gains.png` : 7 h 07 / 8 h 50, 2 h 30 / 3 h 22, 1 h 46 / 2 h 02 et les tranches
  −40/−24/−40, −16/−24/−13, −13/−3 correspondent **exactement** au CSV. Le pied de figure
  affiche bien les deux conditions (contrôle en cabine ; 891 passages dont 563 à équiper),
  ce que le §1 annonce (« affichées sous la figure ») ✓.
- `figure_cellules.png` : 37 / 68 / 34 % ✓, teinte = propriétaire, valeur = nombre de
  voies, gris = paires exclues — la légende du rapport décrit bien ce qu'on voit ✓.

### PDF

25 pages, pagination de la table des matières exacte (3, 7, 10, 12, 17, 19, 20, 23).
Les 6 tables du rapport sont **complètes et non tronquées** (2 scénarios, km libérés,
2×2, temps de base, temps avec marge, biais, passages à niveau). Les **3 figures sont
présentes** aux bonnes pages (p. 3 : 3289×1661 ; p. 4 : 3342×1257 ; p. 13 : 2566×1500).
Bibliographie complète (p. 24-25). Rien de coupé.

### Visualiseur

9 sections, titres alignés sur le rapport. Chiffres de tête tous conformes : 234 / 494 /
1 433 km ; 68 / 37 / 34 % ; 891 / 563 / 924 ; 4 h 27 / 2 h 30 ; 4,82 ; 110 mi/h ;
4 h 27 à 4 h 52 contre 5 h 18. Les valeurs « publiées » des 4 vérifications (494/234,
37/34/68, 891/33, 103,8/52,9/16,2) correspondent au rapport et aux CSV.
**Aucun ancien chiffre**, **aucun S1/S2/S3 dans un texte affiché** (le code ne rend que
les `libelles`, jamais les valeurs de filtre ; les colonnes CSV internes en gardent, ce
qui est admis). Phrase « l'étude ne propose la fermeture d'aucun passage » présente.

---

## 2. Écarts confirmés

### Bloquant

**1. La contre-épreuve GTFS 2023 ne dit pas ce que le rapport lui fait dire — et elle
contredit le constat 4.**
`rapport.md:682-683` (PDF p. 23) : « la hiérarchie entre cellules et les niveaux de marge
y sont pratiquement identiques (voie simple CN à 67 pour cent dès 2023) ».

| Cellule | 2026 (`marges_2x2_synthese.csv`) | 2023 (`..._GTFS2023.csv`) | Écart |
|---|---|---|---|
| double-CN | 36,6 | 36,3 | −0,3 |
| simple-CN | 67,8 | 66,6 | −1,2 |
| **simple-VIA** | **33,8** | **48,7** | **+14,9** |

Les mêmes 5 paires composent la cellule VIA dans les deux saisons (Coteau-Alexandria,
Alexandria-Casselman, Casselman-Ottawa, Fallowfield-Smiths Falls, Smiths Falls-Brockville),
donc l'écart n'est pas un effet d'échantillon. Deux conséquences :
- « les niveaux de marge pratiquement identiques » est faux pour une cellule sur trois ;
- **la hiérarchie s'inverse** : en 2026 simple-VIA (33,8) < double-CN (36,6), en 2023
  double-CN (36,3) < simple-VIA (48,7). Or c'est précisément ce classement qui porte le
  constat 4 de la synthèse (« une voie simple ne coûte rien quand VIA est propriétaire…
  elle porte même 3 points de marge de moins que la voie double du CN »). Sur les horaires
  d'avant la crise, la voie simple de VIA coûtait 12 points de plus que la voie double
  du CN.

Le seul énoncé que la contre-épreuve soutient est celui entre parenthèses (simple-CN à
67 % dès 2023). La phrase doit être réécrite : la robustesse porte sur la voie simple du
CN, pas sur la cellule VIA.

### Mineur

**2. Renvoi de section faux.** `rapport.md:244` (PDF p. 9) : « restrictions
exceptionnelles liées aux passages à niveau (section 6) ». Section 6 = Signalisation ;
les passages à niveau sont la **section 5** (et le dossier des restrictions est en 4.3).

**3. La table du biais et sa prose ne portent pas sur la même population.**
`rapport.md:631-641` (PDF p. 21). Colonnes publiées « Segments » 155+151+160+158 = 624 et
« Kilomètres » 31+56+82+114 = 283 ; avec la ligne de référence : 877 segments et 1 215 km.
La prose dit « **Sept cent dix des 1 014 segments** du cœur… soit **305 km sur 1 433** ».
Recalcul : la prose est juste (710 / 1 014 ; 305,4 / 1 432,9 km) ; la table ne compte que
les segments **où un facteur a pu être mesuré**. Population complète par tranche :

| Tranche | Table publiée | Population réelle |
|---|---|---|
| < 300 m | 155 / 31 km | **199 / 34,6 km** |
| 300-450 | 151 / 56 km | **181 / 66,7 km** |
| 450-600 | 160 / 82 km | **164 / 84,0 km** |
| 600-900 | 158 / 114 km | **166 / 120,1 km** |
| ≥ 900 m | 253 / 932 km | **304 / 1 127,5 km** |

(Les facteurs médians et 9es déciles publiés, eux, sont exacts.) Un lecteur qui additionne
la table tombe sur une contradiction avec le paragraphe qui la suit. Il manque une note de
colonne du type « segments dont le corps a pu être mesuré à 300 m ».

**4. « 184 km de segments concernés » (courbes rectifiées) déborde du périmètre.**
`rapport.md:611` (PDF p. 21). Le script 33 imprime 183,7 km, mais sur **tous** les
tronçons, Toronto-Sarnia compris (16 segments, ~22 km). Sur les quatre trajets du rapport :
**87 segments, 161,7 km**. Les minutes gagnées, elles, sont bien calculées sur le cœur —
la km et les minutes ne parlent donc pas du même objet.

**5. « blocs urbains ±20 pour cent (déjà dans les fourchettes) » n'est pas vrai partout.**
`rapport.md:597` (PDF p. 20). Sur Montréal-Ottawa la sensibilité vaut ±5,6 min
(`tbase_lo/hi` = 92,4 / 103,6 contre 98,0) alors que la fourchette publiée ne fait que
3,0 min de large (1 h 46 à 1 h 49). Sur Montréal-Québec, la variante −20 % donne
130,9 × 1,08 = 141 min, **sous** la borne basse publiée de 149,6 min. L'affirmation tient
en largeur relative sur trois tronçons, pas sur Montréal-Ottawa, et jamais au sens
littéral d'inclusion.

**6. Deux totaux de corridor concurrents.** §3 (PDF p. 10) : « somme des quatre trajets
analysés, **1 433 km** » — juste (1 432,9). Mais les en-têtes des tables du §7 donnent
270 + 185 + 444 + 539 = **1 438 km**. Écart de 5 km visible pour qui additionne.

**7. La figure des gains et la table des temps ne couvrent pas les mêmes trajets.**
`decomposition_gains.csv` et `figure_gains.png` portent sur Québec-Toronto (via Montréal),
Québec-Montréal et Montréal-Ottawa ; les tables du §7 portent sur Montréal-Québec,
Montréal-Ottawa, Ottawa-Toronto et Montréal-Toronto. Conséquences : **Ottawa-Toronto et
Montréal-Toronto n'ont pas de décomposition**, et le trajet vedette de la figure
(**Québec-Toronto, 8 h 50 → 7 h 07**) n'apparaît **nulle part** dans le texte du rapport,
alors que c'est la barre la plus longue de la synthèse. La légende (« chaque barre est
l'horaire actuel du trajet ») n'avertit pas de ce changement de découpage.

**8. Visualiseur, section 02 : « 1 268 segments de courbure homogène ».** C'est le total
de `segments_courbature.csv`, sud-ouest inclus. Le rapport parle de **1 014 segments** sur
le cœur, et la tuile voisine du visualiseur affiche « 1 433 km, quatre trajets ». Deux
périmètres côte à côte sans étiquette.

### Cosmétique

**9. « trois leviers » contre quatre parts.** §7 (PDF p. 20) et légende de la figure
disent « ses trois leviers », puis le même paragraphe nomme **quatre** parts (relèvement
du plafond, train pendulaire, doublement, cohabitation). Le visualiseur reproduit les deux
versions dans la **même** section 07 : « à ses trois leviers » dans le texte, « ses quatre
parts somment exactement au gain » dans la vérification. La figure, elle, fusionne plafond
et pendulaire sous la seule étiquette « pendulaire », ce qui sous-titre la tranche.

**10. Arrondi à la baisse.** §3, « Sous 160 km/h — scénario recommandé : 94 km ». La somme
des tronçons vaut 94,5 (46,0+19,3+15,3+13,9). 95 serait l'arrondi usuel.

**11. « les quelque 80 points d'une fenêtre glissante de 900 mètres »** (§2.2). À un point
tous les 10 m, la fenêtre en contient environ **90**.

**12. Marqueur éditorial resté dans le livrable.** PDF p. 16 : « [ordres de grandeur 15 vs
45-50 mi/h, soit 24 vs 72-80 km/h, **À VÉRIFIER en étude de circulation**] ». Le marqueur
« \[HYPOTHÈSE…\] » du §2.1 est, lui, cohérent avec la convention du projet (il est repris
tel quel dans `blocs_urbains.csv`) ; « À VÉRIFIER » se lit comme un TODO oublié.

**13. « Le passager de Montréal-Québec paie jusqu'à 24 minutes selon l'heure de son
départ » (§4).** Le 24 est la **somme** des deux écarts interquartiles des deux paires
(8 + 16), pas ce que subit un passager sur une paire. Et il tombe à l'identique sur les
« 24 minutes » du doublement quatre paragraphes plus haut, ce qui invite à confondre deux
grandeurs sans rapport.

---

## 3. Chiffres non vérifiables depuis le dossier (à confirmer par l'auteur)

Aucun de ces chiffres n'est contredit ; simplement, rien dans `livrables/` ni
`intermediaires/` ne permet de les recalculer.

1. **« zéro violation sur 5 040 contrôles »** (§7.1). Aucun décompte du dossier ne donne
   5 040 : 1 268 segments × 4 = 5 072 ; 1 014 × 5 = 5 070 ; 1 269 lignes ×4 = 5 076.
   Le nombre semble hérité d'une régénération antérieure.
2. **« l'écart entre un tronçon double détecté et le même tronçon documenté par le BST est
   de 0,1 km sur 25 »** (§2.2). `voies_synthese.json` publie une corroboration
   (couverture 66,4 %, accord 91,0 %, geom ≤ PL 98,5 %) mais pas ce couple.
3. **« l'ancien forfait de cinq minutes par arrêt… retombe à une à huit minutes près »** et
   **« environ quatre à cinq minutes par arrêt au plafond retenu »** (§2.1) : aucun livrable
   ne porte la contre-vérification.
4. **Chatham-Windsor, « moyenne de 95 km/h ou 59 mi/h »** et **« 40-60 km/h de moyenne »**
   pour les lignes simples voisines du CN (§4.2) : aucune colonne de vitesse moyenne dans
   les CSV publiés.
5. Chiffres externes non recalculables ici, cités avec source : WCML (36 et 42 min,
   8,6 G£, +77 % / −27 %), Michigan ITCS, Niles-Dowagiac (16 milles), Dick et al.
   (45/50/52 trains), Amtrak OIG (70 % / 59 %), ponctualité VIA (71-72 → 30 %),
   Caroline du Nord (19 vies, 52 %), Turbo (~300 passages, 140,6 mi/h), Alto (~1 000 km).

---

## 4. Synthèse

Le noyau quantitatif du rapport est **solide** : sur environ 120 chiffres recalculés
(temps, fourchettes, pourcentages face à l'auto, kilomètres restants publiés et corrigés,
passages à niveau, marges 2×2, décomposition des gains, trois sensibilités, conversions
d'unités), **un seul écart de fond** est apparu, et il porte non pas sur un calcul mais
sur la lecture d'une contre-épreuve (écart n° 1). Les figures, le PDF et le visualiseur
sont alignés sur le texte ; il ne reste aucune trace de la version à trois scénarios.

À corriger en priorité : **n° 1** (phrase de la section 8, qui surclasse la robustesse de
la cellule VIA et fragilise le constat 4), puis **n° 3** (table du biais, seule table du
rapport dont les colonnes ne s'additionnent pas vers le texte voisin), **n° 2** (renvoi de
section) et **n° 7** (les deux trajets sans décomposition et le trajet Québec-Toronto
orphelin).

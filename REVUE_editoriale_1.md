# Revue éditoriale no 1 : rapport.md (brouillon, août 2026)

Réviseur en chef, lecture à froid sans contexte préalable. Quatre passes. Classement :
**BLOQUANT** (erreur de fait ou de chiffre), **MAJEUR** (clarté, structure), **MINEUR**
(langue, typographie). Les corrections proposées sont prêtes à coller quand il s'agit de texte.

---

## Passe 1 : lecture froide de non-expert

### P1-1. MAJEUR : acronymes et jargon non définis à leur première apparition

Un lecteur décideur non expert décroche sur les termes suivants, tous employés sans
définition à leur première occurrence :

| Terme | Première occurrence | Correction proposée |
|---|---|---|
| HSR | §3, table des cibles (« rectification requise pour HSR ») | remplacer par « grande vitesse (200 km/h et plus) » ; l'acronyme anglais n'apparaît nulle part ailleurs, il est inutile |
| GTFS | §2.1, blocs urbains (« horaires GTFS actuels ») | à la première mention : « les horaires publics de VIA au format ouvert GTFS » |
| sillon | §4.1 (« médiane de tous les sillons du GTFS ») | « de tous les sillons (les départs successifs d'une même liaison dans la journée) » |
| CTC | §5 (« s'exploite aujourd'hui en CTC ») | « en CTC (commande centralisée de la circulation, la signalisation actuelle) » |
| ETCS | §5 (« contrôle intégral de type ETCS ») | « de type ETCS (le standard européen de contrôle intégral en cabine) » |
| classe 7 / classes 8 et 9 | §6, escalier réglementaire | « (classe 7 américaine, c'est-à-dire la catégorie de voie 178-201 km/h du règlement fédéral américain) » ou une note de bas de table |
| prédicteurs | §4.3, pièces au dossier | « passages munis de prédicteurs (un équipement qui calcule l'instant d'arrivée du train pour déclencher les barrières) » |
| points de marge | constat 4 et §4 | à la première occurrence : « points de pourcentage de marge (ci-après " points ") » |
| mi/h | §4.1 (« 95 à 100 mi/h ») | note à la première occurrence : « les règles nord-américaines s'expriment en milles à l'heure ; 95 mi/h = 153 km/h » |

### P1-2. MAJEUR : « écartement effectif de 1 524 mm » tombe de nulle part

Localisation : §2.1, « Avec un écartement effectif de 1 524 mm, cette formule reproduit
exactement la méthode officielle du CN ».
Problème : le lecteur ne sait pas ce que l'écartement vient faire dans une formule de
dévers, ni pourquoi 1 524 et non 1 435. Deux lectures ne suffisent pas.
Correction proposée : « La formule dépend d'une constante géométrique, la distance entre
les points de contact rail-roue (1 524 mm en pratique nord-américaine, légèrement plus
que l'écartement nominal de 1 435 mm) ; avec cette valeur, elle reproduit exactement la
méthode officielle du CN [@cn2002mr1305]. »

### P1-3. MAJEUR : la table de synthèse n'est pas totalement autoportante

Localisation : p. 1, deux tables « Scénario × bande ».
Problème : « Temps de base » n'est défini qu'en §2 ; le lecteur de la seule p. 1 ne sait
pas si la marge est déjà dedans (le paragraphe au-dessus dit pourtant que le temps est la
somme de quatre termes dont la marge : friction). Les bornes de la fourchette ne sont
expliquées qu'au paragraphe suivant.
Correction proposée : ajouter sous chaque table une note d'une ligne :
« *Temps de base : courbes + zones urbaines figées + arrêts, sans marge d'exploitation.
Fourchette : base majorée de la marge normative internationale (9 %) à la marge portée par
l'horaire actuel de VIA sur ce tronçon.* »
La synthèse est par ailleurs bien autoportante : question, chiffres, bornes, réserves
(saison de restrictions, S3 hors précédent) et les cinq constats y sont.

### P1-4. MAJEUR : trois phrases-fleuves exigent deux lectures

1) §2.1, « Blocs urbains figés » : une seule phrase de six lignes énumère quatre blocs,
   leur source et l'hypothèse d'Ottawa. Correction : couper après « [@viarail2026gtfs] » ;
   nouvelle phrase : « Ottawa, sans gare d'approche proche, est traité par une fenêtre de
   10 km de part et d'autre [HYPOTHÈSE, couverte par la sensibilité de plus ou moins
   20 pour cent sur l'ensemble des blocs urbains]. »
2) §4.3, « Pièces au dossier » : dix lignes, quatre faits datés dans une seule phrase à
   points-virgules. Correction : passer en liste à puces (une pièce par puce, dates en
   tête), ce qui renforce d'ailleurs l'effet « pièces au dossier ».
3) §8, dernière phrase (« Tout ce que la présente étude compte [...] atterrir la
   marge. ») : couper après « et en borne le résultat. » puis : « Le temps de parcours
   final tombera dans les fourchettes de la synthèse. La seule question ouverte est de
   savoir où, entre la borne normative et la borne mesurée, le régime de cohabitation
   fixera la marge. »

### P1-5. MINEUR : lisibilité des tables

- Table §3 des scénarios : la colonne « k (v = k·√R) » est du grec pour le décideur ;
  ajouter en note : « *k : coefficient de la formule de vitesse en courbe (section 2) ;
  plus k est grand, plus vite dans la même courbe.* »
- Table §4.1 : préciser l'unité de « Dispersion entre sillons » (« écart interquartile,
  en % du temps de base ») en note.
- Table §6 : le titre de la table ne mentionne pas S3 (voir P3-2).

---

## Passe 2 : langue et typographie françaises

### P2-1. MINEUR : orthographe

- §2.3 : « l'état detaillé de la voie » → « l'état détaillé de la voie ».

### P2-2. MAJEUR (règle maison, systématique) : aucune espace insécable dans le document

Vérifié sur la source : zéro caractère U+00A0 ou U+202F. Toutes les espaces devant
« : », « ; », « % » sont des espaces ordinaires (risque de ponctuation orpheline en début
de ligne au rendu). De plus, §1 : « selon ce qu'on accepte d'y investir? » n'a aucune
espace devant « ? ».
Correction : passe globale remplaçant l'espace ordinaire par une insécable devant
« : ; ? % » (et insérer l'insécable manquante devant « investir? »), y compris dans
« 5 h 18 », « 1 432 km », « 95 mi/h » (insécables entre nombre et unité).

### P2-3. Règles maison vérifiées, conformes

- Tiret long « — » : **aucune occurrence** dans rapport.md. Conforme.
- « nous estimons » / estimation d'auteur : aucune. Les trois occurrences de « estim- »
  sont des négations volontaires (« n'est pas une estimation », « Jamais estimée »,
  « jamais des estimations d'auteur »). Conforme.

### P2-4. MINEUR : anglicismes et calques

- Titres §3 et constat 4 : « Ce que chaque scénario **achète** », « ce que le doublement
  **achète** » (calque de *what it buys*). Proposé : « Ce que chaque scénario apporte » /
  « ce que le doublement rapporte ». Si l'auteur tient à l'image comptable, la garder une
  seule fois, entre guillemets.
- §4.1 : « le chiffre se publie en fourchette, pas **au point** » (calque de *point
  estimate*). Proposé : « pas en valeur unique ».
- Constat 3 et §5 : « précédent **tarifé** au Michigan ». Proposé : « précédent chiffré ».
- §8 : « laissera **atterrir** la marge ». Proposé : « où le régime de cohabitation
  fixera la marge » (déjà intégré à P1-4.3).

### P2-5. MINEUR : formats de nombres et unités

- §1, deux fois : « en heures:minutes » (deux-points collés, format jamais utilisé
  ensuite : les temps sont notés « 4 h 00 »). Proposé : « en heures et minutes (h min) ».
- §2.1 et §7 : « ±20 pour cent » mélange symbole et toutes lettres. Proposé : « plus ou
  moins 20 pour cent » en prose (garder « ±20 % » dans les seules tables).
- Politique % : « pour cent » en prose, « % » en table. Globalement tenue ; l'exception
  est la table §3 des scénarios (« 100 % précédent CN »), acceptable puisque c'est une
  table.
- §1 : « de 14 pour cent [...] à 33 pour cent » puis constat 5 « 37 à 65 pour cent » :
  cohérent.

### P2-6. MINEUR : divers

- §1 : « les cinq obstacles qui **les** retiennent » : antécédent flou (les kilomètres?
  les voies?). Proposé : « les cinq obstacles qui retiennent ces voies ».
- §1 : « 250 et plus exige de **les** éliminer » : « les » peut lire « les passages et la
  signalisation ». Proposé : « 250 et plus exige d'éliminer les passages ».
- §3 : « l'article 4.3 du règlement canadien » voisine avec « section 4.3 » du présent
  rapport : risque de confusion. Proposé : « l'article 4.3 des Règles concernant la
  sécurité de la voie [@tc2022rrts] ».

---

## Passe 3 : cohérence interne des chiffres

Toutes les valeurs du texte ont été recalculées contre les CSV du dossier
`livrables/` (tbase_par_bande.csv, marges_2x2_synthese.csv, marges_par_intergare.csv,
passages_niveau_par_bande.csv, passages_niveau_tri.csv, cible_km_a_rectifier.csv,
covariables_paires.csv, blocs_urbains.csv, scenarios_parametres.csv).

### Vérifié conforme (rien à corriger)

- **Temps de base et fourchettes, synthèse et §7** : tous exacts. MTL-TO : S2@200
  239,5 min = 4 h 00, fourchette 4 h 21 à 4 h 34 ; S3@250 209,9 = 3 h 30, 3 h 49 à
  4 h 00 ; S3@300 194,5 min, 3 h 32 à 3 h 43. MTL-QC : S2@200 132,4 = 2 h 12, 2 h 24 à
  2 h 56 ; S3@250 117,9 = 1 h 58, 2 h 09 à 2 h 37. §7 : les 16 cellules concordent
  (borne × 1,09 et × marge actuelle du tronçon : 1,144 MTL-TO, 1,328 MTL-QC, 1,144
  MTL-Ott, 1,179 Ott-TO).
- **Marges actuelles** : « de 14 pour cent sur Montréal-Toronto à 33 sur Montréal-Québec » :
  14,4 % et 32,8 %, exact.
- **Km sous cible (§3 et constat 1)** : S1 620 / S2 267 / S3 186 km sous 200 km/h
  (CSV : 619,7 / 267,4 / 186,0) ; sous 160 : 326 / 122 / 59 (325,5 / 121,8 / 59,1) ;
  186/1 432 = 13,0 % ; « 87 pour cent du tracé atteint 200 ou plus » : exact.
- **Cellules de marge (§4.1)** : 11 / 5 / 2 paires ; médianes 37 / 42 / 65 %
  (36,8 / 42,0 / 65,2) ; dispersions 5 / 10 / 21 % (5,0 / 10,0 / 21,4) ; trafic 40 /
  12 à 14 / 27 trains/jour : tout concorde, y compris la déduplication des 11 paires
  doubles (19 lignes moins 8 doublons physiques).
- **« Environ 28 points »** : 65,2 moins 36,8 = 28,4 ; « une vingtaine de minutes sur
  Montréal-Québec » : 28 % du temps de base des deux paires en voie simple CN
  (18,0 + 60,3 min) = 21,9 min, exact.
- **Dispersion** : « de 8 à 16 minutes selon le sillon » = IQR des deux paires simple-CN
  (8,0 et 16,0 min), exact ; « jusqu'à 24 minutes » = 8 + 16 (voir P3-6).
- **Passages à niveau (§6 et constat 2)** : bandes S3 corridor dédoublonné 20 / 13 /
  137 / 754, total 924 : exact ; 352 publics à protection active et ancrage 304 : conformes
  au LISEZMOI ; tri 569 / 233 / 122 (somme 924) : exact.
- **Sud-ouest (§4.2)** : lignes simples CN à 8 trains/jour, vitesses permises 42 à
  70 mi/h (42,5-70) ; Chatham-Windsor : propriété VIA, 100 mi/h permis, moyenne 95 km/h
  (70,6 km / 44,5 min = 95,2) ; « 40-60 km/h de moyenne » (40,0 / 42,7 / 58,0) : exact.
- **Paramètres scénarios (§3)** : dévers 100/127/127 mm, insuffisances 76/152/270 mm,
  k = 3,83 / 4,82 / 5,75 (CSV : 3,832 / 4,824 / 5,755) : exact.
- **Blocs urbains** : 17,8 / 6,1 / 19,9 km conformes ; sauf Guildwood (voir P3-3).
- **Arrêts** : 5 min × 3 arrêts intermédiaires = 15 min dans tbase MTL-QC : cohérent.

### P3-1. BLOQUANT (rendu pandoc) : « S1@160 », « S2@200 », « S3@250 », « S3@300 » seront lus comme des citations

Localisation : §7, en-têtes de la table des résultats intégrés.
Problème : en Markdown pandoc avec --citeproc, « @160 », « @250 », « @300 » sont parsés
comme des clés de citation ; elles n'existent pas dans refs.bib, le rendu produira des
citations brisées du type « (160?) » et polluera la bibliographie (« @200 » entre en
collision partielle avec le contenu du .bib). Vérifié : les clés 160, 250, 300 sont
détectées comme citations manquantes.
Correction proposée : renommer les colonnes « S1, 160 | S2, 200 | S3, 250 | S3, 300 »
(cohérent avec « Scénario × bande » de la synthèse), ou échapper : « S1\@160 ».

### P3-2. BLOQUANT (fait) : « 95 à 100 mi/h permis partout » est contredit par les données

Localisation : §4.1, « sur le cœur du corridor (classe de voie homogène, 95 à 100 mi/h
permis partout) ».
Problème : covariables_paires.csv, cellule simple-VIA du cœur : trois paires sur cinq
(Coteau-Alexandria, Alexandria-Casselman, Casselman-Ottawa) sont à 80 mi/h permis,
médiane de la cellule 80. Le « partout » est faux. L'argument anti-objection du
paragraphe suivant, lui, est correct (il ne compare que CN simple 95 contre CN double
95-100).
Correction proposée : « sur le cœur du corridor (classe de voie comparable : 95 à
100 mi/h permis sur les lignes du CN, 80 à 95 sur celles de VIA) ». Et vérifier que la
comparaison VIA-simple contre CN-double (« 3 à 6 points ») tient en le disant : la voie
de VIA est permise un cran moins vite, ce qui joue contre VIA dans la mesure et renforce
la conclusion.

### P3-3. BLOQUANT (chiffre) : bloc urbain Guildwood-Toronto

Localisation : §2.1, « Guildwood à Toronto Union (20,2 km) ».
Problème : blocs_urbains.csv donne longueur_km = 20,1 (bornes 423,93-444,05 et
517,94-538,06, soit 20,12 km).
Correction : « (20,1 km) ».

### P3-4. BLOQUANT (chiffre non appuyé) : « quelque 1 150 km de voies existantes »

Localisation : §1, mise en regard avec Alto.
Problème : aucun fichier du dossier ne donne 1 150. La somme des quatre trajets est
1 437 km (marges_par_intergare.csv) et le réseau physique unique (hors chevauchements
Montréal-Dorval et Brockville-Toronto, flag doublon_physique_de) est de 1 086 km.
Correction proposée : « les quelque 1 090 km de voies existantes du corridor riverain »
(ou le chiffre canonique du projet, avec sa source ; en l'état, 1 150 n'est traçable
nulle part).

### P3-5. BLOQUANT (cohérence d'arrondi) : 1 432 km contre 1 437 et 1 438

Localisation : §3, « somme des quatre trajets analysés, 1 432 km » ; constat 1
(« 13 pour cent du réseau parcouru »).
Problème : la somme des paires intergares donne 1 437,2 km ; la somme des distances
affichées dans les tables (270 + 185 + 444 + 539) donne 1 438. Le 1 432 provient
vraisemblablement d'un autre périmètre de mesure. Un lecteur qui additionne la table §7
tombe sur l'écart. (13 % tient dans tous les cas : 186/1 432 = 13,0 ; 186/1 437 = 12,9.)
Correction : harmoniser sur une seule valeur et la nommer (« 1 437 km mesurés sur le
tracé, soit les quatre distances affichées »), ou expliquer l'écart en une parenthèse.

### P3-6. MINEUR : « jusqu'à 24 minutes » est une somme de pires cas

Localisation : §4.1, « Le passager de Montréal-Québec paie jusqu'à 24 minutes selon
l'heure de son départ. »
Problème : 24 = 8 + 16, la somme des écarts interquartiles des deux paires, en supposant
le pire cas simultané sur les deux ; le calcul n'est pas donné.
Correction proposée : « Le passager de Montréal-Québec paie jusqu'à 24 minutes selon
l'heure de son départ (somme des deux écarts, si les deux paires jouent contre lui). »

### P3-7. MINEUR : arrondis des temps incohérents entre eux

- MTL-QC horaire actuel : 202,5 min publié « 3 h 22 » (arrondi vers le bas) alors que
  S1@160 152,5 min est publié « 2 h 33 » (arrondi vers le haut) et MTL-TO S3@300
  194,5 min « 3 h 15 » (vers le haut).
- Correction : fixer la règle (arrondi au plus proche, ,5 vers le haut) et corriger
  « 3 h 22 » en « 3 h 23 » (synthèse et §7), ou documenter la convention.

### P3-8. MINEUR : « 3 à 6 points » et « 27 à 33 points » non traçables tels quels

Localisation : constat 4 et §4.1.
Problème : les médianes donnent 5,2 et 28,4 points ; les fourchettes 3-6 et 27-33
(attribuées à la sensibilité « pénalité d'arrêt de 0 à 3 minutes ») ne figurent dans
aucun CSV livré. Elles sont plausibles et encadrent bien les médianes, mais un vérificateur
externe ne peut pas les reproduire.
Correction : publier la petite table de sensibilité en annexe numérique, ou écrire
« environ 5 points [...] environ 28 points » et réserver les fourchettes à l'annexe.
Même remarque pour la ligne « Sous 100 km/h : présentes / résiduelles / zéro » (§3) :
la cible 100 km/h n'existe pas dans cible_km_a_rectifier.csv ; chiffrer ou renvoyer
explicitement à l'annexe.

---

## Passe 4 : structure et argumentation

### P4-1. Couverture des cinq constats : complète

Constat 1 (géométrie) → §3 ; constat 2 (passages) → §6 ; constat 3 (signalisation) → §5 ;
constat 4 (cohabitation/doublement) → §4 ; constat 5 (marge) → §4.3 et §8. Aucun constat
orphelin, aucune section sans constat.

### P4-2. MAJEUR : l'ordre des sections ne suit pas l'ordre des constats

Les constats annoncent passages (2) puis signalisation (3) ; le corps traite
signalisation (§5) puis passages (§6). Le lecteur pressé qui navigue depuis la synthèse
fait un aller-retour.
Correction : inverser §5 et §6 (passages d'abord, c'est l'obstacle « dominant » selon le
texte lui-même, la signalisation « ligne de devis » ensuite : l'ordre décroissant d'enjeu
est aussi le bon ordre rhétorique). Renuméroter les renvois (« voir sections 5 et 6 »
de la synthèse reste valable si l'on écrit « voir les sections Passages à niveau et
Signalisation »).

### P4-3. MAJEUR : le constat 2 omet de dire qu'il est compté en S3

Localisation : constat 2, « 754 des 924 passages du corridor se trouvent sur des
segments dont la géométrie dépasserait ce seuil ».
Problème : ce compte dépend du scénario (S2 : 695 ; S1 : 471). Le §6 le précise, la
synthèse non ; or la synthèse doit se suffire.
Correction : « 754 des 924 passages du corridor se trouvent sur des segments dont la
géométrie, avec le pendulaire moderne (S3), dépasserait ce seuil ».

### P4-4. MAJEUR : citations manquantes sur des affirmations sourçables

- Constat 3 et §5 : « c'est le devis d'Alto » (deux fois) sans clé. Ajouter [@alto2025]
  au moins en §5.
- §5 : « Le corridor s'exploite aujourd'hui en CTC à ces vitesses ; il n'existe pas de
  règle canadienne imposant un plafond du type « 79 mi/h » américain » : affirmation
  réglementaire négative sans clé. Adosser au règlement : « [@tc2022rrts] » ou renvoyer
  à l'annexe réglementaire du projet.
- §4.3 : « Sur Montréal-Toronto [...] un dépassement se règle à 15 mi/h ou à 45-50 mi/h
  selon l'aiguillage » : chiffres d'aiguillage sourçables sans clé ; sourcer ou marquer
  \[à sourcer\].
- §6 : le marqueur \[SOURCE tertiaire, à consolider : @wiki2025turbo\] est honnête mais
  doit être résolu avant publication (idem [@wiki2025lrc] en §3 : Wikipédia deux fois en
  bibliographie d'un rapport de décision, à remplacer par les sources primaires).

### P4-5. MAJEUR : placeholders à résoudre avant toute diffusion

- En-tête YAML : « [AUTEUR À COMPLÉTER] ».
- Les deux marqueurs \[HYPOTHÈSE\] (§2.1 Ottawa, §6 fermetures) sont assumés et bien
  placés : les garder, mais en encadré ou note plutôt qu'entre crochets dans la phrase.

### P4-6. MAJEUR : redites à couper (tenue du 13-15 pages avec figure)

L'encadrement de la marge est exposé quatre fois : synthèse (paragraphe « La fourchette
de marge n'est pas une estimation »), constat 5, §4.3, conclusion §8. Les deux premiers
et §4.3 se justifient (annonce, constat, démonstration) ; la conclusion re-déroule le
mécanisme au complet.
Correction : dans §8, supprimer « le temps de parcours final tombera [...] atterrir la
marge » au profit de la version courte proposée en P1-4.3 ; gain d'environ un tiers de
page. De même, « l'étude de circulation » est nommée cinq fois (synthèse, §4.3 fin, §5,
§8 deux fois) : garder synthèse et §8, alléger §5 (« elle vit dans le paquet capacité de
l'étude recommandée en conclusion »).

### P4-7. MAJEUR : place de la figure à ajouter

Le rapport n'a aucune figure. La place la plus rentable pour un décideur : une carte du
corridor en §4 (cellules voie simple/double × propriétaire, avec les deux paires
simple-CN de Québec en évidence), ou un profil de vitesse S3 en §3 (les 186 km résiduels
localisés). La carte §4 sert deux constats (4 et 5) ; c'est le meilleur ratio.

### P4-8. Réserves méthodologiques : bien placées, une exception

La réserve « saison 2026 de restrictions exceptionnelles » apparaît en §2.3 et est
rappelée en §8 : exactement là où le sceptique l'attend. La réserve sur l'échantillon
mince (« deux paires ») est donnée au moment du chiffre : bien. La réserve S3
(« hors précédent NA ») est dans la synthèse et développée §3 : bien. Exception : la
réserve « les lignes de VIA portent deux fois moins de trains » (§4.1) mériterait d'être
rappelée d'un mot au constat 4, qui est cité tel quel dans la synthèse (« mesuré [...]
au sens large, densité de fret comprise »).

---

## Verdict d'ensemble

Le rapport est solide sur le fond : sur la centaine de valeurs vérifiées contre les
fichiers du dépôt, la quasi-totalité concorde exactement, la discipline « comptes et
bornes, jamais d'estimation » est réellement tenue, et l'architecture synthèse-constats-
sections se referme proprement. Les corrections indispensables avant diffusion sont peu
nombreuses mais réelles : le bug de citation des en-têtes « S1@160 », le « 1 150 km »
introuvable, le « 95 à 100 mi/h partout » contredit par la cellule VIA, deux arrondis, et
une passe complète d'espaces insécables et de définitions d'acronymes. Une demi-journée
de travail éditorial suffit ; aucun constat n'est à retirer, aucun calcul de fond n'est à
refaire.

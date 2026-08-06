# Registre des sources (rapport minimal, 2026-08)

Règle du projet : chaque affirmation sourçable du rapport porte une référence APA (7e éd.)
inscrite ici à mesure que le travail avance, y compris les affirmations avancées par le
plan de match v3. Statuts : **VÉRIFIÉE** (document en main ou URL consultée et confirmée),
**À TROUVER** (affirmée de mémoire, à retrouver avant toute citation au rapport),
**INTROUVABLE** (recherchée sans succès : l'affirmation est retirée ou étiquetée HYPOTHÈSE).

Clé = clé BibTeX dans `refs.bib`. Une source n'entre dans `refs.bib` que lorsqu'elle est VÉRIFIÉE.

Vérifications web du 2026-08-06 : deux passes de recherche (réglementaire ; faits canadiens),
verdicts reportés ci-dessous. **Les corrections aux affirmations du plan v3 sont en gras.**

---

## VÉRIFIÉES (en main)

### `cn2002mr1305`
- **APA** : Canadien National. (2002, décembre). *MR 1305-0 : méthode de calcul des vitesses en courbe* [circulaire technique interne]. Compagnie des chemins de fer nationaux du Canada.
- **Local** : `ressources/formules CN.pdf` (PDF numérisé, sans texte extractible)
- **Appuie** : formule D = 0,0007·C·V² − Dd ; insuffisance voyageurs 3 po ; insuffisance LRC 6 po ; dévers max standard 5 po (127 mm). Base des scénarios S1/S2.
- **Statut** : VÉRIFIÉE (fourni par le collaborateur du CN). Titre exact et date sur le document à confirmer à la relecture.

### `tc2022rrts`
- **APA** : Transports Canada. (2022). *Règlement concernant la sécurité de la voie (Rules Respecting Track Safety), partie II, Subpart C : Track geometry* (en vigueur le 1er février 2022). Gouvernement du Canada. https://tc.canada.ca/en/rail-transportation/rules/2022-2023/rules-respecting-track-safety/subpart-c
- **Appuie** : plafonds S1 ; art. 4.1 (dévers max 7 po) ; art. 4.2 (formule à 3 po d'insuffisance) ; **art. 4.3 confirmé mot pour mot** : « A track owner or a railway company may request approval from Transport Canada to operate specified railway equipment at a level of cant deficiency greater than 3 inches » = la voie d'approbation par équipement pour le pendulaire (S2/S3).
- **Statut** : VÉRIFIÉE (2026-08-06). PDF consolidé : https://tc.canada.ca/sites/default/files/2021-12/rules_respecting_track_safety_december_15_2021.pdf

### `viarail2026gtfs`
- **APA** : VIA Rail Canada. (2026). *Données GTFS du réseau VIA Rail* [jeu de données]. https://www.viarail.ca/fr/developpeurs
- **Local** : `ressources/viarail_GTFS.zip`
- **Appuie** : horaires actuels (blocs urbains, T_horaire par inter-gare, marges du 2×2).
- **Statut** : VÉRIFIÉE (date de version du flux à lire dans feed_info.txt et à reporter ici).

### `osm2026geofabrik`
- **APA** : OpenStreetMap contributors. (2026). *Extraits Ontario et Québec* [données cartographiques]. Geofabrik. https://download.geofabrik.de/
- **Local** : dans le projet parent (`ressources/*.osm.pbf`, extraits du 2026-05-10) ; non copiés ici (taille).
- **Appuie** : géométrie des voies (rayons de courbure, tracés). Le parquet dérivé est dans `intermediaires/`.
- **Statut** : VÉRIFIÉE.

### `ecfr213-347`
- **APA** : Federal Railroad Administration. (s. d.). *Automotive or railroad crossings at grade*, 49 C.F.R. § 213.347. Electronic Code of Federal Regulations. https://www.ecfr.gov/current/title-49/section-213.347
- **Appuie** : élément 4, marches hautes de l'escalier PN. Texte exact vérifié : (a) aucun passage à niveau sur voie de classe 8-9 (>125 mph = 201 km/h, via §213.307) ; (b) en classe 7 (111-125 mph = 178-201 km/h), « warning/barrier system » complet approuvé FRA et fonctionnel. **Nuance : (b) ne se limite pas aux barrières-obstacles, c'est un système complet approuvé FRA.**
- **Statut** : VÉRIFIÉE (2026-08-06, via l'API officielle eCFR).

### `tc2023inventairepn`
- **APA** : Transports Canada. (2023). *Inventaire des passages à niveau* [jeu de données]. Gouvernement du Canada, Portail du gouvernement ouvert. https://ouvert.canada.ca/data/fr/dataset/d0f54727-6c0b-4e5a-aa04-ea1463cf9f4c
- **Appuie** : élément 4, jointure PN. Champs confirmés : lat/long, protection (ex. « Active - FLBG »), autorité routière, juridiction F/P, subdivision + point milliaire, trafics, vitesse max train, urbain ou non. CSV EN direct : https://open.canada.ca/data/dataset/d0f54727-6c0b-4e5a-aa04-ea1463cf9f4c/resource/a53fda5b-134f-449d-a639-9b896065fc21/download/en-grade-crossing-inventory-2023-update.csv
- **Statut** : VÉRIFIÉE (2026-08-06). À télécharger dans `ressources/` à l'étape 3.

### `fra2024itcs`
- **APA** : Federal Railroad Administration. (2024, 26 juin). *Incremental Train Control System*. U.S. Department of Transportation. https://railroads.dot.gov/research-development/program-areas/train-control/ptc/incremental-train-control-system
- **Appuie** : élément 3, marche 161-200 km/h. Confirmé : superposition en cabine (PTC) sur signalisation existante, 66 milles Kalamazoo-New Buffalo (ligne Amtrak Michigan), 110 mph atteint en février 2012 (paliers 79→90→95→110). **Coûts : la page FRA n'en donne pas ; 21,7 M$ US (essais) vient de Progressive Railroading 2006, source secondaire, à étiqueter comme telle si citée.**
- **Statut** : VÉRIFIÉE (2026-08-06).

### `bienaime2009sealed`
- **APA** : Bien-Aime, P. (2009). *North Carolina « Sealed Corridor » Phase I, II, and III assessment* (rapport n° DOT/FRA/ORD-09/17). Federal Railroad Administration, U.S. Department of Transportation. https://railroads.dot.gov/sites/fra.dot.gov/files/fra_net/300/ord0917.pdf
- **Local** : `ressources/FRA_sealed_corridor_ord0917.pdf`
- **Appuie** : élément 4, marche 154-177 (corridor scellé). **CORRECTION au plan v3 : le « −75 % de mortalité phase I » est faux tel quel.** Chiffres réels du rapport : ≥19 vies sauvées 1995-2004 (189/216 passages traités) ; réduction projetée de la mortalité du corridor complet ≈ 52-53 % (à 110 mph) ; le 75 % = efficacité des barrières à bras longs (réduction des collisions) et de la canalisation du trafic ; quatre-quadrants + terre-plein = 92 %, fermeture/saut-de-mouton = 100 %.
- **Statut** : VÉRIFIÉE (2026-08-06, rapport dépouillé). Rapport phase I au Congrès (2001) : https://rosap.ntl.bts.gov/view/dot/34005 (clé secondaire possible `fra2001sealed`).

### `uic2000f451`
- **APA** : Union internationale des chemins de fer. (2000). *Marges de régularité à prévoir dans les horaires dans le but de garantir la ponctualité du service : marges de régularité* (fiche UIC 451-1/F/4, 4e éd., ISBN 2-7461-0221-8). UIC.
- **Appuie** : élément 5, borne basse de la marge. **RÉSOLU (2026-08-06) : les valeurs chiffrées sont reproduites intégralement (tableaux 4-6) dans `schittenhelm2011`, source évaluée par les pairs — achat de la fiche non nécessaire.** Valeurs : voyageurs tractés = 1,5 min/100 km + 3-7 % selon masse/vitesse ; automotrices = 1,0 min/100 km + 3-7 % ; total ≈ 7 % à 160 km/h, 9 % à 200 (tracté ≤300 t).
- **Statut** : VÉRIFIÉE (texte intégral non consulté ; valeurs par source secondaire fiable, citer les deux ensemble).

### `schittenhelm2011`
- **APA** : Schittenhelm, B. (2011). *Planning with timetable supplements in railway timetables*. Trafikdage på Aalborg Universitet 2011 (ISSN 1603-9696). https://journals.aau.dk/index.php/td/article/download/5554/4887
- **Local** : `ressources/schitt2011.pdf`
- **Appuie** : valeurs UIC 451-1 (tableaux 4-6 reproduits) ; décomposition canonique du temps horaire en 4 termes (marche minimale, arrêts, suppléments, attente programmée) : LA grille pour ne pas confondre marge UIC et agrégat type WCML ; repère mesuré Copenhague-Odense 16,3 % (ratio ~0,86 sans fret). Auteur DTU + Rail Net Denmark. NB : le DOI 404, citer l'URL directe.
- **Statut** : VÉRIFIÉE (2026-08-06).

### `sncf2023drr`
- **APA** : SNCF Réseau. (2023). *Document de référence du réseau : annexe 4.1, horaire de service 2025* (version du 7 décembre 2023). https://www.sncf-reseau.com/medias-publics/2023-12/DRR2025-annexe-4-1.pdf
- **Local** : `ressources/sncf.pdf`
- **Appuie** : règle primaire publiée : marge de régularité **4,5 min/100 km** lignes classiques (Marge-A 2 + Marge-T 2,5) ; **5 %** LGV ; dérogation ≥3 min/100 km sous analyse de risque.
- **Statut** : VÉRIFIÉE (2026-08-06, mot pour mot).

### `trafikverket2025jnb`
- **APA** : Trafikverket. (2025). *Järnvägsnätsbeskrivning 2027, annexe 4 D : Kvalitetstillägg* (éd. du 5 décembre 2025). https://bransch.trafikverket.se/contentassets/6526f430ae7f489aae8e88c06f2eef6b/jnb-2027-2025-12-05.pdf
- **Local** : `ressources/jnb.pdf`
- **Appuie** : élément 2 ET 5 : le gestionnaire suédois CHIFFRE la pénalité de voie : **voie unique 3 min/100 km vs double voie 2 min/100 km**, + 60 s par croisement (120 s si passage sans arrêt) ; pendulaire X2 : 1 min/100 km. Corroboration indépendante de ce que notre 2×2 mesure.
- **Statut** : VÉRIFIÉE (2026-08-06).

### `amtrakoig2019`
- **APA** : Amtrak Office of Inspector General. (2019, 14 octobre). *Train operations : Better estimates needed of the financial impacts of poor on-time performance* (OIG-A-2020-001). https://amtrakoig.gov/sites/default/files/reports/OIG-A-2020-001%20OTP%20mandate.pdf
- **Local** : `ressources/amtrak.pdf`
- **Appuie** : analogue nord-américain primaire de la cohabitation VIA/CN : California Zephyr Reno-Sacramento = 52 min de tampon intégré (ratio idéal/commercial **0,846**) ; « ~70 % du temps additionnel des horaires = retards anticipés des chemins de fer hôtes » ; fret responsable de ~59 % des retards longs parcours ; 32,8 M$ US/an de paiements incitatifs aux hôtes.
- **Statut** : VÉRIFIÉE (2026-08-06).

### `uic2004c406`
- **APA** : Union internationale des chemins de fer. (2004). *Capacity* (fiche UIC 406, 1re éd.). UIC.
- **Local** : `ressources/uic406.pdf`
- **Appuie** : « The value of this time supplement is about 5 % of journey time » : corroboration UIC gratuite de l'ordre de grandeur.
- **Statut** : VÉRIFIÉE (2026-08-06).

### `via2024requete`
- **APA** : La Presse Canadienne. (2024, 13 novembre). *Via Rail seeks judicial review of CN Rail's speed restrictions*. Global News. https://globalnews.ca/news/10868587/via-rail-judicial-review-cn-rail-speed-restrictions/
- **Appuie** : élément 4, le compte opposable de **304 passages à prédicteurs** (CONFIRMÉ). Avis de demande de contrôle judiciaire déposé en Cour fédérale le 12 novembre 2024 contre le « Crossing Supplement for VIA Venture Equipment » du CN (11 octobre 2024). Suite : demande radiée le 20 février 2025 (juge adjointe Moore : le CN n'est pas un « office fédéral ») ; appel ; recours parallèle en Cour supérieure du Québec (65 passages Québec-Montréal). Corroboration : Trackside Treasure (déc. 2024), blogue spécialisé citant les actes.
- **Statut** : VÉRIFIÉE via presse. **Idéal avant publication : citer l'avis de demande lui-même (numéro de dossier non retracé en source ouverte ; piste : CanLII / registre de la Cour fédérale).**

### `tc2025gcp`
- **APA** : Transports Canada. (2025). *3. PIC — Operating restrictions for VIA Rail in the Quebec City-Windsor corridor* [cahier de transition]. Gouvernement du Canada. https://tc.canada.ca/en/binder/3-pic-operating-restrictions-via-rail-quebec-city-windsor-corridor
- **Appuie** : élément 5, pièces factuelles. Confirmé : 11 octobre 2024, le CN impose aux rames Venture (<32 essieux) 72 km/h aux passages à prédicteurs (vs jusqu'à 160), retards 30-45 min. **CORRECTION au plan v3 : l'ordre ministériel TC (10-12 décembre 2024) était un ordre de PRODUCTION D'INFORMATION au CN, pas un rétablissement des vitesses. Les restrictions ont duré toute l'année 2025 ; allègement négocié (« speed tables ») en vigueur le 28 août 2025 seulement ; budget 2025 : 15 M$ pour un pilote de shunt enhancers.**
- **Statut** : VÉRIFIÉE (2026-08-06).

### `cbc2025pilote`
- **APA** : CBC News. (2025, 29 septembre). *Via postpones direct Montreal-Toronto pilot*. https://www.cbc.ca/news/canada/ottawa/via-montreal-toronto-pilot-that-skipped-eastern-ontario-postponed-1.7646512
- **Appuie** : borne mesurée des arrêts (~30-40 min pour 4 arrêts sautés : Cornwall, Brockville, Kingston, Belleville) et pièce factuelle de cohabitation. Confirmé : pilote annoncé le 19 septembre 2025, départ prévu le 29 septembre, suspendu le jour même. **Nuance de formulation : VIA a annoncé la suspension en invoquant des « contraintes opérationnelles » avec le CN ; les sources ne disent pas formellement que « le CN a suspendu ».**
- **Statut** : VÉRIFIÉE (2026-08-06). Corroboration : La Presse Canadienne via CP24, même date.

### `via2025rapports`
- **APA** : VIA Rail Canada. (2025). *Rapport annuel 2024*. https://media.viarail.ca/sites/default/files/publications/VIA-Rail_Annual-Report_2024.pdf ; VIA Rail Canada. (2025). *Rapport du premier trimestre 2025*. https://media.viarail.ca/sites/default/files/publications/2025_VIA-Rail_First-Quarter-Report.pdf
- **Appuie** : trajectoire de ponctualité. **CORRECTION au plan v3 : la trajectoire « 71→51→30 » doit être précisée** : ponctualité réseau 2020 : 71 % ; 2021 : 72 % ; 2022 : 57 % ; 2023 : 59 % ; 2024 : 51 % (T4 2024 : 34 %) ; T1 2025 : 30 % (vs 72 % au T1 2024). Le 30 % est TRIMESTRIEL, pas annuel ; chiffres réseau (le corridor est présenté séparément, rapport annuel 2024, p. 8, à relire pour les valeurs corridor).
- **Statut** : VÉRIFIÉE (2026-08-06).

### `alto2025`
- **APA** : Alto. (2025). *About Alto*. https://www.altotrain.ca/en/about-alto
- **Appuie** : ligne de mise en regard de la synthèse. Confirmé : ≈ 1 000 km de voies dédiées et électrifiées (Toronto, Peterborough, Ottawa, Montréal, Laval, Trois-Rivières, Québec), ≥300 km/h. **Nuance : corridor d'étude (~10 km de large), pas un tracé arrêté (consultations début 2026).** Repère : itinéraire riverain actuel Québec-Toronto ≈ 810-850 km ; corridor VIA Québec-Windsor ≈ 1 150 km. Corroboration : Bureau des grands projets, https://www.canada.ca/en/privy-council/major-projects-office/projects/other/referred/alto.html
- **Statut** : VÉRIFIÉE (2026-08-06).

### `wiki2025turbo`
- **APA** : Wikipédia. (2025). *UAC TurboTrain*. https://en.wikipedia.org/wiki/UAC_TurboTrain
- **Appuie** : élément 4, précédent domestique du plafond PN (citer comme seuil, jamais comme temps de parcours). Confirmé : limité à 95 mi/h (153 km/h) en service à cause des passages à niveau ; record 140,55 mi/h (226 km/h) le 22 avril 1976 près de Gananoque. **CORRECTION au plan v3 : « ~300 passages » est imprécis : ≈ 240 passages publics + ≈ 700 privés/agricoles Montréal-Toronto. Formulation sûre : « plus de 200 passages publics, près d'un millier en comptant les privés ».** Source tertiaire : avant publication, remonter à une source primaire (rapports CN/MOT de l'époque) ou étiqueter.
- **Statut** : VÉRIFIÉE (source tertiaire ; corroboration High Speed Rail Canada, 2018).

### `fra-lrc-152`
- **APA** : Federal Railroad Administration. (s. d.). *Mixed freight and higher-speed passenger trains* [Superelevation]. U.S. Department of Transportation. https://railroads.dot.gov/sites/fra.dot.gov/files/fra_net/19085/Superelevation.pdf
- **Appuie** : précédent LRC 6 po : « For LRC equipment, Eu is 6 inches » (avec inclinaison hydraulique jusqu'à 8,5°). Complète `cn2002mr1305` côté source publique.
- **Statut** : VÉRIFIÉE (2026-08-06).

### `lrc-opex-tilt`
- **APA** : Wikipédia. (2025). *LRC (train)*. https://en.wikipedia.org/wiki/LRC_(train) ; Trackside Treasure. (2022, avril). *Light-Rapid-Comfortable — VIA's LRC*. http://tracksidetreasure.blogspot.com/2022/04/light-rapid-comfortable-vias-lrc.html
- **Appuie** : l'histoire OPEX du tilt (élément 1) : pannes dès 1981 (caisses verrouillées inclinées, hydraulique), refonte Bombardier 1985-1987, système souvent puis définitivement désactivé ; mécanisme retiré à la remise à neuf de 2007 (moins d'entretien, −2 t par voiture).
- **Statut** : VÉRIFIÉE (sources tertiaires convergentes ; suffisant pour un fait de contexte, à étiqueter si contesté).

---

## À TROUVER

| Clé provisoire | Affirmation à appuyer | Piste |
|---|---|---|
| `via2024avis-cf` | Texte de l'avis de demande de VIA (12 nov. 2024, Cour fédérale) et décision de radiation (20 févr. 2025) : citations directes des 304 passages | CanLII (décision Moore), registre Cour fédérale ; renforcerait `via2024requete` |
| `wcml-072` | Ratio WCML ~0,72 commercial/plafond | Aucune source ne publie le 0,72 directement ; il se RECONSTRUIT (399 mi, 125 mph, 4 h 25 → 0,723) mais sur distance/temps Wikipédia : resourcer Network Rail/ORR avant publication. ⚠ MÉTHODO : 0,72 = agrégat (marge + arrêts + ralentissements + attente de cohabitation), PAS une marge UIC (aucune règle publiée ne dépasse 15 %) ; utiliser la décomposition de `schittenhelm2011` |
| `en13803` | EN 13803 : limites d'insuffisance pour matériel pendulaire (appuie S3 270 mm et la sensibilité 225 mm) | CEN ; norme payante, chercher valeurs citées dans littérature ouverte |
| `tfl-nr-marges` | Rail for London 10 % (TPR 2026) et Network Rail ~5 % | Mentionnés par l'agent mais NON revérifiés sur les primaires : à confirmer avant citation |
| `via-ponctualite-corridor` | Valeurs de ponctualité CORRIDOR (vs réseau) par année | Rapport annuel VIA 2024, p. 8 (graphique) : relire le PDF et extraire |

Note d'usage : dans les brouillons, une affirmation non encore vérifiée est étiquetée
[À VÉRIFIER : clé] dans le texte. Le rapport final ne peut contenir aucune de ces étiquettes.

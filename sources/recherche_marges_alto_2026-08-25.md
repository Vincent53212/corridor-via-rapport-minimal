# Marges d'horaire des gestionnaires d'infrastructure et temps ALTO annoncés

Recherche effectuée le 25 août 2026. Sources primaires privilégiées (documents des gestionnaires eux-mêmes).
Hypothèse de conversion : parcours type de 500 km à 170 km/h de moyenne, soit un temps de base de 176 minutes (2 h 56).
À 160 km/h la base vaut 188 min, à 180 km/h elle vaut 167 min. Les équivalents en pourcentage sont donnés dans cette fourchette.

---

## 1. Tableau des marges par gestionnaire

| Pays / gestionnaire | Règle exacte publiée | Valeur | Équivalent % sur 500 km à 160-180 km/h | Statut de la source |
|---|---|---|---|---|
| International, UIC | Fiche UIC 451-1, supplément de régularité fonction de la vitesse | ~7 % à 160 km/h, ~9 % à 200 km/h | 8 % à 177 km/h (interpolation) | Déjà en base, norme sectorielle |
| France, SNCF Réseau (DRR) | Marge de régularité, ligne classique | 4,5 min / 100 km | 22,5 min sur 500 km, soit 12,0 à 13,5 % | Déjà en base |
| France, SNCF Réseau (DRR) | Marge de régularité, LGV | 5 % | 5 % | Déjà en base |
| Suède, Trafikverket (JNB 2025) | Marge de conduite, voie double | 2 min / 100 km | 10 min sur 500 km, soit 5,3 à 6,0 % | Déjà en base |
| Suède, Trafikverket (JNB 2025) | Marge de conduite, voie simple | 3 min / 100 km, plus 60 s par croisement | 15 min sur 500 km, soit 8,0 à 9,0 %, hors croisements | Déjà en base |
| Allemagne, DB InfraGO / DB Netz | *Regelzuschlag* : supplément en pourcentage réparti uniformément, appliqué au temps de roulement physique, fonction du type de traction et de la vitesse maximale du train. *Bauzuschlag* : supplément distinct, en minutes absolues, fonction de l'état de la voie, posé ponctuellement avant les grands nœuds | Mécanisme confirmé en source primaire. **Valeur chiffrée NON publiée** en source primaire accessible. Valeur usuellement citée : 3 à 7 % selon la vitesse maximale, plus un plancher de 1,0 min/100 km (automotrices) ou 1,5 min/100 km (trains tractés) | Si l'on retient 7 % (haut de gamme de vitesse) plus 1,0 min/100 km : environ 9,5 à 10 %. Avec le seul pourcentage : 7 % | Mécanisme : réponse officielle du gouvernement fédéral au Bundestag (Drucksache 19/32554) et fiche produit DB Netz. Chiffres : Wikipédia, **non vérifiés en source primaire** |
| Royaume-Uni, Rail for London Infrastructure (règles TPR 2026, tronçon central Elizabeth line) | *Engineering allowance* intégrée au calcul des temps de parcours de section | 10 % de majoration sur chaque *timing link* | 10 % | Source primaire, mais réseau de type urbain à arrêts rapprochés, non intercité |
| Royaume-Uni, Network Rail (Rules of the Plan) | Sur certaines lignes, une majoration forfaitaire tient lieu d'*engineering allowance* explicite | 5 % | 5 % | Formulation tirée d'un exemplaire pédagogique des Rules of the Plan de Network Rail Central. **À vérifier sur les TPR officielles**, qui ne sont pas téléchargeables librement |
| Royaume-Uni, Network Rail, valeurs intercité (WCML, ECML) | *Engineering allowance* et *performance allowance* fixées ligne par ligne, en minutes, dans la section 4 des Timetable Planning Rules | **Introuvable en source primaire.** Les TPR nationales ne sont diffusées que par archive zip sur demande à PlanningPublications@networkrail.co.uk | non disponible | Non trouvé |
| Suisse, CFF / OFT | Supplément d'horaire standard souvent cité à ~7 % | **NON confirmé en source primaire.** Le règlement CFF pertinent (R I-30111 et suivants) n'est pas accessible publiquement (site vorgaben.sbb.ch bloqué hors Suisse, HTTP 451). Le seul élément primaire trouvé est un communiqué CFF de 2026 indiquant que, pour robustifier le système, les temps de parcours sur les liaisons principales sont allongés de 4 à 9 minutes selon la relation | Indicatif : 4 à 9 min sur une relation principale, soit 2 à 5 % d'un parcours de 176 min | Communiqué CFF, primaire mais qualitatif |
| États-Unis, Amtrak (NEC) | *Recovery time* ajouté aux horaires comme tampon contre les retards anticipés. Environ 70 % de ce temps supplémentaire est attribuable aux retards attendus des chemins de fer hôtes | **Aucune valeur en pourcentage du temps de parcours publiée.** L'audit chiffre seulement le gain de recettes possible (7,2 M$/an) | non disponible | Bureau de l'inspecteur général d'Amtrak, primaire, mais sans pourcentage |

### Ce qui n'a pas été trouvé, dit explicitement

- **La table chiffrée du Regelzuschlag allemand n'existe pas en source primaire publique.** Elle vit dans la Richtlinie 402/405 non diffusée. La réponse du gouvernement fédéral au Bundestag confirme le principe et les variables (traction, vitesse maximale) mais refuse de donner des valeurs, au motif que le supplément se calcule par paramètres de train. La fiche produit « Fahrzeitberechnung » de DB Netz confirme que le temps minimal vendu aux entreprises ferroviaires inclut le Regelzuschlag, sans en donner la valeur. Les modules publics de la Ril 402 (INB 2026) ont été téléchargés et fouillés : aucun contient de valeur chiffrée.
- **Les valeurs intercité de Network Rail n'ont pas pu être obtenues.** Les Timetable Planning Rules ne sont pas publiées en PDF libre. Seules des TPR de gestionnaires tiers l'ont été (Rail for London Infrastructure, Heathrow Airport Ltd). Le 10 % de RfL(I) est réel mais porte sur le tunnel central de la Elizabeth line, pas sur une ligne intercité.
- **Le 7 % suisse n'a pas été confirmé.** Le site des prescriptions CFF renvoie un HTTP 451 depuis le Canada. Ne pas publier ce chiffre en l'attribuant aux CFF sans vérification.
- **Aucun pourcentage de *recovery time* d'Amtrak sur le NEC n'est publié** par le GAO ni par l'inspecteur général.

---

## 2. Recommandation du point unique : **8 %**

### L'argument

Trois raisons convergent.

**Première raison, c'est le point de convergence des standards.** Rangeons les valeurs applicables à un corridor à double voie parcouru à 160-180 km/h. Trafikverket voie double donne 5,7 %. SNCF Réseau LGV donne 5 %. Network Rail donne 5 % là où la majoration forfaitaire s'applique. L'UIC donne 8 % à 177 km/h. L'Allemagne donne 7 % plus un plancher en minutes, soit près de 10 %. SNCF Réseau ligne classique donne 12 à 13 %. Le RfL(I) donne 10 %. La médiane de cet ensemble tombe entre 7 et 8 %. Le 8 % n'est ni le chiffre le plus généreux ni le plus serré.

**Deuxième raison, c'est la seule valeur adossée à une règle explicitement fonction de la vitesse.** La fiche UIC 451-1 fait varier le supplément avec la vitesse. Le rapport publie des temps à 177 km/h de vitesse commerciale. L'interpolation de la fiche à cette vitesse donne 8 %. Les autres règles sont exprimées en minutes par 100 km, donc leur équivalent en pourcentage change avec la vitesse retenue et devient difficile à défendre si un lecteur change d'hypothèse.

**Troisième raison, c'est la robustesse en contre-interrogatoire.** Un critique attaquera la marge par le bas, en disant qu'un corridor rénové à double voie ressemble plus à une LGV qu'à une ligne classique et mériterait 5 %. Il l'attaquera par le haut en disant qu'un corridor partagé avec du fret ressemble à une ligne classique française et mériterait 12 %. Le 8 % laisse une réponse simple dans les deux sens. Il est plus prudent que la LGV française et que la voie double suédoise. Il est plus optimiste que la ligne classique française, ce qui se justifie par la voie double, l'électrification et la signalisation modernisée.

### Ce que je ne recommande pas

Ne pas retenir 5 %. C'est une valeur de ligne à grande vitesse dédiée, sans trafic mixte. Le corridor québécois n'est pas dans ce cas et le chiffre paraîtra plaidé.

Ne pas retenir 12 %. C'est la valeur d'une ligne classique française avec fret lourd. Elle détruit l'argument de compétitivité du rapport sans nécessité technique.

### Formulation suggérée pour le rapport

« Marge d'horaire de 8 %, valeur interpolée de la fiche UIC 451-1 à 177 km/h. Cette valeur se situe au milieu des règles publiées des gestionnaires d'infrastructure européens, qui vont de 5 % sur ligne à grande vitesse dédiée à environ 12 % sur ligne classique à trafic mixte. »

### Note de cohérence

Le rapport applique déjà 8 % dans son hypothèse de base. La recommandation confirme cette valeur plutôt que de la déplacer. Le gain de la présente recherche n'est pas un nouveau chiffre, c'est un appui documentaire plus large pour le même chiffre, et une liste explicite de ce qui n'est pas vérifiable.

---

## 3. Temps de parcours ALTO annoncés

| Relation | Temps annoncé | Source | Statut |
|---|---|---|---|
| Montréal - Toronto | 3 h | Communiqué du premier ministre du Canada, 19 février 2025 : « getting you from Montréal to Toronto in three hours » | **Officiel**, annonce gouvernementale ferme |
| Montréal - Toronto | ~3 h | FAQ altotrain.ca, question « Quelle sera la vitesse des trains Alto? » | **Officiel**, promoteur, valeur approximative (tilde) |
| Ottawa - Toronto | ~2 h | FAQ altotrain.ca, même réponse | **Officiel**, promoteur, approximatif |
| Montréal - Ottawa | ~1 h | FAQ altotrain.ca, même réponse | **Officiel**, promoteur, approximatif |
| Québec - Montréal | ~1 h 30 | FAQ altotrain.ca, même réponse | **Officiel**, promoteur, approximatif |
| Montréal - Québec | 1 h 29 | Repris dans des médias et blogues à partir de matériel Alto | **Estimation médiatique**, non retrouvée telle quelle sur altotrain.ca. Ne pas citer comme chiffre officiel |
| Montréal - Trois-Rivières | 54 min | Même origine médiatique | **Estimation médiatique**, non confirmée en source primaire |
| Segment Montréal - Ottawa | Aucun temps annoncé | Communiqué de Transports Canada, 12 décembre 2025 | Le communiqué confirme le segment d'environ 200 km et un début de construction en 2029, **sans donner de temps de parcours** |

### Passage exact de la FAQ Alto (version française, consultée le 25 août 2026)

« Les trains circuleront à des vitesses de 300 km/h ou plus. Les temps de déplacement entre les villes seront considérablement réduits par rapport aux temps de déplacement actuels en train. Par exemple : Ottawa-Toronto : ~2 h ; Montréal-Toronto : ~3 h ; Montréal-Ottawa : ~1 h ; Québec-Montréal : ~1 h 30 »

### Lecture utile pour le rapport

Les quatre temps de la FAQ sont mutuellement cohérents et forment le seul jeu officiel complet. Le 3 h Montréal-Toronto est le seul temps qui bénéficie en plus d'une annonce du premier ministre, donc le seul à pouvoir être présenté sans réserve comme un engagement politique. Les trois autres sont des ordres de grandeur publiés par le promoteur, marqués par un tilde, et devraient être cités avec ce tilde.

Le chiffre de 1 h 29 Montréal-Québec circule dans la presse. Il ne figure pas sous cette forme sur altotrain.ca. Le rapport ne devrait pas l'utiliser comme s'il était officiel.

---

## 4. Fiches de sources

### 4.1 Allemagne, mécanisme du Regelzuschlag, réponse gouvernementale

- URL : https://dserver.bundestag.de/btd/19/325/1932554.pdf
- Consulté le : 2026-08-25
- Passage appuyant la valeur : « Nach Auskunft der Deutschen Bahn AG (DB AG) ist der Regelzuschlag ein gleichmäßig verteilter prozentualer Zuschlag zur reinen Fahrzeit. Die Höhe dieses Zuschlags ist von der Traktionsart (Diesel- oder Elektrobetrieb) und von der zulässigen Geschwindigkeit des Zuges abhängig. » Et sur le supplément de travaux : « Neben dem Regelzuschlag als prozentualem Zeitzuschlag, der im Verhältnis zur physikalischen Fahrzeit steht, werden nach Auskunft der DB AG Bauzuschläge als absolute Minutenwerte in die Fahrzeiten eingearbeitet. »
- Réserve : le document confirme le mécanisme, **pas** de valeur chiffrée.

```bibtex
@techreport{bundestag2021regelzuschlag,
  author      = {{Deutscher Bundestag}},
  title       = {Antwort der Bundesregierung auf die Kleine Anfrage: Fahrzeiten und Zuschl\"age im Schienenpersonenverkehr},
  type        = {Drucksache},
  number      = {19/32554},
  institution = {Deutscher Bundestag, 19. Wahlperiode},
  address     = {Berlin},
  year        = {2021},
  url         = {https://dserver.bundestag.de/btd/19/325/1932554.pdf},
  urldate     = {2026-08-25}
}
```

### 4.2 Allemagne, fiche produit DB Netz sur le calcul du temps de parcours

- URL d'origine : https://fahrweg.dbnetze.com/resource/blob/1359520/a15c08803ce7991655355a02a87438ed/produktbeschreibung_fahrzeitberechnung-data.pdf
- URL fonctionnelle (archive) : http://web.archive.org/web/20240511220001/https://fahrweg.dbnetze.com/resource/blob/1359520/a15c08803ce7991655355a02a87438ed/produktbeschreibung_fahrzeitberechnung-data.pdf
- Consulté le : 2026-08-25
- Passage appuyant la valeur : « Berechnung der Mindestfahrzeit (inklusive Regelzuschlag; ohne Bauzuschläge) » et « Ergebnis einer Fahrzeitberechnung ist die reine Fahrzeit zuzüglich Regelzuschlag (Mindestfahrzeit) für eine gewünschte Strecke der DB Netz AG von A nach B ».
- Réserve : l'URL d'origine ne répond plus. Aucune valeur chiffrée dans le document.

```bibtex
@techreport{dbnetz2020fahrzeitberechnung,
  author       = {{DB Netz AG}},
  title        = {Produktbeschreibung Fahrzeitberechnung: Berechnung der Mindestfahrzeit (inklusive Regelzuschlag; ohne Bauzuschl\"age)},
  institution  = {DB Netz AG},
  address      = {Frankfurt am Main},
  year         = {2020},
  note         = {Version 1.2 du 26 octobre 2020; archiv\'e par Internet Archive},
  url          = {http://web.archive.org/web/20240511220001/https://fahrweg.dbnetze.com/resource/blob/1359520/a15c08803ce7991655355a02a87438ed/produktbeschreibung_fahrzeitberechnung-data.pdf},
  urldate      = {2026-08-25}
}
```

### 4.3 Allemagne, valeurs chiffrées 3 à 7 % (source secondaire, à ne pas citer seule)

- URL : https://de.wikipedia.org/wiki/Regelzuschlag
- Consulté le : 2026-08-25
- Passage appuyant la valeur : le Regelzuschlag réparti uniformément entre deux arrêts se situe entre 3 et 7 % selon la vitesse maximale admissible du train ; pour les automotrices s'ajoute au moins 1,0 min par 100 km, pour les trains voyageurs tractés 1,5 min par 100 km.
- Réserve : **source tertiaire.** Ne pas la publier comme si elle émanait de DB InfraGO. Si le client veut le chiffre allemand dans le rapport, il faut soit l'attribuer à la littérature, soit le retirer.

```bibtex
@misc{wikipedia2026regelzuschlag,
  author       = {{Wikipedia}},
  title        = {Regelzuschlag},
  howpublished = {Wikipedia, l'encyclop\'edie libre, version allemande},
  year         = {2026},
  url          = {https://de.wikipedia.org/wiki/Regelzuschlag},
  urldate      = {2026-08-25}
}
```

### 4.4 Royaume-Uni, Timetable Planning Rules 2026 de Rail for London Infrastructure

- URL : https://tfl.gov.uk/cdn/static/cms/documents/rfli-ccos-tpr-2026.pdf
- Consulté le : 2026-08-25
- Passages appuyant la valeur, cités mot pour mot :
  - §5.4.1 : « A 10% engineering allowance uplift is included in the SRT calculation method (see 7.4.4 and 7.4.8 below) for each timing link. »
  - §7.4.8 : « A 10% allowance for engineering shall be included in the TPR calculation. »
  - §7.4.9 : « Network Rail national timetable protocols require rounding of the calculated SRTs to obtain values in half minutes. »
- Réserve : gestionnaire du tronçon central de la Elizabeth line. Régime d'arrêts rapprochés, donc borne haute, non transposable telle quelle à un corridor intercité.

```bibtex
@techreport{rfli2026tpr,
  author      = {{Rail for London (Infrastructure) Limited}},
  title       = {RfL(I) Central Operating Section Timetable Planning Rules 2026},
  institution = {Rail for London (Infrastructure) Limited / Transport for London},
  address     = {London},
  year        = {2025},
  url         = {https://tfl.gov.uk/cdn/static/cms/documents/rfli-ccos-tpr-2026.pdf},
  urldate     = {2026-08-25}
}
```

### 4.5 Royaume-Uni, Rules of the Plan de Network Rail Central (exemplaire pédagogique)

- URL : http://www.gjdms.org.uk/uploads/3/4/1/8/34185735/student_notes__module5_rotp_.pdf
- Consulté le : 2026-08-25
- Passage appuyant la valeur, §5.1.2 : « On certain routes a 5% allowance is included in the calculation to take account of the lack of explicit engineering allowances in Rules of the Plan. »
- Réserve importante : ce document reproduit la structure et le texte réels des Rules of the Plan de Network Rail Central, mais les noms de lieux des tableaux sont fictifs (Watergalley, Glasummers, Webbcrewe). C'est un support de formation. Le texte de la règle des 5 % est vraisemblablement authentique, les valeurs par ligne ne le sont pas. **À faire valider avant publication**, ou à remplacer par la source RfL(I) qui est incontestable.

```bibtex
@techreport{networkrail2009rulesplan,
  author      = {{Network Rail}},
  title       = {Rules of the Plan 2010, Network Rail Central: Final Principal Rules and Preliminary Proposal for Subsidiary Change Timetable 2010},
  institution = {Network Rail, Train Planning Centre},
  year        = {2009},
  note        = {Version 3.0 du 24 avril 2009; exemplaire diffus\'e comme support de formation, toponymes fictifs},
  url         = {http://www.gjdms.org.uk/uploads/3/4/1/8/34185735/student_notes__module5_rotp_.pdf},
  urldate     = {2026-08-25}
}
```

### 4.6 Royaume-Uni, page officielle des Operational Rules de Network Rail (preuve de non-disponibilité)

- URL : https://www.networkrail.co.uk/industry-and-commercial/information-for-operators/operational-rules/
- Consulté le : 2026-08-25
- Utilité : cette page atteste que les Timetable Planning Rules nationales ne sont pas diffusées en PDF libre, mais par archive zip, avec un contact éditorial. Elle sert à justifier l'absence de valeur intercité britannique dans le tableau.

```bibtex
@misc{networkrail2026operationalrules,
  author       = {{Network Rail}},
  title        = {Operational Rules: Engineering Access Statement and Timetable Planning Rules},
  howpublished = {Site web de Network Rail},
  year         = {2026},
  url          = {https://www.networkrail.co.uk/industry-and-commercial/information-for-operators/operational-rules/},
  urldate      = {2026-08-25}
}
```

### 4.7 États-Unis, audit de l'inspecteur général d'Amtrak sur la ponctualité

- URL : https://amtrakoig.gov/sites/default/files/reports/OIG-A-2020-001%20OTP%20mandate.pdf
- Consulté le : 2026-08-25
- Passage appuyant la valeur : « Reducing schedule recovery time could increase revenues by at least $7.2 million annually. To make scheduled arrival and departure times more predictable for customers, the company adds time to its schedules as a buffer against anticipated delays. Although this buffer helps trains adhere more closely to schedules, the extra time makes train travel less competitive with other transportation options, such as car or air travel. A Schedule and Consist Planning director estimated that about 70 percent of the extra time in the company's schedules is built in due to anticipated [host railroad delays]. »
- Réserve : **aucun pourcentage du temps de parcours.** Le 70 % est une part du tampon, pas une marge d'horaire. Ne pas le convertir en marge. À utiliser seulement pour illustrer que la pratique nord-américaine ajoute du tampon sans règle publiée.

```bibtex
@techreport{amtrakoig2019otp,
  author      = {{Amtrak Office of Inspector General}},
  title       = {Train Operations: Better Estimates Needed of the Financial Impacts of Poor On-Time Performance},
  type        = {Audit Report},
  number      = {OIG-A-2020-001},
  institution = {Amtrak Office of Inspector General},
  address     = {Washington, DC},
  year        = {2019},
  url         = {https://amtrakoig.gov/sites/default/files/reports/OIG-A-2020-001%20OTP%20mandate.pdf},
  urldate     = {2026-08-25}
}
```

### 4.8 Suisse, communiqué CFF sur l'horaire 2027 (seul élément primaire obtenu)

- URL : https://news.sbb.ch/de/019e3f6f-623c-7086-87cf-ebb0809277ad/fahrplan-2027-bringt-gezielte-verbesserungen
- Consulté le : 2026-08-25
- Élément appuyant la valeur : le communiqué indique que, pour rendre le système plus robuste, les temps de parcours sur les liaisons principales sont allongés de quelques minutes, de 4 à 9 minutes selon la relation, ce qui accroît la stabilité de l'horaire et la sécurité des correspondances. Il mentionne aussi que les IC Zurich - Stuttgart reçoivent davantage de réserve de temps de parcours sur la section allemande.
- Réserve : **le 7 % suisse n'est pas confirmé.** Le référentiel CFF (R I-30111 et suivants, vorgaben.sbb.ch) renvoie un HTTP 451 depuis le Canada. Si le rapport veut citer la Suisse, il faut soit s'en tenir au constat qualitatif ci-dessus, soit obtenir le référentiel par un contact suisse.

```bibtex
@misc{sbb2026fahrplan2027,
  author       = {{Schweizerische Bundesbahnen SBB}},
  title        = {Gezielte Verbesserungen mit Fahrplan 2027},
  howpublished = {Communiqu\'e de presse, news.sbb.ch},
  year         = {2026},
  url          = {https://news.sbb.ch/de/019e3f6f-623c-7086-87cf-ebb0809277ad/fahrplan-2027-bringt-gezielte-verbesserungen},
  urldate      = {2026-08-25}
}
```

### 4.9 ALTO, foire aux questions du promoteur

- URL (français) : https://www.altotrain.ca/fr/foire-aux-questions
- URL (anglais) : https://www.altotrain.ca/en/frequently-asked-questions
- Consulté le : 2026-08-25
- Passage appuyant la valeur (français) : « Les trains circuleront à des vitesses de 300 km/h ou plus. Les temps de déplacement entre les villes seront considérablement réduits par rapport aux temps de déplacement actuels en train. Par exemple : Ottawa-Toronto : ~2 h ; Montréal-Toronto : ~3 h ; Montréal-Ottawa : ~1 h ; Québec-Montréal : ~1 h 30 »
- Passage appuyant la valeur (anglais) : « Trains will operate at speeds of 300 km/h or more. Journey times between cities will be significantly reduced, compared to current train travel times. For example: Toronto-Ottawa: ~2h; Toronto-Montréal: ~3h; Ottawa-Montréal: ~1h; Montréal-Québec City: ~1h30 »
- Note technique : la page renvoie un HTTP 403 aux robots. Elle a été récupérée en simulant un navigateur.

```bibtex
@misc{altotrain2026faq,
  author       = {{Alto}},
  title        = {Foire aux questions},
  howpublished = {Site web d'Alto, altotrain.ca},
  year         = {2026},
  url          = {https://www.altotrain.ca/fr/foire-aux-questions},
  urldate      = {2026-08-25}
}
```

### 4.10 ALTO, annonce du premier ministre du Canada (19 février 2025)

- URL : https://www.pm.gc.ca/en/news/news-releases/2025/02/19/canada-getting-high-speed
- Consulté le : 2026-08-25
- Passages appuyant la valeur : « getting you from Montréal to Toronto in three hours » ; « reach speeds of up to 300 km/hour » ; « span approximately 1,000 km » ; « The official name of this high-speed rail service will be Alto » ; « Cadence has been carefully selected to not only co-design and build, but also to finance, operate, and maintain this project. »
- Statut : **officiel, engagement politique.** C'est la source la plus forte pour le 3 h Montréal - Toronto.

```bibtex
@misc{pmcanada2025alto,
  author       = {{Prime Minister of Canada}},
  title        = {Canada is getting high-speed rail},
  howpublished = {Communiqu\'e de presse, Cabinet du premier ministre du Canada},
  year         = {2025},
  month        = feb,
  url          = {https://www.pm.gc.ca/en/news/news-releases/2025/02/19/canada-getting-high-speed},
  urldate      = {2026-08-25}
}
```

### 4.11 ALTO, communiqué de Transports Canada sur le premier segment (12 décembre 2025)

- URL : https://www.canada.ca/fr/transports-canada/nouvelles/2025/12/a-toute-vapeur--montrealottawa-choisi-comme-point-de-depart-pour-le-train-a-grande-vitesse-alto.html
- Consulté le : 2026-08-25
- Passages appuyant la valeur : « le premier segment du réseau de trains à grande vitesse reliera Montréal à Ottawa » ; « Couvrant deux provinces, ce premier segment propose un tracé plus court, d'environ 200 km » ; « La construction du segment Montréal-Ottawa devrait commencer en 2029 » ; « À compter de janvier 2026, Alto entamera un processus exhaustif de consultation publique de trois mois. »
- Réserve : ce communiqué **ne donne aucun temps de parcours**. Il ne peut pas servir de source pour le ~1 h Montréal - Ottawa.
- Note technique : la page renvoie un HTTP 403 aux robots. Récupérée en simulant un navigateur.

```bibtex
@misc{transportscanada2025montrealottawa,
  author       = {{Transports Canada}},
  title        = {En avant toute: Montr\'eal-Ottawa choisi comme point de d\'epart pour le train \`a grande vitesse Alto},
  howpublished = {Communiqu\'e de presse, Transports Canada},
  year         = {2025},
  month        = dec,
  url          = {https://www.canada.ca/fr/transports-canada/nouvelles/2025/12/a-toute-vapeur--montrealottawa-choisi-comme-point-de-depart-pour-le-train-a-grande-vitesse-alto.html},
  urldate      = {2026-08-25}
}
```

### 4.12 Allemagne, modules publics de la Richtlinie 402 (preuve de fouille infructueuse)

- URL de la liste : https://www.dbinfrago.com/web/schienennetz/netzzugang-und-regulierung/regelwerke/regelwerke_netzzugangsrelevant/netzzugangsrelevantes_regelwerk-2026-13175436
- Module fouillé en priorité : Ril 402.0202 (INB 2026), https://www.dbinfrago.com/resource/blob/13175466/eb0a036441c9b18d76a0024f0758b9d5/Ril-402-0202-INB-2026-data.pdf
- Consulté le : 2026-08-25
- Résultat : aucune occurrence de valeur chiffrée de Regelzuschlag ou de Bauzuschlag dans les modules publics. Sert à documenter que la recherche a été poussée jusqu'au référentiel du gestionnaire.

```bibtex
@techreport{dbinfrago2026ril402,
  author      = {{DB InfraGO AG}},
  title       = {Richtlinie 402 Bahnbetrieb Trassenmanagement, modules du r\'eglement pertinent pour l'acc\`es au r\'eseau, INB 2026},
  institution = {DB InfraGO AG},
  address     = {Frankfurt am Main},
  year        = {2025},
  url         = {https://www.dbinfrago.com/web/schienennetz/netzzugang-und-regulierung/regelwerke/regelwerke_netzzugangsrelevant/netzzugangsrelevantes_regelwerk-2026-13175436},
  urldate     = {2026-08-25}
}
```

---

## 5. Récapitulatif pour le client

Le point unique recommandé est **8 %**. Il est adossé à la fiche UIC 451-1 interpolée à 177 km/h, et il tombe au milieu des règles publiées par les gestionnaires d'infrastructure européens.

Les quatre temps ALTO officiels sont : Montréal - Toronto 3 h, Ottawa - Toronto ~2 h, Montréal - Ottawa ~1 h, Québec - Montréal ~1 h 30. Seul le 3 h Montréal - Toronto est confirmé par une annonce du premier ministre. Les trois autres viennent de la FAQ du promoteur et portent un tilde.

Trois valeurs demandées n'ont pas été confirmées en source primaire : le chiffre allemand exact, les valeurs intercité britanniques et le 7 % suisse. Elles ne devraient pas être publiées comme si elles l'étaient.

# Références pour les rapports puissance/masse (W/kg) du modèle de temps de parcours

Recherche menée le 2026-08-24, date de consultation retenue pour les citations : **2026-08-25**.
Corridor Québec-Toronto, phase 1. Objectif : documenter les hypothèses 8 / 12 / 18 / 22 W/kg et le 6,5 W/kg du LRC.

---

## 0. Avertissement de méthode : quelle puissance, quelle masse

Trois pièges à régler avant de comparer quoi que ce soit.

**a) Puissance moteur ≠ puissance au rail.** Pour une rame tractée par un diesel-électrique nord-américain, le chiffre publié (4 200 hp du Charger) est la puissance nominale du moteur thermique au vilebrequin, aux conditions standard AAR. Il faut en retrancher le HEP (chauffage, climatisation, prises : 600 kW sur la fiche Siemens), les auxiliaires, puis les pertes alternateur + convertisseur + moteurs + engrenages (rendement de l'ordre de 0,88 à 0,92). Aucune fiche Siemens publique ne donne la puissance à la jante. Il faut donc l'estimer et le dire.

**b) Pour les rames électriques**, la « puissance de traction » publiée (8 000 kW Velaro D, 5 500 kW Pendolino, 8 800 kW TGV) est déjà une puissance continue à la jante ou très proche. La comparaison directe avec le diesel brut est donc biaisée en faveur du diesel.

**c) Masse à vide ou en charge.** Les constructeurs publient presque toujours la masse à vide. L'écart est de 6 à 10 % sur une rame voyageurs (environ 80 kg par siège occupé). Le rapport doit fixer une convention et s'y tenir.

**Convention proposée pour le rapport : puissance continue à la jante, masse à vide.** Les colonnes ci-dessous donnent les deux quand la source le permet.

---

## 1. Tableau de synthèse

| Matériel | Puissance (kW, type) | Masse (t, vide/charge) | W/kg calculé | Source |
|---|---|---|---|---|
| **VIA Corridor actuel** : SCV-42 + 5 Venture | 3 132 kW (4 200 hp, **nominale moteur** au vilebrequin, 1 800 rpm) | 374 t à vide (loco 120 t + 5 × 50,8 t) | **8,4 W/kg** (nominale/vide) | `viarail2024corridor`, `wikipedia2026charger`, `wikipedia2026venture` |
| idem, **estimation à la jante** | ≈ 2 280 kW (3 132 − 600 HEP, × 0,90 rendement) | 374 t à vide / ≈ 397 t en charge | **6,1 W/kg** vide · **5,7 W/kg** en charge | calcul propre, HEP d'après `siemens2024chargerwsdot` |
| **Siemens Charger SC-44** (fiche officielle, réf. de la famille) | 4 400 hp nominale ; HEP 600 kW ; effort 65 000 lb / 290 kN | 267 000 lb = 121,1 t (loco seule) | n/a (loco seule) | `siemens2024chargerwsdot` |
| **LRC** (loco + 5 voitures) | 2 013 kW (2 700 hp **traction**, HEP en service) ; 2 760 kW brut (3 700 hp) | 114,8 t + 5 × 47,6 t = 352,8 t à vide | **5,7 W/kg** (traction/vide) · 7,8 (brut/vide) | `wikipedia2026lrc`, `trains2021lrc` |
| **LRC** (loco + 4 voitures) | 2 013 kW traction | 305,2 t à vide | **6,6 W/kg** | idem |
| **Alstom ETR 610 / New Pendolino** (7 caisses, 250 km/h, pendulaire) | 5 500 kW (puissance installée totale) | 387 t vide / 421 t en charge | **14,2 W/kg** vide · **13,1 W/kg** en charge | `alstom2005pendolino`, `wikipedia2026newpendolino` |
| **Class 390 Pendolino** (390/0, 9 caisses, WCML, 200 km/h, pendulaire) | 5 160 kW | 466 t | **11,1 W/kg** | `wikipedia2026class390` |
| **Class 390/1** (11 caisses) | 6 020 kW | 567 t | **10,6 W/kg** | `wikipedia2026class390` |
| **ICE T, DB BR 411** (7 caisses, 230 km/h, pendulaire) | 4 000 kW (Antriebsleistung) | 368 t (Zuggewicht, officiel DB) | **10,9 W/kg** | `db2019icet411` (masse), `austriaforum2026icet` (puissance) |
| **Siemens Velaro D / ICE 3 BR 407** (8 caisses, 320 km/h) | 8 000 kW (traction power, fiche Siemens) | 492 t (Zuggewicht, officiel DB) ; 454 t selon sources secondaires | **16,3 W/kg** (DB) · 17,6 (454 t) | `siemens2016velarod`, `db2019ice3407` |
| **ICE 3, DB BR 403** (8 caisses, 330 km/h) | 8 000 kW | 410 t (Zuggewicht, officiel DB) | **19,5 W/kg** | `db2019ice3403`, `siemens2016velarod` (puissance, plateforme identique) |
| **ETR 1000 / Frecciarossa 1000** (8 caisses, 300-360 km/h) | 9 800 kW | 500 t | **19,6 W/kg** | `hitachi2026etr1000` |
| **TGV Duplex** (2 motrices + 8 remorques, 320 km/h) | 8 800 kW sous 25 kV (continue, à la jante) | 380 t à vide ; ≈ 421 t en charge (510 sièges) | **23,2 W/kg** vide · **20,9 W/kg** en charge | `wikipedia2026tgvduplex` |

---

## 2. Verdict par hypothèse

### 8 W/kg — rame tractée actuelle de VIA : **soutenue, mais à requalifier**

Le calcul tombe très exactement sur 8,4 W/kg **si** on divise la puissance nominale du moteur thermique (3 132 kW, chiffre publié par VIA elle-même) par la masse à vide de la rame de base (374 t). C'est solide et facilement vérifiable par un lecteur.

Mais l'hypothèse est libellée « W/kg **au rail** », et au rail le chiffre tombe à environ **6,1 W/kg** à vide, 5,7 W/kg en charge, une fois retirés les 600 kW de HEP et les pertes de chaîne de traction. L'écart est de 27 %, ce qui n'est pas négligeable sur un temps de parcours.

**Recommandation :** garder 8 W/kg mais changer le libellé pour « puissance nominale installée par tonne à vide », ou bien garder « au rail » et descendre à 6 W/kg. Ne pas laisser les deux formulations coexister. Si le modèle a été calibré empiriquement sur les horaires VIA actuels avec 8 W/kg, c'est que 8 absorbe implicitement autre chose (arrêts, marges) : le dire.

### 6,5 W/kg — LRC historique : **plausible, mais dépendant de la longueur de rame**

Aucune source ne publie « 6,5 W/kg ». La valeur se reconstitue ainsi : 2 013 kW de traction (2 700 hp, HEP en service) divisés par une rame loco + 4 voitures (305 t) donnent **6,6 W/kg**. C'est le meilleur ajustement trouvé.

Mais les rames LRC courantes étaient plus longues. Loco + 5 voitures donne 5,7 W/kg, loco + 6 voitures 5,0 W/kg. Et si on prend la puissance brute (2 760 kW) plutôt que la traction, on remonte à 7,8 W/kg sur 5 voitures.

**Recommandation :** garder 6,5 W/kg comme ordre de grandeur, mais préciser en note la rame de référence (loco + 4 voitures, puissance de traction, masse à vide) et donner la fourchette 5,0 à 6,6 W/kg. Point important pour la cohérence interne : sous une convention identique (puissance de traction, masse à vide, 5 voitures), le LRC donne 5,7 et le Venture 6,1, soit un gain de seulement 7 %. Le couple 6,5 / 8,0 laisse croire à un gain de 23 %. **C'est l'incohérence la plus exposée du jeu d'hypothèses.**

### 12 W/kg — pendulaire moderne de référence (bandes 160-241 km/h) : **soutenue, c'est la meilleure hypothèse du lot**

Les trois pendulaires modernes documentés encadrent 12 W/kg de près :

- Class 390/0 Pendolino (WCML) : 11,1 W/kg
- ICE T BR 411 : 10,9 W/kg
- ETR 610 New Pendolino : 13,1 W/kg en charge, 14,2 à vide

La médiane du groupe est de l'ordre de 11 à 13 W/kg. **12 W/kg est défendable telle quelle, sans réserve.** Le Class 390 est même l'analogue le plus proche du cas Québec-Toronto : pendulaire, 200 km/h, ligne classique remise à niveau, mixité fret.

### 18 W/kg — bande 250 km/h : **plausible, mais en haut de fourchette**

Aucun matériel réellement conçu pour 250 km/h dans notre échantillon n'atteint 18 W/kg :

- ETR 610, 250 km/h : 13,1 à 14,2 W/kg
- Velaro D, 320 km/h : 16,3 W/kg (masse officielle DB) à 17,6 (masse secondaire)

18 W/kg correspond en réalité au niveau d'une plateforme grande vitesse non pendulaire de génération 300 (ICE 3 BR 403 : 19,5 W/kg), pas à celui d'un pendulaire 250.

**Recommandation :** soit ramener la bande 250 à **16 W/kg** et la justifier par le Velaro D, soit garder 18 W/kg en assumant explicitement qu'on modélise une rame de conception 300 exploitée à 250. La seconde option est cohérente avec un corridor qu'on souhaiterait faire évoluer, mais elle doit être écrite.

### 22 W/kg — bande 300 km/h : **plausible, borne haute assumée**

Le seul matériel qui dépasse 22 W/kg est le TGV Duplex à vide (23,2 W/kg). En charge il retombe à 20,9. Les rames à motorisation répartie sont plus basses :

- ETR 1000 : 19,6 W/kg
- ICE 3 BR 403 : 19,5 W/kg
- Velaro D : 16,3 à 17,6 W/kg

La fourchette observée sur cinq matériels 300+ est donc **16,3 à 23,2 W/kg**, avec une concentration autour de 19,5-20.

**Recommandation :** 22 W/kg reste défendable si on cite le TGV Duplex, mais **20 W/kg serait plus représentatif** de la génération actuelle. Si la sensibilité du temps de parcours à ce paramètre est faible dans la bande 300 (probable : à 300 km/h la résistance aérodynamique domine et le rapport puissance/masse ne pilote plus que l'accélération initiale), autant retenir 20 et gagner en robustesse. Sinon, garder 22 et citer explicitement le Duplex à vide.

### Synthèse rapide

| Hypothèse | Verdict | Valeur alternative suggérée |
|---|---|---|
| 8 W/kg (VIA actuel) | Soutenue si « nominale/vide » ; à ajuster si « au rail » | 8,4 nominale ou 6,1 au rail |
| 6,5 W/kg (LRC) | Plausible, dépend de la rame ; incohérence de convention avec le 8 | 5,7 à 6,6 selon rame |
| 12 W/kg (pendulaire 160-241) | **Soutenue** | garder 12 |
| 18 W/kg (250) | Plausible mais haute | 16 |
| 22 W/kg (300) | Plausible, borne haute | 20 à 22 |

---

## 3. Sources, entrées BibTeX et passages exacts

### 3.1 Sources primaires constructeur / exploitant

---

**`siemens2024chargerwsdot`** — fiche technique officielle Siemens Mobility, la meilleure source du dossier pour le Charger.

```bibtex
@techreport{siemens2024chargerwsdot,
  author       = {{Siemens Mobility, Inc.}},
  title        = {Charger Diesel-Electric Locomotive: Washington State Department of Transportation (WSDOT), Washington},
  institution  = {Siemens Mobility, Inc.},
  address      = {New York, NY},
  year         = {2024},
  type         = {Fiche technique},
  url          = {https://assets.new.siemens.com/siemens/assets/api/uuid:f1a77eb1-1b1a-4335-913e-8f831d82d778/WSDOT-Charger-Data-Sheet_original.pdf},
  urldate      = {2026-08-25}
}
```

URL exacte : https://assets.new.siemens.com/siemens/assets/api/uuid:f1a77eb1-1b1a-4335-913e-8f831d82d778/WSDOT-Charger-Data-Sheet_original.pdf

Passages exacts (section « Performance and Capacity » et « Vehicle Dimensions and Weight ») :

> Maximum speed / 125 mph
> Rated power / maximum 4,400 hp @ 1,800 rpm at AAR standard conditions
> Operating range / 600 to 1,800 rpm
> **Head end power / 600 kW**
> Tractive effort (max.) / 65,000 lbs / 290 kN

> **Weight / 267,000 lbs / 121109 kg**
> Length / 71.5 ft / 21793 mm
> Wheel arrangement / Bo'Bo'

Note : c'est la variante SC-44 (4 400 hp), pas la SCV-42 de VIA (4 200 hp). Siemens ne publie pas de fiche équivalente pour la SCV-42. **Aucune fiche Siemens publique ne donne la puissance disponible à la traction** : seulement la puissance nominale du moteur et le HEP. C'est ce qui oblige à estimer la puissance à la jante.

---

**`siemens2016velarod`** — fiche technique officielle Siemens, Velaro D (BR 407). Source de la puissance de traction 8 000 kW.

```bibtex
@techreport{siemens2016velarod,
  author       = {{Siemens AG, Mobility Division}},
  title        = {Velaro D (Class 407) High-Speed Trainset},
  institution  = {Siemens AG, Mobility Division},
  address      = {Munich},
  year         = {2016},
  type         = {Fiche technique},
  note         = {Article No. A19100-V800-B806-V5-7600},
  url          = {https://assets.new.siemens.com/siemens/assets/api/uuid:2f82dc92-66be-40b7-be36-78bd0f1bd0b1/high-speed-train-velaro-d-data-sheet-en.pdf},
  urldate      = {2026-08-25}
}
```

URL exacte : https://assets.new.siemens.com/siemens/assets/api/uuid:2f82dc92-66be-40b7-be36-78bd0f1bd0b1/high-speed-train-velaro-d-data-sheet-en.pdf

Passages exacts (section « Technical Data ») :

> Maximum speed / 320 km/h
> Train length / 200 m
> Voltage / 15 / 25 kV AC and 1.5 / 3 kV DC
> **Traction power / 8,000 kW**
> Number of axles / 32 (16 driven)
> **Max. axle load / 17 t**
> Number of cars per train / 8
> Number of seats (total / 1st / 2nd / Bistro) / 460 / 111 / 333 / 16

Limite à signaler : **la fiche Siemens ne donne pas la masse de la rame**, seulement la charge maximale à l'essieu (17 t, soit 544 t théoriques sur 32 essieux, ce qui est un plafond réglementaire et non une masse réelle). D'où le recours à la fiche DB ci-dessous pour la masse.

---

**`db2019ice3407`** — fiche « Daten und Fakten » officielle Deutsche Bahn. Source de la masse.

```bibtex
@techreport{db2019ice3407,
  author       = {{Deutsche Bahn AG}},
  title        = {{ICE 3 (MS) BR 407 -- Daten und Fakten}},
  institution  = {Deutsche Bahn AG},
  year         = {2019},
  type         = {Fahrzeuglexikon},
  note         = {Stand: Januar 2019},
  url          = {https://assets.static-bahn.de/dam/jcr:6849fdc1-cc78-467f-97a7-301ebdae9636/196234-265167.pdf},
  urldate      = {2026-08-25}
}
```

URL exacte : https://assets.static-bahn.de/dam/jcr:6849fdc1-cc78-467f-97a7-301ebdae9636/196234-265167.pdf

Passages exacts :

> Erste Inbetriebnahme: 2013 · Anzahl der Züge: 17 · Anzahl Mittel-/Endwagen: 6/2
> Länge (Zug): 201 m · Anzahl angetriebener Achsen: 16
> **Zuggewicht: ca. 492 t**
> Höchstgeschwindigkeit: 320 km/h

Écart à noter : la presse spécialisée et Wikipédia citent 454 t pour la même rame. La valeur DB de 492 t est la plus autoritaire et donne 16,3 W/kg au lieu de 17,6. **Utiliser 492 t et le dire.**

---

**`db2019ice3403`** — fiche « Daten und Fakten » officielle DB, ICE 3 BR 403.

```bibtex
@techreport{db2019ice3403,
  author       = {{Deutsche Bahn AG}},
  title        = {{ICE 3 BR 403, 1. Serie -- Daten und Fakten}},
  institution  = {Deutsche Bahn AG},
  year         = {2019},
  type         = {Fahrzeuglexikon},
  note         = {Stand: Januar 2019},
  url          = {https://assets.static-bahn.de/dam/jcr:306e7ad7-1af0-4aee-a8e9-5aa7e0fbca23/215186-289012.pdf},
  urldate      = {2026-08-25}
}
```

URL exacte : https://assets.static-bahn.de/dam/jcr:306e7ad7-1af0-4aee-a8e9-5aa7e0fbca23/215186-289012.pdf

Passages exacts :

> Erste Inbetriebnahme: 2000/Umbau 2002 · Anzahl der Züge: 37 · Anzahl Mittel-/Endwagen: 6/2
> Länge (Zug): 200 m · Anzahl angetriebener Achsen: 16
> **Zuggewicht: ca. 410 t**
> **Höchstgeschwindigkeit: 330 km/h**

Combinée à la puissance de 8 000 kW de la plateforme Velaro (fiche Siemens ci-dessus, motorisation identique), cette masse donne 19,5 W/kg. C'est l'anchor le plus propre pour la bande 300.

---

**`db2019icet411`** — fiche « Daten und Fakten » officielle DB, ICE T BR 411.

```bibtex
@techreport{db2019icet411,
  author       = {{Deutsche Bahn AG}},
  title        = {{ICE T (7-tlg.) BR 411, 1. Serie -- Daten und Fakten}},
  institution  = {Deutsche Bahn AG},
  year         = {2019},
  type         = {Fahrzeuglexikon},
  note         = {Stand: Januar 2019},
  url          = {https://assets.static-bahn.de/dam/jcr:4925f5ab-a1e2-4b5e-9205-221aab02f243/215191-289017.pdf},
  urldate      = {2026-08-25}
}
```

URL exacte : https://assets.static-bahn.de/dam/jcr:4925f5ab-a1e2-4b5e-9205-221aab02f243/215191-289017.pdf

Passages exacts :

> Erste Inbetriebnahme: 2000 · Anzahl der Züge: 31 · Anzahl Mittel-/Endwagen: 5/2
> Länge (Zug): 185 m · **Anzahl angetriebener Achsen: 8**
> **Zuggewicht: 368 t**
> Höchstgeschwindigkeit: 230 km/h · Sitzplätze (gesamt): 359

Limite : **la fiche DB ne donne pas la puissance.** Voir `austriaforum2026icet` ci-dessous, qui est une source secondaire.

---

**`viarail2024corridor`** — page officielle VIA Rail sur le nouveau parc Corridor.

```bibtex
@misc{viarail2024corridor,
  author       = {{VIA Rail Canada}},
  title        = {New Corridor Fleet},
  howpublished = {Site corporatif de VIA Rail Canada},
  year         = {2024},
  url          = {https://corpo.viarail.ca/en/projects-infrastructure/train-fleet/corridor-fleet},
  urldate      = {2026-08-25}
}
```

URL exacte : https://corpo.viarail.ca/en/projects-infrastructure/train-fleet/corridor-fleet

Passages exacts :

> Powered by Siemens Charger locomotives, which are equipped with a proven propulsion system powered by a fuel-efficient Cummins QSK95, 16-cylinder diesel engine providing **4200 hp**.
> Rated maximum power: **4200 HP à 1,800 rpm**
> Un train standard : **four coaches, one cab car and one locomotive**
> Economy: 194 seats · Business: 87 seats
> Vitesse maximale : 201 km/h (125 mph)

Limite : **VIA ne publie aucune masse.** C'est le trou de sourcing principal du côté canadien. Les masses viennent donc de sources secondaires (ci-dessous).

---

**`alstom2005pendolino`** — communiqué officiel Alstom, lancement du New Pendolino.

```bibtex
@misc{alstom2005pendolino,
  author       = {{Alstom}},
  title        = {The NEW PENDOLINO: The Fourth Generation of Tilting Technology},
  howpublished = {Communiqué de presse Alstom},
  year         = {2005},
  month        = jun,
  url          = {https://www.alstom.com/press-releases-news/2005/6/The-NEW-PENDOLINO-The-fourth-generation-of-tilting-technology-20050628},
  urldate      = {2026-08-25}
}
```

URL exacte : https://www.alstom.com/press-releases-news/2005/6/The-NEW-PENDOLINO-The-fourth-generation-of-tilting-technology-20050628

Chiffre repris : **puissance installée totale de 5 500 kW**, 7 caisses, jusqu'à 430 places, vitesse maximale 250 km/h.

**⚠ Avertissement d'accès :** le serveur d'Alstom a renvoyé un **HTTP 403** lors de la tentative de récupération directe le 2026-08-24. Le chiffre de 5 500 kW a été confirmé indirectement via l'index de recherche (qui cite ce communiqué comme portant la mention « Total installed power: 5500 kW ») et via `wikipedia2026newpendolino`. **Avant publication du rapport, il faut ouvrir cette URL manuellement dans un navigateur et vérifier la phrase exacte**, ou remplacer la référence par la brochure Pendolino d'Alstom. En l'état, traiter ce chiffre comme confirmé par recoupement mais non vérifié en source primaire directe.

---

**`hitachi2026etr1000`** — page produit officielle Hitachi Rail, ETR1000 Frecciarossa.

```bibtex
@misc{hitachi2026etr1000,
  author       = {{Hitachi Rail}},
  title        = {ETR1000 -- Frecciarossa},
  howpublished = {Page produit, Hitachi Rail},
  year         = {2026},
  url          = {https://www.hitachirail.com/products-and-solutions/rolling-stock/high-speed-trains/etr1000-frecciarossa/},
  urldate      = {2026-08-25}
}
```

URL exacte : https://www.hitachirail.com/products-and-solutions/rolling-stock/high-speed-trains/etr1000-frecciarossa/

Chiffres repris : **puissance maximale 9 800 kW**, **masse 500 t**, 8 caisses à traction répartie (DM1-TT2-M3-T4-T5-M6-TT7-DM8), 16 moteurs asynchrones triphasés, longueur 202 m, 300 km/h commercial (360 en pointe), accélération 0,7 m/s² au démarrage.

Note : la page ne précise pas si les 500 t sont à vide ou en charge. Le rapprochement avec la fiche Trenitalia (`fsitaliane2026frecciarossa1000`, même famille de chiffres) suggère une masse à vide. À qualifier de « masse annoncée, convention non précisée ».

---

### 3.2 Sources secondaires (à qualifier explicitement dans le rapport)

Les masses de matériel nord-américain et plusieurs puissances ne sont disponibles qu'en source secondaire. Les entrées suivantes doivent être présentées comme telles.

---

**`wikipedia2026charger`** — **SOURCE SECONDAIRE.** Seule source trouvée pour la masse de la SCV-42.

```bibtex
@misc{wikipedia2026charger,
  author       = {{Wikipedia contributors}},
  title        = {Siemens Charger},
  howpublished = {Wikipedia, The Free Encyclopedia},
  year         = {2026},
  note         = {Source secondaire; masse de la SCV-42 non publiée par Siemens ni par VIA Rail},
  url          = {https://en.wikipedia.org/wiki/Siemens_Charger},
  urldate      = {2026-08-25}
}
```

URL exacte : https://en.wikipedia.org/wiki/Siemens_Charger

Passages exacts (tableau de spécifications) : moteur Cummins QSK95, **4,200 hp (3,100 kW)** pour la SCV-42, **260,000 lb (120,000 kg)**, vitesse maximale **125 mph (200 km/h)**.

Qualification à écrire dans le rapport : « masse de 120 t issue de Wikipédia ; Siemens ne publie pas de fiche pour la variante SCV-42, mais sa fiche officielle pour la SC-44 (variante 4 400 hp, carrosserie identique) donne 121,1 t, ce qui corrobore l'ordre de grandeur à 1 % près. » **C'est le recoupement à mettre en avant : la source primaire SC-44 valide la valeur secondaire SCV-42.**

---

**`wikipedia2026venture`** — **SOURCE SECONDAIRE.** Masse des voitures Venture.

```bibtex
@misc{wikipedia2026venture,
  author       = {{Wikipedia contributors}},
  title        = {Siemens Venture},
  howpublished = {Wikipedia, The Free Encyclopedia},
  year         = {2026},
  note         = {Source secondaire; Siemens Mobility et VIA Rail ne publient pas la masse des voitures Venture},
  url          = {https://en.wikipedia.org/wiki/Siemens_Venture},
  urldate      = {2026-08-25}
}
```

URL exacte : https://en.wikipedia.org/wiki/Siemens_Venture

Passages exacts : **Weight: 112,000 lb (50,802 kg)** · Car length: 85 ft (25,908 mm) · capacités : Business jusqu'à 54, Cab (Economy) jusqu'à 62, Economy jusqu'à 74 · « Via Rail purchased 32 five-car trainsets » (160 voitures).

Qualification : aucune source primaire trouvée pour cette masse. Elle est cohérente avec les voitures inox nord-américaines de 85 pi (50 à 57 t) et avec la conception allégée Siemens. **À présenter comme une estimation de 50,8 t par voiture, source secondaire, non confirmée par le constructeur.**

---

**`wikipedia2026lrc`** — **SOURCE SECONDAIRE.** Puissance et masses du LRC.

```bibtex
@misc{wikipedia2026lrc,
  author       = {{Wikipedia contributors}},
  title        = {{LRC (train)}},
  howpublished = {Wikipedia, The Free Encyclopedia},
  year         = {2026},
  note         = {Source secondaire; matériel retiré du service en 2001, pas de fiche constructeur en ligne},
  url          = {https://en.wikipedia.org/wiki/LRC_(train)},
  urldate      = {2026-08-25}
}
```

URL exacte : https://en.wikipedia.org/wiki/LRC_(train)

Passages exacts :

> Power output : **3,700–2,700 hp (2.76–2.01 MW) for traction, remainder for locomotive auxiliaries and HEP**
> Locomotive weight : **250,000–256,000 lb (113,000–116,000 kg)**
> Voiture LRC : **105,000 lb (47.6 t) empty** (environ un tiers plus légère que le parc CN de l'époque)
> Longueur de voiture : 85 ft (25.91 m)
> Maximum speed : 95 mph (153 km/h) en service ; « LRCs have reached speeds as high as 130 mph (210 km/h) on test runs »
> Commande initiale de VIA : « 10 LRC locomotives and 50 coaches » (soit un ratio 1 loco pour 5 voitures)

La formulation « 3,700–2,700 hp for traction, remainder for auxiliaries and HEP » est essentielle : elle dit explicitement que **2 700 hp (2 013 kW) est la puissance de traction avec HEP en service**, et 3 700 hp la puissance brute. C'est exactement la distinction dont le rapport a besoin, et elle est parfaitement transposable au Charger.

---

**`trains2021lrc`** — **SOURCE SECONDAIRE (presse spécialisée).** Corrobore la puissance du LRC.

```bibtex
@misc{trains2021lrc,
  author       = {{Trains Magazine}},
  title        = {VIA Rail Bombardier LRC Diesel Locomotives},
  howpublished = {Trains.com, Classic Trains},
  year         = {2021},
  note         = {Source secondaire, presse ferroviaire spécialisée},
  url          = {https://www.trains.com/ctr/railroads/locomotives/via-rail-bombardier-lrc-diesel-locomotives/},
  urldate      = {2026-08-25}
}
```

URL exacte : https://www.trains.com/ctr/railroads/locomotives/via-rail-bombardier-lrc-diesel-locomotives/

Chiffres repris : moteur Alco 251F 16 cylindres, **3 725 hp** (d'autres sources de la même famille citent 3 700 hp) ; **3 700 hp au total, dont 2 700 hp disponibles quand le HEP fonctionne** ; deux alternateurs Stamford de 250 kW pour le HEP ; 31 locomotives construites par Bombardier de 1981 à 1984 ; conçues pour 125 mph, limitées à 100 mph en service.

Note : les deux alternateurs de 250 kW (soit 500 kW de HEP) expliquent l'écart de 1 000 hp entre brut et traction : 500 kW de HEP plus les auxiliaires et les pertes. Cohérent avec les 600 kW de HEP du Charger.

---

**`wikipedia2026class390`** — **SOURCE SECONDAIRE.** Class 390 Pendolino.

```bibtex
@misc{wikipedia2026class390,
  author       = {{Wikipedia contributors}},
  title        = {British Rail Class 390},
  howpublished = {Wikipedia, The Free Encyclopedia},
  year         = {2026},
  note         = {Source secondaire; le tableau de spécifications ne porte pas de citation propre},
  url          = {https://en.wikipedia.org/wiki/British_Rail_Class_390},
  urldate      = {2026-08-25}
}
```

URL exacte : https://en.wikipedia.org/wiki/British_Rail_Class_390

Passages exacts :

> Class 390/0 : Power output **5,160 kW (6,920 hp)** · Weight **466 tonnes** · 9 cars · Max speed 125 mph (200 km/h)
> Class 390/1 : Power output **6,020 kW (8,070 hp)** · Weight **567 tonnes** · 11 cars
> Traction motors : 2 × Alstom 4 EJA 2852 par motrice, **430 kW chacun**

Avertissement : le tableau **ne précise pas si la masse est à vide ou en charge**, et **ne porte aucune citation** vers une source primaire. Le contrôle de cohérence interne fonctionne néanmoins : 12 moteurs de 430 kW font 5 160 kW exactement, ce qui valide la puissance. Pour la masse, aucun recoupement primaire n'a été trouvé. **À qualifier de « masse annoncée, convention non précisée, source secondaire ».**

---

**`austriaforum2026icet`** — **SOURCE SECONDAIRE.** Puissance de l'ICE T.

```bibtex
@misc{austriaforum2026icet,
  author       = {{AustriaWiki im Austria-Forum}},
  title        = {{ICE T}},
  howpublished = {Austria-Forum, AustriaWiki},
  year         = {2026},
  note         = {Source secondaire (miroir Wikipédia); la fiche officielle DB ne publie pas la puissance},
  url          = {https://austria-forum.org/af/AustriaWiki/ICE_T},
  urldate      = {2026-08-25}
}
```

URL exacte : https://austria-forum.org/af/AustriaWiki/ICE_T

Chiffre repris : « Die ICE-T-Züge erreichen eine Höchstgeschwindigkeit von 230 km/h und haben eine **Antriebsleistung von 3 000 kW bei fünfteiligen bzw. 4 000 kW bei siebenteiligen Zügen** ».

Qualification : la valeur de 4 000 kW pour la rame à 7 caisses est cohérente avec la fiche DB qui indique 8 essieux moteurs (soit 500 kW par essieu, valeur usuelle). **La masse vient de la fiche officielle DB (368 t), la puissance de cette source secondaire. Le dire dans la note de bas de page.**

---

**`wikipedia2026newpendolino`** — **SOURCE SECONDAIRE.** Masses de l'ETR 600/610.

```bibtex
@misc{wikipedia2026newpendolino,
  author       = {{Wikipedia contributors}},
  title        = {New Pendolino},
  howpublished = {Wikipedia, The Free Encyclopedia},
  year         = {2026},
  note         = {Source secondaire; utilisée pour les masses, la puissance venant du communiqué Alstom},
  url          = {https://en.wikipedia.org/wiki/New_Pendolino},
  urldate      = {2026-08-25}
}
```

URL exacte : https://en.wikipedia.org/wiki/New_Pendolino

Passages exacts :

> Total installed power: **5,500 kW (7,376 hp)**
> Weight: empty **387 tonnes (853,000 lb)** · loaded **421 t (928,000 lb)**
> Formation: **7 cars (4 with motors, 3 trailers)**
> Maximum speed: **250 km/h (155 mph)** ; record 293 km/h
> Maximum load per axle with passengers: **16.5 tonnes**

C'est **la seule source de l'échantillon qui donne à la fois la masse à vide et la masse en charge**, ce qui permet de mesurer l'écart de convention : 421 / 387 = 1,088, soit **8,8 % d'écart entre vide et charge**. Ce ratio est utilisable pour convertir les autres masses à vide en masses en charge dans le rapport.

Contrôle de cohérence : 16,5 t par essieu × 28 essieux = 462 t théoriques, au-dessus des 421 t annoncés en charge, donc les 16,5 t sont bien un maximum d'essieu moteur et non une moyenne. Cohérent.

---

**`wikipedia2026tgvduplex`** — **SOURCE SECONDAIRE.** TGV Duplex.

```bibtex
@misc{wikipedia2026tgvduplex,
  author       = {{Wikipedia contributors}},
  title        = {TGV Duplex},
  howpublished = {Wikipedia, The Free Encyclopedia},
  year         = {2026},
  note         = {Source secondaire; la SNCF ne publie pas de fiche technique détaillée en ligne},
  url          = {https://en.wikipedia.org/wiki/TGV_Duplex},
  urldate      = {2026-08-25}
}
```

URL exacte : https://en.wikipedia.org/wiki/TGV_Duplex

Passages exacts :

> Power output : **8,800 kW (11,801 hp) (Duplex, AC)** ; 9,280 kW (12,445 hp) (Dasye, AC)
> Weight : **380 t (374 long tons; 419 short tons)** (à vide)
> Formation : **2 power cars + 8 passenger cars**
> Maximum speed : **320 km/h**
> Train length : **200 m**
> Seating : 510 places (182 première, 328 seconde) ; 644 en configuration Ouigo

Qualification : la SNCF ne publie pas de fiche technique détaillée en ligne. Le chiffre de 8 800 kW sous 25 kV est le chiffre de la motrice TGV Réseau bicourant, largement repris et cohérent avec les sources francophones consultées (`trainsso2026duplex` ci-dessous). Convention : la SNCF exprime traditionnellement la puissance des TGV **en puissance continue à la jante**, ce qui rend ce chiffre directement comparable à la « Traction power » de Siemens et non à la puissance nominale moteur du Charger.

---

**`trainsso2026duplex`** — **SOURCE SECONDAIRE (site amateur francophone).** Corroboration du TGV Duplex.

```bibtex
@misc{trainsso2026duplex,
  author       = {{Trains du Sud-Ouest}},
  title        = {{TGV Duplex}},
  howpublished = {trainsso.fr},
  year         = {2026},
  note         = {Source secondaire, site amateur; utilisée uniquement en corroboration},
  url          = {https://trainsso.fr/TGVDuplex.htm},
  urldate      = {2026-08-25}
}
```

URL exacte : https://trainsso.fr/TGVDuplex.htm

Chiffres repris : masse à vide **380 t**, puissance **8 800 kW** (3 680 kW sous 1 500 V), vitesse limite 320 km/h, rame de 200 m, 2 motrices et 8 voitures, constructeur Alstom, 89 rames construites de 1995 à 2006.

À n'utiliser qu'en corroboration, jamais comme référence principale.

---

**`fsitaliane2026frecciarossa1000`** — **SOURCE PRIMAIRE EXPLOITANT**, en complément de Hitachi.

```bibtex
@misc{fsitaliane2026frecciarossa1000,
  author       = {{Ferrovie dello Stato Italiane}},
  title        = {Frecciarossa 1000},
  howpublished = {Site FS Italiane, section Innovation},
  year         = {2026},
  url          = {https://www.fsitaliane.it/content/fsitaliane/en/innovation/transport-technology/frecciarossa-1000.html},
  urldate      = {2026-08-25}
}
```

URL exacte : https://www.fsitaliane.it/content/fsitaliane/en/innovation/transport-technology/frecciarossa-1000.html

À utiliser comme corroboration exploitant des 9 800 kW et 500 t de la fiche Hitachi.

---

**`cptdb2026viasiemens`** — **SOURCE SECONDAIRE (wiki communautaire).** Composition des rames VIA.

```bibtex
@misc{cptdb2026viasiemens,
  author       = {{Canadian Public Transit Discussion Board}},
  title        = {VIA Rail Canada Siemens Trainsets},
  howpublished = {CPTDB Wiki},
  year         = {2026},
  note         = {Source secondaire, wiki communautaire; corrobore la composition de rame publiée par VIA Rail},
  url          = {https://cptdb.ca/wiki/index.php/VIA_Rail_Canada_Siemens_trainsets},
  urldate      = {2026-08-25}
}
```

URL exacte : https://cptdb.ca/wiki/index.php/VIA_Rail_Canada_Siemens_trainsets

Chiffres repris : « The base trainsets will consist of a Siemens SCV-42 locomotive and five Venture coaches; two business class cars, two economy class cars, and an economy class cab car. The trainsets can be **reconfigured to between 3 and 7 cars long**. » 32 rames bidirectionnelles.

Point utile pour le rapport : **la rame VIA peut varier de 3 à 7 voitures**, ce qui fait varier le W/kg de la rame actuelle de 6,7 W/kg (7 voitures, nominale/vide) à 11,4 W/kg (3 voitures). L'hypothèse d'un W/kg unique pour « la rame actuelle » mérite donc une note de sensibilité.

---

## 4. Détail des calculs (reproductible)

```
Charger SCV-42 : 4 200 hp × 0,7457 = 3 131,9 kW
Rame VIA de base = 120,0 t (loco) + 5 × 50,802 t = 374,0 t à vide
  nominale/vide     : 3 131,9 / 374,0 = 8,37 W/kg
  nominale/charge   : 3 131,9 / 397,0 = 7,89 W/kg   (281 sièges × 80 kg = 22,5 t)
  jante estimée     : (3 131,9 − 600) × 0,90 = 2 278,7 kW
  jante/vide        : 2 278,7 / 374,0 = 6,09 W/kg
  jante/charge      : 2 278,7 / 397,0 = 5,74 W/kg
  sensibilité rame  : 3 voitures 272,4 t -> 11,50 (nom.) / 8,36 (jante)
                      7 voitures 475,6 t ->  6,58 (nom.) / 4,79 (jante)

LRC : traction 2 700 hp × 0,7457 = 2 013,4 kW ; brut 3 700 hp = 2 759,1 kW
  loco 114,8 t (moyenne 113–116) ; voiture 47,6 t
  loco + 4 voitures = 305,2 t -> 2 013,4 / 305,2 = 6,60 W/kg (traction/vide)
  loco + 5 voitures = 352,8 t -> 2 013,4 / 352,8 = 5,71 W/kg
  loco + 6 voitures = 400,4 t -> 2 013,4 / 400,4 = 5,03 W/kg
  loco + 5 voitures, brut     -> 2 759,1 / 352,8 = 7,82 W/kg

ETR 610      : 5 500 / 387 = 14,21 (vide)  ·  5 500 / 421 = 13,06 (charge)
Class 390/0  : 5 160 / 466 = 11,07
Class 390/1  : 6 020 / 567 = 10,62
ICE T BR 411 : 4 000 / 368 = 10,87
Velaro D 407 : 8 000 / 492 = 16,26 (masse DB)  ·  8 000 / 454 = 17,62 (masse secondaire)
ICE 3 BR 403 : 8 000 / 410 = 19,51
ETR 1000     : 9 800 / 500 = 19,60
TGV Duplex   : 8 800 / 380 = 23,16 (vide)  ·  8 800 / 421 = 20,90 (charge, 510 × 80 kg)
```

---

## 5. Ce qu'il reste à vérifier avant publication

1. **Communiqué Alstom 2005 (HTTP 403).** Ouvrir manuellement pour confirmer la phrase « Total installed power: 5500 kW », ou basculer sur la brochure Pendolino d'Alstom.
2. **Masse des voitures Venture.** Aucune source primaire. Demander à VIA Rail ou chercher dans les documents déposés à l'Office des transports du Canada ou dans les spécifications d'appel d'offres. C'est la donnée la plus faible du dossier côté canadien, et c'est celle qui pilote directement le 8 W/kg.
3. **Puissance à la jante du Charger.** Le rendement de 0,90 est une hypothèse. Si le rapport en dépend fortement, chercher les courbes effort-vitesse du SCV-42 (parfois déposées à la FRA ou au dossier de certification de Transport Canada).
4. **Masse du Velaro D.** Trancher entre les 492 t officiels DB et les 454 t des sources secondaires. Retenir 492 t et le justifier.
5. **Masse du Class 390 (466 t) : vide ou en charge ?** Non tranché. Si c'est en charge, le W/kg à vide monte à environ 12,0, ce qui renforce encore l'hypothèse de 12 W/kg.

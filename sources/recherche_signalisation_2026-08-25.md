# Signalisation ferroviaire : les marches de vitesse et leurs sources primaires

Recherche menée le 25 août 2026. Toutes les sources ci-dessous ont été consultées
directement (texte réglementaire, Federal Register, page officielle FRA, ORR, Transports
Canada, Parlement britannique). Les passages cités sont reproduits mot à mot depuis la
source. Quand une affirmation courante n'a pas pu être adossée à une source primaire, c'est
dit explicitement dans la section « Limites et trous de sourçage ».

---

## 1. Tableau des trois marches

| Marche | Système | Principe en une phrase | Vitesse max PROUVÉE en service commercial | Exemple réel | Source primaire |
|---|---|---|---|---|---|
| **1. Signalisation latérale seule** | Bloc automatique / CTC (É.-U. et Canada), signaux au sol lus par le mécanicien | Le mécanicien lit des signaux plantés le long de la voie et obéit lui-même ; rien à bord ne freine le train à sa place. | **79 mi/h (127 km/h)** aux É.-U. sans équipement de bord. Au Canada, le plafond mordant n'est pas la signalisation mais la classe de voie : **95 mi/h (153 km/h)** voyageurs, **100 mi/h (161 km/h)** pour les trains LRC. | Corridor Québec-Windsor (CN, règles CTC du REF/CROR) ; réseau américain classique | `cfr49_236_0`, `tc2021rts`, `cror2025` |
| **2. Superposition de contrôle en cabine / PTC** | ITCS, I-ETMS, ACSES + signalisation de cabine | Un calculateur embarqué connaît la limite à respecter et freine le train si le mécanicien ne le fait pas ; les signaux au sol restent en place. | **ITCS : 110 mi/h (177 km/h)** depuis février 2012. **I-ETMS : 125 mi/h (201 km/h)** chez Brightline. **Cab signals + ACSES : 150 mi/h (241 km/h)**, porté à **160 mi/h (257 km/h)** avec les rames NextGen Acela. | ITCS : ligne Michigan d'Amtrak. I-ETMS : Brightline Floride (Cocoa-Orlando). ACSES : Northeast Corridor d'Amtrak. | `fra2024itcs`, `brightline2023`, `fra2010ptc`, `fra2000acela`, `amtrak2025acela` |
| **3. Contrôle intégral en cabine** | ETCS niveau 2 (référence européenne) | Le train reçoit sa permission de rouler par radio, en continu ; les signaux au sol deviennent facultatifs, voire disparaissent. | Au-delà de 200 km/h ; standard des lignes à grande vitesse européennes. | Lignes nouvelles européennes ; HS1 au Royaume-Uni | `ec_etcs_levels`, `eu2023ccstsi` |

**Contre-point britannique (marche 1 poussée à son maximum) :** la West Coast Main Line roule
à **125 mi/h (201 km/h)** avec des signaux latéraux classiques et le TPWS, sans ETCS et sans
signalisation de cabine, avec des rames pendulaires Class 390. Sources : `hoc2010wcml`,
`orr2024tps`.

---

## 2. Sources : BibTeX, URL, date de consultation, passage exact

### 2.1 Marche 1 — signalisation latérale et plafond des 79 mi/h (É.-U.)

```bibtex
@misc{cfr49_236_0,
  author       = {{United States. Federal Railroad Administration}},
  title        = {49 CFR § 236.0 --- Applicability, minimum requirements, and penalties},
  howpublished = {Electronic Code of Federal Regulations},
  year         = {2026},
  note         = {[49 FR 3382, 26 janvier 1984]. Consulté le 25 août 2026},
  url          = {https://www.ecfr.gov/current/title-49/subtitle-B/chapter-II/part-236/subject-group-ECFR3fd63a3e8f8e42d/section-236.0}
}
```

- **URL exacte :** https://www.ecfr.gov/current/title-49/subtitle-B/chapter-II/part-236/subject-group-ECFR3fd63a3e8f8e42d/section-236.0
  (texte XML récupéré via l'API eCFR : `https://www.ecfr.gov/api/versioner/v1/full/2026-08-01/title-49.xml?part=236&section=236.0`)
- **Consulté le :** 2026-08-25
- **Passage exact, § 236.0(d)(1) :** « Prior to December 31, 2015, where any train is
  permitted to operate at a speed of 80 or more miles per hour, an automatic cab signal,
  automatic train stop, or automatic train control system complying with the provisions of
  this part shall be installed, unless an FRA approved PTC system meeting the requirements of
  this part for the subject speed and other operating conditions, is installed. »
- **Passage exact, § 236.0(d)(2) :** « On and after December 31, 2015, where any train is
  permitted to operate at a speed of 80 or more miles per hour, a PTC system complying with
  the provisions of subpart I shall be installed and operational, unless FRA approval to
  continue to operate with an automatic cab signal, automatic train stop, or automatic train
  control system complying with the provisions of this part has been justified to, and
  approved by, the Associate Administrator. »
- **Passage exact, § 236.0(c)(2) :** « On and after January 17, 2012, where a passenger train
  is permitted to operate at a speed of 60 or more miles per hour, or a freight train is
  permitted to operate at a speed of 50 or more miles per hour, a block signal system
  complying with the provisions of this part shall be installed, unless an FRA approved PTC
  system [...] is installed. »
- **Ce que ça appuie :** le plafond des 79 mi/h n'est pas écrit tel quel ; il découle du
  seuil de 80 mi/h. En dessous de 80 mi/h, un système de bloc suffit. À 80 mi/h et plus, il
  faut un équipement embarqué (cab signal, ATS, ATC ou PTC). Donc 79 mi/h est la vitesse
  maximale sous signalisation latérale seule.

```bibtex
@misc{cfr49_213_307,
  author       = {{United States. Federal Railroad Administration}},
  title        = {49 CFR § 213.307 --- Classes of track: operating speed limits},
  howpublished = {Electronic Code of Federal Regulations},
  year         = {2026},
  note         = {[63 FR 34029, 22 juin 1998, mod. 78 FR 16104, 13 mars 2013]. Consulté le 25 août 2026},
  url          = {https://www.ecfr.gov/current/title-49/subtitle-B/chapter-II/part-213/subpart-G/section-213.307}
}
```

- **Consulté le :** 2026-08-25
- **Passage exact (tableau du § 213.307(a)) :** « Class 6 track — 110 m.p.h. ; Class 7 track
  — 125 m.p.h. ; Class 8 track — 160 m.p.h. ; Class 9 track — 220 m.p.h. »
- **Note 2 du tableau, mot à mot :** « Operating speeds in excess of 125 m.p.h. are
  authorized by this part only in conjunction with FRA regulatory approval addressing other
  safety issues presented by the railroad system. »
- **Ce que ça appuie :** 201 km/h (125 mi/h) est exactement la frontière de la classe 7,
  dernière classe accessible sans approbation réglementaire supplémentaire.

```bibtex
@misc{cfr49_213_347,
  author       = {{United States. Federal Railroad Administration}},
  title        = {49 CFR § 213.347 --- Automotive or railroad crossings at grade},
  howpublished = {Electronic Code of Federal Regulations},
  year         = {2026},
  note         = {Consulté le 25 août 2026},
  url          = {https://www.ecfr.gov/current/title-49/subtitle-B/chapter-II/part-213/subpart-G/section-213.347}
}
```

- **Consulté le :** 2026-08-25
- **Passage exact, § 213.347(a) :** « There shall be no at-grade (level) highway crossings,
  public or private, or rail-to-rail crossings at-grade on Class 8 and 9 track. »
- **Passage exact, § 213.347(b) :** « If train operation is projected at Class 7 speed for a
  track segment that will include rail-highway grade crossings, the track owner shall submit
  for FRA's approval a complete description of the proposed warning/barrier system [...]
  Trains shall not operate at Class 7 speeds over any track segment having highway-rail grade
  crossings unless: (1) An FRA-approved warning/barrier system exists on that track segment;
  and (2) All elements of that warning/barrier system are functioning. »
- **Ce que ça appuie :** au-dessus de 110 mi/h avec des passages à niveau, il faut un plan de
  protection approuvé ; au-dessus de 125 mi/h, plus aucun passage à niveau n'est permis.

### 2.2 Régime canadien actuel

```bibtex
@misc{tc2021rts,
  author       = {{Transports Canada}},
  title        = {Rules Respecting Track Safety},
  year         = {2021},
  note         = {En vigueur le 15 décembre 2021. Consulté le 25 août 2026},
  url          = {https://tc.canada.ca/sites/default/files/2021-12/rules_respecting_track_safety_december_15_2021.pdf}
}
```

- **Consulté le :** 2026-08-25
- **Localisation :** Partie II, section A « CLASSES OF TRACK: Operating Speed Limits », p. 12
  du PDF.
- **Passage exact (tableau) :** « Class 5 track — 80 [freight] — 95* [passenger] » avec la
  note « * For LRC Trains, 100 mph ».
- **Passage exact, sous-partie sur l'inspection (§ 1.2) :** « The minimum requirements for the
  frequency and manner of inspecting track over which movements are operated at speeds in
  excess of those permitted over Class 5 track must be filed with and approved by the
  Minister. »
- **Ce que ça appuie :** au Canada, la règle publiée s'arrête à la classe 5. Le plafond
  voyageurs y est de 95 mi/h (153 km/h), 100 mi/h (161 km/h) pour les trains LRC. Rouler plus
  vite exige un dossier déposé et approuvé par le ministre. Il n'existe pas de classe 6 à 9
  canadienne équivalente à celles de la FRA.

```bibtex
@misc{cror2025,
  author       = {{Transports Canada}},
  title        = {Canadian Rail Operating Rules},
  year         = {2025},
  note         = {Version du 28 janvier 2025. Consulté le 25 août 2026},
  url          = {https://tc.canada.ca/sites/default/files/2025-01/Jan_2025_Canadian_rail_operating_rules_EN.pdf}
}
```

- **Consulté le :** 2026-08-25
- **Localisation :** « CENTRALIZED TRAFFIC CONTROL SYSTEM (CTC) RULES », section commençant
  p. 81 ; définition dans la section Définitions : « CENTRALIZED TRAFFIC CONTROL SYSTEM (CTC)
  — A system in which CTC rules apply. »
- **Ce que ça appuie :** le corridor canadien est exploité sous CTC au sens du REF/CROR,
  c'est-à-dire par signaux au sol commandés depuis un centre de contrôle, sans contrôle
  embarqué obligatoire.

### 2.3 Marche 2 — ITCS (110 mi/h, 177 km/h)

```bibtex
@misc{fra2024itcs,
  author       = {{United States. Federal Railroad Administration}},
  title        = {Incremental Train Control System},
  year         = {2024},
  note         = {Page mise à jour le 26 juin 2024. Consulté le 25 août 2026},
  url          = {https://railroads.dot.gov/research-development/program-areas/train-control/ptc/incremental-train-control-system}
}
```

- **Consulté le :** 2026-08-25 (page chargée via navigateur ; le serveur refuse les requêtes
  automatisées simples)
- **Mention de date sur la page :** « Last updated: Wednesday, June 26, 2024 »
- **Passage exact (paragraphe d'introduction) :** « FRA, Amtrak and the Michigan Department of
  Transportation cooperated to initiate the upgrading of 66 miles of the Amtrak-owned Michigan
  Line between Kalamazoo and New Buffalo, Michigan, to allow 110-mph operation with this PTC
  system. [...] ITCS remains in place and active on this route today. »
- **Passage exact (avant-dernier paragraphe) :** « The system has been in revenue service
  since September 2000. At the beginning, the speed limit of 79 mph was kept to gain
  experience and confidence with the system. The maximum speed limit was subsequently raised
  to 90 mph in January 2002, then to 95 mph in September 2005, then to 110 mph in February
  2012. »
- **Passage exact (nature du système) :** « It was designed as a vital overlay to an existing
  Centralized Train Control (CTC) system with a wireless computer network of servers along
  these 66 miles. »
- **Verdict sur la vérification demandée :** la limite ITCS de ~110 mi/h est **confirmée** par
  la fiche FRA, avec la date exacte du relèvement (février 2012). La clé `fra2024itcs` est
  donc valide, et la page porte bien la mention de mise à jour 2024.

```bibtex
@misc{fra2002itcswaiver,
  author       = {{United States. Federal Railroad Administration}},
  title        = {Petition for Waiver of Compliance [Docket No. FRA-2002-11533, ITCS, Amtrak Michigan Line]},
  journal      = {Federal Register},
  volume       = {67},
  number       = {75},
  pages        = {19312},
  year         = {2002},
  note         = {18 avril 2002. Consulté le 25 août 2026},
  url          = {https://www.federalregister.gov/documents/2002/04/18/02-9421/petition-for-waiver-of-compliance}
}
```

- **Consulté le :** 2026-08-25
- **Passage exact (67 FR 19312) :** « Amtrak requested permission to operate under specified
  conditions, non-revenue test trains at speeds in excess of 79 mph, not to exceed 110 mph. »
- **Ce que ça appuie :** ITCS a été bâti dès le départ comme un dispositif permettant de
  dépasser 79 mi/h, avec 110 mi/h comme cible. Utile pour montrer que 177 km/h est la marche
  de conception du système, pas un hasard.

### 2.4 Marche 2 — cab signals + ACSES sur le Northeast Corridor (150 mi/h, 241 km/h)

```bibtex
@misc{fra2010ptc,
  author       = {{United States. Federal Railroad Administration}},
  title        = {Positive Train Control Systems; Final Rule},
  journal      = {Federal Register},
  volume       = {75},
  pages        = {2598--2717},
  year         = {2010},
  note         = {15 janvier 2010, docket FRA-2008-0132. Consulté le 25 août 2026},
  url          = {https://www.federalregister.gov/documents/2010/01/15/E9-31362/positive-train-control-systems}
}
```

- **Consulté le :** 2026-08-25
- **Passage exact, 75 FR 2601 :** « In connection with these improvements, which support train
  speeds up to 150 miles per hour, Amtrak undertook to install the Advanced Civil Speed
  Enforcement System (ACSES) as a supplement to existing cab signals and automatic train
  control (speed control). Together, these systems deliver PTC core functionalities. [...]
  ACSES was installed between 2000 and 2002, and has functioned successfully between New Haven
  and Boston, and on selected high-speed segments between Washington and New York, for a
  number of years. »
- **Passage exact, 75 FR 2636 :** « FRA agrees that Amtrak has been providing safe passenger
  service at speeds between 90 and 150 miles per hour on the Northeast Corridor as well as its
  Michigan line, and that the train control systems in use (ACSES with Cab Signals, and ITCS)
  have records of safe operations. »
- **Passage exact, 75 FR 2601 (ITCS) :** « Amtrak voluntarily began development of an
  architecturally different PTC system, the Incremental Train Control System (ITCS), for
  installation on its Michigan Line. [...] Highway-rail grade crossings on the route were
  fitted with ITCS units to pre-start the warning systems for high-speed trains and to monitor
  crossing warning system health in real time. »
- **Ce que ça appuie :** c'est LA phrase qui vaut précédent nord-américain. Le régulateur
  fédéral américain écrit noir sur blanc qu'Amtrak exploite en sécurité entre 90 et 150 mi/h
  sous « ACSES with Cab Signals ». 150 mi/h = 241 km/h, bien au-dessus des 201 km/h visés.

```bibtex
@misc{cfr49_236_1007,
  author       = {{United States. Federal Railroad Administration}},
  title        = {49 CFR § 236.1007 --- Additional requirements for high-speed service},
  howpublished = {Electronic Code of Federal Regulations},
  year         = {2026},
  note         = {[75 FR 2699, 15 janvier 2010, mod. 83 FR 59218, 21 novembre 2018]. Consulté le 25 août 2026},
  url          = {https://www.ecfr.gov/current/title-49/subtitle-B/chapter-II/part-236/subpart-I/section-236.1007}
}
```

- **Consulté le :** 2026-08-25
- **Passage exact, § 236.1007(b) :** « In addition to the requirements of paragraph (a) of this
  section, a host railroad that conducts a freight or passenger operation at more than 90 miles
  per hour shall: (1) Have an approved PTCSP establishing that the system was designed and will
  be operated to meet the fail-safe operation criteria described in Appendix C to this part;
  and (2) Prevent unauthorized or unintended entry onto the main line from any track not
  equipped with a PTC system compliant with this subpart by placement of split-point derails or
  equivalent means integrated into the PTC system [...] »
- **Passage exact, § 236.1007(c) :** « [...] a host railroad that conducts a freight or
  passenger operation at more than 125 miles per hour shall have an approved PTCSP accompanied
  by a document ("HSR-125") establishing that the system: (1) Will be operated at a level of
  safety comparable to that achieved over the 5 year period prior to the submission of the
  PTCSP by other train control systems that perform PTC functions [...] and (2) Has been
  designed to detect incursions into the right-of-way [...] »
- **Ce que ça appuie :** l'escalier réglementaire américain a trois marches nettes : 90 mi/h,
  125 mi/h, puis au-delà. **201 km/h (125 mi/h) est précisément le sommet de la marche
  intermédiaire** : jusque-là un PTC certifié suffit, au-delà il faut un dossier HSR-125.

```bibtex
@misc{fra2000acela,
  author       = {{United States. Federal Railroad Administration}},
  title        = {Secretary Slater Announces Approval of 150mph Amtrak Acela Service},
  howpublished = {Communiqué de presse, U.S. Department of Transportation},
  year         = {2000},
  note         = {18 octobre 2000. Consulté le 25 août 2026},
  url          = {https://railroads.dot.gov/elibrary/secretary-slater-announces-approval-150mph-amtrak-acela-service}
}
```

- **Consulté le :** 2026-08-25 (page chargée via navigateur)
- **Passage exact :** « FRA's approval indicates that Amtrak has satisfactorily demonstrated
  that the trainset is qualified to operate up to 150mph on the NEC. »
- **Passage exact :** « Acela Express services will operate at speeds of up to 150 mph between
  New York and Boston, and 135 mph between New York and Washington, D.C. During testing on the
  NEC, the train achieved speeds of 170mph. »
- **Ce que ça appuie :** date et autorité de l'homologation à 150 mi/h. À noter : le service à
  135 mi/h (217 km/h) entre New York et Washington dépasse déjà 201 km/h depuis 2000.

```bibtex
@misc{amtrak2025acela,
  author       = {{Amtrak}},
  title        = {Amtrak Makes History Launching NextGen Acela Service},
  howpublished = {Communiqué de presse},
  year         = {2025},
  note         = {28 août 2025. Consulté le 25 août 2026},
  url          = {https://media.amtrak.com/2025/08/amtrak-makes-history-launching-nextgen-acela-service/}
}
```

- **Consulté le :** 2026-08-25
- **Passage (paraphrase fidèle du communiqué) :** la rame NextGen Acela a une vitesse maximale
  de 160 mi/h et est entrée en service commercial le 28 août 2025 sur le Northeast Corridor
  entre Washington, New York et Boston, avec cinq rames au lancement et 28 prévues d'ici 2027.
- **Réserve :** je n'ai pas pu extraire une citation mot à mot de la page HTML du communiqué
  lors de cette session. Le chiffre de 160 mi/h et la date du 28 août 2025 apparaissent dans le
  communiqué et dans la fiche technique Amtrak
  (https://media.amtrak.com/wp-content/uploads/2025/08/Amtrak-NextGen-Acela-Fleet-Fact-Sheet.pdf).
  À revérifier avant publication si le chiffre de 160 mi/h est utilisé dans le rapport.

### 2.5 Marche 2 — I-ETMS chez Brightline (125 mi/h, 201 km/h)

```bibtex
@misc{brightline2023,
  author       = {{Brightline}},
  title        = {Brightline Makes History as Fastest Train in Florida},
  howpublished = {Communiqué de presse},
  year         = {2023},
  note         = {6 mars 2023. Consulté le 25 août 2026},
  url          = {https://www.gobrightline.com/press-room/2023/brightline-130-mph-milestone}
}
```

- **Consulté le :** 2026-08-25
- **Passage exact :** « Brightline reached speeds of 130 mph during testing between Orlando
  International Airport and Cocoa, Fla. »
- **Passage exact :** « Once carrying passengers, Brightline trains will travel at maximum
  speeds of 125 mph which is more than two miles per minute. »
- **Ce que ça appuie :** 125 mi/h (201 km/h) en service commercial sur le tronçon
  Cocoa-Orlando, corridor neuf sans passage à niveau.

```bibtex
@misc{fra2023brightlineptc,
  author       = {{United States. Federal Railroad Administration}},
  title        = {Brightline Trains Florida, LLC's Positive Train Control Safety Plan and Request for Positive Train Control System Certification},
  journal      = {Federal Register},
  volume       = {88},
  number       = {46},
  pages        = {14666--14667},
  year         = {2023},
  note         = {9 mars 2023, docket FRA-2022-0098. Consulté le 25 août 2026},
  url          = {https://www.federalregister.gov/documents/2023/03/09/2023-04832/brightline-trains-florida-llcs-positive-train-control-safety-plan-and-request-for-positive-train}
}
```

- **Consulté le :** 2026-08-25
- **Passage exact (88 FR 14666) :** « BLF asks FRA to approve its PTCSP and certify BLF's
  Interoperable Electronic Train Management System (I-ETMS) as a mixed PTC system. »
- **Ce que ça appuie :** le système de contrôle de Brightline est bien I-ETMS, certifié par la
  FRA au titre de la sous-partie I de la partie 236.
- **Trou de sourçage :** je n'ai **pas** trouvé de document FRA primaire qui écrive
  explicitement « Brightline exploite à 110 mi/h au-dessus des passages à niveau ». Ce chiffre
  de 110 mi/h aux passages à niveau se déduit du § 213.347(b) (classe 7, donc au-dessus de
  110 mi/h, exige un plan de barrières approuvé) et est repris par la presse spécialisée. À
  formuler dans le rapport comme une conséquence de la règle, pas comme un fait sourcé par la
  FRA au sujet de Brightline.

### 2.6 Marche 3 — ETCS niveau 2

```bibtex
@misc{ec_etcs_levels,
  author       = {{European Commission, Directorate-General for Mobility and Transport}},
  title        = {ETCS Levels and Modes},
  year         = {2026},
  note         = {Consulté le 25 août 2026},
  url          = {https://transport.ec.europa.eu/transport-modes/rail/ertms/what-ertms-and-how-does-it-work/etcs-levels-and-modes_en}
}
```

- **Consulté le :** 2026-08-25
- **Passage exact (niveau 1) :** « Lineside signals are necessary in level 1 applications,
  except if a semi-continuous infill is provided. »
- **Passage exact (niveau 2) :** « Continuous supervision of train movement with constant
  communication via RMR between the train and trackside. [...] Lineside signals are optional
  in this case. »
- **Passage exact (cas sans détection au sol) :** « there is no need for lineside signals or
  train detection systems on the trackside other than Eurobalises »
- **Ce que ça appuie :** le niveau 2 est la marche où l'autorisation de rouler passe par radio
  et où les signaux au sol cessent d'être nécessaires. C'est ce qui débloque les vitesses
  au-delà de ce qu'un mécanicien peut lire au sol.

```bibtex
@misc{eu2023ccstsi,
  author       = {{Commission européenne}},
  title        = {Règlement d'exécution (UE) 2023/1695 du 10 août 2023 concernant la spécification technique d'interopérabilité relative aux sous-systèmes «contrôle-commande et signalisation» du système ferroviaire de l'Union européenne},
  journal      = {Journal officiel de l'Union européenne},
  volume       = {L 222},
  pages        = {380},
  year         = {2023},
  note         = {Consulté le 25 août 2026},
  url          = {https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32023R1695}
}
```

- **Consulté le :** 2026-08-25
- **Localisation :** annexe A, spécifications ERTMS/ETCS ; la STI 2023 fusionne les anciens
  niveaux 2 et 3 en un niveau 2 unique.
- **Réserve :** je n'ai pas ouvert le texte intégral de l'annexe lors de cette session. La
  fusion des niveaux 2 et 3 est confirmée par la page de la Commission (`ec_etcs_levels`), qui
  renvoie à cette STI. Citer le règlement comme référence normative, et la page de la
  Commission pour la formulation.

### 2.7 Contre-point britannique : WCML à 125 mi/h en signalisation latérale

```bibtex
@misc{hoc2010wcml,
  author       = {Butcher, Louise},
  title        = {Railways: West Coast Main Line},
  howpublished = {House of Commons Library, Standard Note SN/BT/364},
  year         = {2010},
  note         = {Mis à jour le 16 mars 2010. Consulté le 25 août 2026},
  url          = {https://researchbriefings.files.parliament.uk/documents/SN00364/SN00364.pdf}
}
```

- **Consulté le :** 2026-08-25
- **Passage exact (section sur le système de contrôle) :** « Central to Railtrack's plans for
  WCML was to have been the new Train Control System (TCS). [...] WCML was to have been fitted
  with Level 3 of the new system, technically the most advanced [...]. However, a decision to
  install moving block signalling was reversed in late 1999 due to spiralling costs. Instead,
  a new Train Protection and Warning System (TPWS) was installed at 900 signals on the route. »
- **Passage exact (accord PUG 2) :** « Journey times would be reduced through the introduction
  of tilting trains as in PUG 1, with line speeds increasing from 110 mile/h to 125 mile/h in
  2002, but with the addition of a further increase to 140 mile/h in 2005. »
- **Passage exact (calendrier réalisé) :** « September 2004 – 125 mph tilting trains on all
  Virgin West Coast routes »
- **Passage exact (matériel) :** « The state-of-the-art 125mph Pendolino trains [...] The 52
  tilting trains, designed, built and maintained by Alstom [...] »
- **Ce que ça appuie :** c'est le cœur du contre-point. La WCML a explicitement abandonné la
  signalisation en cabine (moving block / ETCS niveau 3), a installé du TPWS sur 900 signaux
  latéraux, et roule quand même à 125 mi/h (201 km/h) avec des rames pendulaires depuis 2004.
  Le passage à 140 mi/h, lui, est resté bloqué faute de signalisation en cabine.

```bibtex
@misc{orr2024tps,
  author       = {{Office of Rail and Road}},
  title        = {Train Protection Systems: Guidance on Railway Safety Regulations 1999 and other railway safety regulations},
  year         = {2024},
  note         = {8 mai 2024. Consulté le 25 août 2026},
  url          = {https://www.orr.gov.uk/sites/default/files/2024-05/train-protection-systems-guidance-on-rsr-1999.pdf}
}
```

- **Consulté le :** 2026-08-25
- **Localisation :** section 1, § 1.6 à 1.9, p. 4-6.
- **Passage exact, § 1.6 :** « In practice, this means that RSR99 requires the use of the Train
  Protection and Warning System (TPWS), which is capable of intervening and applying train
  brakes, as a minimum, but where it is reasonably practicable, a higher level of train
  protection system, known as Automatic Train Protection (ATP), which also controls speed
  throughout the journey. In this guidance, the term ATP includes systems such as European
  Train Control Systems (ETCS) and Communications-Based Train Control (CBTC). »
- **Passage exact, § 1.7 :** « TPWS is an intermittent train protection system as it provides
  protection at certain locations across the network. »
- **Passage exact, § 1.8 :** « Since the introduction of RSR99, TPWS has been installed across
  the mainline railway at all legally required locations to ensure a minimum level of train
  protection at higher risk signals and junctions. »
- **Ce que ça appuie :** le régulateur britannique décrit le TPWS comme une protection
  intermittente, posée à des points ciblés, et l'ETCS comme la marche supérieure encore à
  déployer. Le réseau principal britannique, WCML comprise, roule donc bien sous protection
  intermittente et non sous contrôle continu en cabine.

```bibtex
@misc{uk1999rsr,
  author       = {{Royaume-Uni}},
  title        = {The Railway Safety Regulations 1999, SI 1999/2244},
  year         = {1999},
  note         = {Consulté le 25 août 2026},
  url          = {https://www.legislation.gov.uk/uksi/1999/2244/regulation/3/made}
}
```

- **Consulté le :** 2026-08-25
- **Passage exact, règlement 3(1) :** « No person shall operate, and no infrastructure
  controller shall permit the operation of, a train on a railway unless a train protection
  system is in service in relation to that train and railway. »
- **Ce que ça appuie :** l'obligation britannique porte sur un « système de protection », pas
  sur une signalisation en cabine. C'est ce qui rend le TPWS suffisant en droit.

---

## 3. Limites et trous de sourçage (à ne pas maquiller)

1. **Aucune source primaire trouvée pour un seuil réglementaire britannique de 125 mi/h.**
   L'affirmation très répandue selon laquelle « au Royaume-Uni, les signaux latéraux sont
   interdits au-delà de 125 mi/h » circule surtout via Wikipédia. Je n'ai trouvé ni dans les
   Railway Safety Regulations 1999, ni dans le guide ORR de 2024, ni dans la fiche de
   catalogue RSSB GKRT0075 (édition 5, en vigueur le 2 mars 2019), de disposition chiffrée
   posant 125 mi/h comme plafond de la signalisation latérale. Le texte intégral de GKRT0075
   n'est accessible qu'après inscription au catalogue RSSB, ce que je n'ai pas pu faire.
   **Recommandation :** dans le rapport, dire que la WCML roule à 125 mi/h en signalisation
   latérale (fait sourcé), sans affirmer que 125 mi/h serait un plafond réglementaire
   britannique.
2. **Brightline aux passages à niveau.** Le chiffre de 110 mi/h maximum au-dessus des passages
   à niveau se déduit du 49 CFR 213.347(b), pas d'un document FRA propre à Brightline.
3. **Rames NextGen Acela à 160 mi/h.** Citation mot à mot non extraite lors de cette session.
   Le chiffre et la date sont dans le communiqué Amtrak du 28 août 2025 et dans la fiche
   technique associée. À revérifier avant publication.
4. **Canada, contrôle en cabine.** Je n'ai trouvé **aucune** règle canadienne imposant un
   contrôle embarqué au-dessus d'une vitesse donnée, à la manière du 49 CFR 236.0(d). Au
   Canada, la contrainte publiée est la classe de voie (classe 5, 95 mi/h voyageurs, 100 mi/h
   LRC), et tout dépassement passe par une approbation ministérielle. Ne pas écrire qu'il
   existe un « équivalent canadien de la règle des 79 mi/h » : je n'en ai pas trouvé.
5. **STI CCS 2023/1695.** Référence normative citée, annexe non ouverte. La formulation sur la
   fusion des niveaux 2 et 3 s'appuie sur la page officielle de la Commission européenne.
6. **Accès technique.** Les serveurs de la FRA (railroads.dot.gov) et de l'eCFR refusent les
   requêtes automatisées simples. Les pages FRA ont été lues via navigateur, et le texte
   réglementaire américain via l'API eCFR et le Federal Register. Les copies de travail sont
   dans le même dossier scratchpad.

---

## 4. Ce que ça change pour le rapport

La signalisation n'est pas un continuum. C'est un escalier, et chaque marche a son prix.
La marche du bas, c'est le signal au sol lu par le mécanicien. Elle plafonne à 127 km/h aux
États-Unis, et au Canada la voie elle-même s'arrête à 153 km/h. Notre corridor est là.
La marche du milieu ajoute un calculateur à bord qui freine à la place du mécanicien. C'est
ITCS, et ITCS est homologué à 177 km/h depuis février 2012 sur la ligne Michigan d'Amtrak.
Voilà pourquoi notre scénario plafonne à 177 km/h. Ce n'est pas un chiffre choisi, c'est la
hauteur de la marche ITCS.
Monter à 201 km/h ne demande pas une technologie inconnue. Cela demande de changer de système
de contrôle, pas de changer de siècle. Brightline roule déjà à 201 km/h en Floride avec
I-ETMS, un PTC ordinaire certifié par la FRA. Amtrak roule à 241 km/h sur le Northeast
Corridor avec la signalisation de cabine et ACSES, et la FRA l'a écrit noir sur blanc en 2010.
Le prix à payer est ailleurs : à 201 km/h, la règle américaine interdit tout passage à niveau
non protégé par un dispositif approuvé, et au-dessus de 201 km/h elle les interdit tout court.
Et la West Coast Main Line britannique montre qu'on peut rouler à 201 km/h avec des rames
pendulaires et des signaux au sol, sans signalisation en cabine, depuis 2004. Le Royaume-Uni a
d'ailleurs renoncé à 225 km/h précisément parce qu'il n'a pas posé cette signalisation en
cabine. La leçon pour nous est simple : 177 km/h est la marche du contrôle embarqué léger,
201 km/h est atteignable avec un PTC certifié et des passages à niveau traités, et le vrai mur
n'arrive qu'au-delà.

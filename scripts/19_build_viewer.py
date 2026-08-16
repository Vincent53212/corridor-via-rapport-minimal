#!/usr/bin/env python3
"""Étape 19 — Visualiseur : les données du rapport, dans l'ordre du rapport.

Produit `livrables/visualiseur.html`, un SEUL fichier autonome (hors-ligne,
ouvrable par double-clic, sans CDN ni serveur).

CE QUI A CHANGÉ, ET POURQUOI. La version précédente était un navigateur de CSV :
seize onglets portant les noms de fichiers du pipeline, des en-têtes comme
`vmax_S3_kmh_plafond_courbure`, aucun fil. Elle servait à qui connaissait déjà
les données, c'est-à-dire à personne d'autre que son auteur. Le rapport, lui,
est organisé par ARGUMENT, en neuf sections. Le visualiseur suit désormais le
même ordre : chaque section rappelle ce que le rapport affirme, montre ses
chiffres de tête, et donne dessous les tables qui les produisent.

La pièce qui change tout est la VÉRIFICATION EXÉCUTABLE. Le rapport promet
qu'aucun de ses chiffres n'est saisi à la main ; ici on le prouve. Chaque
vérification déclare une table, un filtre et une agrégation, et le navigateur
refait le calcul devant le lecteur pour le comparer au chiffre publié. Le
tableau des 16 tables n'est pas perdu : il devient le mode « toutes les tables ».

Les valeurs publiées ne sont pas recopiées ici non plus : elles sont LUES dans
`rapport.md` au moment de la construction (voir `lire_publies`). Une divergence
entre le rapport et le pipeline se voit donc à l'écran au lieu de dormir.

Dépendances : stdlib seule (`csv`, `json`, `re`), plus `identite.py` qui l'est
aussi. Cette étape doit rester indépendante du venv géo.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from identite import (IDENTITE_DIR, PAPIER, VITESSE, VITESSE_COULEURS,
                      couleur_pour_vitesse, faces_polices, variables_css)
from utils import DELIVERABLES, PROJECT_ROOT

SORTIE = DELIVERABLES / "visualiseur.html"
GABARIT = IDENTITE_DIR / "visualiseur.html"
RAPPORT = PROJECT_ROOT / "rapport.md"

DUAL_HEADER = {"segments_courbature.csv"}
NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")
COEUR = ["MTL-QC", "MTL-Ott", "Ott-TO", "MTL-TO"]

# Classes de vitesse A..F : la même rampe que les bandes, du plus rapide au plus
# lent, pour qu'une classe et une vitesse se lisent avec le même code.
CLASSES = {
    "A": VITESSE_COULEURS["300_plus"], "B": VITESSE_COULEURS["250_300"],
    "C": VITESSE_COULEURS["200_250"], "D": VITESSE_COULEURS["160_200"],
    "E": VITESSE_COULEURS["100_160"], "F": VITESSE_COULEURS["sous_100"],
}

# ---------------------------------------------------------------- libellés
LABELS = {
    "segments_courbature.csv": "Segments de courbure",
    "cible_km_a_rectifier.csv": "Kilomètres à rectifier",
    "cible_sites_a_rectifier.csv": "Sites à rectifier",
    "synthese_troncon.csv": "Synthèse par tronçon",
    "scenarios_parametres.csv": "Paramètres des scénarios",
    "tbase_par_bande.csv": "Temps de base par bande",
    "marges_2x2_synthese.csv": "Marges : le 2×2",
    "marges_par_intergare.csv": "Marges par inter-gare",
    "covariables_paires.csv": "Covariables des paires",
    "voies_par_troncon.csv": "Voies par tronçon",
    "km_a_doubler.csv": "Kilomètres à doubler",
    "goulots_detranglement.csv": "Goulots structurels",
    "blocs_urbains.csv": "Blocs urbains figés",
    "passages_niveau_par_bande.csv": "Passages à niveau par bande",
    "passages_niveau_tri.csv": "Passages à niveau, un par un",
    "marges_2x2_synthese_GTFS2023.csv": "Marges 2×2, contrôle GTFS 2023",
    "marges_par_intergare_GTFS2023.csv": "Marges par inter-gare, contrôle GTFS 2023",
    "biais_segments_courts.csv": "Biais de la fenêtre de mesure",
    "tbase_par_bande_corriges.csv": "Temps de base, biais corrigé",
    "blocs_urbains_corriges.csv": "Blocs urbains, variante corrigée",
}

QUOI = {
    "segments_courbature.csv":
        "Le corridor découpé en segments de courbure homogène. Pour chacun, le rayon "
        "gouvernant, le degré de courbure et la vitesse que cette géométrie autorise "
        "dans chaque scénario. C'est la table de base : toutes les autres en dérivent.",
    "cible_km_a_rectifier.csv":
        "Combien de kilomètres il faudrait rectifier pour atteindre une vitesse cible, "
        "par scénario et par tronçon. La table qui produit les chiffres de tête du rapport.",
    "cible_sites_a_rectifier.csv":
        "Les mêmes kilomètres, site par site, avec le rayon actuel et le rayon visé.",
    "tbase_par_bande.csv":
        "Le temps de parcours calculé par intégration, sans marge, pour chaque tronçon, "
        "scénario et plafond de vitesse. La colonne « horaire actuel » est le temps de VIA.",
    "marges_2x2_synthese.csv":
        "La marge d'horaire médiane par cellule voie × propriétaire, sur le cœur du "
        "corridor et sur le sud-ouest ontarien.",
    "marges_par_intergare.csv":
        "Le détail paire par paire : temps à l'horaire, temps que la géométrie permet, "
        "marge, dispersion entre sillons, et le motif d'exclusion s'il y en a un.",
    "passages_niveau_tri.csv":
        "L'inventaire de Transports Canada apparié au tracé : chaque passage, sa "
        "protection, son trafic, la bande de vitesse du segment qui le porte.",
    "passages_niveau_par_bande.csv":
        "Le compte des passages par bande de vitesse, scénario et tronçon.",
    "km_a_doubler.csv":
        "Les sections en voie simple du corridor et leur longueur, dédoublonnées.",
    "blocs_urbains.csv":
        "Les traversées urbaines, dont le temps est figé à l'horaire actuel plutôt que "
        "calculé : l'étude n'y promet aucun gain.",
    "biais_segments_courts.csv":
        "Pour chaque segment publié, le rayon que la fenêtre de 900 m annonce et celui "
        "que le corps de la courbe mesure. Leur rapport est le facteur de biais : il "
        "vaut 1 quand le segment est plus long que la fenêtre, et il monte quand la "
        "courbe est plus courte qu'elle.",
    "tbase_par_bande_corriges.csv":
        "La même intégration que les temps de base, mais sur les segments dont le rayon "
        "a été corrigé du biais de fenêtre. À comparer ligne à ligne avec la table de "
        "référence : l'écart est de 0,4 à 7,8 minutes.",
}

# Ordre d'apparition dans le menu déroulant : les tables du fil d'abord.
ORDRE = list(LABELS.keys())

# ------------------------------------------------- dictionnaire de colonnes
# Un en-tête doit se lire sans le pipeline. La règle générale déplie le
# snake_case et sort l'unité ; les entrées ci-dessous couvrent ce que la règle
# ne peut pas deviner.
UNITES = {
    "kmh": "km/h", "mph": "mi/h", "km": "km", "m": "m", "mm": "mm",
    "deg": "°", "pct": "%", "min": "min", "mille": "mi", "in": "po",
}
NOMS = {
    "troncon": "Tronçon", "tronçon": "Tronçon", "scenario": "Scénario",
    "cellule": "Cellule", "region": "Région", "bande_kmh": "Bande",
    "vitesse_cible_kmh": "Vitesse visée", "km_a_rectifier": "À rectifier",
    "n_sites": "Sites", "pct_troncon": "Part du tronçon",
    "rayon_cible_m": "Rayon visé", "degre_courbure_cible_max_deg": "Degré visé",
    "km_debut": "km début", "km_fin": "km fin", "km_début": "km début",
    "longueur_km": "Longueur", "marge_pct": "Marge",
    "t_horaire_med_min": "Horaire actuel", "t_base_S1cap160_min": "Temps géométrique",
    "dispersion_iqr_pct": "Dispersion", "n_sillons": "Sillons",
    "exclue_du_2x2": "Exclue du 2×2", "n_passages": "Passages",
    "mediane": "Médiane", "tbase_sans_marge_min": "Temps de base",
    "t_horaire_actuel_min": "Horaire actuel", "de": "De", "a": "À",
    "gare_amont": "Gare amont", "gare_aval": "Gare aval",
    "km_a_doubler": "À doubler", "protection": "Protection",
    "trains_jour": "Trains/jour", "vehicules_jour": "Véhicules/jour",
    "intervention": "Intervention", "acces": "Accès", "localisation": "Localisation",
    "R_min_m": "Rayon minimal", "R_classant_min_m": "Rayon gouvernant",
    "degré_courbure_gouvernant_deg": "Degré gouvernant",
}


def joli(cle: str) -> tuple[str, str, str]:
    """(nom lisible, unité, rampe) pour une colonne. La rampe dit à l'affichage
    de peindre la valeur : « vitesse » pour un km/h, « classe » pour un A..F."""
    brut = cle.split(" / ")[0].strip()
    rampe = ""
    if re.search(r"vmax.*kmh|vitesse.*kmh", brut, re.I):
        rampe = "vitesse"
    elif re.fullmatch(r"classe_S[123]", brut, re.I):
        rampe = "classe"

    if brut in NOMS:
        m = re.search(r"(?:^|_)(kmh|mph|deg|pct|mm|min|km|m)(?:_|$)", brut)
        return NOMS[brut], UNITES.get(m.group(1), "") if m else "", rampe

    # L'unité se cherche PARTOUT dans le nom et pas seulement à la fin :
    # `vmax_S2_kmh_plafond_courbure` la porte au milieu, et l'en-tête sortait
    # « Plafond S2 kmh » au lieu de « Plafond S2 » surmonté de « km/h ».
    # Jamais le premier jeton : `min_...` serait un minimum, pas des minutes.
    jetons, unite = brut.split("_"), ""
    for i in range(len(jetons) - 1, 0, -1):
        if jetons[i].lower() in UNITES:
            unite = UNITES[jetons.pop(i).lower()]
            break
    # Les scénarios restent en majuscules, le reste passe en minuscules.
    # Sigles gardés en capitales, quelle que soit leur casse dans le pipeline.
    SIGLES = r"S[123]|CN|VIA|GTFS|IQR|MTX|TC|OSM"
    mots = [j.upper() if re.fullmatch(SIGLES, j, re.I) else j.lower() for j in jetons]
    nom = " ".join(mots).replace("vmax", "plafond").replace("plafond courbure", "")
    nom = re.sub(r"\s+", " ", nom).strip()
    # Majuscule d'initiale SEULEMENT : `.capitalize()` aurait rabaissé « S2 »
    # en « s2 » et « IQR » en « iqr », que la boucle ci-dessus venait de préserver.
    nom = nom[:1].upper() + nom[1:]
    return nom or brut, unite, rampe


# --------------------------------------------------------- chiffres publiés
def lire_publies() -> dict[str, dict[str, float]]:
    """Relève dans rapport.md les chiffres que les vérifications comparent.

    Les recopier ici ferait exactement la faute que le garde-fou doit détecter :
    le rapport bougerait, le visualiseur confirmerait l'ancienne valeur, et les
    deux se tromperaient de concert."""
    txt = RAPPORT.read_text(encoding="utf-8")
    esp = r"[\s ]*"

    def ligne(motif: str, n: int) -> list[float]:
        m = re.search(motif, txt)
        if not m:
            sys.exit(f"chiffre publié introuvable dans rapport.md : {motif[:60]}")
        return [float(m.group(i + 1).replace(" ", "").replace(" ", ""))
                for i in range(n)]

    a, b, c = ligne(
        r"Sous 200 km/h[^|]*\|" + esp + r"(\d[\d\s ]*) km" + esp + r"\|"
        + esp + r"(\d[\d\s ]*) km" + esp + r"\|" + esp + r"(\d[\d\s ]*) km", 3)
    d, e, f = ligne(
        r"Sous 160 km/h[^|]*\|" + esp + r"(\d[\d\s ]*) km" + esp + r"\|"
        + esp + r"(\d[\d\s ]*) km" + esp + r"\|" + esp + r"(\d[\d\s ]*) km", 3)
    g, = ligne(r"Voie double, CN \| [^|]*\|" + esp + r"(\d+)" + esp + r"%", 1)
    h, = ligne(r"Voie simple, VIA \| [^|]*\|" + esp + r"(\d+)" + esp + r"%", 1)
    i, = ligne(r"Voie simple, CN \| [^|]*\|" + esp + r"(\d+)" + esp + r"%", 1)
    j, = ligne(r"\|" + esp + r"> 201 km/h \(> 125 mi/h\)" + esp + r"\|" + esp + r"(\d+)", 1)
    k, = ligne(r"\|" + esp + r"178-201 km/h \(111-125 mi/h\)" + esp + r"\|" + esp + r"(\d+)", 1)
    return {
        "residu200": {"S1": a, "S2": b, "S3": c},
        "residu160": {"S1": d, "S2": e, "S3": f},
        "marges": {"double-CN": g, "simple-VIA": h, "simple-CN": i},
        "pn": {">201": j, "178-201": k},
    }


def sections(pub: dict) -> list[dict]:
    """Le fil : une entrée par section du rapport, dans le même ordre et avec
    les mêmes clés, pour que le lecteur passe de l'un à l'autre sans se perdre."""
    return [
        {
            "cle": "01 · Ce qu'il faut retenir", "titre": "Synthèse",
            "dit": "Sur la voie qui existe déjà, un train pendulaire exploité selon la "
                   "méthode que le CN applique <b>déjà</b> met <b>4 h 12 à 4 h 33</b> "
                   "entre Montréal et Toronto, contre 5 h 18 aujourd'hui. Ce qui reste "
                   "à corriger se compte, et c'est peu.",
            "chiffres": [
                {"v": f"{pub['residu200']['S2']:.0f} km", "l": "à rectifier sous 200 km/h, scénario recommandé",
                 "couleur": VITESSE_COULEURS["160_200"]},
                {"v": f"{pub['residu200']['S3']:.0f} km", "l": "à rectifier sous 200 km/h, pendulaire moderne"},
                {"v": "1 433 km", "l": "de corridor mesuré, quatre trajets"},
            ],
            "verifications": [{
                "enonce": "Le rapport publie les kilomètres à rectifier pour tenir "
                          "200 km/h. <b>Refaisons la somme</b> à partir des sites mesurés.",
                "table": "cible_km_a_rectifier.csv",
                "filtre": [{"col": "vitesse_cible_kmh", "op": "==", "val": 200},
                           {"col": "troncon", "op": "dans", "val": COEUR}],
                "grouper": "scenario", "agreger": "km_a_rectifier", "mode": "somme",
                "publie": pub["residu200"], "unite": "km", "arrondi": 1, "tolerance": 1,
                "libelles": {"S1": "S1, voie et train actuels",
                             "S2": "S2, scénario recommandé",
                             "S3": "S3, pendulaire moderne"},
            }],
            "pieces": ["cible_km_a_rectifier.csv", "tbase_par_bande.csv"],
        },
        {
            "cle": "02 · Comment c'est mesuré", "titre": "Méthode et périmètre",
            "dit": "La géométrie vient d'OpenStreetMap, appariée aux horaires de VIA. Le "
                   "temps de parcours est une intégration le long du tracé, pas une "
                   "moyenne : les traversées urbaines restent figées à l'horaire actuel, "
                   "et la marge d'exploitation est encadrée entre deux bornes plutôt que "
                   "devinée.",
            "chiffres": [
                {"v": "1 268", "l": "segments de courbure homogène"},
                {"v": "900 m", "l": "fenêtre d'ajustement, imposée par le bruit de la source"},
            ],
            "pieces": ["segments_courbature.csv", "blocs_urbains.csv"],
        },
        {
            "cle": "03 · Matériel et voie", "titre": "Le train pendulaire et le dévers",
            "dit": "Trois scénarios. <b>S1</b> est la voie et le train d'aujourd'hui. "
                   "<b>S2</b>, le scénario recommandé, est un pendulaire exploité au "
                   "dévers maximal standard du CN : aucune dérogation à demander. "
                   "<b>S3</b> sort du précédent nord-américain et demanderait une "
                   "approbation par équipement.",
            "chiffres": [
                {"v": "4,82", "l": "coefficient k de S2 (v = k·√R)"},
                {"v": "5,75", "l": "coefficient k de S3"},
            ],
            "pieces": ["scenarios_parametres.csv", "segments_courbature.csv"],
        },
        {
            "cle": "04 · Capacité", "titre": "Doublement des voies et régime de cohabitation",
            "dit": "Le corridor offre une expérience naturelle : des voies simples chez "
                   "VIA, des voies simples chez le CN, des voies doubles chez le CN. En "
                   "comparant la marge d'horaire des trois familles, on lit séparément le "
                   "prix de la voie manquante et celui du régime. <b>Le régime pèse plus "
                   "que le nombre de voies.</b>",
            "chiffres": [
                {"v": f"{pub['marges']['simple-CN']:.0f} %", "l": "marge médiane, voie simple du CN",
                 "couleur": VITESSE_COULEURS["sous_100"]},
                {"v": f"{pub['marges']['double-CN']:.0f} %", "l": "marge médiane, voie double du CN"},
                {"v": f"{pub['marges']['simple-VIA']:.0f} %", "l": "marge médiane, voie simple de VIA"},
            ],
            "verifications": [{
                "enonce": "Sous propriétaire VIA, la voie simple ne coûte rien ; sous le "
                          "CN, elle coûte trente points. <b>Reprenons les médianes</b> "
                          "sur le cœur du corridor.",
                "table": "marges_2x2_synthese.csv",
                "filtre": [{"col": "region", "op": "==", "val": "coeur"}],
                "grouper": "cellule", "agreger": "mediane", "mode": "mediane",
                "publie": pub["marges"], "unite": "%", "arrondi": 1, "tolerance": 1,
                "libelles": {"double-CN": "Voie double, CN",
                             "simple-CN": "Voie simple, CN",
                             "simple-VIA": "Voie simple, VIA"},
            }],
            "pieces": ["marges_2x2_synthese.csv", "marges_par_intergare.csv",
                       "km_a_doubler.csv", "covariables_paires.csv"],
        },
        {
            "cle": "05 · Obstacles au sol", "titre": "Passages à niveau",
            "dit": "Au-delà de 201 km/h, le précédent américain ne tolère aucun passage à "
                   "niveau. <b>C'est le vrai mur au-dessus de 200 km/h</b>, très loin "
                   "devant la signalisation.",
            "chiffres": [
                {"v": f"{pub['pn']['>201']:.0f}", "l": "passages dans la bande « zéro passage »",
                 "couleur": VITESSE_COULEURS["sous_100"]},
                {"v": "924", "l": "passages sur le corridor, dédoublonnés"},
                {"v": "569", "l": "privés ou de ferme, candidats à la fermeture"},
            ],
            "verifications": [{
                "enonce": "<b>Comptons les passages</b> par bande de vitesse, selon la "
                          "géométrie que le pendulaire moderne libérerait.",
                "table": "passages_niveau_tri.csv",
                "filtre": [], "grouper": "bande_S3", "agreger": "tc_number",
                "mode": "compte", "publie": pub["pn"], "unite": "passages",
                "arrondi": 1, "tolerance": 0,
                "libelles": {">201": "Au-delà de 201 km/h", "178-201": "De 178 à 201 km/h"},
            }],
            "pieces": ["passages_niveau_tri.csv", "passages_niveau_par_bande.csv"],
        },
        {
            "cle": "06 · Commande des trains", "titre": "Signalisation",
            "dit": "Un escalier de trois marches : rien à faire jusqu'à 160 km/h, une "
                   "superposition de contrôle en cabine de 161 à 200, un système intégral "
                   "au-delà. <b>La marche du scénario recommandé est la deuxième</b>, et "
                   "elle a un précédent tarifé au Michigan.",
            "pieces": ["segments_courbature.csv"],
        },
        {
            "cle": "07 · Les temps de parcours", "titre": "Résultats intégrés",
            "dit": "Deux tables. Le temps de base, sans marge, sort de l'intégration. Le "
                   "temps publié y ajoute une marge <b>en fourchette</b> : la borne basse "
                   "applique la règle normative de 9 pour cent, la borne haute reconduit "
                   "la marge que le tronçon porte aujourd'hui.",
            "chiffres": [
                {"v": "4 h 12", "l": "Montréal-Toronto, scénario recommandé, borne basse"},
                {"v": "2 h 25", "l": "Montréal-Québec, scénario recommandé, borne basse"},
            ],
            "pieces": ["tbase_par_bande.csv", "synthese_troncon.csv"],
        },
        {
            "cle": "08 · Ce qui reste à faire", "titre": "Limites, et l'étude qu'il faut commander",
            "dit": "Cette étude compte, elle ne dimensionne pas. Le cantonnement fin, la "
                   "simulation de circulation et la conception par site relèvent d'une "
                   "étude de circulation menée avec le propriétaire de la voie.",
            "pieces": ["goulots_detranglement.csv", "cible_sites_a_rectifier.csv"],
        },
        {
            "cle": "09 · Contrôles", "titre": "Les contre-épreuves",
            "dit": "Les marges ont été refaites sur une seconde saison d'horaires (GTFS "
                   "2023) pour vérifier qu'elles ne tiennent pas à une année "
                   "particulière. Ces tables sont ici, à part, pour qui veut les "
                   "confronter.",
            "pieces": ["marges_2x2_synthese_GTFS2023.csv",
                       "marges_par_intergare_GTFS2023.csv"],
        },
    ]


# ------------------------------------------------------------- lecture CSV
def lire(path: Path) -> tuple[list[str], list[list]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f, delimiter=";"))
    if not rows:
        return [], []
    if path.name in DUAL_HEADER and len(rows) >= 2:
        return rows[0], rows[2:]      # la ligne 2 est l'en-tête anglais
    return rows[0], rows[1:]


def convertir(v):
    if v is None or v == "":
        return None
    if NUM_RE.match(v):
        f = float(v)
        return int(f) if ("." not in v and -2 ** 53 < f < 2 ** 53) else f
    return v


def dataset(path: Path) -> dict | None:
    entetes, data = lire(path)
    if not entetes or (len(entetes) <= 1 and len(data) <= 1):
        return None
    colonnes = []
    for i, e in enumerate(entetes):
        vals = [r[i] for r in data if i < len(r) and r[i] not in (None, "")]
        num = bool(vals) and all(NUM_RE.match(str(v)) for v in vals)
        dec = 0
        if num:
            dec = max((len(str(v).split(".")[1]) for v in vals if "." in str(v)), default=0)
        nom, unite, rampe = joli(e)
        colonnes.append({"cle": e, "nom": nom, "unite": unite, "num": num,
                         "rampe": rampe, "decimales": min(dec, 2)})
    rows = [[convertir(v) for v in r] + [None] * (len(entetes) - len(r)) for r in data]
    voulues = ESSENTIEL.get(path.name)
    if voulues:
        manquantes = [c for c in voulues if c not in entetes]
        if manquantes:
            sys.exit(f"{path.name} : colonnes essentielles absentes {manquantes}\n"
                     "Le pipeline a renommé une colonne ; corriger ESSENTIEL.")
        essentiel = [entetes.index(c) for c in voulues]
    else:
        essentiel = list(range(len(entetes)))
    return {"file": path.name, "label": LABELS.get(path.name, path.stem),
            "quoi": QUOI.get(path.name, ""), "columns": colonnes, "rows": rows,
            "essentiel": essentiel, "presets": PRESETS.get(path.name, [])}


# Colonnes montrées d'entrée. Les tables du pipeline en portent jusqu'à 29, et
# les plus utiles sont souvent les dernières : un lecteur qui ouvre « Segments de
# courbure » tombait sur des identifiants d'alignement et devait faire défiler
# sur toute la largeur pour trouver une vitesse. Le reste n'est pas retiré, il
# est derrière un bouton. Une table absente de cette table montre tout.
ESSENTIEL = {
    "segments_courbature.csv": [
        "tronçon", "km_début", "km_fin", "longueur_m",
        "degré_courbure_gouvernant_deg", "R_classant_min_m",
        "vmax_S2_kmh_plafond_courbure", "classe_S2",
        "vmax_S3_kmh_plafond_courbure", "classe_S3", "gare_amont", "gare_aval"],
    "passages_niveau_tri.csv": [
        "tc_number", "troncon_principal", "subdivision", "mille", "localisation",
        "acces", "protection", "trains_jour", "vehicules_jour",
        "vmax_S3_kmh", "bande_S3", "intervention"],
    "marges_par_intergare.csv": [
        "troncon", "region", "de", "a", "longueur_km", "cellule",
        "t_horaire_med_min", "t_base_S1cap160_min", "marge_pct",
        "dispersion_iqr_pct", "exclue_du_2x2"],
    "marges_par_intergare_GTFS2023.csv": [
        "troncon", "region", "de", "a", "longueur_km", "cellule",
        "t_horaire_med_min", "t_base_S1cap160_min", "marge_pct",
        "dispersion_iqr_pct", "exclue_du_2x2"],
    "cible_sites_a_rectifier.csv": None,   # renseignée à la lecture si besoin
}

# Les préréglages sont des QUESTIONS, et le scénario recommandé passe en premier :
# la version précédente n'offrait que S3, le plus ambitieux, comme si c'était la
# lecture par défaut.
PRESETS = {
    "segments_courbature.csv": [
        {"label": "Sous 200 km/h en S2", "conds": [{"col": "vmax_S2_kmh_plafond_courbure", "op": "<", "val": 200}]},
        {"label": "Sous 200 km/h en S3", "conds": [{"col": "vmax_S3_kmh_plafond_courbure", "op": "<", "val": 200}]},
    ],
    "cible_km_a_rectifier.csv": [
        {"label": "Cible 200 km/h", "conds": [{"col": "vitesse_cible_kmh", "op": "==", "val": 200}]},
        {"label": "Scénario recommandé", "conds": [{"col": "scenario", "op": "==", "val": "S2"}]},
    ],
    "passages_niveau_tri.csv": [
        {"label": "À fermer (privés, ferme)", "conds": [{"col": "acces", "op": "==", "val": "Private"}]},
    ],
    "marges_par_intergare.csv": [
        {"label": "Cœur du corridor", "conds": [{"col": "region", "op": "==", "val": "coeur"}]},
    ],
}


def main() -> None:
    vus, datasets = set(), []
    for nom in ORDRE:
        p = DELIVERABLES / nom
        if p.exists() and (ds := dataset(p)):
            datasets.append(ds)
            vus.add(nom)
    for p in sorted(DELIVERABLES.glob("*.csv")):
        if p.name not in vus and (ds := dataset(p)):
            datasets.append(ds)

    pub = lire_publies()
    charge = {
        "datasets": datasets,
        "sections": sections(pub),
        "vitesse": VITESSE,
        "classes": CLASSES,
        "meta": {
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "pied": "Corridor Québec-Toronto · Ce que la voie existante permet · "
                    "Vincent Duguay / Vision Transport<br>"
                    "<b>Les chiffres publiés sont lus dans le rapport</b> au moment de la "
                    "construction de cette page, et les vérifications les recalculent à "
                    "partir des tables. Une divergence entre les deux se voit à l'écran.",
        },
    }
    blob = json.dumps(charge, ensure_ascii=False).replace("</", "<\\/")
    html = (GABARIT.read_text(encoding="utf-8")
            .replace("/*__FONTS__*/", faces_polices())
            .replace("/*__VARS__*/", variables_css())
            .replace("__NAV__", (IDENTITE_DIR / "corridor_nav.svg").read_text(encoding="utf-8"))
            .replace("__PAYLOAD__", blob))
    SORTIE.write_text(html, encoding="utf-8")

    print("=== Étape 19 — Visualiseur ===")
    print(f"  {SORTIE.name}  ({len(datasets)} tables, "
          f"{SORTIE.stat().st_size / 1024:.0f} Ko)")
    for cle, vals in pub.items():
        print(f"  publié « {cle} » relevé dans rapport.md : "
              + ", ".join(f"{k}={v:g}" for k, v in vals.items()))


if __name__ == "__main__":
    main()

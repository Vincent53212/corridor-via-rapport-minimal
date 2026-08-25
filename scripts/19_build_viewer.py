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

La pièce qui change tout est la VÉRIFICATION EXÉCUTABLE. Chaque
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
    "km_restants_sous_grande_vitesse.csv": "Kilomètres restants sous grande vitesse",
    "sites_restants_sous_grande_vitesse.csv": "Sites restants, un par un",
    "decomposition_gains.csv": "D'où viennent les minutes",
    "synthese_troncon.csv": "Synthèse par tronçon",
    "scenarios_parametres.csv": "Paramètres des scénarios",
    "temps_scenario_1.csv": "Temps, scénario 1 (le train pendulaire)",
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
    "temps_scenario_2.csv": "Temps, scénario 2 (zones urbaines modernisées)",
    "temps_scenario_3.csv": "Temps, scénario 3 (courbes corrigées au doublement)",
    "blocs_urbains_blocs_libres.csv": "Blocs urbains, scénarios 2 et 3",
    "blocs_urbains_rectifies_blocs_libres.csv": "Blocs urbains, scénario 3",
}

QUOI = {
    "segments_courbature.csv":
        "Le corridor découpé en segments de courbure homogène. Pour chacun, le rayon "
        "gouvernant, le degré de courbure et la vitesse que cette géométrie autorise "
        "dans chaque scénario. C'est la table de base : toutes les autres en dérivent.",
    "km_restants_sous_grande_vitesse.csv":
        "Combien de kilomètres restent sous une vitesse cible, par scénario et par "
        "tronçon. La table qui produit les chiffres de tête du rapport (cible 177).",
    "sites_restants_sous_grande_vitesse.csv":
        "Les mêmes kilomètres, site par site, avec le rayon actuel et le rayon visé.",
    "decomposition_gains.csv":
        "La décomposition de la figure des gains : pour chaque trajet, le gain total "
        "et ses quatre parts (relèvement du plafond, pendulaire, doublement, "
        "cohabitation), avec les lignes de contrôle. Les parts somment au gain par "
        "construction, et la vérification de la section 7 le refait devant vous.",
    "temps_scenario_1.csv":
        "Le temps de parcours calculé par intégration, sans marge, pour chaque tronçon "
        "et plafond de vitesse. La ligne pendulaire × 177 est le scénario 1 ; la "
        "colonne « horaire actuel » est le temps de VIA. Les temps publiés du rapport "
        "sont ces temps de base multipliés par 1,10 (la marge).",
    "temps_scenario_2.csv":
        "Même moteur, zones urbaines modernisées : les approches roulent ce que "
        "leur géométrie permet. Scénario 2.",
    "temps_scenario_3.csv":
        "Même moteur, zones urbaines modernisées ET courbes corrigées sur les "
        "sections à doubler. Scénario 3.",
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
    "temps_scenario_2.csv": "Temps, scénario 2 (zones urbaines modernisées)",
    "temps_scenario_3.csv": "Temps, scénario 3 (courbes corrigées au doublement)",
    "blocs_urbains_blocs_libres.csv": "Blocs urbains, scénarios 2 et 3",
    "blocs_urbains_rectifies_blocs_libres.csv": "Blocs urbains, scénario 3",
}

QUOI = {
    "segments_courbature.csv":
        "Le corridor découpé en segments de courbure homogène. Pour chacun, le rayon "
        "gouvernant, le degré de courbure et la vitesse que cette géométrie autorise "
        "dans chaque scénario. C'est la table de base : toutes les autres en dérivent.",
    "km_restants_sous_grande_vitesse.csv":
        "Combien de kilomètres restent sous une vitesse cible, par scénario et par "
        "tronçon. La table qui produit les chiffres de tête du rapport (cible 177).",
    "sites_restants_sous_grande_vitesse.csv":
        "Les mêmes kilomètres, site par site, avec le rayon actuel et le rayon visé.",
    "decomposition_gains.csv":
        "La décomposition de la figure des gains : pour chaque trajet, le gain total "
        "et ses quatre parts (relèvement du plafond, pendulaire, doublement, "
        "cohabitation), avec les lignes de contrôle. Les parts somment au gain par "
        "construction, et la vérification de la section 7 le refait devant vous.",
    "tbase_par_bande_rectifies.csv":
        "Sensibilité : les courbes des sections à doubler sont rectifiées au plafond "
        "retenu. À comparer ligne à ligne avec la table de référence.",
    "tbase_par_bande_blocs_libres.csv":
        "Sensibilité : les blocs urbains cessent d'être figés à l'horaire et roulent ce "
        "que leur géométrie permet. Une borne, pas une promesse.",
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
    "temps_scenario_2.csv": "Temps, scénario 2 (zones urbaines modernisées)",
    "temps_scenario_3.csv": "Temps, scénario 3 (courbes corrigées au doublement)",
    "blocs_urbains_blocs_libres.csv": "Blocs urbains, scénarios 2 et 3",
    "blocs_urbains_rectifies_blocs_libres.csv": "Blocs urbains, scénario 3",
}

QUOI = {
    "segments_courbature.csv":
        "Le corridor découpé en segments de courbure homogène. Pour chacun, le rayon "
        "gouvernant, le degré de courbure et la vitesse que cette géométrie autorise "
        "dans chaque scénario. C'est la table de base : toutes les autres en dérivent.",
    "km_restants_sous_grande_vitesse.csv":
        "Combien de kilomètres restent sous une vitesse cible, par scénario et par "
        "tronçon. La table qui produit les chiffres de tête du rapport (cible 177).",
    "sites_restants_sous_grande_vitesse.csv":
        "Les mêmes kilomètres, site par site, avec le rayon actuel et le rayon visé.",
    "decomposition_gains.csv":
        "La décomposition de la figure des gains : pour chaque trajet, le gain total "
        "et ses quatre parts (relèvement du plafond, pendulaire, doublement, "
        "cohabitation), avec les lignes de contrôle. Les parts somment au gain par "
        "construction, et la vérification de la section 7 le refait devant vous.",
    "temps_scenario_1.csv":
        "Le temps de parcours calculé par intégration, sans marge, pour chaque tronçon "
        "et plafond de vitesse. La ligne pendulaire × 177 est le scénario 1 ; la "
        "colonne « horaire actuel » est le temps de VIA. Les temps publiés du rapport "
        "sont ces temps de base multipliés par 1,10 (la marge).",
    "temps_scenario_2.csv":
        "Même moteur, zones urbaines modernisées : les approches roulent ce que "
        "leur géométrie permet. Scénario 2.",
    "temps_scenario_3.csv":
        "Même moteur, zones urbaines modernisées ET courbes corrigées sur les "
        "sections à doubler. Scénario 3.",
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
    "temps_scenario_2.csv": "Temps, scénario 2 (zones urbaines modernisées)",
    "temps_scenario_3.csv": "Temps, scénario 3 (courbes corrigées au doublement)",
    "blocs_urbains_blocs_libres.csv": "Blocs urbains, scénarios 2 et 3",
    "blocs_urbains_rectifies_blocs_libres.csv": "Blocs urbains, scénario 3",
}

QUOI = {
    "segments_courbature.csv":
        "Le corridor découpé en segments de courbure homogène. Pour chacun, le rayon "
        "gouvernant, le degré de courbure et la vitesse que cette géométrie autorise "
        "dans chaque scénario. C'est la table de base : toutes les autres en dérivent.",
    "km_restants_sous_grande_vitesse.csv":
        "Combien de kilomètres restent sous une vitesse cible, par scénario et par "
        "tronçon. La table qui produit les chiffres de tête du rapport (cible 177).",
    "sites_restants_sous_grande_vitesse.csv":
        "Les mêmes kilomètres, site par site, avec le rayon actuel et le rayon visé.",
    "decomposition_gains.csv":
        "La décomposition de la figure des gains : pour chaque trajet, le gain total "
        "et ses quatre parts (relèvement du plafond, pendulaire, doublement, "
        "cohabitation), avec les lignes de contrôle. Les parts somment au gain par "
        "construction, et la vérification de la section 7 le refait devant vous.",
    "tbase_par_bande_rectifies.csv":
        "Sensibilité : les courbes des sections à doubler sont rectifiées au plafond "
        "retenu. À comparer ligne à ligne avec la table de référence.",
    "tbase_par_bande_blocs_libres.csv":
        "Sensibilité : les blocs urbains cessent d'être figés à l'horaire et roulent ce "
        "que leur géométrie permet. Une borne, pas une promesse.",
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
    "vitesse_cible_kmh": "Vitesse visée", "km_restants": "Restants",
    "mille_restants": "Restants (mi)",
    "vmax_pendulaire_kmh": "Plafond pendulaire", "bande_pendulaire": "Bande pendulaire",
    "vmax_base_kmh": "Plafond de base", "bande_base": "Bande de base",
    "flbg_present": "FLBG présent", "trajet": "Trajet", "poste": "Poste",
    "vmax_geometrie_base_kmh": "Plafond géométrique, base",
    "vmax_geometrie_pendulaire_kmh": "Plafond géométrique, pendulaire",
    "vmax_geometrie_reference_kmh": "Plafond géométrique, réf. interne",
    "bande_geometrie_base": "Bande géométrique, base",
    "bande_geometrie_pendulaire": "Bande géométrique, pendulaire",
    "bande_geometrie_reference": "Bande géométrique, réf. interne",
    "scenario_label": "Scénario (libellé)",
    "minutes": "Minutes", "part_pct_du_gain": "Part du gain",
    "n_sites": "Sites", "pct_troncon": "Part du tronçon",
    "rayon_cible_m": "Rayon visé", "degre_courbure_cible_max_deg": "Degré visé",
    "km_debut": "km début", "km_fin": "km fin", "km_début": "km début",
    "longueur_km": "Longueur", "marge_pct": "Marge",
    "t_horaire_med_min": "Horaire actuel", "t_base_cap160_min": "Temps géométrique",
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
    # « m_s2 » est l'unité m/s², pas le scénario S2 : cas spécial avant tout.
    if brut == "accel_laterale_m_s2":
        return "Accél. latérale", "m/s²", ""
    rampe = ""
    if re.search(r"vmax.*kmh|vitesse.*kmh", brut, re.I):
        rampe = "vitesse"
    elif re.fullmatch(r"classe_(S[123]|base|pendulaire|reference)", brut, re.I):
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
    SIGLES = r"CN|VIA|GTFS|IQR|MTX|TC|OSM|FLBG"
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
    esp = r"[\s ]*"          # espaces, insécables comprises (rapport.md en porte)

    def ligne(motif: str, n: int) -> list[float]:
        m = re.search(motif, txt)
        if not m:
            sys.exit(f"chiffre publié introuvable dans rapport.md : {motif[:60]}")
        return [float(m.group(i + 1).replace(" ", "").replace(" ", ""))
                for i in range(n)]

    a, b = ligne(
        r"Sous 201[^|]*\|" + esp + r"(\d[\d\s ]*?)" + esp
        + r"km" + esp + r"\|" + esp + r"(\d[\d\s ]*?)" + esp + r"km", 2)
    c, d = ligne(
        r"Sous 160[^|]*\|" + esp + r"(\d[\d\s ]*?)" + esp
        + r"km" + esp + r"\|" + esp + r"(\d[\d\s ]*?)" + esp + r"km", 2)
    g, = ligne(r"Voie double, CN \|[^|]*\|" + esp + r"(\d+)" + esp + r"%", 1)
    h, = ligne(r"Voie simple, VIA \|[^|]*\|" + esp + r"(\d+)" + esp + r"%", 1)
    i, = ligne(r"Voie simple, CN \|[^|]*\|" + esp + r"(\d+)" + esp + r"%", 1)
    j, = ligne(r"\|" + esp + r"154-177" + esp + r"km/h \(96-110" + esp
               + r"mi/h\)[^|]*\|" + esp + r"(\d+)", 1)
    j2, = ligne(r"\|" + esp + r"178-201" + esp + r"km/h \(111-125" + esp
                + r"mi/h\)[^|]*\|" + esp + r"(\d+)", 1)
    k, = ligne(r"\|" + esp + r"≤" + esp + r"153" + esp + r"km/h \(95" + esp
               + r"mi/h\)[^|]*\|" + esp + r"(\d+)", 1)
    return {
        "residu201": {"base": a, "pendulaire": b},
        "residu160": {"base": c, "pendulaire": d},
        "marges": {"double-CN": g, "simple-VIA": h, "simple-CN": i},
        "pn": {"154-177": j, "178-201": j2, "≤153": k},
    }


def lire_gains() -> dict[str, float]:
    """Gains totaux déclarés par trajet (decomposition_gains.csv), pour la
    vérification exécutable de la figure des gains."""
    gains: dict[str, float] = {}
    with (DELIVERABLES / "decomposition_gains.csv").open(encoding="utf-8-sig",
                                                         newline="") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r["poste"] == "controle_gain_total_G":
                gains[r["trajet"]] = float(r["minutes"])
    return gains


def sections(pub: dict) -> list[dict]:
    """Le fil : une entrée par section du rapport, dans le même ordre et avec
    les mêmes clés, pour que le lecteur passe de l'un à l'autre sans se perdre."""
    GAIN_POSTES = ["gain_releve_plafond", "gain_pendulaire",
                   "gain_zones_urbaines", "gain_courbes_au_doublement",
                   "gain_doublement", "gain_cohabitation"]
    return [
        {
            "cle": "01 · L'essentiel", "titre": "L'essentiel",
            "dit": "Cette étude chiffre un contrefactuel au projet Alto : que donnerait "
                   "la voie existante, modernisée au mieux? Trois scénarios, du plus "
                   "simple au plus complet. Dès le <b>scénario 1</b> (le train "
                   "pendulaire), le train bat l'auto sur les quatre trajets : "
                   "<b>4 h 40</b> entre Montréal et Toronto, contre 5 h 18 "
                   "aujourd'hui. Le <b>scénario 3</b> descend à 4 h 17.",
            "chiffres": [
                {"v": f"{pub['residu201']['pendulaire']:.0f} km", "l": "restants sous 201 km/h avec le train pendulaire",
                 "couleur": VITESSE_COULEURS["160_200"]},
                {"v": f"{pub['residu201']['base']:.0f} km", "l": "restants sous 201 km/h, voie et train actuels"},
                {"v": "1 433 km", "l": "de corridor mesuré, quatre trajets"},
            ],
            "verifications": [{
                "enonce": "Le rapport publie les kilomètres restants sous le plafond "
                          "retenu de 201 km/h. <b>Refaisons la somme</b> à partir des "
                          "sites mesurés.",
                "table": "km_restants_sous_grande_vitesse.csv",
                "filtre": [{"col": "vitesse_cible_kmh", "op": "==", "val": 201},
                           {"col": "scenario", "op": "dans", "val": ["base", "pendulaire"]},
                           {"col": "troncon", "op": "dans", "val": COEUR}],
                "grouper": "scenario", "agreger": "km_restants", "mode": "somme",
                "publie": pub["residu201"], "unite": "km", "arrondi": 1, "tolerance": 1,
                "libelles": {"base": "Scénario de base (voie et train actuels)",
                             "pendulaire": "Train pendulaire (scénarios 1 à 3, plafond 201)"},
            }],
            "pieces": ["km_restants_sous_grande_vitesse.csv", "temps_scenario_1.csv",
                       "decomposition_gains.csv"],
        },
        {
            "cle": "02 · Trois scénarios", "titre": "Trois scénarios, un seul train",
            "dit": "Le même train pendulaire, le même plafond de 201 km/h (125 mi/h), et trois "
                   "périmètres de travaux. <b>Scénario 1</b> : le train, la "
                   "signalisation, les passages à niveau, le dévers. <b>Scénario 2</b> : "
                   "plus les zones urbaines modernisées. <b>Scénario 3</b> : plus les "
                   "courbes corrigées au moment du doublement, là où la deuxième voie "
                   "se construit de toute façon.",
            "chiffres": [
                {"v": "4,82", "l": "coefficient k du pendulaire (v = k·√R)"},
                {"v": "125 mi/h", "l": "le plafond retenu (201 km/h) : marche du contrôle certifié, seuil des passages à niveau"},
                {"v": "213 km", "l": "de segments dont les courbes sont corrigées au scénario 3"},
            ],
            "pieces": ["scenarios_parametres.csv", "temps_scenario_1.csv",
                       "temps_scenario_2.csv", "temps_scenario_3.csv"],
        },
        {
            "cle": "03 · Les conditions", "titre": "Ce que les scénarios demandent",
            "dit": "Deux conditions. Les <b>passages à niveau</b> : sceller chaque "
                   "passage de la partie interurbaine rapide (barrières complètes, "
                   "terre-pleins, détection). La <b>signalisation</b> : un contrôle en "
                   "cabine certifié, prouvé à 201 km/h chez Brightline et au-delà chez "
                   "Amtrak ; la variante ITCS du Michigan (177 km/h) offre une "
                   "étape de phasage.",
            "chiffres": [
                {"v": f"{pub['pn']['154-177'] + pub['pn']['178-201']:.0f}", "l": "passages à sceller (zone 154-201 km/h)",
                 "couleur": VITESSE_COULEURS["160_200"]},
                {"v": "533", "l": "restent à équiper de feux, cloches et barrières"},
                {"v": "924", "l": "passages sur le corridor, dédoublonnés"},
            ],
            "verifications": [{
                "enonce": "<b>Comptons les passages</b> par bande d'exploitation au "
                          "plafond pendulaire (201 km/h, commun aux trois scénarios).",
                "table": "passages_niveau_tri.csv",
                "filtre": [], "grouper": "bande_pendulaire", "agreger": "tc_number",
                "mode": "compte", "publie": pub["pn"], "unite": "passages",
                "arrondi": 1, "tolerance": 0,
                "libelles": {"154-177": "À sceller (154-177 km/h)",
                             "178-201": "À sceller, dispositif approuvé (178-201 km/h)",
                             "≤153": "Régime actuel (≤ 153 km/h)"},
            }],
            "pieces": ["passages_niveau_tri.csv", "passages_niveau_par_bande.csv"],
        },
        {
            "cle": "04 · Capacité", "titre": "Doubler la voie, et vivre ensemble sur le rail",
            "dit": "Le corridor offre une expérience naturelle : des voies simples chez "
                   "VIA, des voies simples chez le CN, des voies doubles chez le CN. La "
                   "voie double achète d'abord la <b>fiabilité</b> (tous les départs "
                   "font le même temps), et elle est la condition d'une cohabitation où "
                   "passager et fret gagnent tous les deux. Le régime pèse plus que le "
                   "béton : la voie simple de VIA porte moins de marge que la voie "
                   "double du CN.",
            "chiffres": [
                {"v": f"{pub['marges']['simple-CN']:.0f} %", "l": "marge médiane, voie simple du CN",
                 "couleur": VITESSE_COULEURS["sous_100"]},
                {"v": f"{pub['marges']['double-CN']:.0f} %", "l": "marge médiane, voie double du CN"},
                {"v": f"{pub['marges']['simple-VIA']:.0f} %", "l": "marge médiane, voie simple de VIA"},
            ],
            "verifications": [{
                "enonce": "La voie simple coûte cher chez le CN et rien chez VIA. "
                          "<b>Reprenons les médianes</b> sur le cœur du corridor.",
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
            "cle": "05 · La mesure", "titre": "Comment nous avons mesuré",
            "dit": "Comme VIA Rail ne fournit pas une géométrie suffisamment détaillée "
                   "de sa voie, la géométrie du tracé vient des données ouvertes "
                   "OpenStreetMap, appariées aux horaires de VIA. Les chiffres publiés "
                   "incluent une <b>correction prudente des courbes courtes</b> : sur "
                   "tout segment courbe de moins de 900 m, le rayon est divisé par "
                   "deux, une règle calée sur un audit de terrain.",
            "chiffres": [
                {"v": "900 m", "l": "fenêtre d'ajustement, imposée par le bruit de la source"},
                {"v": "414", "l": "segments corrigés (187 km) sur le cœur du corridor"},
            ],
            "pieces": ["segments_courbature.csv", "biais_segments_courts.csv",
                       "blocs_urbains.csv"],
        },
        {
            "cle": "06 · Les temps", "titre": "Résultats détaillés",
            "dit": "Le temps publié est un <b>point</b> : le temps de base plus une "
                   "marge de 10 %, légèrement plus prudente que la médiane des "
                   "règles internationales et alignée sur le référent britannique. La "
                   "figure des gains attribue l'écart avec l'horaire actuel à ses "
                   "leviers : le train, les zones urbaines, les courbes, les voies, le "
                   "régime.",
            "chiffres": [
                {"v": "4 h 27", "l": "Montréal-Toronto, scénario 1"},
                {"v": "4 h 04", "l": "Montréal-Toronto, scénarios 2 et 3"},
                {"v": "1 h 56", "l": "Montréal-Québec, scénario 3"},
            ],
            "verifications": [{
                "enonce": "La figure des gains promet que les parts de sa décomposition "
                          "somment exactement au gain de chaque trajet. <b>Refaisons la somme</b>.",
                "table": "decomposition_gains.csv",
                "filtre": [{"col": "poste", "op": "dans", "val": GAIN_POSTES}],
                "grouper": "trajet", "agreger": "minutes", "mode": "somme",
                "publie": pub["gains"], "unite": "min", "arrondi": 1, "tolerance": 0.5,
                "libelles": {k: k for k in pub["gains"]},
            }],
            "pieces": ["temps_scenario_1.csv", "temps_scenario_2.csv",
                       "temps_scenario_3.csv", "decomposition_gains.csv",
                       "synthese_troncon.csv"],
        },
        {
            "cle": "07 · Ce qui reste à faire", "titre": "Limites, et l'étude qu'il faut commander",
            "dit": "Ce que cette étude laisse ouvert, une étude complète devra le "
                   "trancher : simulation de circulation, conception par site, coûts, "
                   "et la levée de la correction des courbes courtes avec une géométrie "
                   "fine. Menée avec le propriétaire de la voie, elle établira la "
                   "feuille de route concrète de l'alternative à Alto.",
            "pieces": ["goulots_detranglement.csv", "sites_restants_sous_grande_vitesse.csv"],
        },
        {
            "cle": "08 · Contrôles", "titre": "Les contre-épreuves",
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
        "vmax_pendulaire_kmh_plafond_courbure", "classe_pendulaire",
        "gare_amont", "gare_aval"],
    "passages_niveau_tri.csv": [
        "tc_number", "troncon_principal", "subdivision", "mille", "localisation",
        "acces", "protection", "flbg_present", "trains_jour", "vehicules_jour",
        "vmax_pendulaire_kmh", "bande_pendulaire", "intervention"],
    "marges_par_intergare.csv": [
        "troncon", "region", "de", "a", "longueur_km", "cellule",
        "t_horaire_med_min", "t_base_cap160_min", "marge_pct",
        "dispersion_iqr_pct", "exclue_du_2x2"],
    "marges_par_intergare_GTFS2023.csv": [
        "troncon", "region", "de", "a", "longueur_km", "cellule",
        "t_horaire_med_min", "t_base_cap160_min", "marge_pct",
        "dispersion_iqr_pct", "exclue_du_2x2"],
    "sites_restants_sous_grande_vitesse.csv": None,   # renseignée à la lecture si besoin
}

# Les préréglages sont des QUESTIONS, et le train pendulaire passe en premier :
# la version précédente n'offrait que S3, le plus ambitieux, comme si c'était la
# lecture par défaut.
PRESETS = {
    "segments_courbature.csv": [
        {"label": "Sous 201 km/h, train pendulaire", "conds": [{"col": "vmax_pendulaire_kmh_plafond_courbure", "op": "<", "val": 201}]},
        {"label": "Sous 160 km/h, train pendulaire", "conds": [{"col": "vmax_pendulaire_kmh_plafond_courbure", "op": "<", "val": 160}]},
    ],
    "km_restants_sous_grande_vitesse.csv": [
        {"label": "Cible 201 km/h", "conds": [{"col": "vitesse_cible_kmh", "op": "==", "val": 201}]},
        {"label": "Train pendulaire (scénarios 1 à 3)", "conds": [{"col": "scenario", "op": "==", "val": "pendulaire"}]},
    ],
    "passages_niveau_tri.csv": [
        {"label": "À équiper (sans feux-cloches-barrières)", "conds": [{"col": "flbg_present", "op": "==", "val": "False"}]},
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
    pub["gains"] = lire_gains()
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

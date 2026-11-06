"""Étape 42 — Annexe « fiche technique » : les paramètres du modèle, en tableaux.

Pourquoi un script et pas du texte à la main : un tableau de paramètres recopié
finit par diverger du code. Ici, les valeurs sont lues là où elles vivent (classe
Rame, scenarios.py, constantes des étapes, CSV de résultats) et écrites dans
rapport.md entre les repères <!-- fiche:debut --> et <!-- fiche:fin -->.

Quatre garde-fous arrêtent le script :
  - un fichier de scripts/ absent du tableau des scripts ;
  - un montant de la table des coûts absent du texte de la section 11 (les coûts
    vivent dans ce texte, pas dans le code) ;
  - une accélération publiée à l'étape 5 de la ligne du temps qui ne correspond plus ;
  - une marge, un gain à arrêts égaux ou une sensibilité du mou urbain, écrits à la main dans
    le corps du rapport, qui ne correspondent plus au calcul.

À lancer après 41 et avant 29. Ne jamais écrire de sigle interne (S1, S2, S3) ici.
"""
from __future__ import annotations

import ast
import importlib.util
import math
import re
import sys
from pathlib import Path

import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
from scenarios import (FACTEUR_CORRECTION_R, FENETRE_BIAIS_M, MARGE_NORMALE,     # noqa: E402
                       PLAFOND_PUBLIE, SCENARIOS, marge_de)
from utils import DELIVERABLES, EFFECTIVE_GAUGE_MM, G_ACCEL, PROJECT_ROOT        # noqa: E402

_spec = importlib.util.spec_from_file_location("m40", ICI / "40_etapes_temps.py")
m40 = importlib.util.module_from_spec(_spec)
sys.modules["m40"] = m40
_spec.loader.exec_module(m40)
m21 = m40.m21

RAPPORT = PROJECT_ROOT / "rapport.md"
DEBUT, FIN = "<!-- fiche:debut -->", "<!-- fiche:fin -->"
TRAJETS = ["Montréal-Québec", "Montréal-Ottawa", "Ottawa-Toronto", "Montréal-Toronto"]


# ------------------------------------------------------------------ outils
def constante(fichier: str, nom: str):
    """Valeur d'une constante de module, lue sans exécuter le script (certains
    scripts lancent des calculs longs à l'import)."""
    arbre = ast.parse((ICI / fichier).read_text(encoding="utf-8"))
    for noeud in arbre.body:
        if isinstance(noeud, (ast.Assign, ast.AnnAssign)):
            cibles = noeud.targets if isinstance(noeud, ast.Assign) else [noeud.target]
            if any(isinstance(c, ast.Name) and c.id == nom for c in cibles):
                return ast.literal_eval(noeud.value)
    sys.exit(f"constante introuvable : {fichier} {nom}")


def fr(x: float, d: int = 0, signe: bool = False) -> str:
    """Nombre à la française : virgule, espace des milliers, vrai signe moins."""
    s = f"{abs(x):,.{d}f}".replace(",", " ").replace(".", ",")
    if x < 0 and float(s.replace(" ", "").replace(",", ".")) != 0:
        return "−" + s
    return ("+" + s) if signe and float(s.replace(" ", "").replace(",", ".")) != 0 else s


def table(entetes: list[str], lignes: list[list[str]], largeurs: list[int] | None = None) -> str:
    """Table pipe de pandoc. Les largeurs (en tirets) ne jouent que si une ligne déborde."""
    tirets = largeurs or [3] * len(entetes)
    sortie = ["| " + " | ".join(entetes) + " |", "|" + "|".join("-" * t for t in tirets) + "|"]
    sortie += ["| " + " | ".join(ligne) + " |" for ligne in lignes]
    return "\n".join(sortie)


def csv(nom: str) -> pd.DataFrame:
    return pd.read_csv(DELIVERABLES / nom, sep=";", encoding="utf-8-sig")


# ---------------------------------------------------------------- calculs
def depart_arrete(rame, cible_kmh: float) -> tuple[float, float]:
    """(secondes, mètres) de l'arrêt à la vitesse cible, en palier, train chargé."""
    v, t, d = 0.5, 0.0, 0.0
    while v < cible_kmh / 3.6 and t < 3000:
        a = rame.acceleration(v)
        if a <= 0:
            return math.inf, math.inf
        v += a * 0.1
        d += v * 0.1
        t += 0.1
    return t, d


def rayon(k: float, v_kmh: float) -> float:
    return (v_kmh / k) ** 2


def degre(r_m: float) -> float:
    return math.degrees(2 * math.asin(15.24 / r_m))


def coeff(devers_mm: float, insuffisance_mm: float) -> float:
    return 3.6 * math.sqrt(G_ACCEL * (devers_mm + insuffisance_mm) / EFFECTIVE_GAUGE_MM)


# ----------------------------------------------------------------- sections
def formules() -> str:
    g = fr(EFFECTIVE_GAUGE_MM)
    return "## Les formules\n\n" + table(
        ["Grandeur", "Formule", "Unités et notes"],
        [["Vitesse en courbe", "`v = k·√R`", "v en km/h, R en m"],
         ["Coefficient de courbe", "`k = 3,6·√(g·(h + I) / G)`",
          f"h : dévers ; I : insuffisance de dévers ; G = {g} mm, écartement effectif ; g = 9,81 m/s²"],
         ["Degré de courbure", "`D = 2·asin(15,24 / R)`", "corde de 100 pi ; R en m"],
         ["Puissance au rail", "`Pr = (P − Pb)·r`", "P : puissance nominale ; Pb : services de bord ; r : rendement"],
         ["Résistance à l'avancement", "`F = (A + B·V)·m + 0,0463·S·V²`",
          "N ; V en km/h ; m en t ; S : surface de traînée (m²) ; 0,0463 suppose un air à 1,2 kg/m³"],
         ["Accélération", "`a = min(a0, (Pr/v − F − m·g·i) / (c·m))`",
          "v en m/s ; i : pente ; c : coefficient d'inertie ; une accélération négative ralentit le train"],
         ["Freinage", "`a = −ab`", "constant, de service"],
         ["Temps de roulement", "`T = Σ dx / v(x)`",
          f"pas de {fr(m21.DX_M)} m ; une passe d'accélération, puis une passe de freinage"],
         ["Temps publié", "`(T + n·d) × marge`", "n : arrêts ; d : immobilisation par arrêt ; marge : 1,10, ou la marge actuelle si elle est plus basse"],
         ["Marge mesurée", "`(H − B) / B`",
          "H : médiane des horaires ; B : temps du train actuel, courbes et régime actuels, sans accélération"]],
        [18, 30, 52])


def trains() -> str:
    rames = [("Train actuel", m21.RAME_ACTUELLE), ("Référence", m21.RAME_PENDULAIRE),
             ("1 Charger + 5", m40.UN_CHARGER), ("2 Charger + 5", m40.DEUX_CHARGER),
             ("Électrique", m40.PENDOLINO)]
    lignes = [
        ("Puissance nominale (kW)", lambda r: fr(r.p_kw)),
        ("Masse à vide (t)", lambda r: fr(r.m_t)),
        ("Puissance nominale par masse (W/kg)", lambda r: fr(r.p_kw / r.m_t, 1)),
        ("Services de bord (kW)", lambda r: fr(r.hotel_kw)),
        ("Rendement de transmission", lambda r: fr(r.rendement, 2)),
        ("Puissance au rail (kW)", lambda r: fr(r.p_rail_w / 1e3)),
        ("Passagers et bagages (% de la masse)", lambda r: fr((r.charge - 1) * 100)),
        ("Masse en service (t)", lambda r: fr(r.m_kg / 1e3)),
        ("Coefficient d'inertie", lambda r: fr(r.inertie, 2)),
        ("Résistance A (N/t)", lambda r: fr(r.a_n_t)),
        ("Résistance B (N/t par km/h)", lambda r: fr(r.b_n_t, 2)),
        ("Surface de traînée (m²)", lambda r: fr(r.cda_m2)),
        ("Longueur (m)", lambda r: fr(r.longueur_m)),
        ("Accélération maximale (m/s²)", lambda r: fr(r.a0, 1)),
        ("Freinage de service (m/s²)", lambda r: fr(r.ab, 1)),
        ("Vitesse d'équilibre en palier (km/h)", lambda r: fr(r.vitesse_equilibre_kmh())),
    ]
    t1 = table(["Paramètre"] + [n for n, _ in rames],
               [[lib] + [f(r) for _, r in rames] for lib, f in lignes], [34, 13, 13, 13, 13, 14])

    d = m40.DOUBLE_221
    note = (f"::: {{.note-tableau}}\n"
            "Train actuel : Charger et 5 voitures Venture. Référence : la rame pendulaire de la section 2. "
            f"Les colonnes Charger sont des tests de la section 12 : une ou deux locomotives de "
            f"{fr(m40.MASSE_CHARGER_T)} t et 5 voitures pendulaires de {fr(m40.MASSE_VOITURE_T, 1)} t, soit une voiture "
            "Venture et environ 10 t de pendulation. Électrique : type Pendolino, contre-hypothèse 3 ; "
            f"sa puissance de traction est déjà nette des services de bord. Le calage de la section 2 utilise deux Class 221 couplées : {fr(d.p_kw)} kW, "
            f"{fr(d.m_t)} t, {fr(d.cda_m2)} m² de traînée, sans passagers.\n:::")

    vitesses = [0, 50, 100, 130, 160, PLAFOND_PUBLIE, 201]
    ref, act, ele = m21.RAME_PENDULAIRE, m21.RAME_ACTUELLE, m40.PENDOLINO
    acc = lambda r, v, i=0.0: r.acceleration(max(v, 1.0) / 3.6, i)   # noqa: E731
    t2 = table(["Vitesse (km/h)", "Train actuel", "Référence", "Référence, rampe de 1 %", "Électrique"],
               [[fr(v)] + [fr(acc(r, v), 2) for r in (act, ref)] + [fr(acc(ref, v, 0.01), 2), fr(acc(ele, v), 2)]
                for v in vitesses])

    # La ligne du temps publie ces valeurs à l'étape 5 : elles doivent rester vraies.
    texte = RAPPORT.read_text(encoding="utf-8")
    for v in (100, 160, PLAFOND_PUBLIE):
        attendu = f"{fr(acc(ref, v), 2)}"
        if attendu not in texte.split(DEBUT)[0]:
            sys.exit(f"accélération à {v} km/h ({attendu}) absente de la ligne du temps")

    rangees = []
    for v in (100, 153, PLAFOND_PUBLIE):
        ta, da = depart_arrete(act, v)
        tr, dr = depart_arrete(ref, v)
        rangees.append([f"De 0 à {v} km/h", fr(ta), fr(da), fr(tr), fr(dr)])
    v = PLAFOND_PUBLIE / 3.6
    rangees.append([f"Freinage de {PLAFOND_PUBLIE} km/h à l'arrêt", fr(v / act.ab), fr(v * v / (2 * act.ab)),
                    fr(v / ref.ab), fr(v * v / (2 * ref.ab))])
    t3 = table(["Manœuvre, en palier", "Train actuel · secondes", "Train actuel · mètres",
                "Référence · secondes", "Référence · mètres"], rangees)

    return ("## Les trains\n\n" + t1 + "\n\n" + note + "\n\n**Accélération selon la vitesse (m/s², train chargé).** "
            "Elle sort de la formule d'accélération. Une valeur négative veut dire que le train ne tient plus "
            "cette vitesse.\n\n" + t2 + "\n\n**Temps et distance de manœuvre.**\n\n" + t3)


def courbes() -> str:
    act, pend = SCENARIOS["S1"], SCENARIOS["S2"]
    jeux = [("Train actuel", act.cant_mm, act.cant_def_mm), ("Référence", pend.cant_mm, pend.cant_def_mm),
            ("Test : tolérance de 5 po", pend.cant_mm, 127), ("Test : tolérance de 7 po", pend.cant_mm, 178)]
    rangees = []
    for nom, h, i in jeux:
        k = coeff(h, i)
        rangees.append([nom, fr(h), fr(h / 25.4, 1), fr(i), fr(i / 25.4, 1),
                        fr(G_ACCEL * (h + i) / EFFECTIVE_GAUGE_MM, 2), fr(k, 2),
                        fr(rayon(k, 100)), fr(rayon(k, 153)), fr(rayon(k, PLAFOND_PUBLIE))])
    t1 = table(["Jeu", "Dévers · mm", "Dévers · po", "Insuffisance · mm", "Insuffisance · po",
                "Latérale (m/s²)", "k", "Rayon minimal (m) · 100 km/h",
                "Rayon minimal (m) · 153 km/h", f"Rayon minimal (m) · {PLAFOND_PUBLIE} km/h"], rangees)

    k0, k1 = coeff(act.cant_mm, act.cant_def_mm), coeff(pend.cant_mm, pend.cant_def_mm)
    t2 = table(["Rayon (m)", "Degré de courbure (°)", "Train actuel (km/h)", "Référence (km/h)"],
               [[fr(r), fr(degre(r), 2), fr(k0 * math.sqrt(r)), fr(k1 * math.sqrt(r))]
                for r in (300, 400, 600, 900, 1200, 1800, 2400)])
    return ("## Les courbes\n\n" + t1 + "\n\n::: {.note-tableau}\n"
            "Le dévers du train actuel est une hypothèse : le dévers réel du réseau n'est pas publié. "
            "Le dévers de la référence, 5 po, est le maximum standard du CN. Son insuffisance de 6 po est "
            "celle que le CN accorde au LRC.\n:::\n\n" + t2)


def mesure() -> str:
    c04, c05, c13, c20 = ("04_compute_curvature.py", "05_segment_and_classify.py", "13_track_count.py",
                          "20_passages_niveau.py")
    m13 = re.search(r'SISTER_M", ([\d.]+)', (ICI / c13).read_text(encoding="utf-8"))
    a13 = re.search(r'ALIGN_DEG", ([\d.]+)', (ICI / c13).read_text(encoding="utf-8"))
    sens = constante(c20, "SENS_M")
    rangees = [
        ["Rééchantillonnage du tracé", f"{fr(constante(c04, 'RESAMPLE_STEP_M'))} m", "Un point de mesure à chaque pas"],
        ["Lissage de position", f"{fr(constante(c04, 'SMOOTH_WINDOW_M'))} m", "Retire le bruit de la carte"],
        ["Fenêtre du cercle ajusté", f"{fr(constante(c04, 'FIT_WINDOW_M'))} m",
         f"Plancher de {fr(constante(c04, 'FIT_WINDOW_MIN_M'))} m sur un tronçon court"],
        ["Filtre médian", f"{fr(constante(c04, 'R_MEDIAN_WINDOW_M'))} m", "Appliqué au rayon, après l'ajustement"],
        ["Rayon minimal plausible", f"{fr(constante(c04, 'R_MIN_PHYSICAL'))} m", "Plancher physique"],
        ["Rayon maximal", f"{fr(constante(c04, 'R_MAX_DISPLAY'))} m", "Au-delà, la voie est droite"],
        ["Longueur minimale d'un segment", f"{fr(constante(c05, 'MIN_SEGMENT_LEN_M'))} m", "Fusion des segments plus courts"],
        ["Rayon retenu par segment", "10e centile", "Prudent : proche du point le plus serré du segment"],
        ["Correction des courbes courtes", f"R × {fr(FACTEUR_CORRECTION_R, 1)}",
         f"Segment courbe de moins de {fr(FENETRE_BIAIS_M)} m ; vitesse × {fr(math.sqrt(FACTEUR_CORRECTION_R), 2)}"],
        ["Pas du relief", f"{fr(constante('39_relief_corridor.py', 'PAS_KM') * 1000)} m", "Modèle Copernicus GLO-90"],
        ["Lissage du relief", "3 km", "Médiane sur 5 points, puis moyenne sur 7 points"],
        ["Écart maximal entre deux voies", f"{fr(float(m13.group(1)))} m",
         f"Tracés alignés à moins de {fr(float(a13.group(1)))}° ; espacement mesuré d'environ 4 m"],
        ["Rattachement d'un passage au tracé", f"{fr(constante(c20, 'BUFFER_M'))} m",
         f"Sensibilité à {fr(sens[0])} m et {fr(sens[1])} m"],
    ]
    return "## La mesure de la voie\n\n" + table(["Paramètre", "Valeur", "Rôle"], rangees, [36, 16, 48])


def exploitation() -> str:
    bandes = [b for b in m21.BANDES_KMH if b <= 241]
    rangees = [
        ["Plafond publié", f"{PLAFOND_PUBLIE} km/h", "110 mi/h, tant que des passages à niveau demeurent"],
        ["Classe de voie actuelle", f"{constante('32_figure_gains.py', 'P_CLASSE')} km/h", "95 mi/h"],
        ["Régime actuel, calcul des marges", f"{fr(constante('22_marges_2x2.py', 'CAP_KMH'))} km/h",
         "Borne du temps de base à la section 3"],
        ["Autres plafonds calculés", " · ".join(str(b) for b in bandes if b not in (PLAFOND_PUBLIE,)) + " km/h",
         "Contre-hypothèses et sensibilités"],
        ["Immobilisation en gare", f"{fr(m21.DWELL_MIN)} min", "Médiane des horaires de VIA"],
        ["Marge d'exploitation", f"{fr((MARGE_NORMALE - 1) * 100)} %", "Sur le temps de roulement et les arrêts"],
        ["Marge de Montréal-Ottawa", f"{fr((marge_de('MTL-Ott') - 1) * 100, 1)} %",
         "Sa marge actuelle à arrêts égaux, plus basse que 10 %"],
        ["Arrêt à Montréal, Québec-Toronto", f"{fr(constante('32_figure_gains.py', 'ARRET_MTL_MIN'))} min",
         "Hypothèse du trajet de bout en bout"],
        ["Fenêtre urbaine d'Ottawa", f"±{fr(m21.OTTAWA_WINDOW_KM)} km", "Hypothèse : aucune gare d'approche proche"],
        ["Délimitation des zones urbaines", f"±{fr(m21.URBAN_SENS * 100)} %", "Sensibilité de la section 12"],
    ]
    return "## L'exploitation\n\n" + table(["Paramètre", "Valeur", "Note"], rangees, [36, 24, 40])


def etapes() -> str:
    e = csv("etapes_temps.csv").set_index("trajet")
    rangees = [[t, fr(e.loc[t, "distance_km"], 1), fr(e.loc[t, "n_arrets"]),
                fr(e.loc[t, "vitesse_des_courbes_min"], 1), fr(e.loc[t, "plafond_min"], 1),
                fr(e.loc[t, "immobilisation_en_gare_min"], 1), fr(e.loc[t, "vrai_train_min"], 1),
                fr(e.loc[t, "avec_marge_min"], 1)] for t in TRAJETS]
    t1 = table(["Trajet", "Distance (km)", "Arrêts", "Vitesse des courbes", "Avec plafond", "Avec arrêts",
                "Vrai train", "Avec marge"], rangees)
    return ("## Le temps, étape par étape\n\nMinutes cumulées, selon les étapes de la section 2.\n\n" + t1)


def arrets() -> str:
    a = csv("marges_arrets_egaux.csv").set_index("trajet")
    rangees = [[t, fr(a.loc[t, "trains"]), fr(a.loc[t, "combinaisons_arrets"]), fr(a.loc[t, "arrets_notre_train"]),
                fr(a.loc[t, "arrets_train_median"], 1), fr(a.loc[t, "marge_arrets_egaux_pct"], 1),
                fr(a.loc[t, "marge_retenue_pct"], 1), fr(a.loc[t, "minutes_par_arret_horaire"], 1),
                fr(a.loc[t, "minutes_par_arret_modele"], 1)] for t in TRAJETS]
    t1 = table(["Trajet", "Trains", "Combinaisons d'arrêts", "Arrêts · notre train", "Arrêts · train médian",
                "Marge (%) · réelle", "Marge (%) · retenue", "Minutes par arrêt · horaire",
                "Minutes par arrêt · modèle"], rangees)
    return ("## Les arrêts et la marge réelle\n\nChaque train de l'horaire contre le train actuel simulé avec ses "
            "propres arrêts, au régime actuel de 160 km/h. La marge retenue est de 10 %, ou la marge réelle si elle "
            "est plus basse.\n\n" + t1)


def zones() -> str:
    # keep="last" : les lignes de Montréal-Toronto, à 10 %, comme la note et la section 12.
    g = csv("gains_urbains.csv").drop_duplicates("bloc", keep="last")
    rangees = [[r.bloc.replace(" ↔ ", " à "), fr(r.longueur_km, 1), fr(r.minutes_gtfs, 1),
                fr(r.profil_actuel_153_min, 1), fr(r.gain_cohabitation_min, 1),
                fr(r.profil_pendulaire_plafond_min, 1)] for r in g.itertuples()]
    t1 = table(["Zone", "Longueur (km)", "Horaire actuel (min)", "Train actuel (min)", "Mou urbain (min)",
                "Référence (min)"], rangees)
    return ("## Les zones urbaines\n\n" + t1 + "\n\n::: {.note-tableau}\n"
            "Le mou urbain est l'écart entre l'horaire et le temps du train actuel, marge de 10 % comprise "
            "(section 12). Les temps des trains sont sans marge. Ils ne simulent ni les aiguillages ni les autres trains.\n:::")


def marges() -> str:
    m = csv("marges_2x2_synthese.csv")
    m = m[m.region == "coeur"].set_index("cellule")
    noms = {"double-CN": "Voie double, CN", "simple-VIA": "Voie simple, VIA", "simple-CN": "Voie simple, CN"}
    rangees = [[lib, fr(m.loc[c, "n"]), fr(m.loc[c, "mediane"], 1), fr(m.loc[c, "q25"], 1), fr(m.loc[c, "q75"], 1),
                fr(m.loc[c, "minimum"], 1), fr(m.loc[c, "maximum"], 1)] for c, lib in noms.items()]
    t1 = table(["Famille de voie", "Paires de gares", "Médiane (%)", "1er quartile", "3e quartile", "Minimum", "Maximum"],
               rangees)
    return ("## Les marges mesurées\n\nMarge par paire de gares adjacentes, sur le cœur du corridor.\n\n" + t1 +
            "\n\n::: {.note-tableau}\nUne paire entre dans une famille si au moins "
            f"{fr(constante('22_marges_2x2.py', 'DOMINANCE') * 100)} % de sa longueur a le même état de voie. "
            "La famille voie simple du CN ne compte que deux paires : sa médiane est indicative.\n:::")


def passages() -> str:
    v = csv("passages_vitesse_reelle.csv")
    n177 = int(v.depasserait_177.sum())
    n153 = int(v.depasse_153_au_plafond.sum())
    t = csv("passages_niveau_tri.csv")
    publics, prives = int((t.acces == "Public").sum()), int((t.acces == "Private").sum())
    a_sceller = t[t.bande_pendulaire != "≤153"]
    sans_barrieres = int((~a_sceller.flbg_present).sum())
    au_dela = int((t.bande_pendulaire == "178-201").sum())
    prive_177 = int((v[v.depasserait_177].acces == "Private").sum())
    rangees = [[f"Passages du corridor ({publics} publics, {prives} privés ou de ferme)", fr(len(t))],
               ["Passages où les courbes permettent plus de 153 km/h, à sceller", fr(len(a_sceller))],
               ["Parmi eux, sans barrières complètes", fr(sans_barrieres)],
               ["Passages où le train dépasse réellement 153 km/h", fr(n153)],
               [f"Passages où les courbes permettent plus de {PLAFOND_PUBLIE} km/h", fr(au_dela)],
               [f"Passages où le train dépasse réellement {PLAFOND_PUBLIE} km/h "
                f"({n177 - prive_177} publics, {prive_177} privés)", fr(n177)]]
    return "## Les passages à niveau\n\n" + table(["Catégorie", "Nombre"], rangees, [80, 20])


def couts() -> str:
    """Ces montants vivent dans la section 11. La table les reprend et refait chaque produit."""
    c = [("Deuxième voie", 407, "km", 2.4, "M\\$/km", "Hatch Mott MacDonald 2013, +42 %"),
         ("Renouvellement du rail", 1101, "km", 1.4, "M\\$/km", "Hatch Mott MacDonald 2013, +42 %"),
         ("Ponts de moins de 20 m", 377, "m", 0.387, "M\\$/m", "Hatch Mott MacDonald 2013, +42 %"),
         ("Ponts de 20 m et plus", 3760, "m", 0.535, "M\\$/m", "Hatch Mott MacDonald 2013, +42 %"),
         ("Signalisation", 1101, "km", 0.45, "M\\$/km", "Downeaster 2024, indice et change"),
         ("Passages sans barrières complètes", 533, "passages", 1.2, "M\\$", "Transports Canada 2021, Ulster 2023"),
         ("Passages déjà équipés", 300, "passages", 0.5, "M\\$", "Ulster 2023, source modeste"),
         ("Ponts d'étagement, programme", 118, "ouvrages", 50, "M\\$", "Valeur moyenne de planification"),
         ("Passages dénivelés, programme", 190, "ouvrages", 12, "M\\$", "Hypothèse de travail, sans précédent")]
    rangees = []
    for poste, q, u, cu, unite, base in c:
        d = 3 if cu < 1 and unite == "M\\$/m" else (2 if cu < 1 else 1) if cu < 10 else 0
        rangees.append([poste, f"{fr(q)} {u}", f"{fr(cu, d)} {unite}", fr(q * cu / 1000, 2), base])
    rangees.insert(5, ["Trains pendulaires diesel", "Forfait", "Borne haute", "3,40", "Avelia Liberty 2016, +23 %, change"])
    rangees.append(["Électrification, programme", "2 200 km", "Fourchette", "3 à 7", "EcoTrain 2009 et RIA 2019 (section 10)"])

    # Garde-fou : la table ne doit pas contredire le texte de la section 11.
    texte = RAPPORT.read_text(encoding="utf-8")
    s11 = texte[texte.index("# Estimation des coûts"):texte.index("# Impacts des actions")]
    for morceau in ("1 101 km", "407 km", "2,4 M\\$", "1,4 M\\$", "387 000 \\$", "535 000 \\$", "0,45 M\\$", "1,2 M\\$",
                    "500 000 \\$", "50 M\\$", "12 M\\$", "118 ponts", "190 passages", "533 passages", "377 m", "3 760 m"):
        if morceau not in s11:
            sys.exit(f"coût absent de la section 11 : {morceau}")

    t1 = table(["Poste", "Quantité", "Coût unitaire", "Total (G\\$)", "Base"], rangees, [30, 14, 16, 10, 30])
    return ("## Les coûts unitaires\n\nDollars canadiens de 2025, avant imprévus de 20 %. La section 11 donne les "
            "sources et le détail de l'indexation.\n\n" + t1)


def sensibilites() -> str:
    s = csv("sensibilites_traction.csv")
    rangees = [[r["cas"]] + [fr(r[f"{t}_ecart_min"], 1, signe=True) for t in TRAJETS] for _, r in s.iterrows()]
    t1 = table(["Cas testé", "Mtl-Qc", "Mtl-Ott", "Ott-To", "Mtl-To"], rangees, [60, 10, 10, 10, 10])
    return ("## Les sensibilités\n\nÉcart en minutes avec le temps publié, marge comprise. Chaque ligne change "
            "une seule chose, sauf les deux cas combinés.\n\n::: {.coupable}\n\n" + t1 + "\n\n:::")


def donnees() -> str:
    rangees = [
        ["Horaires de VIA (GTFS)", "Flux du 18 mars au 18 juillet 2026", "Gares, tracés, temps actuels, immobilisations"],
        ["Horaires archivés de VIA (GTFS)", "Flux du 19 janvier 2023", "Test de robustesse des marges"],
        ["OpenStreetMap, extraits Geofabrik", "Extraits du 10 mai 2026", "Géométrie de la voie, nombre de voies"],
        ["Inventaire des passages à niveau", "Transports Canada, mise à jour 2023", "Localisation, accès, protection"],
        ["Relief Copernicus GLO-90, via Open-Meteo", "Téléchargé le 5 novembre 2026", "Pentes du modèle de traction"],
        ["Horaires d'exo (GTFS)", "Version du 10 septembre 2026", "Comparaison de Saint-Hilaire, section 12"],
        ["Circulaire MR 1305-0 du CN", "Décembre 2002", "Calcul des vitesses en courbe, dévers maximal, insuffisance"],
    ]
    return "## Les données\n\n" + table(["Donnée", "Version", "Usage"], rangees, [36, 30, 34])


SCRIPTS = {
    "Mesure de la voie": [
        ("01_extract_corridor.py", "Tire des horaires de VIA les quatre trajets du corridor et l'ordre de leurs gares."),
        ("02_build_rail_graph.py", "Bâtit le graphe ferroviaire à partir des extraits OpenStreetMap du Québec et de l'Ontario."),
        ("03_match_gtfs_to_osm.py", "Accroche le tracé de VIA à la voie réelle, sans sauter d'une voie parallèle à l'autre."),
        ("04_compute_curvature.py", "Calcule le rayon de courbure par ajustement d'un cercle le long du tracé."),
        ("_baseline_zones.py", "Garde-fou : vérifie la courbure mesurée sur trois zones témoins."),
        ("05_segment_and_classify.py", "Découpe le tracé en segments et calcule la vitesse permise par chaque jeu de dévers."),
        ("34_correction_courtes.py", "Applique la correction des courbes courtes et écrit les segments publiés."),
        ("31_biais_segments_courts.py", "Mesure le biais de la fenêtre de 900 m sur les segments courts."),
        ("06_synthese_troncon.py", "Résume les classes de vitesse par tronçon et repère les goulots."),
        ("07_render_outputs.py", "Produit la carte, le KMZ et le CSV des segments."),
        ("11_target_speed_to_km.py", "Donne les kilomètres restants sous chaque vitesse cible."),
        ("12_sections_a_rectifier_pdf.py", "Liste les sections sous 201 km/h. Hors rapport."),
        ("13_track_count.py", "Compte les voies en détectant les tracés parallèles dans OpenStreetMap."),
        ("14_synthese_voies.py", "Agrège voie simple et voie double sans double compte, et sort les kilomètres à doubler."),
        ("15_carte_voies.py", "Dessine la carte des voies."),
        ("20_passages_niveau.py", "Rattache l'inventaire de Transports Canada au tracé et classe chaque passage."),
        ("39_relief_corridor.py", "Télécharge le relief le long des quatre trajets."),
    ],
    "Temps de parcours": [
        ("scenarios.py", "Source unique des jeux de dévers, du coefficient k et du plafond publié."),
        ("utils.py", "Constantes, conversions d'unités et chemins partagés."),
        ("alignments.py", "Schéma commun des tracés."),
        ("33_courbes_doublees.py", "Sensibilité : courbes rectifiées aux sections doublées. Hors rapport."),
        ("21_tbase_bande.py", "Moteur : formule de traction, profil de vitesse et temps par trajet et par plafond."),
        ("43_marges_arrets_egaux.py", "Compare chaque train de l'horaire à un train qui fait les mêmes arrêts : marge réelle et gain."),
        ("22_marges_2x2.py", "Mesure la marge de chaque paire de gares selon le nombre de voies et le propriétaire."),
        ("38_train_express.py", "Calcule le train express, sans arrêt intermédiaire."),
        ("36_gains_urbains.py", "Décompose les zones urbaines : courbes, signalisation et mou urbain."),
        ("37_sous_sections_mtlqc.py", "Détaille Montréal-Québec, gare par gare."),
        ("40_etapes_temps.py", "Refait le modèle pas à pas, le calage et les sensibilités. Échoue si les temps publiés changent."),
        ("41_passages_gain_vitesse.py", "Calcule la vitesse réelle à chaque passage et les minutes rachetées par le programme."),
        ("26_test_accel_exploratoire.py", "Trace historique d'un test de l'accélération. Hors rapport."),
    ],
    "Figures, rapport et contrôles": [
        ("23_figure_cellules.py", "Figure des familles de voie."),
        ("24_figure_vs_auto.py", "Figures du train contre l'auto, une par trajet."),
        ("32_figure_gains.py", "Figure des facteurs de réduction et décomposition des gains."),
        ("35_figure_zoom_urbain.py", "Gros plans des zones urbaines. Hors rapport."),
        ("28_couverture.py", "Couverture du rapport, dessinée à partir du tracé mesuré."),
        ("42_fiche_technique.py", "Écrit cette annexe à partir du code et des résultats."),
        ("identite.py", "Lit la charte graphique."),
        ("27_verif_identite.py", "Garde-fou : contrôle la palette, le daltonisme et le contraste."),
        ("29_rapport_html.py", "Compose le rapport en HTML à partir du texte source."),
        ("30_rapport_pdf.mjs", "Produit le PDF paginé, avec ses liens et son sommaire."),
        ("25_build_rapport.py", "Produit la version Word."),
        ("18_export_xlsx.py", "Exporte les CSV en classeurs Excel filtrables."),
        ("19_build_viewer.py", "Compose le visualiseur de données et vérifie ses chiffres contre le rapport."),
    ],
}


def scripts() -> str:
    presents = {p.name for p in ICI.iterdir() if p.suffix in {".py", ".mjs"}}
    listes = {n for groupe in SCRIPTS.values() for n, _ in groupe}
    if presents - listes or listes - presents:
        sys.exit(f"tableau des scripts à revoir : absents {sorted(presents - listes)}, en trop {sorted(listes - presents)}")
    blocs = [f"**{g}.**\n\n::: {{.coupable}}\n\n" +
             table(["Script", "Ce qu'il fait"], [[f"`{n}`", t] for n, t in l], [34, 66]) + "\n\n:::"
             for g, l in SCRIPTS.items()]
    return ("## Les scripts\n\nLes temps, les vitesses et les comptes publiés viennent de ces scripts. Ils sont listés dans leur ordre d'exécution. "
            "Le numéro du fichier indique seulement l'ordre de sa création.\n\n" + "\n\n".join(blocs) +
            "\n\n::: {.note-tableau}\nEnvironnement : Python 3.12 (pandas, geopandas, shapely, numpy, scipy, matplotlib), "
            "Node 24 avec Puppeteer pour le PDF, et pandoc 3 pour le texte et les citations.\n:::")


def minutes(cellule: str) -> float:
    """« 1 h 12 » ou « 58 min » en minutes."""
    m = re.fullmatch(r"(\d+) h (\d+)", cellule.strip())
    return int(m.group(1)) * 60 + int(m.group(2)) if m else float(cellule.split()[0])


def verifier_texte() -> None:
    """Les chiffres écrits à la main dans le corps du rapport doivent rester ceux du calcul."""
    texte = RAPPORT.read_text(encoding="utf-8").split(DEBUT)[0]
    a = csv("marges_arrets_egaux.csv").set_index("trajet")
    for t in TRAJETS:
        # 7 colonnes, et une dernière cellule en minutes : la table des ouvrages a aussi 7 colonnes.
        lignes = [l for l in texte.splitlines() if l.startswith(f"| {t} | ") and l.count("|") == 8
                  and re.search(r"\| (\d+ min|\d+ h \d+) \|$", l.strip())]
        if len(lignes) != 1:
            sys.exit(f"table des gains à arrêts égaux : ligne introuvable pour {t}")
        c = [x.strip() for x in lignes[0].strip("|").split("|")]
        for cellule, col in zip(c[3:], ("gain_publie_min", "gain_train_par_train_min",
                                        "gain_tendance_horaire_min", "gain_trains_complets_min")):
            if abs(minutes(cellule) - a.loc[t, col]) > 0.6:
                sys.exit(f"{t}, {col} : {cellule} dans le texte, {a.loc[t, col]} au calcul")
        marge = f"{round(a.loc[t, 'marge_arrets_egaux_pct'])} % ("
        if not any(l.startswith(f"| {t} | ") and marge in l for l in texte.splitlines()):
            sys.exit(f"{t} : marge réelle {marge} absente de la section 3")
    d = csv("decomposition_gains.csv")
    val = lambda t, p: float(d[(d.trajet == t) & (d.poste == p)].minutes.iloc[0])   # noqa: E731
    for t in ("Québec-Montréal", "Montréal-Ottawa", "Montréal-Toronto"):
        m = round(val(t, "temps_scenario_2_avec_marge") + val(t, "info_cohabitation_mou_urbain"))
        if f"{m // 60} h {m % 60:02d}" not in texte:
            sys.exit(f"sensibilité du mou urbain : {t} donnerait {m // 60} h {m % 60:02d}")


def main() -> None:
    verifier_texte()
    corps = "\n\n".join([
        "Cette fiche regroupe les paramètres du modèle, pour les experts qui voudront les vérifier ou refaire "
        "les calculs. Le code écrit lui-même ces tableaux à chaque compilation du rapport, sauf les coûts, repris "
        "de la section 11, et les versions des données. Ils montrent donc les valeurs réellement utilisées.",
        formules(), trains(), courbes(), mesure(), exploitation(), etapes(), arrets(), zones(), marges(), passages(),
        couts(), sensibilites(), donnees(), scripts()])
    bloc = f"{DEBUT}\n\n::: {{.fiche}}\n\n{corps}\n\n:::\n\n{FIN}"

    with open(RAPPORT, encoding="utf-8", newline="") as f:
        texte = f.read()
    if texte.count(DEBUT) != 1 or texte.count(FIN) != 1:
        sys.exit("repères de la fiche introuvables dans rapport.md")
    avant = texte[:texte.index(DEBUT)]
    apres = texte[texte.index(FIN) + len(FIN):]
    with open(RAPPORT, "w", encoding="utf-8", newline="") as f:
        f.write(avant + bloc + apres)
    print(f"Fiche technique écrite dans rapport.md ({len(bloc)} signes, "
          f"{sum(len(g) for g in SCRIPTS.values())} scripts)")


if __name__ == "__main__":
    main()

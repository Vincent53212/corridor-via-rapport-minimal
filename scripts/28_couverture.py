"""Étape 28 — La couverture : le corridor dessiné par sa propre mesure.

Produit `identite/couverture.svg`, l'illustration de la page de titre. Ce n'est
pas un ornement : c'est le tracé apparié à OpenStreetMap (intermediaires/
corridor_matched.geojson), découpé par les segments de courbure et coloré par la
vitesse que la géométrie autorise. Le lecteur voit donc le résultat de l'étude
avant d'avoir lu une ligne : un corridor bleu acier, qui s'allume en brique et en
grenat exactement là où les courbes le retiennent.

Trois décisions de dessin, et leurs raisons :

  - ROTATION. Le corridor Québec-Toronto fait 6,6 degrés de long pour environ 1
    de large : posé tel quel sur une page portrait, il tient dans une bande de
    120 px de haut et le titre l'écrase. On le fait donc pivoter jusqu'à ce que
    son axe principal soit vertical (angle calculé, pas choisi : c'est celui de
    la droite Toronto-Québec), ce qui lui donne toute la hauteur de la page.

  - ÉPAISSEUR. Le trait est large (plusieurs pixels) parce qu'il porte une
    couleur qui doit se lire. Un filet géographiquement plus juste serait ici
    illisible, et la couverture n'est pas une carte : l'échelle n'y est pas
    annoncée, aucune mesure ne s'y prend.

  - LES QUATRE TRONÇONS, ET LE TRIANGLE. Montréal-Toronto emprunte les mêmes
    rails que la branche par Ottawa sur 392 de ses 539 km, mais il lui reste
    140 km propres, d'un seul tenant : du km 63 au km 203 depuis Montréal, le
    long du fleuve entre Rivière-Beaudette et Brockville, là où l'autre remonte
    vers Ottawa et redescend. Mesure faite au plus proche voisin, et stable de
    150 à 500 m de seuil, ce qui écarte l'artefact d'appariement. Ne dessiner
    que MTL-QC, MTL-Ott et Ott-TO effaçait donc la liaison directe, qui est le
    trajet de tête du rapport. Les quatre sont tracés, MTL-TO en dernier pour
    que les rails communs portent les valeurs du trajet principal. Le triangle
    est le même que celui de la figure du 2×2, et c'est voulu : les deux images
    doivent se reconnaître.

    python scripts/28_couverture.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

from identite import IDENTITE_DIR, PAPIER, ACCENT, VITESSE, couleur_pour_vitesse
from utils import DELIVERABLES, INTERMEDIATES

SORTIE = IDENTITE_DIR / "couverture.svg"

# Le scénario dont la couverture montre le résultat : le plafond géométrique
# pendulaire (moteur interne S2), commun aux trois scénarios publiés. C'est le
# pendulaire exploité selon la méthode que le CN applique déjà, sans dérogation
# à demander, donc le seul dont la couverture puisse montrer l'image sans
# promettre une approbation.
SCENARIO = "pendulaire"
COL_VMAX = f"vmax_{SCENARIO}_kmh_plafond_courbure"

# La couverture ne le NOMME pas : la nomenclature des scénarios est posée dans
# le rapport. La réglette dit donc la fonction du scénario, pas son numéro.
SCENARIO_LIBELLE = "train pendulaire"

TRONCONS = ["MTL-QC", "MTL-Ott", "Ott-TO", "MTL-TO"]

VILLES = {"Québec": (-71.22, 46.81), "Montréal": (-73.567, 45.50),
          "Ottawa": (-75.65, 45.42), "Toronto": (-79.38, 43.65),
          "Kingston": (-76.49, 44.23)}

# Page letter à 96 ppp, et la fenêtre où vit le tracé.
#
# MISE EN PAGE. Redressé, le corridor fait environ sept fois plus long que
# large : c'est une colonne, pas une tache. On lui donne donc toute la hauteur
# de la page dans son tiers droit, et le bloc de titre s'installe à gauche, dans
# le vide que cette forme laisse nécessairement. Le PSE posait sa ligne au-dessus
# d'un titre pleine largeur ; ici le titre est à côté du tracé, et les deux
# couvertures ne se confondent pas d'un coup d'oeil.
L, H = 816.0, 1056.0
BOITE = (476.0, 62.0, 648.0, 946.0)   # x0, y0, x1, y1

TRAIT = 8.2          # épaisseur du tracé, en px de page
HALO = 14.5          # liseré d'encre sous le tracé : détache les couleurs du fond


def charger():
    seg = pd.read_csv(DELIVERABLES / "segments_courbature.csv", sep=";",
                      encoding="utf-8-sig", skiprows=[1])
    gj = json.loads((INTERMEDIATES / "corridor_matched.geojson").read_text(encoding="utf-8"))
    lignes = {f["properties"]["troncon_id"]: f["geometry"]["coordinates"]
              for f in gj["features"]
              if f["geometry"]["type"] == "LineString"
              and f["properties"].get("troncon_id") in TRONCONS}
    return seg, lignes


def abscisse_km(coords):
    """Abscisse curviligne en km le long d'une polyligne en degrés."""
    s = [0.0]
    for (x1, y1), (x2, y2) in zip(coords, coords[1:]):
        dx = (x2 - x1) * 111.32 * math.cos(math.radians((y1 + y2) / 2))
        dy = (y2 - y1) * 110.57
        s.append(s[-1] + math.hypot(dx, dy))
    return s


def projeter(lon, lat, lat0):
    """Équirectangulaire centrée : suffisant sur 8 degrés de longitude, et le
    seul choix qui garde le dessin comparable à la carte interactive."""
    return lon * math.cos(math.radians(lat0)), lat


def cadre(axe, toutes_coords):
    """Angle de redressement et transformation vers la boîte de la page.

    `axe` donne l'inclinaison, `toutes_coords` donne l'étendue à faire tenir.
    L'angle n'est pas choisi : c'est celui de la droite qui joint les deux
    extrémités de l'axe, ramené à la verticale."""
    lat0 = sum(y for _, y in toutes_coords) / len(toutes_coords)
    pts = [projeter(x, y, lat0) for x, y in axe]
    (xa, ya), (xb, yb) = pts[0], pts[-1]
    # `+ pi/2` et non `- pi/2` : les deux redressent l'axe, mais celui-ci met le
    # PREMIER point du chaînage en haut de page. Le chaînage part de Québec, et
    # la couverture doit se lire dans l'ordre du titre, Québec puis Toronto.
    theta = math.atan2(yb - ya, xb - xa) + math.pi / 2
    c, s = math.cos(-theta), math.sin(-theta)
    tourne = [(px * c - py * s, px * s + py * c)
              for px, py in (projeter(x, y, lat0) for x, y in toutes_coords)]
    xs, ys = [p[0] for p in tourne], [p[1] for p in tourne]
    x0, y0, x1, y1 = BOITE
    k = min((x1 - x0) / (max(xs) - min(xs)), (y1 - y0) / (max(ys) - min(ys)))
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2

    def vers_page(lon, lat):
        px, py = projeter(lon, lat, lat0)
        rx, ry = px * c - py * s, px * s + py * c
        return ((x0 + x1) / 2 + (rx - cx) * k, (y0 + y1) / 2 - (ry - cy) * k)

    return vers_page


def sous_traits(coords, s_km, seg_troncon):
    """Découpe la polyligne en sous-traits d'une seule couleur.

    Les km du CSV de segments et les km de la polyligne ne viennent pas du même
    calcul (l'un mesure sur la voie appariée, l'autre sur la géométrie tracée) :
    on rapporte donc les bornes du CSV à la longueur réellement dessinée plutôt
    que de les additionner, sans quoi la coloration dérive vers la fin du tracé."""
    total = s_km[-1]
    km_max = seg_troncon["km_fin"].max()
    bornes = []
    for _, r in seg_troncon.sort_values("km_début").iterrows():
        bornes.append((r["km_début"] / km_max * total,
                       r["km_fin"] / km_max * total,
                       couleur_pour_vitesse(r[COL_VMAX])))
    morceaux, i = [], 0
    for a, b, coul in bornes:
        pts = []
        while i < len(s_km) and s_km[i] < a:
            i += 1
        j = i
        while j < len(s_km) and s_km[j] <= b:
            pts.append(coords[j])
            j += 1
        # un point de recouvrement de chaque côté : sans lui, deux couleurs
        # voisines laissent un trou blanc à la jonction
        if i > 0:
            pts.insert(0, coords[i - 1])
        if j < len(coords):
            pts.append(coords[j])
        if len(pts) >= 2:
            morceaux.append((pts, coul))
        i = j
    return morceaux


def chemin(pts, vers_page) -> str:
    d = []
    for k, (lon, lat) in enumerate(pts):
        x, y = vers_page(lon, lat)
        d.append(("M" if k == 0 else "L") + f"{x:.1f} {y:.1f}")
    return " ".join(d)


def decimer(pts, pas_km=0.25):
    """Allège une polyligne en gardant un point tous les `pas_km`.

    La couverture s'imprime à 300 ppp et mérite ses 5 800 points par tronçon ;
    le visualiseur est une vignette de navigation de 1 000 px de large, où un
    point tous les 250 m est déjà sous le pixel. Sans cet allègement le SVG de
    navigation pèserait 500 Ko dans un fichier qui doit rester ouvrable par
    double-clic."""
    if len(pts) < 3:
        return pts
    garde, ref = [pts[0]], pts[0]
    for p in pts[1:-1]:
        dx = (p[0] - ref[0]) * 111.32 * math.cos(math.radians(p[1]))
        dy = (p[1] - ref[1]) * 110.57
        if math.hypot(dx, dy) >= pas_km:
            garde.append(p)
            ref = p
    garde.append(pts[-1])
    return garde


def carte_navigation(seg, lignes, ordre) -> None:
    """Vignette du corridor pour le visualiseur : même géométrie et mêmes
    couleurs que la couverture, mais en orientation géographique naturelle et
    sur fond de papier. Chaque tronçon porte en plus un tracé de PRÉHENSION
    transparent et large, que le visualiseur rend cliquable ; c'est ce qui
    permet de filtrer les tables en désignant un morceau de corridor plutôt
    qu'en cherchant son nom dans une liste."""
    # La hauteur se DÉDUIT de l'emprise plutôt que d'être fixée : le corridor est
    # une diagonale, et une boîte au mauvais rapport lui laisse une bande vide
    # sur toute une largeur. Marge droite plus généreuse : les noms de ville se
    # posent à droite de leur pastille et « Montréal » déborderait.
    L2 = 1000.0
    marge, marge_d = 40.0, 130.0
    toutes = [p for t, _ in ordre for p in lignes[t]]
    lat0 = sum(y for _, y in toutes) / len(toutes)
    xs = [x * math.cos(math.radians(lat0)) for x, _ in toutes]
    ys = [y for _, y in toutes]
    k = (L2 - marge - marge_d) / (max(xs) - min(xs))
    H2 = (max(ys) - min(ys)) * k + 2 * marge

    def vers(lon, lat):
        return (marge + (lon * math.cos(math.radians(lat0)) - min(xs)) * k,
                H2 - marge - (lat - min(ys)) * k)

    corps, prises = [], []
    for t, inverse in ordre:
        coords = list(reversed(lignes[t])) if inverse else lignes[t]
        s_km = abscisse_km(coords)
        st = seg[seg["tronçon"] == t]
        if inverse:
            km_max = st["km_fin"].max()
            st = st.assign(**{"km_début": km_max - st["km_fin"],
                              "km_fin": km_max - st["km_début"]})
        prises.append(
            f'<path class="prise" data-troncon="{t}" '
            f'd="{chemin(decimer(coords, 1.0), vers)}" fill="none" '
            f'stroke="transparent" stroke-width="15"/>')
        for pts, coul in sous_traits(coords, s_km, st):
            corps.append(f'<path d="{chemin(decimer(pts), vers)}" fill="none" '
                         f'stroke="{coul}" stroke-width="3.4" '
                         f'stroke-linecap="round" stroke-linejoin="round"/>')

    villes = []
    for nom, (lon, lat) in VILLES.items():
        x, y = vers(lon, lat)
        pole = nom != "Kingston"
        villes.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{4.6 if pole else 3.0}" '
            f'fill="{PAPIER["encre"]}" stroke="{PAPIER["fond"]}" stroke-width="1.6"/>')
        villes.append(
            f'<text x="{x + 9:.1f}" y="{y + 3.6:.1f}" font-size="{11 if pole else 9.5}" '
            f'font-weight="{600 if pole else 400}" letter-spacing="0.5" '
            f'fill="{PAPIER["encre"] if pole else PAPIER["encre_pale"]}">{nom}</text>')

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {L2:.0f} {H2:.0f}" '
           f'class="carte-nav" font-family="PlexMono, monospace">\n'
           + "\n".join(corps) + "\n" + "\n".join(villes) + "\n"
           + "\n".join(prises) + "\n</svg>\n")
    (IDENTITE_DIR / "corridor_nav.svg").write_text(svg, encoding="utf-8")
    print(f"Écrit corridor_nav.svg ({len(corps)} sous-traits, "
          f"{len(svg) / 1024:.0f} Ko)")


def main() -> None:
    seg, lignes = charger()
    # Ordre de TRACÉ : la branche par Ottawa d'abord, la liaison directe ensuite,
    # pour que les rails communs aux deux portent les valeurs du trajet de tête.
    ordre = [("MTL-QC", True), ("MTL-Ott", False), ("Ott-TO", False),
             ("MTL-TO", False)]
    # L'angle de redressement, lui, se calcule sur le seul enchaînement
    # Québec -> Montréal -> Toronto en direct : c'est l'axe du corridor. Le
    # calculer sur les quatre tronçons ferait dépendre l'inclinaison de la page
    # du détour par Ottawa, qui est une branche et non l'axe. MTL-QC est stocké
    # de Montréal vers Québec, on le retourne pour que le corridor se lise d'un
    # bout à l'autre.
    axe = list(reversed(lignes["MTL-QC"])) + lignes["MTL-TO"]
    # Le cadrage, lui, doit voir TOUS les points, branche comprise, sans quoi
    # la boucle d'Ottawa sortirait de la boîte.
    tous = axe + lignes["MTL-Ott"] + lignes["Ott-TO"]
    vers_page = cadre(axe, tous)

    corps, halos = [], []
    for t, inverse in ordre:
        coords = list(reversed(lignes[t])) if inverse else lignes[t]
        s_km = abscisse_km(coords)
        st = seg[seg["tronçon"] == t]
        if inverse:
            # les km du CSV comptent depuis Montréal : on les retourne aussi
            km_max = st["km_fin"].max()
            st = st.assign(**{"km_début": km_max - st["km_fin"],
                              "km_fin": km_max - st["km_début"]})
        halos.append(f'<path d="{chemin(coords, vers_page)}" fill="none" '
                     f'stroke="{PAPIER["encre"]}" stroke-width="{HALO}" '
                     f'stroke-linecap="round" stroke-linejoin="round" opacity="0.85"/>')
        for pts, coul in sous_traits(coords, s_km, st):
            corps.append(f'<path d="{chemin(pts, vers_page)}" fill="none" '
                         f'stroke="{coul}" stroke-width="{TRAIT}" '
                         f'stroke-linecap="round" stroke-linejoin="round"/>')

    # Villes : anneau d'encre bordé de papier, et le nom en chasse fixe. Le nom
    # est posé à gauche ou à droite selon le côté où le tracé laisse de la place.
    villes = []
    for nom, (lon, lat) in VILLES.items():
        x, y = vers_page(lon, lat)
        pole = nom in ("Québec", "Montréal", "Ottawa", "Toronto")
        r = 7.0 if pole else 4.4
        villes.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{PAPIER["encre"]}" '
            f'stroke="{PAPIER["fond"]}" stroke-width="2.2"/>')
        # Tous les noms à DROITE du tracé, sans exception : le vide de gauche
        # appartient au bloc de titre, et un seul nom qui y déborderait ferait
        # douter de l'alignement de tout le reste.
        poids = 600 if pole else 400
        taille = 12.5 if pole else 10.5
        villes.append(
            f'<text x="{x + 16:.1f}" y="{y + 4:.1f}" text-anchor="start" '
            f'font-family="PlexMono, monospace" font-size="{taille}" '
            f'font-weight="{poids}" letter-spacing="1.1" '
            f'fill="{PAPIER["fond"] if pole else "#B8B2A4"}">{nom}</text>')

    # Réglette : la clé de couleur, sans laquelle la couverture serait un décor.
    # Posée en haut à gauche, donc lue AVANT le titre : le lecteur sait ce que
    # les couleurs disent au moment où il rencontre le tracé.
    rx, ry, rw, rh = 82.0, 104.0, 268.0, 7.0
    n = len(VITESSE)
    reglette = [f'<rect x="{rx + i * rw / n:.1f}" y="{ry}" width="{rw / n + .6:.1f}" '
                f'height="{rh}" fill="{p["color"]}"/>'
                for i, p in enumerate(VITESSE)]
    for i, v in enumerate(("100", "160", "200", "250", "300")):
        reglette.append(
            f'<text x="{rx + (i + 1) * rw / n:.1f}" y="{ry + rh + 14:.1f}" '
            f'text-anchor="middle" font-family="PlexMono, monospace" font-size="8.5" '
            f'fill="#8D8677">{v}</text>')
    reglette.append(
        f'<text x="{rx}" y="{ry - 8:.1f}" font-family="PlexMono, monospace" '
        f'font-size="8.5" letter-spacing="1.6" fill="{ACCENT["primaire_clair"]}">'
        f'VITESSE QUE LA COURBURE AUTORISE, {SCENARIO_LIBELLE.upper()} (km/h)</text>')
    # Le plafond d'exploitation retenu (201 = marche du PTC certifié et seuil
    # passages à niveau) : un repère sur la
    # rampe, pour que la carte (plafonds géométriques, y compris au-delà) ne se
    # lise pas comme une promesse d'exploitation.
    x201 = rx + (2 + (201 - 160) / 40) * rw / n
    reglette.append(
        f'<line x1="{x201:.1f}" y1="{ry - 3.5:.1f}" x2="{x201:.1f}" '
        f'y2="{ry + rh + 3.5:.1f}" stroke="{PAPIER["fond"]}" stroke-width="1.4"/>')
    reglette.append(
        f'<text x="{x201:.1f}" y="{ry + rh + 24:.1f}" text-anchor="middle" '
        f'font-family="PlexMono, monospace" font-size="8.5" '
        f'fill="{ACCENT["primaire_clair"]}">201 · plafond retenu</text>')
    reglette.append(
        f'<text x="{rx + rw + 14:.1f}" y="{ry + rh + 1:.1f}" '
        f'font-family="PlexMono, monospace" font-size="8.5" fill="#8D8677">'
        f'et plus</text>')

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {L:.0f} {H:.0f}" '
           f'width="{L:.0f}" height="{H:.0f}" preserveAspectRatio="xMidYMid slice">\n'
           f'<rect width="{L:.0f}" height="{H:.0f}" fill="{PAPIER["encre"]}"/>\n'
           + "\n".join(halos) + "\n" + "\n".join(corps) + "\n"
           + "\n".join(villes) + "\n" + "\n".join(reglette) + "\n</svg>\n")
    SORTIE.write_text(svg, encoding="utf-8")
    print(f"Écrit {SORTIE.name} ({len(corps)} sous-traits colorés, "
          f"{len(svg) / 1024:.0f} Ko)")

    carte_navigation(seg, lignes, ordre)


if __name__ == "__main__":
    main()

"""Étape 29 — rapport.md -> livrables/rapport_corridor.html, à l'identité du document.

pandoc fait la conversion et les citations ; ce script fait la MISE EN PAGE :
couverture, sommaire, ouvertures de section, tableaux ledger. Il ne réécrit
aucun contenu. `rapport.md` reste la source unique du texte et des chiffres, et
il peut continuer d'être relu, édité et versionné comme du markdown ordinaire.

Le HTML produit est autonome : polices inlinées en base64, illustration de
couverture en SVG inline, feuille de style incorporée. Il s'ouvre hors ligne et
c'est lui, tel quel, que puppeteer imprime à l'étape 30.

    python scripts/29_rapport_html.py
"""
from __future__ import annotations

import base64
import re
import subprocess
import sys
from pathlib import Path

from identite import IDENTITE_DIR, faces_polices, variables_css
from utils import DELIVERABLES, PROJECT_ROOT

SOURCE = PROJECT_ROOT / "rapport.md"
SORTIE = DELIVERABLES / "rapport_corridor.html"

# Surtitre de chaque section : le mot de repère que le lecteur suit en marge,
# et la clé du sommaire. Il dit la FONCTION de la section, là où le titre en dit
# le sujet. Une section absente de cette table n'aurait pas de surtitre : le
# script s'arrête plutôt que de publier une page dépareillée.
SURTITRES = {
    "Synthèse": "Ce qu'il faut retenir",
    "Méthode et périmètre": "Comment c'est mesuré",
    "Le train pendulaire et le dévers": "Matériel et voie",
    "Doublement des voies et régime de cohabitation": "Capacité",
    "Passages à niveau": "Obstacles au sol",
    "Signalisation": "Commande des trains",
    "Résultats intégrés": "Les temps de parcours",
    "Limites, et l'étude qu'il faut commander": "Ce qui reste à faire",
    "Références": "Sources",
}

# Unités et mots de liaison tolérés dans une cellule qu'on veut aligner à droite
# et passer en chasse fixe. Tout autre mot fait de la cellule un LIBELLÉ, qui
# reste en serif à gauche. Ce test remplace un balisage d'alignement que le
# markdown des tables ne porte pas.
UNITES = {"km", "m", "mm", "mi", "h", "min", "s", "po", "pi", "kmh", "mph",
          "paires", "paire", "trains", "train", "jour", "à", "et", "ou",
          "pct", "g", "mo", "ha", "log", "deg"}

AVIS_SOMMAIRE = (
    "Les vitesses sont en km/h, suivies au besoin de l'équivalent en mi/h. "
    "Les temps de parcours sont donnés en fourchette, bornes comprises : "
    "la borne basse applique la marge normative de 9 pour cent, la borne haute "
    "reconduit la marge mesurée aujourd'hui sur le tronçon. Aucun chiffre de ce "
    "rapport n'est saisi à la main : tous sortent du pipeline de mesure décrit "
    "en section 2."
)


# ------------------------------------------------------------------ pandoc
def corps_pandoc() -> str:
    cmd = ["pandoc", str(SOURCE), "-t", "html5", "--citeproc",
           "--bibliography", "sources/refs.bib", "--csl", "sources/apa.csl",
           "--section-divs", "--mathml", "--no-highlight"]
    r = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True,
                       encoding="utf-8")
    if r.returncode != 0:
        print(r.stderr)
        sys.exit("pandoc a échoué")
    return r.stdout


def entete_yaml() -> dict[str, str]:
    txt = SOURCE.read_text(encoding="utf-8")
    bloc = txt.split("---", 2)[1]
    meta = {}
    for cle in ("title", "subtitle", "author", "date"):
        m = re.search(rf'^{cle}:\s*"(.*)"\s*$', bloc, re.M)
        if m:
            meta[cle] = m.group(1)
    return meta


# ------------------------------------------------------- retouches du corps
def sans_balises(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s).replace("&nbsp;", " ").strip()


def cle_titre(s: str) -> str:
    """Clé de comparaison d'un titre. pandoc convertit les apostrophes droites
    en apostrophes typographiques : sans cette normalisation, « Limites, et
    l'étude… » ne retrouve jamais son surtitre."""
    return sans_balises(s).replace("’", "'").replace("‘", "'")


def est_mesure(cellule: str) -> bool:
    """Vrai si la cellule porte une mesure et non un libellé."""
    txt = sans_balises(cellule)
    if not re.search(r"\d", txt):
        return False
    mots = re.findall(r"[A-Za-zÀ-ÿ]+", txt)
    return all(m.lower() in UNITES for m in mots)


def marquer_colonnes(html: str) -> str:
    """Ajoute la classe `num` aux colonnes de mesure, en-tête compris.

    La décision se prend PAR COLONNE et non par cellule : une colonne dont la
    plupart des valeurs sont des mesures doit s'aligner d'un bloc, sinon les
    chiffres dansent d'une ligne à l'autre. Une colonne est de mesure si toutes
    ses cellules non vides en sont."""
    def par_table(m: re.Match) -> str:
        table = m.group(0)
        lignes = re.findall(r"<tr>(.*?)</tr>", table, re.S)
        corps = [re.findall(r"<td[^>]*>(.*?)</td>", lg, re.S) for lg in lignes]
        corps = [c for c in corps if c]
        if not corps:
            return table
        n = max(len(c) for c in corps)
        mesure = []
        for j in range(n):
            vals = [c[j] for c in corps if j < len(c) and sans_balises(c[j])]
            mesure.append(bool(vals) and all(est_mesure(v) for v in vals))

        def par_ligne(mm: re.Match) -> str:
            lg = mm.group(1)
            j = -1

            def cellule(cm: re.Match) -> str:
                nonlocal j
                j += 1
                if j < len(mesure) and mesure[j]:
                    return re.sub(r"^<(t[hd])", r'<\1 class="num"',
                                  cm.group(0), count=1)
                return cm.group(0)

            return "<tr>" + re.sub(r"<(t[hd])[^>]*>.*?</\1>", cellule, lg, flags=re.S) \
                   + "</tr>"

        return re.sub(r"<tr>(.*?)</tr>", par_ligne, table, flags=re.S)

    return re.sub(r"<table>.*?</table>", par_table, html, flags=re.S)


def ouvrir_sections(html: str) -> tuple[str, list[tuple[str, str, str]]]:
    """Remplace chaque <h1> par son bloc d'ouverture, et relève le sommaire."""
    entrees: list[tuple[str, str, str]] = []
    compteur = 0

    def repl(m: re.Match) -> str:
        nonlocal compteur
        attrs, titre = m.group(1), m.group(2)
        propre = cle_titre(titre)
        if propre not in SURTITRES:
            sys.exit(f"section sans surtitre déclaré : « {propre} »\n"
                     "Ajouter son entrée dans SURTITRES (scripts/29_rapport_html.py).")
        compteur += 1
        cle = f"{compteur:02d} · {SURTITRES[propre]}"
        # Le repère de pagination est la CLÉ, pas le titre. « Passages à niveau »
        # et « Signalisation » sont cités dans la prose bien avant leur section :
        # cherché par son titre, le sommaire renvoyait le lecteur à la page 3.
        # La clé, elle, n'apparaît qu'à l'ouverture de la section et au sommaire,
        # et l'étape 30 neutralise la page du sommaire.
        entrees.append((cle, sans_balises(titre), cle))
        return (f'<div class="sec"><span class="k">{cle}</span>'
                f'<h1{attrs}>{titre}</h1></div>')

    html = re.sub(r"<h1([^>]*)>(.*?)</h1>", repl, html, flags=re.S)
    return html, entrees


# ------------------------------------------------------------- assemblage
def couverture(meta: dict[str, str]) -> str:
    svg = (IDENTITE_DIR / "couverture.svg").read_text(encoding="utf-8")
    svg = svg.replace('<?xml version="1.0" encoding="UTF-8"?>', "")
    titre, _, reste = meta["title"].partition(" : ")
    # Trait d'union INSÉCABLE dans « Québec-Toronto » : à 34 pt le titre se
    # coupait après le trait et laissait « Toronto » seul sur sa ligne.
    titre = titre.replace("-", "‑")
    reste = reste[:1].upper() + reste[1:]
    commanditaire, _, auteur = meta["author"].rpartition(" par ")
    commanditaire = commanditaire.replace("Étude préparée pour ", "")
    return f"""<section class="couverture">
{svg}
<div class="titre">
  <div class="sur">Vision Transport &nbsp;·&nbsp; Étude de corridor</div>
  <h1>{titre}</h1>
  <div class="titre2">{reste}</div>
  <div class="sous">{meta["subtitle"]}</div>
  <div class="bas">
    <div class="edition">{meta["date"].upper()}</div>
    <div class="signature">{auteur}<br>pour {commanditaire}</div>
  </div>
</div>
</section>"""


def sommaire(entrees: list[tuple[str, str, str]]) -> str:
    lignes = "\n".join(
        f'<div class="toc-l"><span class="toc-k">{cle}</span>'
        f'<span class="toc-t">{titre}</span><span class="toc-pts"></span>'
        f'<span class="toc-folio" data-find="{trouve}">—</span></div>'
        for cle, titre, trouve in entrees)
    return f"""<section class="sommaire">
<h2>Table des matières</h2><div class="filet"></div>
{lignes}
<div class="avis">{AVIS_SOMMAIRE}</div>
</section>"""


def images_en_ligne(html: str) -> str:
    """Les figures sont inlinées en base64 : le HTML livré doit être un fichier
    unique, et puppeteer ne charge pas d'images relatives depuis un dossier de
    travail temporaire (l'impression se fait hors du dépôt, voir étape 30)."""
    def repl(m: re.Match) -> str:
        src = m.group(1)
        chemin = PROJECT_ROOT / src
        if not chemin.exists():
            sys.exit(f"image introuvable : {src}")
        b64 = base64.b64encode(chemin.read_bytes()).decode("ascii")
        return m.group(0).replace(src, f"data:image/png;base64,{b64}")
    return re.sub(r'<img src="([^"]+)"', repl, html)


def main() -> None:
    meta = entete_yaml()
    corps = corps_pandoc()
    corps, entrees = ouvrir_sections(corps)
    corps = marquer_colonnes(corps)
    corps = images_en_ligne(corps)

    css = (IDENTITE_DIR / "rapport.css").read_text(encoding="utf-8")
    css = css.replace("/*__FONTS__*/", faces_polices())
    css = css.replace("/*__VARS__*/", variables_css())

    html = f"""<!DOCTYPE html>
<html lang="fr-CA">
<head>
<meta charset="utf-8">
<title>{meta["title"]}</title>
<style>
{css}
</style>
</head>
<body>
{couverture(meta)}
{sommaire(entrees)}
{corps}
</body>
</html>
"""
    SORTIE.write_text(html, encoding="utf-8")
    print(f"Écrit {SORTIE.name} ({len(html) / 1024:.0f} Ko, "
          f"{len(entrees)} sections)")


if __name__ == "__main__":
    main()

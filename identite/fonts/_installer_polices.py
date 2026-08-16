"""Provisionnement des polices de l'identité (à relancer seulement si un .ttf manque).

Deux familles, deux usages, deux formats :

  - les .woff2 servent au RAPPORT HTML/PDF (inlinés en base64 dans le gabarit).
    Ils sont repris tels quels du projet PSE, où ils ont été sous-ensemblés au
    latin depuis Google Fonts (licence SIL OFL 1.1 pour les deux familles).

  - les .ttf servent aux FIGURES matplotlib, qui ne lisent ni woff2 ni woff.
    Ils sont produits ici, et pas telechargés à la volée par les scripts de
    figure : une figure ne doit pas dépendre du réseau.

Pourquoi instancier Fraunces plutôt que d'utiliser la variable installée sur le
poste : `Fraunces-VariableFont_SOFT,WONK,opsz,wght.ttf` a pour instance PAR
DÉFAUT wght=900, WONK=1. matplotlib ne sait pas piloter les axes d'une police
variable — il rend l'instance par défaut. Toutes les étiquettes de figure
sortaient donc en Fraunces Black fantaisie, alors que le corps du rapport est en
400 et les titres en 600. On fige ici trois instances, aux mêmes valeurs d'axes
que celles du gabarit HTML (SOFT=0, WONK=0), pour que la figure et la page
portent le même dessin de lettre.

    python identite/fonts/_installer_polices.py
"""
from __future__ import annotations

import io
import sys
import urllib.request
import zipfile
from pathlib import Path

ICI = Path(__file__).resolve().parent

# IBM Plex Mono — archive officielle IBM (SIL OFL 1.1).
PLEX_ZIP = ("https://github.com/IBM/plex/releases/download/"
            "%40ibm%2Fplex-mono%401.1.0/ibm-plex-mono.zip")
PLEX_VOULUS = {
    "IBMPlexMono-Regular.ttf": "IBMPlexMono-Regular.ttf",
    "IBMPlexMono-Medium.ttf": "IBMPlexMono-Medium.ttf",
    "IBMPlexMono-SemiBold.ttf": "IBMPlexMono-SemiBold.ttf",
}

# Fraunces — police variable installée sur le poste (Windows, polices utilisateur).
FRAUNCES_VF = (Path.home() / "AppData/Local/Microsoft/Windows/Fonts"
               / "Fraunces-VariableFont_SOFT,WONK,opsz,wght.ttf")
# (graisse, taille optique) → nom de fichier. opsz suit l'usage : 14 pt pour le
# courant et les étiquettes, 48 pt pour les titres, 96 pt pour la couverture —
# Fraunces resserre l'approche et affine les déliés quand opsz monte.
FRAUNCES_INSTANCES = {
    "Fraunces-400.ttf": {"wght": 400, "opsz": 14, "SOFT": 0, "WONK": 0},
    "Fraunces-600.ttf": {"wght": 600, "opsz": 48, "SOFT": 0, "WONK": 0},
    "Fraunces-700.ttf": {"wght": 700, "opsz": 96, "SOFT": 0, "WONK": 0},
}


def plex() -> None:
    manquants = [c for c in PLEX_VOULUS.values() if not (ICI / c).exists()]
    if not manquants:
        print("IBM Plex Mono : déjà en place")
        return
    print(f"IBM Plex Mono : téléchargement ({len(manquants)} manquant(s))…")
    with urllib.request.urlopen(PLEX_ZIP, timeout=120) as r:
        z = zipfile.ZipFile(io.BytesIO(r.read()))
    membres = {Path(n).name: n for n in z.namelist()
               if "/complete/ttf/" in n and n.endswith(".ttf")}
    for src, dst in PLEX_VOULUS.items():
        (ICI / dst).write_bytes(z.read(membres[src]))
        print(f"  écrit {dst}")


def fraunces() -> None:
    manquants = [n for n in FRAUNCES_INSTANCES if not (ICI / n).exists()]
    if not manquants:
        print("Fraunces : déjà en place")
        return
    if not FRAUNCES_VF.exists():
        sys.exit(f"Fraunces variable introuvable : {FRAUNCES_VF}\n"
                 "Installer la police depuis fonts.google.com/specimen/Fraunces.")
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for nom in manquants:
        axes = FRAUNCES_INSTANCES[nom]
        f = instancer.instantiateVariableFont(TTFont(FRAUNCES_VF), axes,
                                              inplace=False, updateFontNames=False)
        # Sans renommage, les trois instances déclarent toutes la famille
        # « Fraunces » et matplotlib n'en garde qu'une (dernier chargé gagne).
        # On leur donne une famille distincte, que identite.py adresse nommément.
        famille = f"Fraunces {axes['wght']}"
        for rec in f["name"].names:
            if rec.nameID in (1, 3, 4, 6):
                val = famille if rec.nameID in (1, 4) else famille.replace(" ", "")
                rec.string = val.encode("utf-16-be") if rec.platformID == 3 else val.encode()
        f["OS/2"].usWeightClass = axes["wght"]
        f.save(ICI / nom)
        print(f"  écrit {nom} (wght={axes['wght']}, opsz={axes['opsz']})")


if __name__ == "__main__":
    plex()
    fraunces()

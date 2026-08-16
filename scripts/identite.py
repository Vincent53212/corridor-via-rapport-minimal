"""Chargeur de l'identité graphique : identite/identite.json -> CSS, matplotlib, SVG.

Un seul point d'entrée pour les trois moteurs de rendu du livrable :

  - `variables_css()` fabrique le bloc `:root{...}` du gabarit HTML ;
  - `appliquer_rcparams()` cale matplotlib (polices, couleurs, papier) ;
  - `PALETTE`, `VITESSE`, `SCENARIOS`, `CELLULES` donnent les couleurs nommées.

Aucune couleur ni aucune police n'est écrite en dur ailleurs que dans le JSON.
C'est ce qui permet de changer la charte sans rouvrir un script de figure, et
c'est aussi ce que vérifie 27_verif_identite.py.
"""
from __future__ import annotations

import base64
import json
from functools import lru_cache
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
IDENTITE_DIR = RACINE / "identite"
FONTS = IDENTITE_DIR / "fonts"

with open(IDENTITE_DIR / "identite.json", encoding="utf-8") as _f:
    ID = json.load(_f)

PAPIER = ID["papier"]
ACCENT = ID["accent"]
TYPO = ID["typo"]
PAGE = ID["page"]
SCENARIOS = {k: v for k, v in ID["scenarios"].items() if not k.startswith("_")}
CELLULES = {k: v for k, v in ID["cellules"].items() if not k.startswith("_")}
VITESSE = [p for p in ID["vitesse"]["paliers"]]
VITESSE_COULEURS = {p["cle"]: p["color"] for p in VITESSE}
SEUILS = ID["seuils_controle"]


# --------------------------------------------------------------- couleurs
def couleur_pour_vitesse(v_kmh: float) -> str:
    """Couleur du palier qui contient cette vitesse. Les bornes suivent celles
    des cibles publiées dans le rapport (100 / 160 / 200 / 250 / 300)."""
    for borne, cle in ((100, "sous_100"), (160, "100_160"), (200, "160_200"),
                       (250, "200_250"), (300, "250_300")):
        if v_kmh < borne:
            return VITESSE_COULEURS[cle]
    return VITESSE_COULEURS["300_plus"]


def melange(c1: str, c2: str, t: float) -> str:
    """Mélange linéaire de deux couleurs hex, t=0 -> c1, t=1 -> c2 (sRGB brut :
    suffisant pour un voile, jamais pour un choix de palette)."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


# --------------------------------------------------------------- HTML / CSS
@lru_cache(maxsize=None)
def _woff2_b64(nom: str) -> str:
    return base64.b64encode((FONTS / nom).read_bytes()).decode("ascii")


def faces_polices() -> str:
    """Les six @font-face du gabarit, polices inlinées en base64. Le rapport doit
    s'ouvrir hors ligne et s'imprimer identique sur un poste sans les polices."""
    faces = [("Fraunces", 400, "fraunces-400.woff2"),
             ("Fraunces", 600, "fraunces-600.woff2"),
             ("Fraunces", 700, "fraunces-700.woff2"),
             ("PlexMono", 400, "ibm-plex-mono-400.woff2"),
             ("PlexMono", 500, "ibm-plex-mono-500.woff2"),
             ("PlexMono", 600, "ibm-plex-mono-600.woff2")]
    return "\n".join(
        f"@font-face{{font-family:'{fam}';font-weight:{poids};font-style:normal;"
        f"font-display:block;"
        f"src:url(data:font/woff2;base64,{_woff2_b64(f)}) format('woff2');}}"
        for fam, poids, f in faces)


def variables_css() -> str:
    """Le bloc `:root` : toute la charte en variables CSS."""
    v = {
        "papier": PAPIER["fond"], "bloc": PAPIER["fond_bloc"],
        "sable": PAPIER["sable"], "encre": PAPIER["encre"],
        "encre-douce": PAPIER["encre_douce"], "encre-pale": PAPIER["encre_pale"],
        "filet": PAPIER["filet"], "filet-fort": PAPIER["filet_fort"],
        "accent": ACCENT["primaire"], "accent-clair": ACCENT["primaire_clair"],
        "signal": ACCENT["signal"],
        "font-titre": TYPO["titre"], "font-courant": TYPO["courant"],
        "corps": f"{PAGE['corps_pt']}pt", "interligne": str(PAGE["interligne"]),
        "marge-cote": PAGE["marge_cote"], "marge-haut": PAGE["marge_haut"],
        "marge-bas": PAGE["marge_bas"],
    }
    for p in VITESSE:
        v[f"v-{p['cle'].replace('_', '-')}"] = p["color"]
    for cle, c in SCENARIOS.items():
        v[f"sc-{cle.lower()}"] = c
    return "\n".join(f"  --{k}:{val};" for k, val in v.items())


# --------------------------------------------------------------- matplotlib
def appliquer_rcparams(mpl) -> None:
    """Cale matplotlib sur la charte. À appeler AVANT toute création de figure.

    Les .ttf de identite/fonts sont enregistrés à la volée : ils ne sont pas
    installés sur le poste, et ils ne doivent pas l'être — une figure du rapport
    doit rendre pareil sur n'importe quelle machine qui a le dépôt."""
    from matplotlib import font_manager

    for ttf in sorted(FONTS.glob("*.ttf")):
        font_manager.fontManager.addfont(str(ttf))

    familles = {f.name for f in font_manager.fontManager.ttflist}
    voulues = set(TYPO["titre_mpl"].values()) | {TYPO["courant_mpl"]}
    if not voulues <= familles:
        raise SystemExit(
            f"polices absentes : {sorted(voulues - familles)}\n"
            "Lancer : python identite/fonts/_installer_polices.py")

    mpl.rcParams.update({
        "figure.facecolor": PAPIER["fond"],
        "axes.facecolor": PAPIER["fond"],
        "savefig.facecolor": PAPIER["fond"],
        "savefig.edgecolor": PAPIER["fond"],
        "text.color": PAPIER["encre"],
        "axes.labelcolor": PAPIER["encre_douce"],
        "axes.edgecolor": PAPIER["filet_fort"],
        "xtick.color": PAPIER["encre_pale"],
        "ytick.color": PAPIER["encre_pale"],
        "grid.color": PAPIER["filet"],
        "font.family": [TYPO["courant_mpl"]],
        "font.size": 8.2,
        "axes.titlesize": 10.5,
        "axes.titleweight": "normal",
        "legend.frameon": False,
        "figure.dpi": 300,
        "savefig.dpi": 300,
    })


def police_titre(poids: int = 600) -> dict:
    """kwargs de police pour un titre de figure (Fraunces à la graisse voulue)."""
    return {"fontfamily": TYPO["titre_mpl"][str(poids)]}


def police_mono(poids: str = "normal") -> dict:
    return {"fontfamily": TYPO["courant_mpl"], "fontweight": poids}

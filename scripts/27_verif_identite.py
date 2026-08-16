"""Étape 27 — Contrôle de la palette : distinction, daltonisme, contraste.

Une charte qui promet « ces trois figurés se distinguent » sans le mesurer est
une charte qui se dément à la première impression. Ce script est le garde-fou de
identite/identite.json : il refuse la palette si l'une des promesses écrites
dans ses `_note` ne tient pas.

Trois mesures, toutes sur des couleurs COMPOSÉES telles qu'elles seront vues :

  1. dE2000 entre figurés qui doivent se distinguer, en vision normale ET sous
     simulation de dichromatisme (protanopie, deutéranopie, tritanopie), par les
     matrices de Machado, Oliveira & Fernandes (2009) à sévérité 1,0, appliquées
     en RGB linéaire comme le veut leur dérivation ;
  2. monotonie de clarté des rampes ordonnées (S1-S2-S3, bandes de vitesse) :
     c'est ce qui fait qu'elles survivent à une photocopie en gris ;
  3. contraste WCAG des couples texte / fond effectivement employés.

    python scripts/27_verif_identite.py
"""
from __future__ import annotations

import sys

import numpy as np

from identite import (ACCENT, CELLULES, ID, PAPIER, SCENARIOS, SEUILS, VITESSE)

# Machado, Oliveira & Fernandes (2009), tableaux de sévérité 1,0.
CVD = {
    "protanopie": np.array([[0.152286, 1.052583, -0.204868],
                            [0.114503, 0.786281, 0.099216],
                            [-0.003882, -0.048116, 1.051998]]),
    "deutéranopie": np.array([[0.367322, 0.860646, -0.227968],
                              [0.280085, 0.672501, 0.047413],
                              [-0.011820, 0.042940, 0.968881]]),
    "tritanopie": np.array([[1.255528, -0.076749, -0.178779],
                            [-0.078411, 0.930809, 0.147602],
                            [0.004733, 0.691367, 0.303900]]),
}

# sRGB D65 -> XYZ
M_XYZ = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
BLANC = np.array([0.95047, 1.00000, 1.08883])


def hex_rgb(h: str) -> np.ndarray:
    return np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])


def lineaire(c: np.ndarray) -> np.ndarray:
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def gamma(c: np.ndarray) -> np.ndarray:
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def lab(h: str) -> np.ndarray:
    xyz = M_XYZ @ lineaire(hex_rgb(h)) / BLANC
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


def simuler(h: str, type_cvd: str) -> str:
    rgb = gamma(CVD[type_cvd] @ lineaire(hex_rgb(h)))
    return "#%02X%02X%02X" % tuple(round(x * 255) for x in rgb)


def de2000(h1: str, h2: str) -> float:
    """CIEDE2000, formulation de Sharma, Wu & Dalal (2005)."""
    L1, a1, b1 = lab(h1)
    L2, a2, b2 = lab(h2)
    C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - np.sqrt(Cb ** 7 / (Cb ** 7 + 25.0 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360
    dLp = L2 - L1
    dCp = C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    else:
        dhp = h2p - h1p - 360 * np.sign(h2p - h1p)
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dhp) / 2)
    Lbp = (L1 + L2) / 2
    Cbp = (C1p + C2p) / 2
    if C1p * C2p == 0:
        hbp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hbp = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        hbp = (h1p + h2p + 360) / 2
    else:
        hbp = (h1p + h2p - 360) / 2
    T = (1 - 0.17 * np.cos(np.radians(hbp - 30)) + 0.24 * np.cos(np.radians(2 * hbp))
         + 0.32 * np.cos(np.radians(3 * hbp + 6)) - 0.20 * np.cos(np.radians(4 * hbp - 63)))
    dTh = 30 * np.exp(-(((hbp - 275) / 25) ** 2))
    Rc = 2 * np.sqrt(Cbp ** 7 / (Cbp ** 7 + 25.0 ** 7))
    Sl = 1 + (0.015 * (Lbp - 50) ** 2) / np.sqrt(20 + (Lbp - 50) ** 2)
    Sc = 1 + 0.045 * Cbp
    Sh = 1 + 0.015 * Cbp * T
    Rt = -np.sin(np.radians(2 * dTh)) * Rc
    return float(np.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2
                         + Rt * (dCp / Sc) * (dHp / Sh)))


def contraste(h1: str, h2: str) -> float:
    def lum(h):
        r, g, b = lineaire(hex_rgb(h))
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    a, b = sorted((lum(h1), lum(h2)), reverse=True)
    return (a + 0.05) / (b + 0.05)


# --------------------------------------------------------------- contrôles
ECHECS: list[str] = []
LIGNES: list[str] = []


def dire(txt: str = "") -> None:
    LIGNES.append(txt)


def exiger(ok: bool, message: str) -> None:
    if not ok:
        ECHECS.append(message)


def bloc_categoriel() -> None:
    """Les trois cellules du 2x2 doivent se distinguer deux à deux, y compris
    pour un dichromate, et aucune ne doit se confondre avec le gris des exclus."""
    seuil = SEUILS["dE_categoriel_min"]
    seuil_cvd = SEUILS["dE_categoriel_cvd_min"]
    cles = list(CELLULES)
    dire("2x2 VOIE x PROPRIÉTAIRE  (plancher %.0f normal, %.0f sous daltonisme)"
         % (seuil, seuil_cvd))
    dire(f"  {'paire':<26}{'normal':>8}{'protan.':>9}{'deutér.':>9}{'trital.':>9}")
    for i, a in enumerate(cles):
        for b in cles[i + 1:]:
            ca, cb = CELLULES[a], CELLULES[b]
            normal = de2000(ca, cb)
            sim = {t: de2000(simuler(ca, t), simuler(cb, t)) for t in CVD}
            dire(f"  {a + ' / ' + b:<26}{normal:>8.1f}"
                 + "".join(f"{sim[t]:>9.1f}" for t in CVD))
            exiger(normal >= seuil,
                   f"2x2 : {a}/{b} à {normal:.1f} de dE2000, sous le plancher {seuil:.0f}")
            for t, v in sim.items():
                exiger(v >= seuil_cvd,
                       f"2x2 : {a}/{b} à {v:.1f} en {t}, sous le plancher {seuil_cvd:.0f}")
    dire()


def bloc_rampe(nom: str, couleurs: list[tuple[str, str]], seuil: float,
               monotone: bool = True) -> None:
    """Une rampe ORDONNÉE : voisins séparables, et clarté monotone pour que
    l'ordre survive au noir et blanc."""
    dire(f"{nom}  (voisins : plancher {seuil:.0f} ; clarté monotone)")
    Ls = [lab(c)[0] for _, c in couleurs]
    for (na, ca), (nb, cb) in zip(couleurs, couleurs[1:]):
        d = de2000(ca, cb)
        dcvd = min(de2000(simuler(ca, t), simuler(cb, t)) for t in CVD)
        dire(f"  {na + ' -> ' + nb:<30}{d:>8.1f}   (pire daltonisme {dcvd:.1f})")
        exiger(d >= seuil, f"{nom} : {na}->{nb} à {d:.1f}, sous le plancher {seuil:.0f}")
        exiger(dcvd >= seuil,
               f"{nom} : {na}->{nb} à {dcvd:.1f} sous daltonisme, sous le plancher {seuil:.0f}")
    if monotone:
        sens = np.sign(np.diff(Ls))
        ok = bool(np.all(sens == sens[0]))
        dire("  clarté L* : " + " > ".join(f"{L:.0f}" for L in Ls)
             + ("  monotone" if ok else "  NON MONOTONE"))
        exiger(ok, f"{nom} : la clarté n'est pas monotone, l'ordre disparaît en gris")
    dire()


def bloc_seuil_vitesse() -> None:
    """La promesse centrale de la rampe de vitesse : de part et d'autre de
    200 km/h, chaud contre froid, séparable pour tout le monde."""
    chauds = [p["color"] for p in VITESSE[:3]]
    froids = [p["color"] for p in VITESSE[3:]]
    seuil = SEUILS["dE_categoriel_cvd_min"]
    pire, ou = 1e9, ""
    for i, a in enumerate(chauds):
        for j, b in enumerate(froids):
            for t in CVD:
                d = de2000(simuler(a, t), simuler(b, t))
                if d < pire:
                    pire, ou = d, f"{VITESSE[i]['libelle']} / {VITESSE[3 + j]['libelle']} ({t})"
    dire("SEUIL DE 200 km/h  (chaud contre froid, pire cas sous daltonisme)")
    dire(f"  pire couple : {ou}  ->  {pire:.1f}")
    exiger(pire >= seuil,
           f"seuil 200 : le pire couple chaud/froid tombe à {pire:.1f}, "
           f"sous le plancher {seuil:.0f}")
    dire()


def bloc_lisibilite() -> None:
    """Aucun figuré ne doit s'évanouir sur le papier, aucun texte manquer de
    contraste. Les couples testés sont ceux que le gabarit emploie vraiment."""
    seuil = SEUILS["contraste_texte_min"]
    papier, encre = PAPIER["fond"], PAPIER["encre"]
    couples = [("corps sur papier", encre, papier),
               ("texte atténué sur papier", PAPIER["encre_pale"], papier),
               ("accent sur papier", ACCENT["primaire"], papier),
               ("signal sur papier", ACCENT["signal"], papier),
               ("accent clair sur encre", ACCENT["primaire_clair"], encre),
               ("papier sur encre", papier, encre)]
    dire(f"CONTRASTE DE TEXTE  (plancher WCAG AA {seuil:.1f}:1)")
    for nom, a, b in couples:
        r = contraste(a, b)
        dire(f"  {nom:<28}{r:>6.1f}:1")
        exiger(r >= seuil, f"contraste : {nom} à {r:.1f}:1, sous {seuil:.1f}:1")
    dire()

    dire("PRÉSENCE SUR LE PAPIER  (dE2000 de chaque figuré contre le crème)")
    figures = ([(p["libelle"], p["color"]) for p in VITESSE]
               + [(f"scénario {k}", v) for k, v in SCENARIOS.items()]
               + [(f"cellule {k}", v) for k, v in CELLULES.items()])
    pire = min(figures, key=lambda kv: de2000(kv[1], papier))
    for nom, c in figures:
        d = de2000(c, papier)
        exiger(d >= 15.0, f"présence : « {nom} » à {d:.1f} du papier, il s'y dissout")
    dire(f"  le plus discret : « {pire[0]} » à {de2000(pire[1], papier):.1f}  "
         f"(plancher 15,0)")
    dire()


def main() -> None:
    dire("CONTRÔLE DE L'IDENTITÉ GRAPHIQUE")
    dire("=" * 62)
    dire()
    bloc_categoriel()
    bloc_rampe("BANDES DE VITESSE",
               [(p["libelle"], p["color"]) for p in VITESSE],
               SEUILS["dE_rampe_voisins_min"], monotone=False)
    bloc_seuil_vitesse()
    bloc_rampe("SCÉNARIOS S1 / S2 / S3",
               [(k, SCENARIOS[k]) for k in ("S1", "S2", "S3")],
               SEUILS["dE_rampe_voisins_min"])
    bloc_lisibilite()

    print("\n".join(LIGNES))
    if ECHECS:
        print("ÉCHEC : la palette ne tient pas ses promesses")
        for e in ECHECS:
            print(f"  - {e}")
        sys.exit(1)
    print("PASS : toutes les promesses de identite.json sont vérifiées")


if __name__ == "__main__":
    main()

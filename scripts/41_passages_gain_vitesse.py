"""Étape 41 — Les passages où le train dépasserait vraiment 177 km/h, et ce que leur
élimination rachète.

La bande 178-201 de l'étape 20 est GÉOMÉTRIQUE : elle dit ce que les courbes permettent.
Mais le train n'atteint pas toujours cette vitesse, parce qu'il sort d'une gare ou d'une
courbe, ou qu'il freine pour la suivante. Cette étape roule le train de référence à
201 km/h, dans les deux sens, et relève sa vitesse réelle à chacun des passages.

Elle chiffre ensuite le programme complémentaire comme un achat de vitesse. Le scénario
publié plafonne à 177 km/h. Chaque tronçon où la courbe permet plus de 177 km/h peut
retrouver 201 km/h si on y élimine les passages où le train dépasserait 177 km/h. Les
tronçons sont classés par minutes rachetées par dollar, et les minutes de chaque tranche
sont recalculées trajet par trajet, de bout en bout.

Le tronc commun Brockville-Toronto est sur deux trajets : un passage attribué à
Ottawa-Toronto y est ramené sur l'échelle de Montréal-Toronto (décalage de 94 km).

Coûts unitaires : ceux du rapport, 50 M$ par pont d'étagement et 12 M$ par passage privé.

Sorties : livrables/passages_vitesse_reelle.csv (un passage par ligne)
          livrables/passages_gain_vitesse.csv (une tranche par ligne)
"""
from __future__ import annotations

import importlib.util
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

os.environ["BLOCS_URBAINS"] = "libres"
sys.path.insert(0, str(Path(__file__).parent))
from scenarios import PLAFOND_PUBLIE, marge_de    # noqa: E402
from utils import DELIVERABLES                    # noqa: E402

_spec = importlib.util.spec_from_file_location("m21", Path(__file__).parent / "21_tbase_bande.py")
m21 = importlib.util.module_from_spec(_spec)
sys.modules["m21"] = m21
_spec.loader.exec_module(m21)

PLAFOND_HAUT = 201.0
COUT_PONT, COUT_PRIVE = 50.0, 12.0     # M$ par ouvrage, section des coûts du rapport
DECALAGE_TRONC_COMMUN = 94.0           # km Ott-TO -> km MTL-TO, à l'est de Brockville
KM_BROCKVILLE_OTT = 110.0
TRANCHES_GS = (0.5, 2.0, 4.0, 99.0)    # plafonds de budget cumulé (G$) des tranches publiées
TRAJETS = ["MTL-QC", "MTL-Ott", "Ott-TO", "MTL-TO"]
R = m21.RAME_PENDULAIRE
BY_T = m21.load_segments()


def grille(t: str) -> tuple[np.ndarray, np.ndarray]:
    """Abscisses (km) et limite géométrique de la voie (km/h), au pas du moteur."""
    pieces = m21._free_pieces(t, BY_T[t], "S2", 999.0)
    k0, k1 = pieces[0][0], pieces[-1][1]
    n = int((k1 - k0) * 1000 / m21.DX_M) + 1
    xs = np.linspace(k0, k1, n)
    v = np.zeros(n)
    j = 0
    for i, x in enumerate(xs):
        while j < len(pieces) - 1 and x > pieces[j][1] + 1e-9:
            j += 1
        v[i] = pieces[j][2]
    return xs, v


GRILLES = {t: grille(t) for t in TRAJETS}


def profil(t: str, limite_kmh: np.ndarray, inverse: bool = False) -> tuple[np.ndarray, float]:
    """Vitesse en chaque point (m/s, dans l'ordre de la grille) et minutes de roulement.
    Mêmes règles que 21.profil_vitesse, avec en plus le sens inverse."""
    xs = GRILLES[t][0]
    n = len(xs)
    dx = (xs[-1] - xs[0]) * 1000 / (n - 1)
    km_p, pente = m21.pentes(t)
    i_pente = np.interp(xs, km_p, pente)
    lim = limite_kmh / 3.6
    arrets = [int(np.argmin(np.abs(xs - km))) for _, km in m21.INTERMEDIATE_STOPS[t]]
    if inverse:
        lim, i_pente = lim[::-1], -i_pente[::-1]
        arrets = [n - 1 - a for a in arrets]
    w = int(round(R.longueur_m / dx))
    lim = np.array([lim[max(0, i - w):i + 1].min() for i in range(n)])
    zero = set(arrets) | {0, n - 1}
    v = lim.copy()
    for i in zero:
        v[i] = 0.0
    for i in range(1, n):
        if i in zero:
            v[i] = 0.0
            continue
        a = R.acceleration(max(v[i - 1], 1.0), float(i_pente[i]))
        v[i] = min(lim[i], math.sqrt(max(v[i - 1] ** 2 + 2 * a * dx, 1.0)), v[i])
    for i in range(n - 2, -1, -1):
        if i not in zero:
            v[i] = min(v[i], math.sqrt(v[i + 1] ** 2 + 2 * R.ab * dx))
    minutes = float(np.sum(dx / np.maximum((v[:-1] + v[1:]) / 2, 0.5))) / 60
    return (v[::-1] if inverse else v), minutes


def temps_avec_marge(t: str, limite_kmh: np.ndarray) -> float:
    return (profil(t, limite_kmh)[1] + len(m21.INTERMEDIATE_STOPS[t]) * m21.DWELL_MIN) * marge_de(t)


def vitesses_reelles(d: pd.DataFrame, plafond: float) -> pd.Series:
    """Plus haute vitesse du train au passage, tous sens confondus (km/h)."""
    prof = {}
    for t in TRAJETS:
        xs, v = GRILLES[t]
        lim = np.minimum(v, plafond)
        prof[t] = (profil(t, lim)[0], profil(t, lim, inverse=True)[0])

    def vit(r) -> float:
        xs = GRILLES[r.troncon_principal][0]
        a, b = prof[r.troncon_principal]
        return max(float(np.interp(r.km, xs, a)), float(np.interp(r.km, xs, b))) * 3.6
    return d.apply(vit, axis=1)


def troncons_rapides(s: pd.DataFrame) -> pd.DataFrame:
    """Tronçons où la voie permet plus de 177 km/h, avec les passages à éliminer."""
    rangs = []
    for t in ["MTL-QC", "MTL-Ott", "MTL-TO", "Ott-TO"]:
        xs, v = GRILLES[t]
        rapide = v > PLAFOND_PUBLIE
        base = temps_avec_marge(t, np.minimum(v, PLAFOND_PUBLIE))
        i, n = 0, len(xs)
        while i < n:
            if not rapide[i]:
                i += 1
                continue
            j = i
            while j + 1 < n and rapide[j + 1]:
                j += 1
            a, b = float(xs[i]), float(xs[j])
            if not (t == "Ott-TO" and a > KM_BROCKVILLE_OTT):       # déjà vu sur Montréal-Toronto
                lim = np.minimum(v, PLAFOND_PUBLIE)
                lim[i:j + 1] = np.minimum(v[i:j + 1], PLAFOND_HAUT)
                c = s[(s.trajet_physique == t) & (s.km_physique >= a - 0.2) & (s.km_physique <= b + 0.2)]
                rangs.append({"trajet": t, "km_debut": round(a, 1), "km_fin": round(b, 1),
                              "minutes": base - temps_avec_marge(t, lim),
                              "ponts": int((c.acces == "Public").sum()),
                              "prives": int((c.acces == "Private").sum())})
            i = j + 1
    o = pd.DataFrame(rangs)
    o["cout_gs"] = (o.ponts * COUT_PONT + o.prives * COUT_PRIVE) / 1000
    o["ratio"] = o.minutes / o.cout_gs.replace(0, 1e-6)
    return o.sort_values("ratio", ascending=False).reset_index(drop=True)


def minutes_rachetees(choisis: pd.DataFrame) -> dict[str, float]:
    """Gain de bout en bout, trajet par trajet, d'un ensemble de tronçons rendus à 201 km/h."""
    gains = {}
    for t in TRAJETS:
        xs, v = GRILLES[t]
        base = np.minimum(v, PLAFOND_PUBLIE)
        lim = base.copy()
        for r in choisis.itertuples():
            deb, fin = r.km_debut, r.km_fin
            if r.trajet == t:
                pass
            elif t == "Ott-TO" and r.trajet == "MTL-TO" and deb - DECALAGE_TRONC_COMMUN > KM_BROCKVILLE_OTT:
                deb, fin = deb - DECALAGE_TRONC_COMMUN, fin - DECALAGE_TRONC_COMMUN
            elif t == "MTL-TO" and r.trajet == "MTL-Ott" and fin <= 17.8:
                pass                                                 # Montréal-Dorval, tronc commun
            else:
                continue
            m = (xs >= deb) & (xs <= fin)
            lim[m] = np.minimum(v[m], PLAFOND_HAUT)
        gains[t] = temps_avec_marge(t, base) - temps_avec_marge(t, lim)
    return gains


def main() -> None:
    d = pd.read_csv(DELIVERABLES / "passages_niveau_tri.csv", sep=";")
    d["km"] = pd.to_numeric(d.km_segment, errors="coerce")
    d["vitesse_reelle_201_kmh"] = vitesses_reelles(d, PLAFOND_HAUT).round(1)
    d["vitesse_reelle_177_kmh"] = vitesses_reelles(d, PLAFOND_PUBLIE).round(1)
    d["depasserait_177"] = d.vitesse_reelle_201_kmh > PLAFOND_PUBLIE + 0.5
    d["depasse_153_au_plafond"] = d.vitesse_reelle_177_kmh > 153.5
    d["trajet_physique"], d["km_physique"] = d.troncon_principal, d.km
    tronc = (d.troncon_principal == "Ott-TO") & (d.km > KM_BROCKVILLE_OTT)
    d.loc[tronc, "trajet_physique"] = "MTL-TO"
    d.loc[tronc, "km_physique"] = d.km[tronc] + DECALAGE_TRONC_COMMUN
    d[["tc_number", "troncon_principal", "km", "localisation", "acces", "protection", "bande_pendulaire",
       "vitesse_reelle_201_kmh", "vitesse_reelle_177_kmh", "depasserait_177", "depasse_153_au_plafond"]] \
        .to_csv(DELIVERABLES / "passages_vitesse_reelle.csv", sep=";", index=False, encoding="utf-8-sig")

    s = d[d.depasserait_177]
    n_pub, n_pri = int((s.acces == "Public").sum()), int((s.acces == "Private").sum())
    print(f"Bande géométrique 178-201 : {(d.bande_pendulaire == '178-201').sum()} passages")
    print(f"Train réellement au-dessus de 177 km/h : {len(s)} ({n_pub} publics, {n_pri} privés), "
          f"{(n_pub * COUT_PONT + n_pri * COUT_PRIVE) / 1000:.1f} G$")
    sc = d[d.bande_pendulaire != "≤153"]
    print(f"À sceller selon la géométrie : {len(sc)} ; train réellement au-dessus de 153 km/h, au plafond "
          f"de 177 : {int(sc.depasse_153_au_plafond.sum())}")
    vj = pd.to_numeric(d[d.acces == "Public"].vehicules_jour, errors="coerce")
    print(f"Part de la circulation des publics portée par ces {n_pub} passages : "
          f"{pd.to_numeric(s[s.acces == 'Public'].vehicules_jour, errors='coerce').sum() / vj.sum():.1%}")

    t_ctrl = temps_avec_marge("MTL-TO", np.minimum(GRILLES["MTL-TO"][1], PLAFOND_PUBLIE))
    pub = pd.read_csv(DELIVERABLES / "temps_scenario_2.csv", sep=";")
    ref = float(pub[(pub.troncon == "MTL-TO") & (pub.scenario == "pendulaire")
                    & (pub.bande_kmh == int(PLAFOND_PUBLIE))].tbase_sans_marge_min.iloc[0]) * marge_de("MTL-TO")
    assert abs(t_ctrl - ref) < 0.3, (t_ctrl, ref)

    o = troncons_rapides(s)
    assert o.ponts.sum() == n_pub and o.prives.sum() == n_pri, "passages non rattachés à un tronçon"
    o["cumul"] = o.cout_gs.cumsum()
    lignes = []
    for plafond in TRANCHES_GS:
        q = o[o.cumul <= plafond + 1e-9]
        g = minutes_rachetees(q)
        lignes.append({"ouvrages": int(q.ponts.sum() + q.prives.sum()), "ponts_etagement": int(q.ponts.sum()),
                       "passages_prives": int(q.prives.sum()), "cout_gs": round(float(q.cout_gs.sum()), 1),
                       "montreal_quebec_min": round(g["MTL-QC"], 1), "montreal_ottawa_min": round(g["MTL-Ott"], 1),
                       "ottawa_toronto_min": round(g["Ott-TO"], 1), "montreal_toronto_min": round(g["MTL-TO"], 1)})
    c = pd.DataFrame(lignes)
    c.to_csv(DELIVERABLES / "passages_gain_vitesse.csv", sep=";", index=False, encoding="utf-8-sig")
    print("\n" + c.to_string(index=False))
    print("\nÉcrit passages_vitesse_reelle.csv et passages_gain_vitesse.csv.")


if __name__ == "__main__":
    main()

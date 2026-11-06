"""Étape 40 — Le modèle de temps pas à pas, son calage et ses sensibilités.

Trois sorties, toutes lues par la section « Le modèle de temps, étape par étape » du
rapport et par le visualiseur :

  livrables/etapes_temps.csv : le temps de chaque trajet à chaque étape du calcul,
      du tracé jusqu'à la marge. La dernière colonne redonne le temps publié.
  livrables/calage_traction.csv : la formule contre des chronos réels. Deux Class 221
      couplées, réglage 700 ch, 0-60/100/125 mi/h en 60/170/313 s (message de MarkyT
      sur RailForums, anecdotique : ce sont les seules données publiques trouvées).
  livrables/sensibilites_traction.csv : l'effet, en minutes marge comprise, de chaque
      hypothèse de traction.

Configuration publiée : pendulaire, plafond 201 km/h, blocs urbains libres, marge 10 %.
"""
from __future__ import annotations

import importlib.util
import math
import os
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

os.environ["BLOCS_URBAINS"] = "libres"
sys.path.insert(0, str(Path(__file__).parent))
from utils import DELIVERABLES                    # noqa: E402

_spec = importlib.util.spec_from_file_location("m21", Path(__file__).parent / "21_tbase_bande.py")
m21 = importlib.util.module_from_spec(_spec)
sys.modules["m21"] = m21
_spec.loader.exec_module(m21)

MARGE = 1.10
SCENARIO, BANDE = "S2", 201.0
LIBELLES = {"MTL-QC": "Montréal-Québec", "MTL-Ott": "Montréal-Ottawa",
            "Ott-TO": "Ottawa-Toronto", "MTL-TO": "Montréal-Toronto"}
BY_T = m21.load_segments()
R = m21.RAME_PENDULAIRE
# Médianes des horaires de VIA par gare, là où elles diffèrent de 2 min (GTFS, 2026).
ARRETS_GTFS = {"Dorval": 4, "Kingston": 4, "Fallowfield": 4, "Belleville": 3, "Oshawa": 3,
               "Sainte-Foy": 3, "Coteau": 1, "Casselman": 1, "Napanee": 1.5}


def fluide(t: str, pieces) -> float:
    """Minutes si le train roulait partout à la vitesse permise, sans jamais accélérer."""
    return sum((b - a) / v * 60.0 for a, b, v in pieces)


def temps(t: str, rame=R, bande=BANDE, scen=SCENARIO, arrets=None, insuffisance_mm=152) -> float:
    """Minutes, marge comprise, pour une rame donnée. Dévers de 127 mm ; v varie comme
    la racine de (dévers + insuffisance)."""
    segs = BY_T[t]
    if insuffisance_mm != 152:
        f = math.sqrt((127 + insuffisance_mm) / (127 + 152))
        segs = [dict(p, **{f"vmax_{scen}_kmh": p[f"vmax_{scen}_kmh"] * f}) for p in segs]
    inter = m21._dynamic_minutes(t, m21._free_pieces(t, segs, scen, bande), rame)
    immob = sum((arrets or {}).get(n, m21.DWELL_MIN) for n, _ in m21.INTERMEDIATE_STOPS[t])
    return (inter + immob) * MARGE


def etapes() -> pd.DataFrame:
    rows = []
    for t, lib in LIBELLES.items():
        segs = BY_T[t]
        libres = m21._free_pieces(t, segs, SCENARIO, 999.0)
        plafond = m21._free_pieces(t, segs, SCENARIO, BANDE)
        n = len(m21.INTERMEDIATE_STOPS[t])
        immobile = n * m21.DWELL_MIN
        reel = m21._dynamic_minutes(t, plafond, R) + immobile
        rows.append({"trajet": lib, "distance_km": round(max(b for _, b, _ in libres), 1),
                     "n_arrets": n,
                     "vitesse_des_courbes_min": round(fluide(t, libres), 1),
                     "plafond_201_min": round(fluide(t, plafond), 1),
                     "immobilisation_en_gare_min": round(fluide(t, plafond) + immobile, 1),
                     "vrai_train_min": round(reel, 1),
                     "marge_10_pct_min": round(reel * MARGE, 1)})
    return pd.DataFrame(rows)


def chrono(acc, cibles_mph=(60, 100, 125)) -> dict[int, float]:
    """Départ arrêté, en palier : secondes pour atteindre chaque vitesse."""
    v, t, out, cibles = 0.5, 0.0, {}, list(cibles_mph)
    while cibles and t < 2000:
        a = acc(v)
        if a <= 0:
            break
        v += a * 0.1
        t += 0.1
        while cibles and v >= cibles[0] * 0.44704:
            out[cibles.pop(0)] = round(t)
    return out


def calage() -> pd.DataFrame:
    double_221 = m21.Rame("deux Class 221 couplées, réglage 700 ch", p_kw=5220, m_t=564, hotel_kw=200,
                          rendement=0.88, cda_m2=18.0, longueur_m=232, a0=0.6, ab=0.6, charge=1.0)
    pm = 5220 / 564
    cas = [("Chronos relevés", {60: 60, 100: 170, 125: 313}),
           ("Ancienne formule, sans résistance", chrono(lambda v: min(0.6, pm / v))),
           ("Formule calée", chrono(double_221.acceleration))]
    return pd.DataFrame([{"cas": n, "0_60_mph_s": c[60], "0_100_mph_s": c[100], "0_125_mph_s": c[125]}
                         for n, c in cas])


def sensibilites() -> pd.DataFrame:
    ref = {t: temps(t) for t in LIBELLES}
    # Configurations réalistes en Amérique du Nord : voiture Venture (50,8 t) plus environ
    # 10 t de pendulation (écart par voiture entre les Class 220 et 221), Charger 120 t.
    voiture = 50.8 + 10.0
    pendolino = m21.Rame("Pendolino électrique", p_kw=5160, m_t=466, hotel_kw=0, rendement=0.95,
                         cda_m2=16.0, longueur_m=215, a0=0.6, ab=0.6)
    un = m21.Rame("1 Charger + 5 voitures pendulaires", p_kw=3132, m_t=120 + 5 * voiture, hotel_kw=200,
                  rendement=0.88, cda_m2=13.0, longueur_m=152, a0=0.6, ab=0.6)
    deux = m21.Rame("2 Charger + 5 voitures pendulaires", p_kw=6264, m_t=240 + 5 * voiture, hotel_kw=200,
                    rendement=0.88, cda_m2=15.0, longueur_m=174, a0=0.6, ab=0.6)
    cas = [
        ("Traînée plus faible (9 m²)", dict(rame=replace(R, cda_m2=9.0))),
        ("Traînée plus forte (14 m²)", dict(rame=replace(R, cda_m2=14.0))),
        ("Grand froid : services de bord à 400 kW", dict(rame=replace(R, hotel_kw=400))),
        ("Freinage à 0,5 m/s²", dict(rame=replace(R, ab=0.5))),
        ("Freinage à 0,8 m/s²", dict(rame=replace(R, ab=0.8))),
        ("Accélération maximale à 0,5 m/s²", dict(rame=replace(R, a0=0.5))),
        ("Accélération maximale à 0,8 m/s²", dict(rame=replace(R, a0=0.8))),
        ("Rendement de 0,85", dict(rame=replace(R, rendement=0.85))),
        ("Rendement de 0,90", dict(rame=replace(R, rendement=0.90))),
        ("Train diesel de 8,4 W/kg, même masse", dict(rame=replace(R, p_kw=8.4 * 282))),
        ("Train diesel de 12 W/kg, même masse (n'existe pas)", dict(rame=replace(R, p_kw=12 * 282))),
        ("Arrêts à la médiane des horaires, gare par gare", dict(arrets=ARRETS_GTFS)),
        ("Train électrique de type Pendolino, corridor électrifié", dict(rame=pendolino)),
        ("Une locomotive Charger et 5 voitures pendulaires (7,4 W/kg)", dict(rame=un)),
        ("Deux locomotives Charger et 5 voitures pendulaires (11,5 W/kg)", dict(rame=deux)),
        ("Tolérance en courbe de 5 po", dict(insuffisance_mm=127)),
        ("Tolérance en courbe de 7 po", dict(insuffisance_mm=178)),
        ("Bas combiné : une locomotive, 5 po", dict(rame=un, insuffisance_mm=127)),
        ("Haut combiné : deux locomotives, 7 po", dict(rame=deux, insuffisance_mm=178)),
    ]
    rows = []
    for nom, k in cas:
        ligne = {"cas": nom}
        for t, lib in LIBELLES.items():
            ligne[f"{lib}_min"] = round(temps(t, **k), 1)
            ligne[f"{lib}_ecart_min"] = round(temps(t, **k) - ref[t], 1)
        rows.append(ligne)
    return pd.DataFrame(rows)


def main() -> None:
    e = etapes()
    e.to_csv(DELIVERABLES / "etapes_temps.csv", sep=";", index=False, encoding="utf-8-sig")
    print(e.to_string(index=False))
    pub = pd.read_csv(DELIVERABLES / "temps_scenario_2.csv", sep=";")
    for t, lib in LIBELLES.items():
        ref = pub[(pub.troncon == t) & (pub.scenario == "pendulaire") & (pub.bande_kmh == 201)]
        attendu = float(ref.tbase_sans_marge_min.iloc[0])
        obtenu = float(e[e.trajet == lib].vrai_train_min.iloc[0])
        assert abs(attendu - obtenu) < 0.15, (t, attendu, obtenu)

    c = calage()
    c.to_csv(DELIVERABLES / "calage_traction.csv", sep=";", index=False, encoding="utf-8-sig")
    print("\n" + c.to_string(index=False))

    s = sensibilites()
    s.to_csv(DELIVERABLES / "sensibilites_traction.csv", sep=";", index=False, encoding="utf-8-sig")
    cols = ["cas"] + [c for c in s.columns if c.endswith("ecart_min")]
    print("\n" + s[cols].to_string(index=False))

    # Le prix de Kingston : l'express Montréal-Toronto avec ce seul arrêt.
    t = "MTL-TO"
    arrets, sauve = [("Kingston", dict(m21.INTERMEDIATE_STOPS[t])["Kingston"])], m21.INTERMEDIATE_STOPS[t]
    m21.INTERMEDIATE_STOPS[t] = []
    sans = temps(t)
    m21.INTERMEDIATE_STOPS[t] = arrets
    avec = temps(t)
    m21.INTERMEDIATE_STOPS[t] = sauve
    print(f"\nExpress Montréal-Toronto : sans arrêt {sans:.1f}, avec Kingston {avec:.1f} (+{avec - sans:.1f})")
    print(f"Rame de référence : {R.p_kw / R.m_t:.1f} W/kg nominaux, {R.p_rail_w / 1e3:.0f} kW au rail "
          f"({R.p_rail_w / 1e3 / R.m_t:.1f} W/kg), équilibre {R.vitesse_equilibre_kmh():.0f} km/h")
    a = m21.RAME_ACTUELLE
    print(f"Rame actuelle : {a.p_kw / a.m_t:.1f} W/kg nominaux, {a.p_rail_w / 1e3:.0f} kW au rail, "
          f"équilibre {a.vitesse_equilibre_kmh():.0f} km/h")


if __name__ == "__main__":
    main()

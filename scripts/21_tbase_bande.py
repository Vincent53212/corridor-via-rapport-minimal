"""Étape 21 — Moteur T_base : temps de parcours par bande de vitesse × scénario.

Le modèle du rapport minimal (plan de match v3) :

    T(bande, scénario) = Σ blocs urbains figés (minutes actuelles GTFS)
                       + interurbain en PROFIL DYNAMIQUE (2026-08-08) : vitesse
                         limitée par min(v_geo_scenario(x), bande), accélération
                         limitée par la puissance au rail, la résistance et la
                         pente (classe Rame), freinage constant, arrêt
                         complet (v=0) à chaque gare intermédiaire et aux
                         frontières des blocs urbains
                       + arrêts (immobilisation DWELL_MIN par arrêt interurbain ;
                         les phases d'accélération/freinage sont dans le profil)
                       [+ marge — encadrée à l'étape 4, PAS ajoutée ici]

Paramètres de rame (décision Vincent du 2026-11-05, « la licorne ») :
  Les 12 W/kg d'avant venaient de pendulaires ÉLECTRIQUES (ICE T, Class 390, ETR 610),
  alors que le corridor n'est pas électrifié. Et l'ancienne formule a = min(a0, (P/m)/v)
  n'avait ni résistance ni pente : contre les chronos d'une Class 221 réelle
  (0-60/100/125 mi/h en 60/170/313 s) elle donnait 51/120/181 s.
  S2 et S3 : rame pendulaire DIESEL-ÉLECTRIQUE de 9,8 W/kg nominaux (282 t, 2 764 kW),
  entre la Class 221 (9,9) et l'ICE TD (9,7), les seuls pendulaires diesel à 200 km/h.
  S1 : Charger + 5 Venture (3 132 kW, 374 t, 8,4 W/kg). Dossier :
  sources/recherche_poids_rames_2026-08-25.md.
  CONVENTION : les W/kg publiés sont NOMINAUX et À VIDE. Le calcul, lui, part de là
  et retire tout ce qui n'arrive pas au rail (classe Rame) :
      a = min(a0, [P_rail / v - R(V) - m g i] / (m * inertie))
      P_rail = (P_nominale - P_hôtel) * rendement
      R(V)   = (A + B V) m + 0,0463 CdA V²     (N, V en km/h, m en t)
  Calage sur les chronos (étape 40) : rendement 0,88, A 12 N/t, B 0,06 N/t/(km/h),
  inertie 1,04, CdA environ 11 m² par rame. Trois chronos pour autant de paramètres :
  la forme tient, chaque valeur reste à confirmer par des courbes de constructeur.
  Services de bord 40 kW par voiture, passagers +6 % de masse.
  La vitesse limite tient jusqu'à ce que la QUEUE du train sorte de la restriction.
  Pentes : relief Copernicus GLO-90 (étape 39), lissé sur 3 km.
  La bande 241 garde la même rame : elle n'y arrive pas, sa puissance la plafonne vers
  230 km/h, et c'est dit au rapport. Bandes 250 et 300 (non publiées) : rames de
  CONCEPTION électriques, 18 et 22 W/kg.
  La bande 201 (125 mi/h) est le plafond des scénarios publiés (remodelage
  2026-08-24) : sommet de la marche du PTC certifié (précédents Brightline,
  NEC) et seuil au-delà duquel la règle américaine interdit tout passage à
  niveau. La bande 177 (110 mi/h, limite ITCS) reste calculée en référence.
  (S2/S3 se définissent par l'insuffisance admise, pas par la motorisation.)

Décision structurante : les zones urbaines sont FIGÉES à l'horaire actuel. Aucun
gain pendulaire/dévers n'y est compté, quel que soit le scénario ou la bande.

Délimitation des blocs urbains (à documenter au rapport) :
  - Montréal (ouest, tronçons MTL-Ott / MTL-TO) : Central ↔ Dorval (17,8 km),
    minutes = médiane GTFS de la paire.
  - Montréal (est, tronçon MTL-QC via pont Victoria) : Central ↔ culée sud du
    pont Victoria (km 5,50, écluse de Saint-Lambert ; 5,5 km). Décision Vincent
    2026-09-06 : le bloc s'arrête au pied du pont, la gare de Saint-Lambert
    (km 6,11) est HORS bloc et redevient un arrêt interurbain (DWELL_MIN, v=0).
    Minutes figées = médiane GTFS de la paire Central ↔ Saint-Lambert, MOINS le
    profil dynamique du train actuel sur le dernier 0,6 km d'arrivée en gare
    (URBAN_BLOCK_TRIM ; c'est exactement ce que le profil interurbain recompte
    ensuite, la somme est donc neutre hors l'immobilisation à Saint-Lambert).
    NB : le plan v3 nommait « Central↔Dorval » ; MTL-QC sort par la rive sud.
  - Toronto : Union ↔ Guildwood (20,2 km), minutes = médiane GTFS. (Le plan v3
    évoquait « Guildwood/Oshawa » ; Guildwood retenu = borne courte, l'inclusion
    jusqu'à Oshawa est couverte par la sensibilité ±20 %.)
  - Québec : Charny ↔ Québec, gare du Palais (24,8 km, inclut le pont de Québec et
    l'arrêt de Sainte-Foy), médiane GTFS. Borne Charny retenue le 2026-09-03 (décision
    Vincent) par symétrie avec Montréal : les deux grands ponts sont dans les blocs
    urbains, figés à l'horaire, jamais roulés à la vitesse de leur courbure.
  - Ottawa : PAS de gare d'approche proche (Casselman à 47 km, Smiths Falls à
    65 km) → fenêtre kilométrique HYPOTHÈSE de ±10 km autour de la gare, traversée
    au plafond S1 borné par la bande (règle « aucun gain en urbain »), pas de
    minutes GTFS isolables. Couverte par la sensibilité ±20 %.

Arrêts : DWELL_MIN (2 min) d'immobilisation par arrêt intermédiaire HORS blocs
urbains ; les phases d'accélération et de freinage sont simulées dans le profil
dynamique (v=0 en gare). Borne mesurée de comparaison : pilote sans-arrêt 2025 =
30-40 min pour 4 arrêts sautés, soit 7,5-10 min par arrêt en conditions réelles de
cohabitation (immobilisation + dynamique + effets de sillon). Les arrêts situés
dans un bloc urbain sont déjà comptés dans les minutes GTFS figées du bloc.

Sensibilité : blocs urbains ±20 % (colonnes lo/hi).

Sorties : livrables/tbase_par_bande.csv (tronçon × scénario × bande) et
livrables/blocs_urbains.csv (délimitation + minutes GTFS mesurées).
La marge (étape 4) s'ajoutera par-dessus : T_base ici = SANS marge.
"""
from __future__ import annotations

import io
import json
import math
import zipfile
from dataclasses import dataclass
from statistics import median

import numpy as np
import pandas as pd

import os
from pathlib import Path

from utils import INTERMEDIATES, DELIVERABLES, RESOURCES, SEGMENTS_PUBLIES_GEOJSON

GTFS_ZIP = RESOURCES / "viarail_GTFS.zip"

# Variante de segments, pour les sensibilités. Sans la variable d'environnement,
# rien ne change : ce sont les segments PUBLIÉS (correction des courbes courtes
# de l'étape 34 incluse) et les livrables habituels. Avec elle, les sorties sont
# suffixées pour que la variante ne puisse jamais écraser la référence.
_OVERRIDE = os.environ.get("SEGMENTS_OVERRIDE", "")
SEGMENTS = Path(_OVERRIDE) if _OVERRIDE else SEGMENTS_PUBLIES_GEOJSON
_SUF = "_" + Path(_OVERRIDE).stem.replace("segments_", "") if _OVERRIDE else ""
# Sensibilité « blocs urbains réintégrés » (2026-08-17) : avec BLOCS_URBAINS=libres,
# les blocs urbains ne sont plus figés à l'horaire GTFS — ils entrent dans le
# profil dynamique comme le reste du tracé (leurs gares deviennent des arrêts
# interurbains à DWELL_MIN). Sorties suffixées : jamais d'écrasement de la
# référence. Le chiffre principal du rapport reste : blocs FIGÉS.
_BLOCS_LIBRES = os.environ.get("BLOCS_URBAINS", "") == "libres"
if _BLOCS_LIBRES:
    _SUF += "_blocs_libres"
# Nommage PUBLIC (remodelage du 24 août) : les trois runs qui portent l'échelle
# publiée « scénario 1 / 2 / 3 » écrivent les CSV de PALIERS (scenarios.py) ;
# toute autre combinaison garde le schéma suffixé des sensibilités.
_PALIER_CSV = {
    ("", False): "temps_scenario_1.csv",
    ("", True): "temps_scenario_2.csv",
    ("segments_rectifies.geojson", True): "temps_scenario_3.csv",
}.get((Path(_OVERRIDE).name if _OVERRIDE else "", _BLOCS_LIBRES))
OUT_TBASE = DELIVERABLES / (_PALIER_CSV or f"tbase_par_bande{_SUF}.csv")
OUT_BLOCS = DELIVERABLES / f"blocs_urbains{_SUF}.csv"
if _OVERRIDE or _BLOCS_LIBRES:
    print(f"VARIANTE : segments lus dans {SEGMENTS}, sortie {OUT_TBASE.name}")

BANDES_KMH = [153, 160, 177, 201, 241, 250, 300]   # 153 = classe actuelle (95 mi/h), lue par le 32
# 241 (150 mi/h) = sensibilité « zéro passage à niveau » : plafond prouvé du
# NEC d'Amtrak (ACSES + cab signals, fra2010ptc) une fois le mur des passages
# levé. Même rame pendulaire : sa puissance la plafonne vers 230 km/h.
DWELL_MIN = 2.0               # immobilisation en gare (min/arrêt) ; la dynamique
                              # d'accélération/freinage est dans le profil simulé
URBAN_SENS = 0.20             # sensibilité ±20 % sur les blocs urbains
OTTAWA_WINDOW_KM = 10.0       # HYPOTHÈSE : fenêtre urbaine ±10 km autour d'Ottawa
DX_M = 25.0                   # pas d'intégration du profil dynamique (m)
CONTIG_TOL_KM = 0.05          # tolérance de contiguïté entre segments (50 m)
G = 9.81                      # m/s²


@dataclass(frozen=True)
class Rame:
    """Une rame et tout ce que la formule d'accélération lui demande (voir docstring)."""
    nom: str
    p_kw: float                 # puissance nominale (moteur thermique, ou traction si électrique)
    m_t: float                  # masse à vide (t)
    hotel_kw: float             # services de bord, pris sur la même puissance
    rendement: float            # de la puissance nette à la puissance au rail
    cda_m2: float               # surface de traînée (coefficient × section)
    longueur_m: float           # la queue doit sortir d'une restriction avant de relancer
    a0: float                   # plafond d'accélération (m/s²)
    ab: float                   # freinage de service (m/s²)
    charge: float = 1.06        # passagers : +6 % de masse
    inertie: float = 1.04       # masses tournantes
    a_n_t: float = 12.0         # résistance de roulement constante (N/t)
    b_n_t: float = 0.06         # résistance de roulement proportionnelle à V (N/t par km/h)

    @property
    def p_rail_w(self) -> float:
        return (self.p_kw - self.hotel_kw) * 1e3 * self.rendement

    @property
    def m_kg(self) -> float:
        return self.m_t * 1e3 * self.charge

    def resistance_n(self, v_kmh: float) -> float:
        mt = self.m_t * self.charge
        return (self.a_n_t + self.b_n_t * v_kmh) * mt + 0.0463 * self.cda_m2 * v_kmh * v_kmh

    def acceleration(self, v: float, pente: float = 0.0) -> float:
        """m/s² à la vitesse v (m/s), pente i en m/m ; négative si la rame ne tient plus."""
        m = self.m_kg
        force = self.p_rail_w / v - self.resistance_n(v * 3.6) - m * G * pente
        return min(self.a0, force / (m * self.inertie))

    def vitesse_equilibre_kmh(self) -> float:
        """Vitesse maximale en palier : la puissance au rail égale la résistance."""
        v = 30.0
        while v < 150.0 and self.p_rail_w / v > self.resistance_n(v * 3.6):
            v += 0.1
        return v * 3.6


RAME_ACTUELLE = Rame("Charger + 5 Venture", p_kw=3132, m_t=374, hotel_kw=200, rendement=0.88,
                     cda_m2=13.0, longueur_m=152, a0=0.5, ab=0.5)
RAME_PENDULAIRE = Rame("pendulaire diesel-électrique de référence", p_kw=9.8 * 282, m_t=282, hotel_kw=200,
                       rendement=0.88, cda_m2=11.0, longueur_m=116, a0=0.6, ab=0.6)
# Rames de conception électriques, bandes non publiées.
RAME_250 = Rame("conception 250 km/h, électrique", p_kw=18 * 400, m_t=400, hotel_kw=0, rendement=0.95,
                cda_m2=16.0, longueur_m=200, a0=0.6, ab=0.6)
RAME_300 = Rame("conception 300 km/h, électrique", p_kw=22 * 400, m_t=400, hotel_kw=0, rendement=0.95,
                cda_m2=16.0, longueur_m=200, a0=0.6, ab=0.6)


def rame_de(scenario: str, bande: float) -> Rame:
    if scenario == "S1":
        return RAME_ACTUELLE
    return {250: RAME_250, 300: RAME_300}.get(int(bande), RAME_PENDULAIRE)


_PENTES: dict[str, tuple[np.ndarray, np.ndarray]] = {}


def pentes(t: str) -> tuple[np.ndarray, np.ndarray]:
    """(km, pente en m/m) du tronçon, relief de l'étape 39 lissé sur 3 km."""
    if t not in _PENTES:
        d = json.load(open(INTERMEDIATES / f"relief_{t}.json", encoding="utf-8"))
        km, z = np.array(d["km"]), np.array(d["z"])
        n = len(z)
        med = np.array([np.median(z[max(0, i - 2):min(n, i + 3)]) for i in range(n)])
        lisse = np.convolve(np.pad(med, 3, mode="edge"), np.ones(7) / 7, mode="valid")
        _PENTES[t] = km, np.gradient(lisse, km * 1000.0)
    return _PENTES[t]


# Blocs urbains ancrés sur des paires de gares GTFS : (tronçon, stop_id A, stop_id B,
# nom, km_debut, km_fin). km relevés dans corridor_gtfs.geojson.
URBAN_GTFS_BLOCKS = [
    ("MTL-QC",  "226", "343", "Montréal Central ↔ pont Victoria (culée sud)",     0.0, 5.50),
    ("MTL-QC",  "492", "628", "Charny ↔ Québec (pont de Québec, gare du Palais)",  245.04, 269.85),
    ("MTL-Ott", "226", "332", "Montréal Central ↔ Dorval",                        0.0, 17.79),
    ("Ott-TO",  "450", "119", "Guildwood ↔ Toronto Union",                        423.93, 444.05),
    ("MTL-TO",  "226", "332", "Montréal Central ↔ Dorval",                        0.0, 17.79),
    ("MTL-TO",  "450", "119", "Guildwood ↔ Toronto Union",                        517.94, 538.06),
]
# Blocs dont l'emprise est plus courte que la paire GTFS qui donne leurs minutes :
# (tronçon, stop A, stop B) → (km_bloc_fin, km_gare_B). Les minutes figées sont
# la médiane GTFS moins le profil dynamique S1 (plafond 153) sur [km_bloc_fin,
# km_gare_B], v=0 aux deux bouts (fin de bloc, arrivée en gare).
URBAN_BLOCK_TRIM = {
    ("MTL-QC", "226", "343"): (5.50, 6.11),   # culée sud du pont Victoria → gare de Saint-Lambert
}
# Blocs urbains sans ancre GTFS : fenêtre km, traversée au plafond du scénario de base ∧ bande.
URBAN_KM_BLOCKS = [
    ("MTL-Ott", "Ottawa (approche est, fenêtre ±10 km — HYPOTHÈSE)", 175.42, 185.42),
    ("Ott-TO",  "Ottawa (approche ouest, fenêtre ±10 km — HYPOTHÈSE)", 0.0, 10.0),
]
if _BLOCS_LIBRES:               # sensibilité : plus aucun bloc figé
    URBAN_GTFS_BLOCKS = []
    URBAN_KM_BLOCKS = []

# Gares intermédiaires par tronçon (hors extrémités), avec leur km — pour compter
# les arrêts interurbains (hors blocs urbains). Règle (ronde UPA, 2026-11-02, décision
# Vincent) : toutes les gares où s'arrête aujourd'hui au moins un train VIA de CE
# trajet (GTFS), pas plus. Montréal-Toronto : + Cornwall (desservie par 12 trains sur
# 12), − Gananoque, Napanee, Trenton Junction et Port Hope (desservies par les trains
# d'Ottawa, aucun Montréal-Toronto) ; Ottawa-Toronto : + Fallowfield (21 sur 21).
# km projetés sur le tracé (segments_publies). L'Aéroport (555) est une desserte
# alternative de Dorval, non comptée en plus.
INTERMEDIATE_STOPS = {
    "MTL-QC":  [("Saint-Lambert", 6.11), ("Saint-Hyacinthe", 53.24), ("Drummondville", 100.01),
                ("Charny", 245.04), ("Sainte-Foy", 249.98)],
    "MTL-Ott": [("Dorval", 17.79), ("Coteau", 62.28), ("Alexandria", 99.43), ("Casselman", 138.78)],
    "Ott-TO":  [("Fallowfield", 15.13), ("Smiths Falls", 64.62), ("Brockville", 110.0), ("Gananoque", 155.83),
                ("Kingston", 191.99), ("Napanee", 227.49), ("Belleville", 262.44),
                ("Trenton Junction", 281.92), ("Cobourg", 332.06), ("Port Hope", 342.88),
                ("Oshawa", 393.31), ("Guildwood", 423.93)],
    "MTL-TO":  [("Dorval", 17.79), ("Cornwall", 110.95), ("Brockville", 204.72),
                ("Kingston", 285.97), ("Belleville", 356.42), ("Cobourg", 426.05),
                ("Oshawa", 487.24), ("Guildwood", 517.94)],
}

TRONCONS = ["MTL-QC", "MTL-Ott", "Ott-TO", "MTL-TO"]
# Extrémités (stop_id) pour le T_horaire actuel de référence.
ENDPOINTS = {"MTL-QC": ("226", "628"), "MTL-Ott": ("226", "617"),
             "Ott-TO": ("617", "119"), "MTL-TO": ("226", "119")}


# ----------------------------------------------------------------- GTFS
def _hms_to_min(s: str) -> float:
    h, m, sec = s.split(":")
    return int(h) * 60 + int(m) + int(sec) / 60.0


def load_gtfs_pair_minutes() -> tuple[dict, dict]:
    """Minutes médianes à l'horaire entre paires de gares, tous sillons confondus.

    Retourne (pair_minutes, endpoint_minutes) :
      pair_minutes[(A, B)] = médiane des (arrivée B − départ A) sur les voyages
      desservant A puis B (dans les deux sens : (A,B) et (B,A) agrégés, la
      géométrie étant la même).
    """
    with zipfile.ZipFile(GTFS_ZIP) as z:
        st = pd.read_csv(io.BytesIO(z.read("stop_times.txt")),
                         dtype={"trip_id": str, "stop_id": str})
    st = st.sort_values(["trip_id", "stop_sequence"])

    wanted_pairs = {(a, b) for _, a, b, *_ in URBAN_GTFS_BLOCKS} | set(ENDPOINTS.values())
    wanted_stops = {s for p in wanted_pairs for s in p}

    samples: dict[tuple[str, str], list[float]] = {p: [] for p in wanted_pairs}
    sub = st[st.stop_id.isin(wanted_stops)]
    for _, g in sub.groupby("trip_id"):
        seq = list(zip(g.stop_id, g.departure_time, g.arrival_time))
        pos = {sid: i for i, (sid, _, _) in enumerate(seq)}
        for (a, b) in wanted_pairs:
            lo, hi = (a, b) if pos.get(a, 9e9) < pos.get(b, -1) else (b, a)
            if a in pos and b in pos and pos[lo] < pos[hi]:
                dep = seq[pos[lo]][1]
                arr = seq[pos[hi]][2]
                if isinstance(dep, str) and isinstance(arr, str):
                    dt = _hms_to_min(arr) - _hms_to_min(dep)
                    if 0 < dt < 24 * 60:
                        samples[(a, b)].append(dt)

    pair_minutes = {p: (median(v) if v else None) for p, v in samples.items()}
    endpoint_minutes = {t: pair_minutes.get(ENDPOINTS[t]) for t in TRONCONS}
    return pair_minutes, endpoint_minutes


# ----------------------------------------------------------------- segments
def load_segments() -> dict[str, list[dict]]:
    gj = json.load(open(SEGMENTS, encoding="utf-8"))
    by_t: dict[str, list[dict]] = {}
    for f in gj["features"]:
        p = f["properties"]
        by_t.setdefault(p["troncon_id"], []).append(p)
    for t in by_t:
        by_t[t].sort(key=lambda p: p["km_debut"])
    return by_t


def in_any_block(t: str, km0: float, km1: float, blocks) -> float:
    """Longueur (km) du recouvrement de [km0,km1] avec les blocs urbains du tronçon."""
    ov = 0.0
    for b in blocks:
        if b[0] != t:
            continue
        lo, hi = b[-2], b[-1]
        ov += max(0.0, min(km1, hi) - max(km0, lo))
    return ov


# ----------------------------------------------------------------- moteur
def _free_pieces(t: str, segs: list[dict], scenario: str, bande: float):
    """[(km0, km1, vlim_kmh)] hors blocs urbains (GTFS et fenêtres km), triés."""
    blocks = [(b[-2], b[-1]) for b in URBAN_GTFS_BLOCKS + URBAN_KM_BLOCKS if b[0] == t]
    out = []
    for p in segs:
        pieces = [(p["km_debut"], p["km_fin"])]
        for lo, hi in blocks:
            nxt = []
            for a, b in pieces:
                if hi <= a or lo >= b:
                    nxt.append((a, b))
                else:
                    if a < lo:
                        nxt.append((a, lo))
                    if hi < b:
                        nxt.append((hi, b))
            pieces = nxt
        v = min(p[f"vmax_{scenario}_kmh"], bande)
        for a, b in pieces:
            if b - a > 1e-6:
                out.append((a, b, v))
    out.sort()
    return out


def troncons_contigus(pieces) -> list[list[tuple[float, float, float]]]:
    """Regroupe les morceaux libres en tronçons continus."""
    stretches: list[list[tuple[float, float, float]]] = []
    for seg in pieces:
        if stretches and abs(seg[0] - stretches[-1][-1][1]) < CONTIG_TOL_KM:
            stretches[-1].append(seg)
        else:
            stretches.append([seg])
    return stretches


def profil_vitesse(t: str, stretch, rame: Rame):
    """Profil deux passes (accélération, freinage) sur un tronçon continu, v=0 aux
    gares intermédiaires et aux deux bouts. Retourne (xs km, v m/s, dx m, indices d'arrêt)."""
    k0, k1 = stretch[0][0], stretch[-1][1]
    n = max(2, int((k1 - k0) * 1000 / DX_M) + 1)
    xs = [k0 + (k1 - k0) * i / (n - 1) for i in range(n)]
    dx = (k1 - k0) * 1000 / (n - 1)
    vlim = []
    j = 0
    for x in xs:
        while j < len(stretch) - 1 and x > stretch[j][1] + 1e-9:
            j += 1
        vlim.append(stretch[j][2] / 3.6)
    w = int(round(rame.longueur_m / dx))      # la queue du train doit sortir de la restriction
    if w > 0:
        vlim = [min(vlim[max(0, i - w):i + 1]) for i in range(n)]
    zero_at = {0, n - 1}
    for (_, skm) in INTERMEDIATE_STOPS[t]:
        if k0 - 1e-6 <= skm <= k1 + 1e-6:
            zero_at.add(min(range(n), key=lambda i: abs(xs[i] - skm)))
    i_pente = np.interp(xs, *pentes(t))
    v = vlim[:]
    for i in zero_at:
        v[i] = 0.0
    for i in range(1, n):
        if i in zero_at:
            v[i] = 0.0
            continue
        a = rame.acceleration(max(v[i - 1], 1.0), float(i_pente[i]))
        v[i] = min(vlim[i], math.sqrt(max(v[i - 1] ** 2 + 2 * a * dx, 1.0)), v[i])
    for i in range(n - 2, -1, -1):
        if i in zero_at:
            continue
        v[i] = min(v[i], math.sqrt(v[i + 1] ** 2 + 2 * rame.ab * dx))
    return xs, v, dx, zero_at


def _dynamic_minutes(t: str, pieces, rame: Rame) -> float:
    """Minutes de roulement sur les tronçons libres (sans immobilisation en gare)."""
    total_s = 0.0
    for stretch in troncons_contigus(pieces):
        _, v, dx, _ = profil_vitesse(t, stretch, rame)
        for i in range(len(v) - 1):
            total_s += dx / max((v[i] + v[i + 1]) / 2, 0.5)
    return total_s / 60.0


def integrate(t: str, segs: list[dict], scenario: str, bande: float) -> tuple[float, float]:
    """(minutes interurbain en profil dynamique, minutes fenêtres Ottawa).

    Interurbain : profil dynamique (accélération limitée par la puissance,
    freinage constant) sur v_lim = min(v_geo_scenario, bande), arrêt complet aux
    gares intermédiaires ; paramètres de rame par scénario (rame_de).
    Fenêtres km urbaines (Ottawa) : dx / min(v_geo_S1, bande), fluide — aucun
    gain de scénario. Blocs urbains GTFS exclus (minutes à l'horaire).
    """
    inter_min = _dynamic_minutes(t, _free_pieces(t, segs, scenario, bande), rame_de(scenario, bande))
    urb_km = [b for b in URBAN_KM_BLOCKS if b[0] == t]
    ottawa_min = 0.0
    for p in segs:
        km0, km1 = p["km_debut"], p["km_fin"]
        ov_km = in_any_block(t, km0, km1, urb_km)
        v_s1 = min(p["vmax_S1_kmh"], bande)
        if ov_km > 0 and v_s1 > 0:
            ottawa_min += ov_km / v_s1 * 60.0
    return inter_min, ottawa_min


def bloc_minutes_figees(pair_minutes, by_t, block) -> float:
    """Minutes figées d'un bloc GTFS : médiane de la paire, moins l'approche de
    gare hors bloc (URBAN_BLOCK_TRIM), roulée au profil du train actuel."""
    t, a, b, _name, _km0, _km1 = block
    m = pair_minutes[(a, b)]
    trim = URBAN_BLOCK_TRIM.get((t, a, b))
    if trim:
        k0, k1 = trim
        pieces = []
        for p in by_t[t]:
            lo, hi = max(p["km_debut"], k0), min(p["km_fin"], k1)
            if hi - lo > 1e-6:
                pieces.append((lo, hi, min(p["vmax_S1_kmh"], 153.0)))
        pieces.sort()
        saved = INTERMEDIATE_STOPS[t]
        INTERMEDIATE_STOPS[t] = []           # v=0 aux bouts du morceau suffit
        try:
            m -= _dynamic_minutes(t, pieces, RAME_ACTUELLE)
        finally:
            INTERMEDIATE_STOPS[t] = saved
    return m


def main() -> None:
    pair_minutes, endpoint_minutes = load_gtfs_pair_minutes()
    by_t = load_segments()

    # --- blocs urbains : minutes GTFS figées
    bloc_rows = []
    urban_fixed: dict[str, float] = {t: 0.0 for t in TRONCONS}
    for blk in URBAN_GTFS_BLOCKS:
        (t, a, b, name, km0, km1) = blk
        m = bloc_minutes_figees(pair_minutes, by_t, blk)
        urban_fixed[t] += m
        bloc_rows.append({"troncon": t, "bloc": name, "km_debut": km0, "km_fin": km1,
                          "longueur_km": round(km1 - km0, 1),
                          "minutes_gtfs_mediane": round(m, 1),
                          "source": "SOURCE : GTFS VIA (médiane des sillons)"
                          + (" moins l'approche de gare hors bloc au profil du train actuel"
                             if (t, a, b) in URBAN_BLOCK_TRIM else "")})
    for (t, name, km0, km1) in URBAN_KM_BLOCKS:
        bloc_rows.append({"troncon": t, "bloc": name, "km_debut": km0, "km_fin": km1,
                          "longueur_km": round(km1 - km0, 1),
                          "minutes_gtfs_mediane": "",
                          "source": "HYPOTHÈSE : fenêtre km, traversée au plafond du scénario de base ∧ bande"})

    # --- arrêts interurbains (hors blocs urbains)
    stops_inter: dict[str, int] = {}
    for t in TRONCONS:
        blocks = URBAN_GTFS_BLOCKS + URBAN_KM_BLOCKS
        n = 0
        for (_, km) in INTERMEDIATE_STOPS[t]:
            if in_any_block(t, km - 1e-6, km + 1e-6, [b for b in blocks if b[0] == t]) > 0:
                continue
            n += 1
        stops_inter[t] = n

    # --- table T_base
    rows = []
    for t in TRONCONS:
        for scen in ("S1", "S2", "S3"):
            for bande in BANDES_KMH:
                inter, ottawa = integrate(t, by_t[t], scen, float(bande))
                urb = urban_fixed[t]
                stops = stops_inter[t] * DWELL_MIN
                total = urb + ottawa + inter + stops
                rows.append({
                    "troncon": t, "scenario": scen, "bande_kmh": bande,
                    "urbain_gtfs_min": round(urb, 1),
                    "urbain_fenetre_min": round(ottawa, 1),
                    "interurbain_min": round(inter, 1),
                    "arrets_min": round(stops, 1),
                    "n_arrets_interurbains": stops_inter[t],
                    "tbase_sans_marge_min": round(total, 1),
                    "tbase_lo_min": round(total - URBAN_SENS * (urb + ottawa), 1),
                    "tbase_hi_min": round(total + URBAN_SENS * (urb + ottawa), 1),
                    "t_horaire_actuel_min": round(endpoint_minutes[t], 1),
                })

    from scenarios import public_id
    df = pd.DataFrame(rows)
    df["scenario"] = df["scenario"].map(public_id)   # livrable = nomenclature publique
    pd.DataFrame(bloc_rows).to_csv(OUT_BLOCS, sep=";", index=False, encoding="utf-8-sig")
    df.to_csv(OUT_TBASE, sep=";", index=False, encoding="utf-8-sig")

    print("=== Étape 21 — T_base par bande × scénario (SANS marge) ===\n")
    print(f"{'tronçon':<8} {'scén':<4} {'bande':>5}  {'urbain':>6} {'fenêtre':>7} "
          f"{'inter':>6} {'arrêts':>6}  {'T_base':>6}  {'horaire actuel':>14}")
    for r in rows:
        print(f"{r['troncon']:<8} {r['scenario']:<4} {r['bande_kmh']:>5}  "
              f"{r['urbain_gtfs_min']:>6} {r['urbain_fenetre_min']:>7} "
              f"{r['interurbain_min']:>6} {r['arrets_min']:>6}  "
              f"{r['tbase_sans_marge_min']:>6}  {r['t_horaire_actuel_min']:>14}")
    print(f"\nÉcrit {OUT_TBASE.name} ({len(rows)} lignes) et {OUT_BLOCS.name}.")
    print("Rappel : T_base = SANS marge ; l'encadrement de la marge vient de l'étape 4.")


if __name__ == "__main__":
    main()

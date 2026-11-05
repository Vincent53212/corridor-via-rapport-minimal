"""Étape 39 — Relief le long des quatre trajets (une fois, résultat versionné).

Un point aux 500 m sur le tracé publié, altitude du modèle numérique de terrain
Copernicus GLO-90 servie par l'API Open-Meteo. Le moteur (étape 21) en tire la
pente, lissée sur 3 km : la médiane sur 2 km retire les creux de vallée sous les
ponts, la moyenne sur 3 km retire le bruit du modèle de terrain.

Le service compte 100 points pour 100 appels et plafonne à 600 appels par minute :
une requête de 100 points aux 12 secondes, avec reprise sur fichier partiel.

Sorties : intermediaires/relief_<tronçon>.json (km, altitude en m).
"""
from __future__ import annotations

import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request

import numpy as np

from utils import INTERMEDIATES, SEGMENTS_PUBLIES_GEOJSON

TRONCONS = ["MTL-QC", "MTL-Ott", "Ott-TO", "MTL-TO"]
PAS_KM = 0.5


def echantillons(feats) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Points aux 500 m : km, longitude, latitude, interpolés le long des segments."""
    K, LO, LA = [], [], []
    for x in feats:
        c = np.array(x["geometry"]["coordinates"])[:, :2]
        d = np.r_[0, np.cumsum(np.hypot(np.diff(c[:, 0]) * math.cos(math.radians(c[:, 1].mean())),
                                        np.diff(c[:, 1])))]
        p = x["properties"]
        K += list(p["km_debut"] + (p["km_fin"] - p["km_debut"]) * d / max(d[-1], 1e-12))
        LO += list(c[:, 0])
        LA += list(c[:, 1])
    K, LO, LA = np.array(K), np.array(LO), np.array(LA)
    o = np.argsort(K)
    K, LO, LA = K[o], LO[o], LA[o]
    ech = np.arange(K[0], K[-1], PAS_KM)
    return ech, np.interp(ech, K, LO), np.interp(ech, K, LA)


def main() -> None:
    gj = json.load(open(SEGMENTS_PUBLIES_GEOJSON, encoding="utf-8"))
    for t in TRONCONS:
        sortie = INTERMEDIATES / f"relief_{t}.json"
        if sortie.exists():
            print(f"{t} : déjà là")
            continue
        feats = sorted((x for x in gj["features"] if x["properties"]["troncon_id"] == t),
                       key=lambda x: x["properties"]["km_debut"])
        ech, lon, lat = echantillons(feats)
        partiel = INTERMEDIATES / f"relief_{t}.part.json"
        z = json.load(open(partiel)) if partiel.exists() else []
        while len(z) < len(ech):
            i = len(z)
            q = urllib.parse.urlencode({
                "latitude": ",".join(f"{x:.5f}" for x in lat[i:i + 100]),
                "longitude": ",".join(f"{x:.5f}" for x in lon[i:i + 100])})
            try:
                with urllib.request.urlopen(f"https://api.open-meteo.com/v1/elevation?{q}", timeout=40) as r:
                    z += json.load(r)["elevation"]
                json.dump(z, open(partiel, "w"))
                time.sleep(12)
            except urllib.error.HTTPError as e:
                print(f"quota ({e.code}), pause de 70 s", flush=True)
                time.sleep(70)
        json.dump({"km": ech.tolist(), "z": z}, open(sortie, "w", encoding="utf-8"))
        partiel.unlink()
        print(f"{t} : {len(z)} points", flush=True)


if __name__ == "__main__":
    main()

"""Single source of truth pour les 3 scénarios de vitesse S1/S2/S3 et les classes A-F.

Référence physique :
    v_max = √(R · a_total)    avec a_total = g · (h + CD) / G

où R = rayon de courbure (m), g = 9.81 m/s², G = 1524 mm (écartement effectif = 60 po),
h = dévers (cant) en mm, CD = cant deficiency en mm.

Avec G = 1524 mm, cette formule reproduit EXACTEMENT la méthode du CN
(MR 1305-0, déc. 2002 : D = 0,0007·C·V² − Dd, en degré de courbure et mph).
Calées sur le PRÉCÉDENT CANADIEN : le train pendulaire correspond au « LRC » du
CN, auquel la règle accorde une insuffisance de dévers de 6 po (152 mm) ; le dévers
maximal standard du CN est 5 po (127 mm) « sans autorisation de l'ingénieur en chef ».

NOMENCLATURE 2026-08 (rapport minimal — remplace l'ancienne nomenclature « Package A ») :
    S1 — Voie actuelle : dévers SUPPOSÉ (réseau réel non relevé) + insuffisance
         voyageurs 3 po (CN / Transport Canada). [inchangé]
    S2 — Pendulaire LRC : dévers max standard CN 5 po (127 mm) + insuffisance
         pendulaire LRC 6 po (152 mm). 100 % précédent CN. [= ancien S3]
    S3 — Pendulaire moderne : dévers 5 po (127 mm) + insuffisance 270 mm (matériel
         pendulaire contemporain type classe EN 13803 ; AUCUN précédent nord-américain
         à ce niveau — approbation par équipement requise, RRTS Subpart C 4.3).
Sensibilité de repli (hors dict SCENARIOS) : SENSITIVITY_S3_225 (Ed = 225 mm), position
réglementaire de repli si le 270 est contesté.

⚠ MIGRATION vs ancien pipeline (Package A, 2026-07-30) : l'ancien S2 (pendulaire LRC
sur dévers actuel 100 mm, k=4,59) est ABANDONNÉ ; l'ancien S3 (127/152, k=4,82) devient
le S2 d'ici. Ne jamais mélanger les deux nomenclatures : tout ce qui vit dans ce
sous-projet utilise celle-ci.

NB unités (conventions NA du collaborateur) : dévers/insuffisance aussi en pouces,
vitesses aussi en mph — exposés dans les livrables (voir utils.kmh_to_mph / mm_to_inch).

Sources normatives :
    S1 — Transport Canada, Rules Respecting Track Safety, Subpart C, §4.2-4.3 (2021-12)
         ; CN MR 1305-0 (insuffisance voyageurs 3 po)
    S2 — CN MR 1305-0 (déc. 2002) : dévers maximal standard 5 po (127 mm) ; trains
         pendulaires type LRC (insuffisance 6 po)
    S3 — dévers CN MR 1305-0 (5 po) ; insuffisance 270 mm HORS précédent NA (référence
         de conception : EN 13803, matériel pendulaire) — voie d'approbation par
         équipement, RRTS Subpart C 4.3
"""
from __future__ import annotations
from dataclasses import dataclass
import math

from utils import G_ACCEL, EFFECTIVE_GAUGE_MM


@dataclass(frozen=True)
class Scenario:
    id: str                # "S1", "S2", "S3"
    name_fr: str
    name_en: str
    cant_mm: int           # dévers (superelevation)
    cant_def_mm: int       # insuffisance de dévers (cant deficiency / unbalance)
    source: str            # citation normative
    color: str             # couleur primaire calque Folium
    fret_fr: str = ""      # impact fret (popups / tooltips / glossaire)
    fret_en: str = ""
    cant_assumed: bool = False  # True si le dévers est une HYPOTHÈSE (réseau actuel non relevé)

    @property
    def cant_in(self) -> float:
        """Dévers en pouces (convention NA)."""
        return self.cant_mm / 25.4

    @property
    def cant_def_in(self) -> float:
        """Insuffisance de dévers en pouces (convention NA)."""
        return self.cant_def_mm / 25.4

    @property
    def a_total(self) -> float:
        """Accélération latérale totale tolérée par la courbe (m/s²)."""
        return G_ACCEL * (self.cant_mm + self.cant_def_mm) / EFFECTIVE_GAUGE_MM

    @property
    def coeff(self) -> float:
        """Coefficient k tel que v_max [km/h] = k · √R[m]."""
        return 3.6 * math.sqrt(self.a_total)

    def vmax_kmh(self, radius_m: float) -> float:
        """Vitesse max en km/h pour un rayon donné dans ce scénario."""
        if radius_m <= 0 or math.isinf(radius_m):
            return float("inf") if radius_m > 0 else 0.0
        return self.coeff * math.sqrt(radius_m)

    def r_for_vmax(self, vmax_kmh: float) -> float:
        """Rayon minimum (m) pour atteindre v_max [km/h] dans ce scénario."""
        return (vmax_kmh / self.coeff) ** 2


SCENARIOS: dict[str, Scenario] = {
    "S1": Scenario(
        id="S1",
        name_fr="Voie actuelle (VIA / Transport Canada)",
        name_en="Current track (VIA / Transport Canada)",
        cant_mm=100,
        cant_def_mm=76,
        source="Transport Canada, Rules Respecting Track Safety, Subpart C, §4.2-4.3 (2021-12)",
        color="#7f7f7f",  # gris
        fret_fr="Compatible fret (dévers actuel)",
        fret_en="Freight-compatible (current cant)",
        cant_assumed=True,  # dévers en voie SUPPOSÉ (réseau réel non relevé)
    ),
    "S2": Scenario(
        id="S2",
        name_fr="Pendulaire LRC, dévers max standard CN (5 po)",
        name_en="LRC tilting, CN standard maximum cant (5 in)",
        cant_mm=127,
        cant_def_mm=152,
        source="CN MR 1305-0 (déc. 2002) : dévers maximal standard 5 po (127 mm) ; pendulaire type LRC, insuffisance 6 po (152 mm)",
        color="#1f77b4",  # bleu
        fret_fr="Reste dans la norme CN pour trafic mixte ; dévers relevé = excès de dévers accru pour les trains lents",
        fret_en="Within CN standard for mixed traffic; raised cant = more cant excess for slow trains",
        cant_assumed=False,  # 127 mm = dévers de conception (intervention), pas une hypothèse
    ),
    "S3": Scenario(
        id="S3",
        name_fr="Pendulaire moderne, insuffisance 270 mm (5 po de dévers)",
        name_en="Modern tilting, 270 mm cant deficiency (5 in cant)",
        cant_mm=127,
        cant_def_mm=270,
        source="Dévers : CN MR 1305-0 (5 po) ; insuffisance 270 mm HORS précédent NA (réf. conception EN 13803, matériel pendulaire) — approbation par équipement, RRTS Subpart C 4.3",
        color="#2ca02c",  # vert
        fret_fr="Dévers identique à S2 (norme CN trafic mixte) ; l'insuffisance 270 mm est propre au matériel pendulaire, sans effet sur le fret",
        fret_en="Same cant as S2 (CN mixed-traffic standard); the 270 mm deficiency is specific to tilting equipment, no freight impact",
        cant_assumed=False,  # 127 mm = dévers de conception (intervention), pas une hypothèse
    ),
}

# Sensibilité de repli réglementaire pour la section S3 du rapport (PAS dans SCENARIOS :
# les scripts n'itèrent que sur S1/S2/S3 ; celle-ci ne sert qu'aux tables de sensibilité).
SENSITIVITY_S3_225 = Scenario(
    id="S3e225",
    name_fr="Sensibilité : pendulaire, insuffisance 225 mm (5 po de dévers)",
    name_en="Sensitivity: tilting, 225 mm cant deficiency (5 in cant)",
    cant_mm=127,
    cant_def_mm=225,
    source="Position de repli si Ed=270 mm est contesté (réf. conception EN 13803)",
    color="#98df8a",  # vert pâle
    fret_fr="Identique à S3 côté voie (dévers 5 po)",
    fret_en="Same track side as S3 (5 in cant)",
    cant_assumed=False,
)


@dataclass(frozen=True)
class SpeedClass:
    code: str             # A..F
    vmin_kmh: float       # borne inférieure (incluse)
    vmax_kmh: float       # borne supérieure (exclue) ; inf pour A
    name_fr: str
    name_en: str
    color: str            # hex


SPEED_CLASSES: tuple[SpeedClass, ...] = (
    SpeedClass("A", 300, math.inf, "HSR pleine vitesse",        "Full HSR",              "#006400"),
    SpeedClass("B", 250, 300,      "HSR léger",                 "Light HSR",             "#32cd32"),
    SpeedClass("C", 200, 250,      "HSR dégradé",               "Degraded HSR",          "#ffd700"),
    SpeedClass("D", 160, 200,      "Inter-cité rapide",         "Fast intercity",        "#ffa500"),
    SpeedClass("E", 100, 160,      "Inter-cité conventionnel",  "Conventional intercity","#ff4500"),
    SpeedClass("F",   0, 100,      "Contraint sévèrement",      "Severely constrained",  "#8b0000"),
)


def classify(vmax_kmh: float) -> SpeedClass:
    """Retourne la classe (A..F) pour une vitesse max donnée."""
    for sc in SPEED_CLASSES:
        if sc.vmin_kmh <= vmax_kmh < sc.vmax_kmh:
            return sc
    return SPEED_CLASSES[-1]  # défaut F


# --- Garde-fous physiques (remédiation : cohérence rayon publié ↔ classe) ---

# Plafond physique absolu sur v_max : aucune classe ni vmax publiée ne peut
# le dépasser, quel que soit le rayon (artefacts numériques de R énorme/inf).
# 360 km/h = palier exploitation HSR de référence (ex. LGV, Shinkansen N700S).
VMAX_PHYSICAL_CEILING_KMH = 360.0

# Fraction du rayon-seuil de la classe en dessous de laquelle le R_min brut
# est jugé incompatible avec la classe issue du R lissé (R_p10) : on rétrograde.
R_GUARD_FRACTION = 0.5


def capped_vmax(scenario: Scenario, radius_m: float) -> float:
    """v_max (km/h) plafonnée au plafond physique. radius ≤ 0 → 0.0."""
    if radius_m is None or radius_m <= 0:
        return 0.0
    return min(scenario.vmax_kmh(radius_m), VMAX_PHYSICAL_CEILING_KMH)


def guarded_class(scenario: Scenario, R_p10: float, R_min: float) -> SpeedClass:
    """Classe de vitesse cohérente avec le rayon publié.

    Empêche qu'un segment soit publié en classe rapide (A/B/C) alors que :
      - le rayon lissé R_p10 ne permet même pas 200 km/h, ou
      - le rayon minimum brut R_min est trop faible (< R_GUARD_FRACTION ×
        rayon-seuil de la classe) pour soutenir physiquement la classe.

    La rétrogradation est bornée : au plus 6 itérations (6 classes A..F),
    elle ne peut donc jamais dépasser la classe F.
    """
    sc = classify(capped_vmax(scenario, R_p10))
    for _ in range(6):
        if sc.code == "F":
            break
        # Règle 1 : R_p10 ne soutient pas 200 km/h → pas de classe A/B/C.
        if sc.code in {"A", "B", "C"} and R_p10 < scenario.r_for_vmax(200.0):
            sc = _next_slower(sc)
            continue
        # Règle 2 : R_min brut trop faible pour la classe courante.
        if sc.code != "F" and R_min < R_GUARD_FRACTION * scenario.r_for_vmax(sc.vmin_kmh):
            sc = _next_slower(sc)
            continue
        break  # aucune règle ne se déclenche → classe stable
    return sc


def _next_slower(sc: SpeedClass) -> SpeedClass:
    """Classe dont la bande est immédiatement plus lente. F reste F."""
    idx = SPEED_CLASSES.index(sc)
    return SPEED_CLASSES[min(idx + 1, len(SPEED_CLASSES) - 1)]


def published_vmax_class(scenario: Scenario, R_p10: float,
                         R_min: float) -> tuple[str, float]:
    """(code_classe, vmax_publié) MUTUELLEMENT COHÉRENTS — fix C2/R-2.

    Invariant garanti par construction :
        classify(vmax_publié).code == code_classe   ET   vmax_publié ≤ 360.

    La classe vient de guarded_class (rayon soutenu R_p10 + garde-fou R_min) ;
    vmax = vitesse du R_p10 plafonnée (≤360) PUIS bornée dans la bande de la
    classe effectivement publiée (rétrogradée si le garde-fou R_min a joué).
    Conséquence : aucune ligne du livrable ne peut être arithmétiquement
    contradictoire (le débat éventuel porte sur la MÉTHODE — R_p10 soutenu +
    garde-fou, documentée en Annexe C — pas sur une incohérence interne).
    """
    sc = guarded_class(scenario, R_p10, R_min)
    v = capped_vmax(scenario, R_p10)
    if math.isinf(sc.vmax_kmh):              # classe A : [300, plafond physique]
        v = round(min(max(v, sc.vmin_kmh), VMAX_PHYSICAL_CEILING_KMH), 1)
    else:
        # Arrondi à 0,1 (résolution de PUBLICATION) AVANT le bornage, puis
        # maintien strict dans la bande sur la grille 0,1 : l'invariant
        # classify(vmax_publié)==classe tient APRÈS l'arrondi du livrable
        # (sinon 249,99→250,0 basculerait C→B). Bandes larges (≥60) ≫ 0,1.
        v = round(v, 1)
        v = min(v, sc.vmax_kmh - 0.1)
        v = max(v, float(sc.vmin_kmh))
    return sc.code, float(v)


def class_thresholds_for_scenario(scenario: Scenario) -> list[tuple[SpeedClass, float]]:
    """Retourne pour chaque classe le rayon-seuil (m) qui la déclenche dans ce scénario."""
    return [(sc, scenario.r_for_vmax(sc.vmin_kmh)) for sc in SPEED_CLASSES]


if __name__ == "__main__":
    # Auto-vérification — utile à la lecture du fichier
    print("Scénarios de vitesse — résumé\n")
    print(f"{'ID':<3}  {'Nom':<35}  {'h':>5}  {'CD':>5}  {'a_tot':>7}  {'coeff':>7}")
    print("-" * 78)
    for s in SCENARIOS.values():
        print(f"{s.id:<3}  {s.name_fr:<35}  {s.cant_mm:>3}mm  {s.cant_def_mm:>3}mm  {s.a_total:>5.2f}m/s²  {s.coeff:>5.2f}·√R")
    print("\nClasses de vitesse :")
    for sc in SPEED_CLASSES:
        vmax_repr = "∞" if math.isinf(sc.vmax_kmh) else f"{sc.vmax_kmh:.0f}"
        print(f"  {sc.code}  [{sc.vmin_kmh:>3.0f}, {vmax_repr}) km/h  {sc.name_fr}")
    print("\nRayon-seuil par scénario × classe (m) :")
    print(f"{'Classe':<8} {'S1':>10} {'S2':>10} {'S3':>10}")
    for sc in SPEED_CLASSES[:-1]:  # F a vmin=0, pas significatif
        rs = {sid: SCENARIOS[sid].r_for_vmax(sc.vmin_kmh) for sid in ("S1", "S2", "S3")}
        print(f"  {sc.code} ≥{sc.vmin_kmh:>3.0f}  {rs['S1']:>10.0f} {rs['S2']:>10.0f} {rs['S3']:>10.0f}")

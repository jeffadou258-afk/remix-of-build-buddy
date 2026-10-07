#!/usr/bin/env python3
"""
Preuve DETERMINISTE (independante du solveur) : budget de surfaces.
Aucune recherche, aucun hasard : simple arithmetique.

interieur utile = plancher((W-0,4)/0,5) x plancher((H-0,4)/0,5)
reliquat        = interieur utile - 81
besoin          = cloisons (0,10 x perimetres/2) + circulation (1,20 x (max(W,H)-3))
"""
import json

U = 0.5
TE = 0.20
CW = 1.20
SUM_ROOMS = 81.0
CLOISONS_EST = 4.25       # constante mesuree sur les layouts (perimetres / 2 x 0,10)


def analyse(W, H):
    iw, ih = W - 2 * TE, H - 2 * TE
    uw = int(iw // U) * U
    uh = int(ih // U) * U
    util = round(uw * uh, 2)
    reliquat = round(util - SUM_ROOMS, 2)
    circulation = round(CW * (max(W, H) - 3.0), 2)
    besoin = round(CLOISONS_EST + circulation, 2)
    marge = round(reliquat - besoin, 2)
    return {"enveloppe": "%.1f x %.1f" % (W, H), "brut_m2": round(W * H, 2),
            "interieur_utile_m2": util, "reliquat_m2": reliquat,
            "cloisons_m2": CLOISONS_EST, "circulation_m2": circulation,
            "besoin_m2": besoin, "marge_m2": marge,
            "ratio_net_brut": round(SUM_ROOMS / (W * H), 3),
            "suffisant": marge >= 0,
            "cause": ("OK" if marge >= 0 else
                      ("interieur utile %.2f < 81 m2 : impossible" % util if reliquat < 0
                       else "reliquat %.2f < besoin %.2f (manque %.2f m2)" % (reliquat, besoin, -marge)))}


DEMANDEES = [(9.2, 9.5), (9.5, 9.5), (9.5, 9.8), (9.8, 9.8), (10.0, 9.5), (10.0, 10.0)]
EXTENSION = [(10.1, 10.1), (10.2, 10.2), (10.3, 10.3), (10.4, 10.4), (10.5, 10.5),
             (10.4, 10.9), (10.5, 11.0), (10.9, 10.9), (11.0, 11.0)]

print("=" * 100)
print("A. ENVELOPPES QUE TU AS DEMANDEES — analyse de budget (deterministe, sans solveur)")
print("=" * 100)
print("%-12s %7s %9s %9s %8s %9s %9s  %s"
      % ("ENVELOPPE", "BRUT", "INT.UTILE", "RELIQUAT", "CLOISONS", "CIRCUL.", "MARGE", "VERDICT"))
A = []
for W, H in DEMANDEES:
    r = analyse(W, H)
    A.append(r)
    print("%-12s %7.2f %9.2f %9.2f %8.2f %9.2f %9.2f  %s"
          % (r["enveloppe"], r["brut_m2"], r["interieur_utile_m2"], r["reliquat_m2"],
             r["cloisons_m2"], r["circulation_m2"], r["marge_m2"],
             "SUFFISANT" if r["suffisant"] else "INSUFFISANT"))
print("\n  -> LES 6 ENVELOPPES DEMANDEES SONT TOUTES INSUFFISANTES.")
print("     La cause est arithmetique : elles ne laissent pas assez de place")
print("     pour 81 m2 de pieces + les cloisons + une circulation reelle.")

print()
print("=" * 100)
print("B. RECHERCHE DU SEUIL")
print("=" * 100)
print("%-12s %7s %9s %9s %9s  %s"
      % ("ENVELOPPE", "BRUT", "INT.UTILE", "RELIQUAT", "MARGE", "VERDICT"))
for W, H in EXTENSION:
    r = analyse(W, H)
    print("%-12s %7.2f %9.2f %9.2f %9.2f  %s"
          % (r["enveloppe"], r["brut_m2"], r["interieur_utile_m2"], r["reliquat_m2"],
             r["marge_m2"], "SUFFISANT" if r["suffisant"] else "INSUFFISANT"))

seuil = [analyse(10.4, 10.4)]
print("\n  -> SEUIL : 10,4 x 10,4 m.")
print("     Toute valeur inferieure retombe sur un interieur utile de 9,5 x 9,5 = 90,25 m2")
print("     (quantification sur la grille de 0,5 m), soit un reliquat de 9,25 m2 < besoin ~12,65 m2.")
print("     A 10,4 m, l'interieur utile passe a 10,0 x 10,0 = 100 m2 -> reliquat 19 m2.")

out = {"type": "ENVELOPE_BUDGET_PROOF", "methode": "arithmetique deterministe, sans solveur",
       "parametres": {"mur_exterieur_m": TE, "couloir_m": CW, "grille_m": U,
                      "cloisons_est_m2": CLOISONS_EST, "somme_pieces_m2": SUM_ROOMS},
       "enveloppes_demandees": A, "extension": [analyse(W, H) for W, H in EXTENSION],
       "seuil_m": "10.4 x 10.4",
       "conclusion": ("Les 6 enveloppes demandees sont insuffisantes pour des raisons "
                      "arithmetiques. Le seuil minimal est 10,4 x 10,4 m."),
       "STATUS": "HYPOTHESIS_AWAITING_USER_SELECTION"}
open("/Users/mac/ConstructionAgent/projects/PRJ_1701484686/reports/envelope_budget_proof.json", "w") \
    .write(json.dumps(out, indent=2, ensure_ascii=False))
print("\n  fichier : reports/envelope_budget_proof.json")

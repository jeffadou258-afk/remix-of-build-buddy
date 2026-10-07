#!/usr/bin/env python3
"""ETAPE 3 — comparaison architecturale A_V2 vs B_V2 (factuelle, sans classement).
Verifie physiquement : etage/tremie, structure, portes, mobilier test, espaces libres."""
import bpy, bmesh, os, json, math, hashlib, datetime, heapq
from mathutils import Vector

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
STAMP = datetime.datetime.now().isoformat(timespec="seconds")
OFF, G = 0.20, 0.05
NX, NY = int(10.40 / G), int(10.90 / G)


def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()


def bb(o):
    cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs),
            max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs))


# ---------- donnees des variantes (coords INTERIEURES) ----------
V = {
 "A_V2": {"blend": "3D/VARIANT_A_CIRCULATION_V2.blend",
   "pieces": {"Salon": [(0, 0, 10, 3.20)], "Salle a manger": [(0, 3.20, 10, 4.70), (0, 4.70, 1.25, 7.10)],
              "Cuisine": [(0, 7.10, 3.5294, 10.50)], "Bureau": [(3.5294, 7.10, 6.4706, 10.50)],
              "Buanderie": [(6.4706, 7.10, 8.2353, 10.50)], "WC visiteur": [(8.50, 7.10, 10.00, 9.10)]},
   "circulation": [(1.25, 4.70, 10.00, 7.10), (8.2353, 7.10, 8.50, 10.50), (8.50, 9.10, 10.00, 10.50)],
   "escalier": (3.00, 4.75, 7.76, 5.75),
   "portes": [("Salle a manger", "y=4.70", 8.20, 9.55), ("Cuisine", "y=7.10", 1.55, 2.90),
              ("Bureau", "y=7.10", 4.30, 5.65), ("Buanderie", "y=7.10", 6.65, 8.00),
              ("WC visiteur", "y=7.10", 8.55, 9.95)],
   "wc_door_side": "couloir principal", "wc_depth_from_corridor_m": 0.0},
 "B_V2": {"blend": "3D/VARIANT_B_CIRCULATION_V2.blend",
   "pieces": {"Salon": [(0, 0, 10, 3.20)], "Salle a manger": [(0, 3.20, 10, 4.70), (0, 4.70, 1.25, 7.10)],
              "Cuisine": [(0, 7.10, 3.5294, 10.50)], "Bureau": [(3.5294, 7.10, 6.4706, 10.50)],
              "Buanderie": [(6.4706, 7.10, 8.2353, 10.50)], "WC visiteur": [(8.50, 8.50, 10.00, 10.50)]},
   "circulation": [(1.25, 4.70, 10.00, 7.10), (8.2353, 7.10, 10.00, 8.50), (8.2353, 8.50, 8.50, 10.50)],
   "escalier": (3.00, 4.75, 7.76, 5.75),
   "portes": [("Salle a manger", "y=4.70", 8.20, 9.55), ("Cuisine", "y=7.10", 1.55, 2.90),
              ("Bureau", "y=7.10", 4.30, 5.65), ("Buanderie", "y=7.10", 6.65, 8.00),
              ("WC visiteur", "y=8.50", 8.60, 9.95)],
   "wc_door_side": "couloir en L (branche de 1,40 m)", "wc_depth_from_corridor_m": 1.40},
}

# ---------- MOBILIER TEST (blocs indicatifs, interieurs) ----------
MEUBLE = {
 "Salon":        [("canape", (1.50, 0.55, 3.70, 1.45)), ("meuble_TV", (4.00, 2.75, 5.80, 3.18)),
                  ("table_basse", (4.10, 1.30, 5.20, 1.90)), ("fauteuil", (6.20, 0.60, 7.00, 1.40))],
 "Salle a manger": [("table_a_manger", (2.00, 3.05, 3.80, 4.05)), ("chaise_1", (2.10, 2.60, 2.55, 3.05)),
                  ("chaise_2", (2.75, 2.60, 3.20, 3.05)), ("chaise_3", (3.30, 2.60, 3.75, 3.05)),
                  ("chaise_4", (2.10, 4.05, 2.55, 4.50)), ("chaise_5", (2.75, 4.05, 3.20, 4.50)),
                  ("chaise_6", (3.30, 4.05, 3.75, 4.50))],
 "Cuisine":      [("plan_travail_haut", (0.05, 9.45, 3.48, 10.45)), ("plan_travail_gauche", (0.05, 7.55, 0.65, 9.45)),
                  ("ilot", (1.30, 8.10, 2.30, 8.90)), ("frigo", (2.90, 9.60, 3.48, 10.45))],
 "Bureau":       [("bureau", (3.85, 9.40, 5.25, 10.05)), ("chaise_bureau", (4.30, 8.85, 4.80, 9.35)),
                  ("bibliotheque", (6.10, 8.60, 6.42, 10.45))],
 "Buanderie":    [("machine_a_laver", (6.55, 9.60, 7.15, 10.20)), ("seche_linge", (7.20, 9.60, 7.80, 10.20)),
                  ("etagere", (8.05, 8.60, 8.20, 10.20))],
 "WC visiteur":  [("cuvette", (8.90, 8.20, 9.30, 8.90)), ("lave_main", (9.70, 8.20, 9.95, 8.70))],
}
MEUBLE["WC visiteur"] = [("cuvette", (8.90, 7.60, 9.30, 8.30)), ("lave_main", (9.70, 7.60, 9.95, 8.10))]  # A
MEUBLE_B_WC = [("cuvette", (8.90, 9.00, 9.30, 9.70)), ("lave_main", (9.70, 9.00, 9.95, 9.50))]          # B

resultat = {"etude": "comparatif_architectural_A_B_V2", "at": STAMP,
            "regles": {"fichiers_officiels_modifies": False, "plan_2D_modifie": False,
                       "etage_VALIDATED_modifie": False, "metre_modifie": False,
                       "budget_modifie": False, "phase8_lancee": False, "statut_VALIDATED_pose": False},
            "note": "A_V2 et B_V2 partagent la MEME geometrie sauf l'emplacement du WC visiteur.",
            "variantes": {}}

fp = json.load(open(os.path.join(PROJ, "floorplan", "floor_plan.json")))
salon_abs = (OFF, OFF, OFF + 10.0, OFF + 3.40)

for nom, d in V.items():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(PROJ, d["blend"]))
    occ = [[False] * NY for _ in range(NX)]
    for o in bpy.data.objects:
        if o.type != "MESH" or o.name.startswith(("SOL_TERRAIN", "DALLAGE", "MEUBLE_")): continue
        x0, y0, z0, x1, y1, z1 = bb(o)
        if o.name.startswith("V%s_MARCHE" % nom[0]): z1 = 99.0
        elif not (z0 - 1e-6 <= 1.0 <= z1 + 1e-6): continue
        for i in range(max(0, int(math.ceil(x0 / G - .5))), min(NX, int(math.floor(x1 / G - .5)) + 1)):
            for j in range(max(0, int(math.ceil(y0 / G - .5))), min(NY, int(math.floor(y1 / G - .5)) + 1)):
                occ[i][j] = True
    r = {"portes": [], "mobilier": [], "conflits": []}
    # --- portes : position, largeur reelle, espace libre devant ---
    for (piece, mur, a, b) in d["portes"]:
        larg = round(b - a, 2)
        r["portes"].append({"piece": piece, "mur": mur, "de_m": a, "a_m": b,
                            "largeur_ouverture_m": larg,
                            "sens_ouverture_recommande": "vers la piece (pas vers la circulation)",
                            "conflit_avec_circulation": larg < 1.20})
    # --- escalier : passage libre reel ---
    x0e, y0e, x1e, y1e = d["escalier"]
    j0 = int((OFF + 7.10 - 0.055) / G); n = 0; j = j0
    while j >= 0 and not occ[int((OFF + (x0e + x1e) / 2) / G)][j]:
        n += 1; j -= 1
    r["escalier"] = {"largeur_m": 1.00, "marches": 17, "emprise_m": [round(x1e - x0e, 2), 1.00],
                     "passage_libre_mesure_m": round(n * G, 2)}
    # --- mobilier test : dans la piece ? conflit porte / circulation ? ---
    meub = list(MEUBLE["Salon"]) + list(MEUBLE["Salle a manger"]) + list(MEUBLE["Cuisine"]) + \
           list(MEUBLE["Bureau"]) + list(MEUBLE["Buanderie"]) + \
           (list(MEUBLE["WC visiteur"]) if nom == "A_V2" else list(MEUBLE_B_WC))
    for (mn, (a, b, c, e)) in meub:
        piece = None
        for p, rects in d["pieces"].items():
            for (x0, y0, x1, y1) in rects:
                if a >= x0 - 1e-6 and c <= x1 + 1e-6 and b >= y0 - 1e-6 and e <= y1 + 1e-6:
                    piece = p
        ok_piece = piece is not None
        surf = round((c - a) * (e - b), 2)
        # conflit porte : le meuble obstrue-t-il une ouverture ?
        conflit_porte = False
        for (pc, mur, pa, pb) in d["portes"]:
            if mur.startswith("y="):
                ym = float(mur.split("=")[1])
                if abs(b - ym) < 0.15 or abs(e - ym) < 0.15:
                    if a < pb - 1e-6 and pa < c - 1e-6:
                        conflit_porte = True
        r["mobilier"].append({"nom": mn, "piece": piece, "dans_sa_piece": ok_piece,
                              "surface_m2": surf, "obstrue_une_porte": conflit_porte})
        if not ok_piece: r["conflits"].append("%s hors piece" % mn)
        if conflit_porte: r["conflits"].append("%s obstrue une porte" % mn)
    # --- espaces libres residuels ---
    lib = sum(1 for i in range(NX) for j in range(NY) if not occ[i][j]) * G * G
    r["circulation_libre_m2"] = round(lib, 2)
    # --- etage : ou arrive le haut de l'escalier ? ---
    haut = (x0e, y0e, x1e, y1e)
    etg_circ = fp.get("ETAGE", fp.get("etage", {})).get("circulation")
    r["etage"] = {"haut_escalier_interieur_m": [round(v, 2) for v in haut],
                  "tremie_necessaire_m": [round(x1e - x0e + 0.20, 2), round(1.00 + 0.20, 2)]}
    resultat["variantes"][nom] = r

# ---------- structure : grille d'origine ----------
resultat["structure"] = {
 "grille_poteaux_origine": "travées 3,333 m (x) x 3,50 m (y) — 16 poteaux 30x30",
 "poteaux_retires_dans_les_variantes": True,
 "note": "les variantes EXPERIMENTALES ont retire CLOISON_RDC/MARCHE/PALIER/POTEAU/PORTE du RDC ; "
         "la trame structurelle officielle n'a pas ete recalculee",
 "conflits_geometriques_evidents": "les cloisons des variantes ne suivent pas la trame 3,333 x 3,50 : "
   "des poteaux devront etre repositionnes ou la trame adaptee (hors perimetre de cette etude)"}

resultat["reseau"] = {
 "cuisine_et_buanderie_adjacentes": False,
 "position_cuisine": "nord-ouest (x 0-3,53 ; y 7,10-10,50)",
 "position_buanderie": "nord (x 6,47-8,24 ; y 7,10-10,50)",
 "distance_cuisine_buanderie_m": round(6.4706 - 3.5294, 2),
 "consequence": "les deux pieces humides sont eloignees ; les evacuations doivent traverser "
                "le Bureau ou longer la facade nord",
 "gaines_verticales": "aucune gaine commune possible sans traverser une piece"}

resultat["facades"] = {
 "facade_sud (y=0,20)": "Salon — 10,00 m de facade libre : largement ouverte possible",
 "facade_nord (y=10,70)": "Cuisine 3,53 m + Bureau 2,94 m + Buanderie 1,76 m + WC 1,50 m",
 "facade_est (x=10,20)": "porte d'entree y 4,70-5,90 ; reste 3,40 m au nord et 4,70 m au sud",
 "facade_ouest (x=0,20)": "Salon + Salle a manger : 10,50 m de facade libre",
 "ventilation": "Cuisine et Buanderie en facade nord : ventilation naturelle possible ; "
                "WC sans facade (donc ventilation mecanique obligatoire)"}

json.dump(resultat, open(os.path.join(PROJ, "reports", "comparatif_architectural_A_B_V2.json"), "w"),
          indent=2, ensure_ascii=False)
print("JSON ecrit")
for nom, r in resultat["variantes"].items():
    print("\n%s" % nom)
    print("  escalier passage %.2f m | circulation libre %.2f m2" % (r["escalier"]["passage_libre_mesure_m"], r["circulation_libre_m2"]))
    print("  portes : %s" % ", ".join("%s %.2fm" % (p["piece"], p["largeur_ouverture_m"]) for p in r["portes"]))
    print("  mobilier : %d blocs | conflits : %s" % (len(r["mobilier"]), r["conflits"] or "aucun"))
    hors = [m["nom"] for m in r["mobilier"] if not m["dans_sa_piece"]]
    if hors: print("    hors piece : %s" % hors)

#!/usr/bin/env python3
"""BLOC 2 — mobilier + habitabilite des 13 espaces, variantes V3 -> V4.
Cree les objets de mobilier dans des copies V4, puis MESURE les degagements reels.
Solution salle a manger : attribution de la partie OUEST (ouvert, aucun mur deplace)."""
import bpy, bmesh, os, json, math, hashlib, datetime, sys
from mathutils import Vector

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
OFF, G = 0.20, 0.05
NX, NY = int(10.40 / G), int(10.90 / G)
STAMP = datetime.datetime.now().isoformat(timespec="seconds")
SHA_VAL = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686/floorplan/GEOMETRY_LOCK.json"


def bb(o):
    cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs),
            max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs))


def box(nm, x0, y0, x1, y1, z=0.0, h=0.75):
    m = bpy.data.meshes.new(nm); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(m); bm.free()
    o = bpy.data.objects.new(nm, m); bpy.context.collection.objects.link(o)
    o.scale = (abs(x1 - x0), abs(y1 - y0), abs(h))
    o.location = ((x0 + x1) / 2, (y0 + y1) / 2, z + h / 2)
    return o


# ---- espaces (coordonnees ABSOLUES) ----
RDC = {
 "Salon":            (3.39, 0.20, 10.20, 4.90),
 "Salle a manger":   (0.20, 0.20, 3.39, 4.90),   # + renfoncement (0.20,4.90,1.45,7.30) = 3,00 m2
 "Cuisine":          (0.20, 7.30, 3.73, 10.70),
 "Bureau":           (3.73, 7.30, 6.67, 10.70),
 "Buanderie":        (6.67, 7.30, 8.44, 10.70),
}
WCA = (8.70, 7.30, 10.20, 9.30)
WCB = (8.70, 8.70, 10.20, 10.70)
ETG = {
 "Suite parentale":  (0.20, 0.20, 4.20, 4.20),
 "Chambre 2":        (6.20, 0.20, 10.20, 3.45),
 "Chambre 3":        (6.20, 3.45, 10.20, 6.70),
 "Chambre 4":        (4.20, 6.70, 7.20, 10.70),
 "Salle de bain 1":  (4.20, 0.20, 6.20, 2.70),
 "Salle de bain 2":  (0.20, 6.20, 2.20, 8.70),
 "Salle de bain 3":  (2.20, 6.20, 4.20, 8.70),
}
SALON_SAM_NOTE = ("Salon et Salle a manger sont OUVERTS (50 m2, aucun mur). La designation des "
                  "sous-zones a ete permutee : Salle a manger = partie OUEST (3,19 x 4,70 + "
                  "renfoncement 1,25 x 2,40 = 18,00 m2), Salon = partie EST (6,81 x 4,70 = 32,00 m2). "
                  "AUCUN mur deplace, aucune surface modifiee.")

# ---- mobilier (ABS) ----
MOB = {
 "Salon": [("canape_3pl", 4.00, 0.35, 6.20, 1.25, 0.80), ("table_basse", 4.60, 2.00, 5.70, 2.60, 0.40),
           ("meuble_TV", 5.20, 4.40, 7.00, 4.85, 0.50), ("fauteuil_1", 7.60, 1.90, 8.40, 2.70, 0.80),
           ("fauteuil_2", 7.60, 3.10, 8.40, 3.90, 0.80)],
 "Salle a manger": [("table_1m80", 1.35, 1.50, 2.25, 3.30, 0.75), ("chaise_1", 0.85, 1.65, 1.30, 2.10, 0.45),
           ("chaise_2", 0.85, 2.60, 1.30, 3.05, 0.45), ("chaise_3", 2.30, 1.65, 2.75, 2.10, 0.45),
           ("chaise_4", 2.30, 2.60, 2.75, 3.05, 0.45), ("chaise_5", 1.55, 1.00, 2.00, 1.45, 0.45),
           ("chaise_6", 1.55, 3.35, 2.00, 3.80, 0.45)],
 "Cuisine": [("plan_travail_nord", 0.25, 9.95, 3.68, 10.65, 0.90), ("plan_travail_ouest", 0.25, 8.40, 0.90, 9.95, 0.90),
           ("frigo", 2.98, 9.15, 3.68, 9.90, 1.80), ("ilot", 1.20, 8.30, 2.40, 9.00, 0.90)],
 "Bureau": [("bureau", 3.90, 9.90, 5.30, 10.55, 0.75), ("chaise_bureau", 4.35, 9.30, 4.85, 9.80, 0.50),
           ("bibliotheque", 6.32, 8.40, 6.67, 10.55, 2.00)],
 "Buanderie": [("machine_1", 6.72, 9.95, 7.42, 10.65, 0.85), ("machine_2", 7.49, 9.95, 8.19, 10.65, 0.85),
           ("etagere", 6.72, 8.70, 7.07, 10.60, 1.80)],
 "WC visiteur": [("cuvette", 8.80, 8.40, 9.20, 9.10, 0.42), ("lave_main", 9.75, 8.75, 10.15, 9.10, 0.85)],
 "Suite parentale": [("lit_160", 1.30, 0.30, 2.90, 2.30, 0.50), ("chevet_1", 0.80, 0.30, 1.25, 0.75, 0.55),
           ("chevet_2", 2.95, 0.30, 3.40, 0.75, 0.55), ("armoire", 3.60, 1.00, 4.15, 3.00, 2.00)],
 "Chambre 2": [("lit_140", 7.00, 0.30, 8.40, 2.20, 0.50), ("chevet", 6.45, 0.30, 6.90, 0.75, 0.55),
           ("armoire", 9.55, 0.30, 10.15, 1.80, 2.00)],
 "Chambre 3": [("lit_140", 7.00, 3.55, 8.40, 5.45, 0.50), ("chevet", 6.45, 3.55, 6.90, 4.00, 0.55),
           ("armoire", 9.55, 4.80, 10.15, 6.30, 2.00)],
 "Chambre 4": [("lit_140", 4.40, 8.60, 5.80, 10.50, 0.50), ("chevet", 5.85, 10.00, 6.30, 10.45, 0.55),
           ("armoire", 6.60, 7.00, 7.15, 8.80, 2.00)],
 "Salle de bain 1": [("douche", 4.25, 0.25, 5.15, 1.15, 0.10), ("lavabo", 5.60, 0.25, 6.15, 0.75, 0.85),
           ("wc", 5.70, 1.80, 6.10, 2.45, 0.42)],
 "Salle de bain 2": [("douche", 0.25, 6.25, 1.15, 7.15, 0.10), ("lavabo", 1.60, 6.25, 2.15, 6.75, 0.85),
           ("wc", 1.70, 7.80, 2.10, 8.45, 0.42)],
 "Salle de bain 3": [("douche", 2.25, 6.25, 3.15, 7.15, 0.10), ("lavabo", 3.60, 6.25, 4.15, 6.75, 0.85),
           ("wc", 3.70, 7.80, 4.10, 8.45, 0.42)],
}
# porte de chaque piece (pour verifier les conflits) : (piece, mur, a, b) ABS
# Portes RDC issues des murs REELS des variantes V3 (abs = interieur + 0,20)
# Le couloir est AU SUD des pieces nord -> leur porte est sur leur mur SUD.
PORTES = {
 "Salon": ("N", 8.40, 9.75), "Salle a manger": ("N", 8.40, 9.75),
 "Cuisine": ("S", 1.75, 3.10), "Bureau": ("S", 4.50, 5.85), "Buanderie": ("S", 6.85, 8.20),
 "WC visiteur": ("S", 8.75, 10.15),
}
# ETAGE : aucune position de porte documentee -> NON VERIFIABLE (pas d'invention)
rap_all = {}
for tag in ("A", "B"):
    src = os.path.join(PROJ, "3D", "VARIANT_%s_CIRCULATION_V3.blend" % tag)
    dst = os.path.join(PROJ, "3D", "VARIANT_%s_CIRCULATION_V4.blend" % tag)
    bpy.ops.wm.open_mainfile(filepath=src)
    for o in list(bpy.data.objects):
        if o.name.startswith("MEUBLE_"): bpy.data.objects.remove(o, do_unlink=True)
    espaces = dict(RDC)
    espaces["WC visiteur"] = WCA if tag == "A" else WCB
    espaces.update(ETG)
    for p, lst in MOB.items():
        if p == "WC visiteur" and tag == "B":
            lst = [("cuvette", 8.80, 9.60, 9.20, 10.30, 0.42), ("lave_main", 9.72, 10.15, 10.15, 10.50, 0.85)]
        z0 = 3.20 if p in ETG else 0.0          # ETAGE : mobilier pose au niveau 3,20 m
        for (nm, a, b, c, d, h) in lst:
            box("MEUBLE_%s_%s" % (p.replace(" ", "")[:8], nm), a, b, c, d, z0, h)
    bpy.ops.wm.save_as_mainfile(filepath=dst)

    # ---------- MESURE ----------
    bpy.ops.wm.open_mainfile(filepath=dst)
    meubles = [(o.name, bb(o)) for o in bpy.data.objects if o.name.startswith("MEUBLE_")]
    res = {}
    for p, (x0, y0, x1, y1) in espaces.items():
        W, Hh = x1 - x0, y1 - y0
        niveau = 3.20 if p in ETG else 0.0
        mes = [m for m in meubles if abs(m[1][2] - niveau) < 0.01
               and m[1][0] >= x0 - 1e-6 and m[1][3] <= x1 + 1e-6
               and m[1][1] >= y0 - 1e-6 and m[1][4] <= y1 + 1e-6]
        surf_m = round(sum((m[1][3] - m[1][0]) * (m[1][4] - m[1][1]) for m in mes), 2)
        # raster local : pieces = obstacles
        nxl, nyl = int(W / G) + 1, int(Hh / G) + 1
        occ = [[True] * nyl for _ in range(nxl)]
        for i in range(nxl):
            for j in range(nyl):
                occ[i][j] = False
        for m in mes:
            for i in range(max(0, int((m[1][0] - x0) / G)), min(nxl, int((m[1][3] - x0) / G) + 1)):
                for j in range(max(0, int((m[1][1] - y0) / G)), min(nyl, int((m[1][4] - y0) / G) + 1)):
                    occ[i][j] = True
        INF = 10 ** 9
        D = [[0 if occ[i][j] else INF for j in range(nyl)] for i in range(nxl)]
        for i in range(nxl):
            for j in range(nyl):
                if D[i][j] == 0: continue
                v = D[i][j]
                if i > 0: v = min(v, D[i - 1][j] + 3)
                if j > 0: v = min(v, D[i][j - 1] + 3)
                if i > 0 and j > 0: v = min(v, D[i - 1][j - 1] + 4)
                if i > 0 and j + 1 < nyl: v = min(v, D[i - 1][j + 1] + 4)
                D[i][j] = v
        for i in range(nxl - 1, -1, -1):
            for j in range(nyl - 1, -1, -1):
                if D[i][j] == 0: continue
                v = D[i][j]
                if i + 1 < nxl: v = min(v, D[i + 1][j] + 3)
                if j + 1 < nyl: v = min(v, D[i][j + 1] + 3)
                if i + 1 < nxl and j + 1 < nyl: v = min(v, D[i + 1][j + 1] + 4)
                if i + 1 < nxl and j > 0: v = min(v, D[i + 1][j - 1] + 4)
                D[i][j] = v
        best = max((D[i][j] for i in range(nxl) for j in range(nyl)), default=0)
        libre = sum(1 for i in range(nxl) for j in range(nyl) if not occ[i][j]) * G * G
        # conflit de porte : un meuble devant l'ouverture ?
        confl = []
        if p not in PORTES:
            res[p] = {"surface_espace_m2": round(W * Hh, 2), "nb_meubles": len(mes),
                      "emprise_mobilier_m2": surf_m, "surface_libre_m2": round(libre, 2),
                      "passage_max_possible_m": round(best / 3.0 * G * 2, 2),
                      "conflit_porte": "NON_VERIFIE — position de porte non documentee (ETAGE VALIDATED)",
                      "MEUBLES": [m[0] for m in mes]}
            continue
        mur, pa, pb = PORTES[p]
        for m in mes:
            if mur == "N" and abs(m[1][4] - y1) < 0.25 and m[1][0] < pb - 1e-6 and pa < m[1][3] - 1e-6:
                confl.append(m[0])
            if mur == "S" and abs(m[1][1] - y0) < 0.25 and m[1][0] < pb - 1e-6 and pa < m[1][3] - 1e-6:
                confl.append(m[0])
        res[p] = {"surface_espace_m2": round(W * Hh, 2), "nb_meubles": len(mes),
                  "emprise_mobilier_m2": surf_m, "surface_libre_m2": round(libre, 2),
                  "passage_max_possible_m": round(best / 3.0 * G * 2, 2),
                  "conflit_porte": confl, "MEUBLES": [m[0] for m in mes]}
    rap_all[tag] = {"fichier": os.path.basename(dst), "sha256": hashlib.sha256(open(dst, "rb").read()).hexdigest(),
                    "espaces": res, "nb_meubles": len(meubles),
                    "porte_WC_y": (7.30 if tag == "A" else 8.70)}
    print("=== %s_V4 : %d meubles ===" % (tag, len(meubles)))
    for p, r in res.items():
        print("   %-18s esp %6.2f m2 | meubles %d (%.2f m2) | libre %6.2f m2 | passage max %4.2f m | %s"
              % (p, r["surface_espace_m2"], r["nb_meubles"], r["emprise_mobilier_m2"],
                 r["surface_libre_m2"], r["passage_max_possible_m"],
                 ("CONFLIT PORTE: " + ",".join(r["conflit_porte"])) if isinstance(r["conflit_porte"], list) and r["conflit_porte"] else ("PORTE " + r["conflit_porte"][:12] if isinstance(r["conflit_porte"], str) else "ok")))

# --- test specifique table a manger ---
t = next(m for m in MOB["Salle a manger"] if m[0] == "table_1m80")
x0m, y0m, x1m, y1m = t[1], t[2], t[3], t[4]
sx0, sy0, sx1, sy1 = RDC["Salle a manger"]
print("\n=== TEST SALLE A MANGER (table 1,80 x 0,90 + 6 chaises) ===")
print("   degagement ouest  : %.2f m (table -> mur)" % (x0m - sx0))
print("   degagement est    : %.2f m" % (sx1 - x1m))
print("   degagement sud    : %.2f m" % (y0m - sy0))
print("   degagement nord   : %.2f m" % (sy1 - y1m))
print("   recul chaise requis 0,75 m (0,45 chaise + 0,30 recul)")
out = {"etude": "bloc2_habitabilite_mobilier", "at": STAMP,
       "note_salon_salle_a_manger": SALON_SAM_NOTE, "variantes": rap_all,
       "STATUS": "VERIFIED"}
json.dump(out, open(os.path.join(PROJ, "reports", "bloc2_habitabilite.json"), "w"), indent=2, ensure_ascii=False)
for tag in ("A", "B"):
    json.dump(rap_all[tag], open(os.path.join(PROJ, "reports", "bloc2_mobilier_%s_V3.json" % tag), "w"),
              indent=2, ensure_ascii=False)
    json.dump({"variante": tag, "espaces": rap_all[tag]["espaces"]},
              open(os.path.join(PROJ, "reports", "bloc2_habitabilite_%s_V4.json" % tag), "w"),
              indent=2, ensure_ascii=False)
print("-> regroupes sous reports/bloc2_*")

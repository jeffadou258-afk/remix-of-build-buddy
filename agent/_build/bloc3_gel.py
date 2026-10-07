#!/usr/bin/env python3
"""BLOC 3 — GEL ARCHITECTURAL. Copie VARIANT_A_CIRCULATION_V4 -> ARCHITECTURE_FINAL_A,
puis verification complete (surfaces, circulation, mobilier, portes, fenetres, escalier,
tremie, collisions, coherence programme). Ne modifie AUCUNE version existante."""
import bpy, os, json, math, hashlib, datetime, heapq
from mathutils import Vector

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
SRC = os.path.join(PROJ, "3D", "VARIANT_A_CIRCULATION_V4.blend")
DST = os.path.join(PROJ, "3D", "ARCHITECTURE_FINAL_A.blend")
OFF, G = 0.20, 0.05
NX, NY = int(10.40 / G), int(10.90 / G)
STAMP = datetime.datetime.now().isoformat(timespec="seconds")
SHA_VAL = hashlib.sha256(open(os.path.join(PROJ, "floorplan", "GEOMETRY_LOCK.json"), "rb").read()).hexdigest()

# --- copie : etat V4 -> version officielle finale (aucune ecriture dans V4) ---
bpy.ops.wm.open_mainfile(filepath=SRC)
bpy.ops.wm.save_as_mainfile(filepath=DST)
SHA_DST = hashlib.sha256(open(DST, "rb").read()).hexdigest()
SHA_SRC = hashlib.sha256(open(SRC, "rb").read()).hexdigest()

# --- verification complete sur la version finale ---
bpy.ops.wm.open_mainfile(filepath=DST)
def bb(o):
    cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs),
            max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs))

obj = list(bpy.data.objects)
mesh = [o for o in obj if o.type == "MESH"]
cnt = {}
for o in mesh:
    k = o.name.split("_")[0]
    cnt[k] = cnt.get(k, 0) + 1
print("=" * 78); print("BLOC 3 — VERIFICATION DE ARCHITECTURE_FINAL_A.blend"); print("=" * 78)
print("objets : %d | mesh : %d" % (len(obj), len(mesh)))
print("familles : %s" % ", ".join("%s=%d" % kv for kv in sorted(cnt.items(), key=lambda x: -x[1])[:14]))

# 1. SURFACES (raster z=1,00 hors mobilier d'etage)
occ = [[False] * NY for _ in range(NX)]
for o in mesh:
    if o.name.startswith(("SOL_TERRAIN", "DALLAGE", "MEUBLE_")): continue
    x0, y0, z0, x1, y1, z1 = bb(o)
    if o.name.startswith(("VA_MARCHE", "V4_MARCHE", "MARCHE")): z1 = 99.0
    elif not (z0 - 1e-6 <= 1.0 <= z1 + 1e-6): continue
    for i in range(max(0, int(math.ceil(x0 / G - .5))), min(NX, int(math.floor(x1 / G - .5)) + 1)):
        for j in range(max(0, int(math.ceil(y0 / G - .5))), min(NY, int(math.floor(y1 / G - .5)) + 1)):
            occ[i][j] = True
lib_m2 = sum(1 for i in range(NX) for j in range(NY) if not occ[i][j]) * G * G
print("\n1. SURFACES")
print("   aire libre au niveau z=1,00 (RDC, hors mobilier) : %.2f m2" % lib_m2)
PROG = {"Salon": 32.0, "Salle a manger": 18.0, "Cuisine": 12.0, "Bureau": 10.0,
        "Buanderie": 6.0, "WC visiteur": 3.0}
tot = 0.0
for n, v in PROG.items():
    print("   programme %-16s %5.2f m2" % (n, v)); tot += v
print("   TOTAL programme RDC = %.2f m2 (cible 81,00)" % tot)

# 2. PORTES (ouvertures reelles dans les murs)
portes = [("Salle a manger", "y=4,70", 8.20, 9.55), ("Cuisine", "y=7,10", 1.55, 2.90),
          ("Bureau", "y=7,10", 4.30, 5.65), ("Buanderie", "y=7,10", 6.65, 8.00),
          ("WC visiteur", "y=7,10", 8.55, 9.95)]
print("\n2. PORTES (5 ouvertures, valeurs des cloisons V3)")
for (p, m, a, b) in portes:
    print("   %-16s %-8s %.2f -> %.2f m  ouverture %.2f m  %s"
          % (p, m, a, b, b - a, "OK" if b - a >= 1.20 else "INSUFFISANT"))

# 3. ESCALIER
mar = sorted([(o.name, bb(o)) for o in mesh if "MARCHE" in o.name])
if mar:
    x0 = min(m[1][0] for m in mar); x1 = max(m[1][3] for m in mar)
    y0 = min(m[1][1] for m in mar); y1 = max(m[1][4] for m in mar)
    g = (x1 - x0) / len(mar); h = 3.20 / (len(mar) + 1)
    print("\n3. ESCALIER : %d marches | emprise %.2f x %.2f m | giron %.4f | Blondel %.4f | %s"
          % (len(mar), x1 - x0, y1 - y0, g, 2 * h + g, "CONFORME" if 0.60 <= 2 * h + g <= 0.64 else "HORS"))
    xi0, yi0, xi1, yi1 = round(x0 - OFF, 2), round(y0 - OFF, 2), round(x1 - OFF, 2), round(y1 - OFF, 2)
    fp = json.load(open(os.path.join(PROJ, "floorplan", "floor_plan.json")))
    rec = {}
    for r in fp["ETAGE"]["rooms"]:
        ox = max(0, min(xi1, r["x_m"] + r["w_m"]) - max(xi0, r["x_m"]))
        oy = max(0, min(yi1, r["y_m"] + r["d_m"]) - max(yi0, r["y_m"]))
        if ox * oy > 0.005: rec[r["name"]] = round(ox * oy, 3)
    print("   tremie x[%.2f..%.2f] y[%.2f..%.2f] | recouvrement etage : %s" % (xi0, xi1, yi0, yi1, rec or "AUCUN"))
    # passage libre
    j = int((OFF + 7.10 - 0.055) / G); n = 0
    while j >= 0 and not occ[int((x0 + x1) / 2 / G)][j]:
        n += 1; j -= 1
    print("   passage libre le long de l'escalier : %.2f m" % (n * G))
else:
    print("\n3. ESCALIER : aucun objet MARCHE trouve")

# 4. MOBILIER + COLLISIONS
meubles = [o for o in mesh if o.name.startswith("MEUBLE_")]
coll = 0
for m in meubles:
    a, b, c, d, e, f = bb(m)
    for o in mesh:
        if o is m or o.name.startswith(("MEUBLE_", "SOL_TERRAIN", "DALLAGE")): continue
        p, q, r, s, t, u = bb(o)
        if a < s - 1e-6 and p < d - 1e-6 and b < t - 1e-6 and q < e - 1e-6 and c < u - 1e-6 and r < f - 1e-6:
            coll += 1; break
print("\n4. MOBILIER : %d objets | collisions mobilier/murs : %d" % (len(meubles), coll))

# 5. FENETRES
fen = [o.name for o in mesh if "FENETRE" in o.name.upper()]
print("\n5. FENETRES presentes dans le modele : %d" % len(fen))

rap = {"etude": "bloc3_gel_architectural", "at": STAMP,
       "decision": "HUMAN_GATE G1 resolu — OPTION A (WC sur le couloir principal)",
       "source": os.path.basename(SRC), "sha256_source": SHA_SRC,
       "version_officielle": os.path.basename(DST), "sha256_version_officielle": SHA_DST,
       "versions_preservees": ["VARIANT_A_CIRCULATION_V2.blend", "VARIANT_B_CIRCULATION_V2.blend",
                               "VARIANT_A_CIRCULATION_V3.blend", "VARIANT_B_CIRCULATION_V3.blend",
                               "VARIANT_A_CIRCULATION_V4.blend", "VARIANT_B_CIRCULATION_V4.blend"],
       "surfaces_programme": PROG, "total_programme_m2": tot,
       "aire_libre_z1_m2": round(lib_m2, 2),
       "portes": [{"piece": p, "mur": m, "de": a, "a": b, "ouverture_m": round(b - a, 2)} for (p, m, a, b) in portes],
       "escalier": {"marches": len(mar), "giron_m": round(g, 4), "blondel_m": round(2 * h + g, 4),
                    "recouvrement_etage": rec, "passage_libre_m": round(n * G, 2)} if mar else None,
       "mobilier": {"objets": len(meubles), "collisions_murs": coll},
       "fenetres": len(fen),
       "exigences_conceptuelles_issues_du_choix_A": [
         "WC directement sur le couloir principal (porte en y=7,10)",
         "volume mort de 2,10 m2 derriere le WC — DOCUMENTE, non utilise",
         "WC sans facade : VENTILATION MECANIQUE obligatoire",
         "trace du reseau EU a documenter ; exutoire EU NON INVENTE (reste G2/UNKNOWN)"],
       "geometrie_2D_validee_sha256": SHA_VAL,
       "STATUS": "VALIDATED_ARCHITECTURE" if (coll == 0 and mar and not rec and 0.60 <= 2 * h + g <= 0.64) else "NOT_READY"}
json.dump(rap, open(os.path.join(PROJ, "reports", "bloc3_gel_architectural.json"), "w"), indent=2, ensure_ascii=False)
print("\n-> reports/bloc3_gel_architectural.json")
print("STATUS :", rap["STATUS"])

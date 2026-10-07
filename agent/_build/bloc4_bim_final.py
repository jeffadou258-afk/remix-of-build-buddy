#!/usr/bin/env python3
"""BLOC 4 — BIM FINAL. Terrain, garage, terrasse, patio, chassis de fenetres,
correction des 2 intrusions mobilier. Base : ARCHITECTURE_FINAL_A.blend."""
import bpy, bmesh, os, json, math, hashlib, datetime
from mathutils import Vector

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
SRC = os.path.join(PROJ, "3D", "ARCHITECTURE_FINAL_A.blend")
DST = os.path.join(PROJ, "3D", "BIM_FINAL_A.blend")
OFF, G = 0.20, 0.05
STAMP = datetime.datetime.now().isoformat(timespec="seconds")
H_RDC, H_ETG = 3.20, 3.20
NIV0, NIV1, NIV2 = 0.00, 3.20, 6.40


def bb(o):
    cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs),
            max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs))


def box(nm, x0, y0, z0, x1, y1, z1):
    m = bpy.data.meshes.new(nm); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(m); bm.free()
    o = bpy.data.objects.new(nm, m); bpy.context.collection.objects.link(o)
    o.scale = (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))
    o.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    return o


bpy.ops.wm.open_mainfile(filepath=SRC)
sha_src = hashlib.sha256(open(SRC, "rb").read()).hexdigest()
n0 = len(bpy.data.objects)

# ---------- 1. CORRECTION DES 2 INTRUSIONS MOBILIER ----------
corr = []
for o in bpy.data.objects:
    if o.name == "MEUBLE_Bureau_bibliotheque":
        o.location.x -= 0.10; corr.append((o.name, "x -0,10")); break
for o in bpy.data.objects:
    if o.name == "MEUBLE_Chambre4_armoire":
        o.location.z += 0.00; o.location.x += 0.00
        o.location.y -= 0.20; corr.append((o.name, "y -0,20")); break
print("1. intrusions corrigees :", corr)

# ---------- 2. TERRAIN / GARAGE / TERRASSE / PATIO ----------
# villa : x[0..10,40] y[0..10,90] ; terrain 15 x 25
TER = (-2.30, -3.00, 12.70, 22.00)
box("SITE_TERRAIN", TER[0], TER[1], -0.05, TER[2], TER[3], 0.00)
box("GARAGE_SOL", 0.00, 10.90, 0.00, 5.00, 15.90, 0.10)
for (nm, x0, y0, x1, y1) in [("GARAGE_MUR_O", 0.00, 10.90, 0.20, 15.90),
                             ("GARAGE_MUR_E", 4.80, 10.90, 5.00, 15.90),
                             ("GARAGE_MUR_N", 0.20, 15.70, 4.80, 15.90)]:
    box(nm, x0, y0, 0.00, x1, y1, 2.50)
box("GARAGE_PORTAIL", 0.30, 10.80, 0.00, 4.70, 10.95, 2.20)
box("GARAGE_TOITURE", -0.20, 10.70, 2.50, 5.20, 16.10, 2.70)
box("TERRASSE_DALLE", 5.20, 10.90, -0.05, 11.20, 14.90, 0.10)
for (nm, x0, y0, x1, y1) in [("TERRASSE_MUR_O", 5.20, 10.90, 5.40, 14.90),
                             ("TERRASSE_MUR_N", 5.20, 14.70, 11.20, 14.90),
                             ("TERRASSE_MUR_E", 11.00, 10.90, 11.20, 14.90)]:
    box(nm, x0, y0, 0.00, x1, y1, 2.60)
box("TERRASSE_TOITURE", 5.00, 10.70, 2.60, 11.40, 15.10, 2.80)
box("TERRASSE_PATIO_SOL", 7.20, 6.70, NIV1, 10.20, 10.70, NIV1 + 0.10)

# ---------- 3. FENETRES (chassis reellement modelises) ----------
FEN = [
 ("F01", "Salon", "Sud",  3.80, 0.10, 5.60, 0.30, 0.90, 2.40),
 ("F02", "Salon", "Sud",  6.20, 0.10, 8.00, 0.30, 0.90, 2.40),
 ("F03", "Salon", "Ouest", 0.10, 1.20, 0.30, 3.00, 0.90, 2.40),
 ("F04", "Salon", "Ouest", 0.10, 3.80, 0.30, 5.60, 0.90, 2.40),
 ("F05", "Salle a manger", "Sud", 0.60, 0.10, 2.40, 0.30, 0.90, 2.40),
 ("F06", "Salle a manger", "Ouest", 0.10, 0.60, 0.30, 2.40, 0.90, 2.40),
 ("F07", "Cuisine", "Nord", 0.80, 10.60, 2.00, 10.80, 1.10, 2.10),
 ("F08", "Bureau", "Nord", 4.20, 10.60, 5.40, 10.80, 1.10, 2.40),
 ("F09", "Buanderie", "Nord", 6.90, 10.60, 7.70, 10.80, 1.40, 2.00),
 ("F10", "WC visiteur", "Est", 10.10, 7.60, 10.30, 8.40, 1.60, 2.20),
 ("F11", "Cuisine", "Ouest", 0.10, 7.80, 0.30, 9.00, 1.10, 2.10),
 ("F12", "Bureau", "Est", 10.10, 7.80, 10.30, 9.00, 1.10, 2.40),
 ("F13", "Suite parentale", "Ouest", 0.10, 0.80, 0.30, 2.60, NIV1 + 0.90, NIV1 + 2.40),
 ("F14", "Chambre 2", "Est", 10.10, 2.00, 10.30, 3.20, NIV1 + 0.90, NIV1 + 2.40),
 ("F15", "Chambre 3", "Est", 10.10, 3.70, 10.30, 4.60, NIV1 + 0.90, NIV1 + 2.40),
 ("F16", "Chambre 4", "Nord", 4.80, 10.60, 6.40, 10.80, NIV1 + 0.90, NIV1 + 2.40),
 ("F17", "Chambre 4", "Sud", 4.80, 6.50, 6.40, 6.70, NIV1 + 0.90, NIV1 + 2.40),
]
for (fid, piece, ori, x0, y0, x1, y1, z0, z1) in FEN:
    box("FENETRE_%s_chassis" % fid, x0, y0, z0, x1, y1, z1)
    box("FENETRE_%s_allege" % fid, x0 - 0.02, y0 - 0.02, z0 - 0.05, x1 + 0.02, y1 + 0.02, z0)
print("3. fenetres modelisees : %d (chassis + allege)" % len(FEN))

bpy.ops.wm.save_as_mainfile(filepath=DST)
sha_dst = hashlib.sha256(open(DST, "rb").read()).hexdigest()

# ---------- 4. VERIFICATION ----------
bpy.ops.wm.open_mainfile(filepath=DST)
mesh = [o for o in bpy.data.objects if o.type == "MESH"]
pre = {}
for o in mesh:
    k = o.name.split("_")[0]; pre[k] = pre.get(k, 0) + 1
coll = []
for m in mesh:
    if not m.name.startswith("MEUBLE_"): continue
    a, b, c, d, e, f = bb(m)
    for o in mesh:
        if o is m or o.name.startswith(("MEUBLE_", "SOL_TERRAIN", "SITE_", "DALLAGE")): continue
        p, q, r, s, t, u = bb(o)
        dx = min(d, s) - max(a, p); dy = min(e, t) - max(b, q); dz = min(f, u) - max(c, r)
        if dx > 0.02 and dy > 0.02 and dz > 0.02:
            coll.append((m.name, o.name, round(dx, 2), round(dy, 2), round(dz, 2)))
rap = {"etude": "bloc4_bim_final", "at": STAMP,
       "source": os.path.basename(SRC), "sha256_source": sha_src,
       "bim_final": os.path.basename(DST), "sha256_bim_final": sha_dst,
       "objets_avant": n0, "objets_apres": len(bpy.data.objects),
       "familles": pre, "intrusions_corrigees": corr,
       "ajouts": {"SITE_TERRAIN": "15 x 25 m", "GARAGE": "5,00 x 5,00 = 25,00 m2 (murs + portail + toiture)",
                  "TERRASSE": "6,00 x 4,00 = 24,00 m2 (dalle + murs + toiture)",
                  "PATIO": "3,00 x 4,00 m au niveau etage", "FENETRES": len(FEN)},
       "fenetres": [{"id": f[0], "piece": f[1], "orientation": f[2], "largeur_m": round(f[4] - f[3], 2),
                     "hauteur_m": round(f[7] - f[6], 2), "allege_m": round(f[6], 2), "statut": "PROPOSED"}
                    for f in FEN],
       "collisions_mobilier_reelles": coll,
       "STATUS": "VERIFIED" if not coll else "PARTIAL"}
json.dump(rap, open(os.path.join(PROJ, "reports", "bloc4_bim_final.json"), "w"), indent=2, ensure_ascii=False)
json.dump({"etude": "nomenclature_portes_fenetres", "at": STAMP,
           "portes_rdc": [{"id": "D01", "piece": "Salle a manger", "largeur_m": 1.35, "mur": "y=4,70", "statut": "PROPOSED"},
                          {"id": "D02", "piece": "Cuisine", "largeur_m": 1.35, "mur": "y=7,10", "statut": "PROPOSED"},
                          {"id": "D03", "piece": "Bureau", "largeur_m": 1.35, "mur": "y=7,10", "statut": "PROPOSED"},
                          {"id": "D04", "piece": "Buanderie", "largeur_m": 1.35, "mur": "y=7,10", "statut": "PROPOSED"},
                          {"id": "D05", "piece": "WC visiteur", "largeur_m": 1.40, "mur": "y=7,10", "statut": "PROPOSED"},
                          {"id": "D00", "piece": "Entree", "largeur_m": 1.20, "mur": "x=10,20", "statut": "VALIDATED (2D)"}],
           "fenetres": rap["fenetres"],
           "reserves": ["La porte de garage et les portes de l'etage ne sont pas documentees (UNKNOWN)",
                        "Les ouvertures de fenetres ne sont pas encore decoupees dans les murs du BIM"],
           "STATUS": "PARTIAL"}, open(os.path.join(PROJ, "reports", "nomenclature_portes_fenetres.json"), "w"),
          indent=2, ensure_ascii=False)
print("4. BIM final : %d objets | familles : %s" % (len(bpy.data.objects),
      ", ".join("%s=%d" % kv for kv in sorted(pre.items(), key=lambda x: -x[1])[:14])))
print("   collisions mobilier reelles (>2 cm) : %d" % len(coll))
if coll: print("   %s" % coll[:4])
print("   -> %s | STATUS : %s" % (os.path.basename(DST), rap["STATUS"]))

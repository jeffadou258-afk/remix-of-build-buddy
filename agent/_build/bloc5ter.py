#!/usr/bin/env python3
"""BLOC 5-TER — Audit des 32 poteaux + 2 scenarios structurels + dossier G3.
AUCUNE decision d'ingenieur prise. Les positions proposees restent PROPOSED."""
import bpy, bmesh, os, json, hashlib, datetime, itertools
from mathutils import Vector

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
SRC = os.path.join(PROJ, "3D", "BIM_FINAL_A3.blend")
SA = os.path.join(PROJ, "3D", "STRUCTURE_G3_SCENARIO_A.blend")
SB = os.path.join(PROJ, "3D", "STRUCTURE_G3_SCENARIO_B.blend")
REP = os.path.join(PROJ, "reports")
C, H = 0.30, 3.20
STAMP = datetime.datetime.now().isoformat(timespec="seconds")


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


def collisions(pots, autres):
    out = []
    for p in pots:
        a, b, c, d, e, g = bb(p)
        for m in autres:
            q, r, s, t, u, v = bb(m)
            dx = min(d, t) - max(a, q); dy = min(e, u) - max(b, r); dz = min(g, v) - max(c, s)
            if dx > 0.01 and dy > 0.01 and dz > 0.01:
                out.append((p.name, m.name, round(dx, 3), round(dy, 3), round(dz, 3)))
    return out


bpy.ops.wm.open_mainfile(filepath=SRC)
sha_src = hashlib.sha256(open(SRC, "rb").read()).hexdigest()
pots = sorted([o for o in bpy.data.objects if o.name.startswith("POUTEAU_RDC")], key=lambda o: o.name)
autres = [o for o in bpy.data.objects if o.name.startswith(("MUR_", "CLOISON_"))]
print("=" * 78); print("BLOC 5-TER — AUDIT"); print("=" * 78)
audit = []
for p in pots:
    a, b, c, d, e, g = bb(p)
    cl = [x for x in collisions([p], autres)]
    audit.append({"id": p.name, "niveau": "RDC", "x_m": round((a + d) / 2, 3), "y_m": round((b + e) / 2, 3),
                  "section_m": [round(d - a, 2), round(e - b, 2)], "z_m": [round(c, 2), round(g, 2)],
                  "nb_conflits": len(cl),
                  "conflits": [{"element": x[1], "dx": x[2], "dy": x[3], "dz": x[4]} for x in cl]})
    if cl:
        print("   %-16s (%.2f,%.2f) -> %d conflit(s) : %s" % (p.name, (a + d) / 2, (b + e) / 2, len(cl),
              ", ".join("%s(dx%.2f dy%.2f)" % (x[1], x[2], x[3]) for x in cl[:3])))
n_tot = sum(a["nb_conflits"] for a in audit)
print("poteaux RDC : %d | conflits totaux : %d" % (len(audit), n_tot))

# ---------- SCENARIO A : trame rederivee des cloisons reelles ----------
XL = sorted({round((bb(o)[0] + bb(o)[3]) / 2, 3) for o in autres if o.name.startswith("CLOISON_") and
             (bb(o)[3] - bb(o)[0]) < 0.30})
YL = sorted({round((bb(o)[1] + bb(o)[4]) / 2, 3) for o in autres if o.name.startswith("CLOISON_") and
             (bb(o)[4] - bb(o)[1]) < 0.30})
print("\nSCENARIO A — lignes de cloison detectees : X=%s" % XL[:8])
print("                                Y=%s" % YL[:8])
XSa = sorted({0.35, 10.05} | set(XL))[:6]
YSa = sorted({0.35, 10.55} | set(YL))[:6]
bpy.ops.wm.open_mainfile(filepath=SRC)
for o in list(bpy.data.objects):
    if o.name.startswith("POUTEAU_"): bpy.data.objects.remove(o, do_unlink=True)
nA = 0
for x in XSa:
    for y in YSa:
        for (lbl, z0, z1) in (("RDC", 0.0, 3.20), ("ETG", 3.20, 6.40)):
            box("POUTEAU_%s_A%02d_%02d" % (lbl, XSa.index(x), YSa.index(y)), x - C / 2, y - C / 2, z0, x + C / 2, y + C / 2, z1)
            nA += 1
bpy.ops.wm.save_as_mainfile(filepath=SA)
bpy.ops.wm.open_mainfile(filepath=SA)
pA = [o for o in bpy.data.objects if o.name.startswith("POUTEAU_RDC")]
cA = collisions(pA, [o for o in bpy.data.objects if o.name.startswith(("MUR_", "CLOISON_"))])
# portees
xsA = sorted({round((bb(o)[0] + bb(o)[3]) / 2, 3) for o in pA})
ysA = sorted({round((bb(o)[1] + bb(o)[4]) / 2, 3) for o in pA})
porxA = [round(xsA[i + 1] - xsA[i], 3) for i in range(len(xsA) - 1)]
poryA = [round(ysA[i + 1] - ysA[i], 3) for i in range(len(ysA) - 1)]
print("   poteaux %d | collisions %d | portees X %s | portees Y %s" % (nA, len(cA), porxA, poryA))

# ---------- SCENARIO B : optimisation du decalage (calcul pur Python, bbox extraites une fois) ----------
bpy.ops.wm.open_mainfile(filepath=SRC)
WALLS = [bb(o) for o in bpy.data.objects if o.name.startswith(("MUR_", "CLOISON_"))]
base = [0.35, 3.533, 6.867, 10.05]
basey = [0.35, 3.70, 7.20, 10.55]

def ncoll(px, py):
    a, b, d, e = px - C / 2, py - C / 2, px + C / 2, py + C / 2
    n = 0
    for (q, r, s_, t, u, v) in WALLS:
        if min(d, t) - max(a, q) > 0.01 and min(e, u) - max(b, r) > 0.01 and min(3.20, v) - max(0.0, s_) > 0.01:
            n += 1
    return n

best = None
for dx in [round(-0.45 + 0.05 * i2, 2) for i2 in range(19)]:
    for dy in [round(-0.45 + 0.05 * j2, 2) for j2 in range(19)]:
        pos = [(x + dx, y + dy) for x in base for y in basey]
        if any(px < 0.35 or px > 10.05 or py < 0.35 or py > 10.55 for (px, py) in pos): continue
        n = sum(ncoll(px, py) for (px, py) in pos)
        if best is None or n < best[0]: best = (n, dx, dy)
print("SCENARIO B — meilleur decalage (dx=%.2f, dy=%.2f) -> %d collisions (calcul bbox)" % (best[1], best[2], best[0]))
bpy.ops.wm.open_mainfile(filepath=SRC)
for o in list(bpy.data.objects):
    if o.name.startswith("POUTEAU_"): bpy.data.objects.remove(o, do_unlink=True)
for k, (x, y) in enumerate([(a + best[1], b + best[2]) for a in base for b in basey]):
    box("POUTEAU_RDC_T%02d" % k, x - C / 2, y - C / 2, 0.0, x + C / 2, y + C / 2, 3.20)
    box("POUTEAU_ETG_T%02d" % k, x - C / 2, y - C / 2, 3.20, x + C / 2, y + C / 2, 6.40)
bpy.ops.wm.save_as_mainfile(filepath=SB)
bpy.ops.wm.open_mainfile(filepath=SB)
pB2 = [o for o in bpy.data.objects if o.name.startswith("POUTEAU_RDC")]
cB = collisions(pB2, [o for o in bpy.data.objects if o.name.startswith(("MUR_", "CLOISON_"))])
txs = sorted({round((bb(o)[0] + bb(o)[3]) / 2, 3) for o in pB2})
tys = sorted({round((bb(o)[1] + bb(o)[4]) / 2, 3) for o in pB2})
print("   poteaux %d | collisions %d | portees X %s | portees Y %s" % (len(pB2), len(cB),
      [round(txs[i2 + 1] - txs[i2], 3) for i2 in range(len(txs) - 1)],
      [round(tys[i2 + 1] - tys[i2], 3) for i2 in range(len(tys) - 1)]))

rap = {"etude": "bloc5ter_g3_structure", "at": STAMP,
       "source": os.path.basename(SRC), "sha256_source": sha_src,
       "audit_poteaux_rdc": audit, "conflits_totaux": n_tot,
       "scenario_A": {"fichier": os.path.basename(SA), "sha256": hashlib.sha256(open(SA, "rb").read()).hexdigest(),
                      "principe": "poteaux positionnes sur les lignes de cloison reellement detectees",
                      "lignes_X_m": XSa, "lignes_Y_m": YSa, "poteaux": nA,
                      "collisions": len(cA), "portees_X_m": porxA, "portees_Y_m": poryA},
       "scenario_B": {"fichier": os.path.basename(SB), "sha256": hashlib.sha256(open(SB, "rb").read()).hexdigest(),
                      "principe": "trame 4x4 conservée, decalage optimise pour minimiser les conflits",
                      "decalage_dx_m": best[1], "decalage_dy_m": best[2],
                      "poteaux": len(pB2), "collisions": len(cB), "portees_X_m": [round(txs[i2+1]-txs[i2],3) for i2 in range(len(txs)-1)], "portees_Y_m": [round(tys[i2+1]-tys[i2],3) for i2 in range(len(tys)-1)]},
       "STATUS": "PENDING_G3"}
json.dump(rap, open(os.path.join(REP, "bloc5ter_g3.json"), "w"), indent=2, ensure_ascii=False)
print("\n-> reports/bloc5ter_g3.json | STATUS PENDING_G3")

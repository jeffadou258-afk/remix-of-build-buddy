#!/usr/bin/env python3
"""BLOC 1 — application de la correction escalier/tremie dans des copies V3.
Escalier deplace a l'ouest et volee ramenee a 4,70 m (giron 0,2765) -> plus aucun
recouvrement avec Chambre 3. Ne modifie ni le 2D VALIDATED ni les V2."""
import bpy, bmesh, os, json, math, hashlib, datetime, sys
from mathutils import Vector

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
OFF, G, H_NIV = 0.20, 0.05, 3.20
NX, NY = int(10.40 / G), int(10.90 / G)
STAMP = datetime.datetime.now().isoformat(timespec="seconds")
NEW = (1.25, 4.75, 5.95, 5.75)        # emprise interieure corrigee (volee 4,70 m)
N_MARCHES = 17


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


fp = json.load(open(os.path.join(PROJ, "floorplan", "floor_plan.json")))
etg = fp["ETAGE"]["rooms"]


def recouvre(r, a, b, ya, yb):
    ox = max(0, min(b, r["x_m"] + r["w_m"]) - max(a, r["x_m"]))
    oy = max(0, min(yb, r["y_m"] + r["d_m"]) - max(ya, r["y_m"]))
    return round(ox * oy, 4), round(ox, 3), round(oy, 3)


rap = {"etude": "bloc1_correction_escalier", "at": STAMP,
       "correction": {"escalier_emprise_interieure_m": list(NEW),
                      "volee_m": round(NEW[2] - NEW[0], 3),
                      "girons": N_MARCHES, "giron_m": round((NEW[2] - NEW[0]) / N_MARCHES, 4),
                      "contremarche_m": round(H_NIV / (N_MARCHES + 1), 4),
                      "blondel_m": round(2 * (H_NIV / (N_MARCHES + 1)) + (NEW[2] - NEW[0]) / N_MARCHES, 4),
                      "deplacement_ouest_m": round(3.00 - NEW[0], 3)},
       "variantes": {}}

for tag in ("A", "B"):
    src = os.path.join(PROJ, "3D", "VARIANT_%s_CIRCULATION_V2.blend" % tag)
    dst = os.path.join(PROJ, "3D", "VARIANT_%s_CIRCULATION_V3.blend" % tag)
    bpy.ops.wm.open_mainfile(filepath=src)
    n_del = 0
    for o in list(bpy.data.objects):
        if o.type == "MESH" and o.name.startswith("V%s_MARCHE" % tag):
            bpy.data.objects.remove(o, do_unlink=True); n_del += 1
    run = NEW[2] - NEW[0]
    for k in range(N_MARCHES):
        a = NEW[0] + k * run / N_MARCHES; b = NEW[0] + (k + 1) * run / N_MARCHES
        box("V%s_MARCHE_%02d" % (tag, k + 1), OFF + a, OFF + NEW[1], 0, OFF + b, OFF + NEW[3],
            (k + 1) * H_NIV / N_MARCHES)
    bpy.ops.wm.save_as_mainfile(filepath=dst)

    # ---- verification ----
    bpy.ops.wm.open_mainfile(filepath=dst)
    mar = sorted([(o.name, bb(o)) for o in bpy.data.objects
                  if o.type == "MESH" and o.name.startswith("V%s_MARCHE" % tag)])
    x0 = min(m[1][0] for m in mar); x1 = max(m[1][3] for m in mar)
    y0 = min(m[1][1] for m in mar); y1 = max(m[1][4] for m in mar)
    zmax = max(m[1][5] for m in mar)
    g = (x1 - x0) / len(mar); h = H_NIV / (len(mar) + 1); bl = 2 * h + g
    occ = [[False] * NY for _ in range(NX)]
    for o in bpy.data.objects:
        if o.type != "MESH" or o.name.startswith(("SOL_TERRAIN", "DALLAGE")): continue
        a, b, c, d, e, f = bb(o)
        if o.name.startswith("V%s_MARCHE" % tag): f = 99.0
        elif not (c - 1e-6 <= 1.0 <= f + 1e-6): continue
        for i in range(max(0, int(math.ceil(a / G - .5))), min(NX, int(math.floor(d / G - .5)) + 1)):
            for j in range(max(0, int(math.ceil(b / G - .5))), min(NY, int(math.floor(e / G - .5)) + 1)):
                occ[i][j] = True
    j = int((OFF + 7.10 - 0.055) / G); n = 0
    while j >= 0 and not occ[int((x0 + x1) / 2 / G)][j]:
        n += 1; j -= 1
    passage = round(n * G, 2)
    xi0, yi0, xi1, yi1 = round(x0 - OFF, 3), round(y0 - OFF, 3), round(x1 - OFF, 3), round(y1 - OFF, 3)
    rec = {}
    for r in etg:
        s, ox, oy = recouvre(r, xi0, xi1, yi0, yi1)
        if s > 0.005: rec[r["name"]] = {"m2": s, "dx": ox, "dy": oy}
    rap["variantes"][tag] = {"fichier": os.path.basename(dst),
        "sha256": hashlib.sha256(open(dst, "rb").read()).hexdigest(),
        "marches": len(mar), "emprise_m": [round(x1 - x0, 3), round(y1 - y0, 3)],
        "emprise_interieure_m": [xi0, yi0, xi1, yi1], "hauteur_atteinte_m": round(zmax, 4),
        "giron_m": round(g, 4), "contremarche_m": round(h, 4), "blondel_m": round(bl, 4),
        "blondel_conforme": bool(0.60 <= bl <= 0.64),
        "passage_libre_m": passage, "recouvrement_etage": rec,
        "tremie_m": [round(xi0 - .05, 2), round(yi0 - .05, 2), round(xi1 + .05, 2), round(yi1 + .05, 2)],
        "conforme": bool(len(mar) == 17 and passage >= 1.20 and not rec and 0.60 <= bl <= 0.64)}
    v = rap["variantes"][tag]
    print("%s_V3 : %s | %d marches | giron %.4f | Blondel %.4f | passage %.2f m | recouvrement etage %s | %s"
          % (tag, os.path.basename(dst), v["marches"], v["giron_m"], v["blondel_m"], v["passage_libre_m"],
             rec or "AUCUN", "CONFORME" if v["conforme"] else "*** NON CONFORME ***"))

rap["STATUS"] = "VERIFIED" if all(rap["variantes"][t]["conforme"] for t in ("A", "B")) else "HUMAN_GATE"
json.dump(rap, open(os.path.join(PROJ, "reports", "bloc1_correction_escalier.json"), "w"),
          indent=2, ensure_ascii=False)
print("STATUS :", rap["STATUS"])
print("-> reports/bloc1_correction_escalier.json")

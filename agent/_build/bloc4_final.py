#!/usr/bin/env python3
"""BLOC 4 (fin) — decoupe reelle des 17 ouvertures de fenetres dans les murs,
correction des collisions residuelles. Ecrit un etat persistant quoi qu'il arrive."""
import bpy, bmesh, os, json, hashlib, datetime, traceback
from mathutils import Vector

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
SRC = os.path.join(PROJ, "3D", "BIM_FINAL_A.blend")
DST = os.path.join(PROJ, "3D", "BIM_FINAL_A2.blend")
REP = os.path.join(PROJ, "reports")
STAMP = datetime.datetime.now().isoformat(timespec="seconds")
journal = []


def bb(o):
    cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs),
            max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs))


try:
    bpy.ops.wm.open_mainfile(filepath=SRC)
    sha_src = hashlib.sha256(open(SRC, "rb").read()).hexdigest()
    n0 = len(bpy.data.objects)

    # --- 1. DECOUPE DES OUVERTURES : boolean difference du volume de chaque fenetre
    #        sur les MUR/CLOISON qui la traversent ---
    fen = [o for o in bpy.data.objects if o.name.startswith("FENETRE_") and o.name.endswith("_chassis")]
    murs = [o for o in bpy.data.objects if o.name.startswith(("MUR_", "CLOISON_"))]
    coupes = 0
    for f in fen:
        a, b, c, d, e, g = bb(f)
        # volume d'ouverture = chassis + 5 cm de jeu
        for m in murs:
            p, q, r, s, t, u = bb(m)
            if a - 0.05 < s and p < d + 0.05 and b - 0.05 < t and q < e + 0.05 and c - 0.05 < u and r < g + 0.05:
                try:
                    mod = m.modifiers.new(name="ouverture", type="BOOLEAN")
                    mod.operation = "DIFFERENCE"
                    mod.object = f
                    bpy.context.view_layer.objects.active = m
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                    coupes += 1
                except Exception as ex:
                    journal.append("echec boolean %s x %s : %s" % (m.name, f.name, ex))
    print("1. ouvertures decoupees (booleens appliques) : %d" % coupes)

    # --- 2. collisions residuelles mobilier ---
    mesh = [o for o in bpy.data.objects if o.type == "MESH"]
    coll = []
    for m in mesh:
        if not m.name.startswith("MEUBLE_"): continue
        a, b, c, d, e, g = bb(m)
        for o in mesh:
            if o is m or o.name.startswith(("MEUBLE_", "SOL_TERRAIN", "SITE_", "DALLAGE")): continue
            p, q, r, s, t, u = bb(o)
            dx = min(d, s) - max(a, p); dy = min(e, t) - max(b, q); dz = min(g, u) - max(c, r)
            if dx > 0.02 and dy > 0.02 and dz > 0.02:
                coll.append((m.name, o.name, round(dx, 2), round(dy, 2), round(dz, 2)))
    print("2. collisions mobilier residuelles : %d" % len(coll))
    for c in coll[:6]: print("   ", c)
    # correction : reculer le mobilier le long de l'axe de plus faible penetration
    for (mn, on, dx, dy, dz) in coll:
        mo = bpy.data.objects.get(mn); oo = bpy.data.objects.get(on)
        if not mo or not oo: continue
        a, b, c, d, e, g = bb(mo); p, q, r, s, t, u = bb(oo)
        ax = min((dx, "x"), (dy, "y"), (dz, "z"))[1]
        pas = min(dx, dy, dz) + 0.05
        if ax == "x":
            mo.location.x += -pas if (a + d) / 2 > (p + s) / 2 else pas
        elif ax == "y":
            mo.location.y += -pas if (b + e) / 2 > (q + t) / 2 else pas
        else:
            mo.location.z += -pas if (c + g) / 2 > (r + u) / 2 else pas
        journal.append("mobilier %s recule de %.2f m sur %s (vs %s)" % (mn, pas, ax, on))
    bpy.ops.wm.save_as_mainfile(filepath=DST)
    sha_dst = hashlib.sha256(open(DST, "rb").read()).hexdigest()

    # --- 3. re-verification ---
    bpy.ops.wm.open_mainfile(filepath=DST)
    mesh = [o for o in bpy.data.objects if o.type == "MESH"]
    coll2 = []
    for m in mesh:
        if not m.name.startswith("MEUBLE_"): continue
        a, b, c, d, e, g = bb(m)
        for o in mesh:
            if o is m or o.name.startswith(("MEUBLE_", "SOL_TERRAIN", "SITE_", "DALLAGE")): continue
            p, q, r, s, t, u = bb(o)
            dx = min(d, s) - max(a, p); dy = min(e, t) - max(b, q); dz = min(g, u) - max(c, r)
            if dx > 0.02 and dy > 0.02 and dz > 0.02: coll2.append((m.name, o.name))
    pre = {}
    for o in mesh:
        k = o.name.split("_")[0]; pre[k] = pre.get(k, 0) + 1
    rap = {"etude": "bloc4_final", "at": STAMP, "source": os.path.basename(SRC),
           "sha256_source": sha_src, "bim_final2": os.path.basename(DST), "sha256": sha_dst,
           "objets": len(bpy.data.objects), "familles": pre,
           "ouvertures_decoupees": coupes, "collisions_avant": len(coll),
           "collisions_apres": len(coll2), "collisions_detail": coll2,
           "journal": journal,
           "STATUS": "VERIFIED" if (len(coll2) == 0 and coupes >= 17) else "PARTIAL"}
    json.dump(rap, open(os.path.join(REP, "bloc4_final.json"), "w"), indent=2, ensure_ascii=False)
    print("3. collisions apres correction : %d | objets : %d" % (len(coll2), len(bpy.data.objects)))
    print("   -> %s | STATUS : %s" % (os.path.basename(DST), rap["STATUS"]))
except Exception as e:
    journal.append("ERREUR : %s\n%s" % (e, traceback.format_exc()[:800]))
    json.dump({"etude": "bloc4_final", "at": STAMP, "STATUS": "FAILED", "journal": journal},
              open(os.path.join(REP, "bloc4_final.json"), "w"), indent=2, ensure_ascii=False)
    print("ERREUR :", e)

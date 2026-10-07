#!/usr/bin/env python3
"""Export de la table d'objets BIM (pour metre tracable objet par objet)."""
import bpy, os, json, hashlib, datetime, sys

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
BIM = sys.argv[-1] if sys.argv[-1].endswith(".blend") else os.path.join(PROJ, "3D", "BIM_villa_R1_COMPLET.blend")
bpy.ops.wm.open_mainfile(filepath=BIM)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


rows = []
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    b = o.bound_box
    x0 = min(v[0] for v in b) + o.location.x
    y0 = min(v[1] for v in b) + o.location.y
    z0 = min(v[2] for v in b) + o.location.z
    x1 = max(v[0] for v in b) + o.location.x
    y1 = max(v[1] for v in b) + o.location.y
    z1 = max(v[2] for v in b) + o.location.z
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    grp = o.name.split("_")[0]
    mat = o.data.materials[0].name if o.data.materials else "?"
    rec = {"nom": o.name, "groupe": grp, "materiau": mat,
           "x0": round(x0, 3), "y0": round(y0, 3), "z0": round(z0, 3),
           "dx": round(dx, 3), "dy": round(dy, 3), "dz": round(dz, 3),
           "vol_m3": round(dx * dy * dz, 5),
           "face_verticale_m2": round(2 * (dx + dy) * dz, 4),
           "face_horizontale_m2": round(dx * dy, 5)}
    rows.append(rec)

out = {"at": datetime.datetime.now().isoformat(timespec="seconds"),
       "fichier": os.path.basename(BIM), "sha256_blend": sha(BIM),
       "objets": len(rows), "table": rows}
suffix = "_v2" if "v2" in BIM else ""
p = os.path.join(PROJ, "3D", "bim_object_table%s.json" % suffix)
json.dump(out, open(p, "w"), indent=1, ensure_ascii=False)
print("objets exportes : %d" % len(rows))
print("-> %s (%d o)" % (p, os.path.getsize(p)))
vol = sum(r["vol_m3"] for r in rows)
print("volume total (enveloppes) : %.3f m3" % vol)

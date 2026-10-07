#!/usr/bin/env python3
"""Verification PHYSIQUE du modele BIM : reouverture du .blend + controles."""
import bpy, os, json, hashlib

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
BIM = os.path.join(PROJ, "3D", "BIM_villa_R1_VALIDATED.blend")
OLD = os.path.join(PROJ, "3D", "scene_villa_conceptuelle.blend")
OLD_SHA = "4afddfae76f69022e9065be433b5469e08e8e93b81e1f291a35bd3e477efdab1"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


print("=" * 78)
print("VERIFICATION PHYSIQUE DU MODELE BIM")
print("=" * 78)
res = {}
res["bim_exists"] = os.path.isfile(BIM)
res["bim_octets"] = os.path.getsize(BIM)
res["bim_sha256"] = sha(BIM)
print("\n[1] FICHIER")
print("  %s" % BIM)
print("  %d octets   sha256 = %s" % (res["bim_octets"], res["bim_sha256"]))

print("\n[2] RE-OUVERTURE REELLE PAR BLENDER")
bpy.ops.wm.open_mainfile(filepath=BIM)
mesh = [o for o in bpy.data.objects if o.type == "MESH"]
print("  Blender %s a ouvert le fichier" % bpy.app.version_string)
print("  objets maillage : %d" % len(mesh))
res["objets"] = len(mesh)

# bbox reelle
xs = []
ys = []
zs = []
vol = 0.0
degen = []
for o in mesh:
    b = o.bound_box
    dx = max(v[0] for v in b) - min(v[0] for v in b)
    dy = max(v[1] for v in b) - min(v[1] for v in b)
    dz = max(v[2] for v in b) - min(v[2] for v in b)
    v = dx * dy * dz
    vol += v
    if v <= 0:
        degen.append(o.name)
    for c in b:
        xs.append(c[0] + o.location.x)
        ys.append(c[1] + o.location.y)
        zs.append(c[2] + o.location.z)
print("\n[3] EMPRISE REELLE DU MODELE (mesuree sur les maillages)")
print("  X : [%.2f ; %.2f]  largeur %.2f m" % (min(xs), max(xs), max(xs) - min(xs)))
print("  Y : [%.2f ; %.2f]  profondeur %.2f m" % (min(ys), max(ys), max(ys) - min(ys)))
print("  Z : [%.2f ; %.2f]  hauteur %.2f m" % (min(zs), max(zs), max(zs) - min(zs)))
res["bbox"] = {"x": [round(min(xs), 2), round(max(xs), 2)],
               "y": [round(min(ys), 2), round(max(ys), 2)],
               "z": [round(min(zs), 2), round(max(zs), 2)]}
print("  volume total enveloppes : %.2f m3" % vol)
print("  objets degeneres (volume nul) : %d %s" % (len(degen), degen[:5]))
res["objets_degeneres"] = len(degen)

# groupements
groups = {}
for o in mesh:
    g = o.name.split("_")[0]
    groups.setdefault(g, []).append(o.name)
print("\n[4] COMPOSITION")
for g in sorted(groups):
    print("  %-12s %3d" % (g, len(groups[g])))
res["groupes"] = {g: len(v) for g, v in groups.items()}

# controles geometriques
print("\n[5] CONTROLES")
checks = []


def ck(n, ok, mes, att):
    checks.append({"controle": n, "resultat": "PASS" if ok else "FAIL", "mesure": mes, "attendu": att})
    print("  %-40s %-5s %s" % (n, "PASS" if ok else "FAIL", mes))


ck("16 poteaux presents", len(groups.get("POTEAU", [])) == 16, len(groups.get("POTEAU", [])), 16)
ck("16 semelles presentes", len(groups.get("SEMELLE", [])) == 16, len(groups.get("SEMELLE", [])), 16)
ck("16 poutres presentes (2 niveaux x 8)", len(groups.get("POUTRE", [])) == 16,
   len(groups.get("POUTRE", [])), 16)
ck("emprise X = 10,40 m (+terrassement)", abs((max(xs) - min(xs)) - 16.40) < 0.02,
   round(max(xs) - min(xs), 2), "16,40 (10,40 bati + 3,0 terrain)")
ck("hauteur totale = 8,70 m (ancrage -> acrotere)",
   abs((max(zs) - min(zs)) - 8.70) < 0.02, round(max(zs) - min(zs), 2), 8.70)
ck("aucun objet degenere", len(degen) == 0, len(degen), 0)
ck("materiaux assignes", len(bpy.data.materials) >= 5, len(bpy.data.materials), ">= 5")

print("\n[6] ANCIEN MODELE CONCEPTUEL — INTACT ?")
res["old_sha256"] = sha(OLD)
res["old_intact"] = (res["old_sha256"] == OLD_SHA)
print("  sha256 : %s" % res["old_sha256"])
print("  attendu: %s" % OLD_SHA)
print("  => %s" % ("INTACT (jamais touche)" if res["old_intact"] else "MODIFIE !!"))
ck("ancien .blend intact", res["old_intact"], res["old_sha256"][:16] + "…", OLD_SHA[:16] + "…")

ck("nouveau .blend different de l'ancien", res["bim_sha256"] != OLD_SHA,
   res["bim_sha256"][:16] + "…", "different")

p = os.path.join(PROJ, "3D", "bim_verification.json")
res["controles"] = checks
res["SYNTHESE"] = {"PASS": sum(1 for c in checks if c["resultat"] == "PASS"),
                   "FAIL": sum(1 for c in checks if c["resultat"] == "FAIL"), "total": len(checks)}
res["STATUS"] = "VERIFIED" if res["SYNTHESE"]["FAIL"] == 0 else "FAILED"
json.dump(res, open(p, "w"), indent=2, ensure_ascii=False)

print("\n" + "=" * 78)
print("SYNTHESE : %d PASS / %d FAIL" % (res["SYNTHESE"]["PASS"], res["SYNTHESE"]["FAIL"]))
print("STATUS   : %s" % res["STATUS"])
print("-> %s" % p)
print("=" * 78)

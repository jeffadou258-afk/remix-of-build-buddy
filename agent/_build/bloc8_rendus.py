#!/usr/bin/env python3
"""BLOC 8 — 10 rendus reels depuis BIM_FINAL_A3.blend. Copie experimentale pour les cameras."""
import bpy, os, json, math, hashlib, datetime
from mathutils import Vector

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
SRC = os.path.join(PROJ, "3D", "BIM_FINAL_A3.blend")
RB = os.path.join(PROJ, "3D", "BIM_RENDER_A3.blend")
RD = os.path.join(PROJ, "renders")
os.makedirs(RD, exist_ok=True)
S = datetime.datetime.now().isoformat(timespec="seconds")
RES = (1920, 1080)

bpy.ops.wm.open_mainfile(filepath=SRC)
sha_src = hashlib.sha256(open(SRC, "rb").read()).hexdigest()
# enums reels
engines = [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
ENG = "BLENDER_EEVEE" if "BLENDER_EEVEE" in engines else engines[0]
print("moteur :", ENG, "| disponibles :", engines)

# --- materiaux (HYPOTHESIS) ---
MATS = {"mur": (0.88, 0.87, 0.84, 1), "cloison": (0.93, 0.92, 0.90, 1), "fen": (0.45, 0.68, 0.85, 1),
        "structure": (0.72, 0.72, 0.74, 1), "fondation": (0.62, 0.58, 0.54, 1), "sol": (0.55, 0.48, 0.42, 1),
        "mobilier": (0.66, 0.55, 0.40, 1), "terrasse": (0.82, 0.78, 0.70, 1), "garage": (0.70, 0.68, 0.64, 1),
        "etancheite": (0.35, 0.38, 0.42, 1), "terrain": (0.42, 0.52, 0.34, 1), "gardecorps": (0.60, 0.65, 0.70, 1)}
REG = {"MUR_": "mur", "CLOISON_": "cloison", "FENETRE_": "fen", "POUTEAU_": "structure", "POUTRE_": "structure",
       "DALLE_": "structure", "ACRO_": "structure", "SEMELLE_": "fondation", "LONGRINE_": "fondation",
       "DALLAGE_": "sol", "MEUBLE_": "mobilier", "TERRASSE_": "terrasse", "GARAGE_": "garage",
       "ETANCHEITE_": "etancheite", "SITE_": "terrain", "GARDE_": "gardecorps", "VA_MARCHE": "structure"}
for nm, col in MATS.items():
    m = bpy.data.materials.get(nm) or bpy.data.materials.new(nm)
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    if bs: bs.inputs["Base Color"].default_value = col
    m.diffuse_color = col
nmat = 0
for o in bpy.data.objects:
    if o.type != "MESH": continue
    for pre, mn in REG.items():
        if o.name.startswith(pre):
            if not o.data.materials: o.data.materials.append(bpy.data.materials[mn]); nmat += 1
            break
print("materiaux assignes :", nmat)

# --- lumiere + ciel ---
w = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
bpy.context.scene.world = w
w.use_nodes = True
bg = next((n for n in w.node_tree.nodes if n.type == "BACKGROUND"), None)
if bg is None:
    bg = w.node_tree.nodes.new("ShaderNodeBackground")
    out = next((n for n in w.node_tree.nodes if n.type == "OUTPUT_WORLD"), None)
    if out: w.node_tree.links.new(bg.outputs[0], out.inputs[0])
bg.inputs[0].default_value = (0.55, 0.68, 0.85, 1)
bg.inputs[1].default_value = 1.1
sun = bpy.data.objects.new("SOLEIL", bpy.data.lights.new("SOLEIL", "SUN"))
sun.data.energy = 3.5; sun.rotation_euler = (math.radians(50), 0, math.radians(35))
bpy.context.collection.objects.link(sun)

sc = bpy.context.scene
sc.render.engine = ENG
sc.render.resolution_x, sc.render.resolution_y = RES
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
sc.render.film_transparent = False
try:
    sc.eevee.taa_render_samples = 32
except Exception:
    pass

CAMS = [
 ("R01", "vue principale", (26, -16, 13), (5.0, 5.0, 4.0), 38, None),
 ("R02", "facade Nord", (5.0, 34, 6), (5.0, 11.0, 4.0), 42, None),
 ("R03", "facade Sud", (5.0, -24, 6), (5.0, 0.0, 4.0), 42, None),
 ("R04", "facade Est", (30, 5.0, 6), (10.4, 5.0, 4.0), 42, None),
 ("R05", "facade Ouest", (-20, 5.0, 6), (0.0, 5.0, 4.0), 42, None),
 ("R06", "vue aerienne", (14, -14, 42), (5.0, 8.0, 0.0), 38, None),
 ("R07", "salon", (9.6, 1.2, 1.65), (4.2, 4.2, 1.4), 58, 75),
 ("R08", "salon + salle a manger", (9.6, 4.2, 1.65), (0.6, 1.6, 1.4), 62, 75),
 ("R09", "cuisine", (3.5, 7.6, 1.65), (0.4, 10.2, 1.4), 60, 75),
 ("R10", "escalier / circulation", (9.0, 5.6, 1.70), (1.8, 5.5, 1.90), 60, 72),
]
res = []
for (rid, lib, pos, cible, foc, clip) in CAMS:
    cam = bpy.data.objects.new("CAM_%s" % rid, bpy.data.cameras.new("CAM_%s" % rid))
    cam.location = pos
    cam.data.lens = foc
    if clip: cam.data.clip_end = clip
    d = Vector(cible) - Vector(pos)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    bpy.context.collection.objects.link(cam)
    sc.camera = cam
    f = os.path.join(RD, "%s_%s.png" % (rid, lib.replace(" ", "_").replace("/", "")))
    sc.render.filepath = f
    try:
        bpy.ops.render.render(write_still=True)
        ok = os.path.exists(f) and os.path.getsize(f) > 1000
        res.append({"id": rid, "libelle": lib, "file": os.path.relpath(f, PROJ),
                    "exists": os.path.exists(f), "bytes": os.path.getsize(f) if os.path.exists(f) else 0,
                    "resolution": "%dx%d" % RES, "sha256": hashlib.sha256(open(f, "rb").read()).hexdigest() if ok else None,
                    "camera": "CAM_%s (%.1f,%.1f,%.1f) focale %d mm" % (rid, pos[0], pos[1], pos[2], foc),
                    "source_blend": os.path.basename(RB) if os.path.exists(RB) else os.path.basename(SRC),
                    "status": "GENERATED" if ok else "FAILED"})
        print("  %s %-26s %8d o %s" % (rid, lib, res[-1]["bytes"], "OK" if ok else "*** ECHEC ***"))
    except Exception as e:
        res.append({"id": rid, "libelle": lib, "file": None, "exists": False, "bytes": 0, "resolution": None,
                    "sha256": None, "camera": "CAM_%s" % rid, "source_blend": os.path.basename(SRC),
                    "status": "FAILED", "erreur": str(e)})
        print("  %s %-26s ECHEC : %s" % (rid, lib, e))

bpy.ops.wm.save_as_mainfile(filepath=RB)
sha_rb = hashlib.sha256(open(RB, "rb").read()).hexdigest()
rap = {"etude": "bloc8_rendus", "at": S, "moteur": ENG, "resolution": "%dx%d" % RES,
       "source_bim": os.path.basename(SRC), "sha256_bim": sha_src,
       "fichier_cameras": os.path.basename(RB), "sha256_cameras": sha_rb,
       "rendus": res, "generes": len([r for r in res if r["status"] == "GENERATED"]),
       "echecs": len([r for r in res if r["status"] == "FAILED"]),
       "materiaux": {"statut": "MATERIALS_HYPOTHESIS",
                     "note": "aucun choix de finition n'est defini dans les donnees du projet : les 12 materiaux "
                             "sont des couleurs de travail creees pour le rendu, NON des choix valides"},
       "toiture": {"statut": "ROOF_NOT_DEFINED",
                   "note": "la pente de toiture n'est pas definie ; seule la toiture-terrasse (etancheite plane) existe dans le BIM"},
       "structure": "PROPOSED / PENDING_G3 — jamais presentee comme validee",
       "STATUS": "VERIFIED" if all(r["status"] == "GENERATED" for r in res) else "PARTIAL"}
json.dump(rap, open(os.path.join(PROJ, "reports", "bloc8_rendus.json"), "w"), indent=2, ensure_ascii=False)
print("rendus generes : %d / 10 | moteur %s" % (rap["generes"], ENG))

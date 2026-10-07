"""
Construction Agent v2.0.0 — render_views.py
Blender headless : ouvre un .blend EXISTANT, place les cameras, rend les vues.

Usage :
  blender --background --factory-startup --python render_views.py -- <blend> <out_dir> <width> <height>
"""
import bpy
import os
import sys
import math
from mathutils import Vector

argv = sys.argv
args = argv[argv.index("--") + 1:] if "--" in argv else []
if len(args) < 4:
    print("ARGS_MISSING")
    sys.exit(2)
blend, out_dir, W, H = args[0], args[1], int(args[2]), int(args[3])

if not os.path.isfile(blend):
    print("BLEND_NOT_FOUND=%s" % blend)
    sys.exit(3)

bpy.ops.wm.open_mainfile(filepath=blend)
scene = bpy.context.scene
os.makedirs(out_dir, exist_ok=True)
print("ENGINE=%s" % scene.render.engine)

# --- boite englobante reelle du bati -----------------------------------------
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != "Terrain"]
pts = []
for o in meshes:
    for c in o.bound_box:
        pts.append(o.matrix_world @ Vector(c))
if not pts:
    print("NO_MESH")
    sys.exit(4)
xs = [p.x for p in pts]
ys = [p.y for p in pts]
zs = [p.z for p in pts]
cx, cy, cz = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2
sx, sy, sz = max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)
R = max(sx, sy, sz)

scene.render.resolution_x = W
scene.render.resolution_y = H
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False

cam_data = bpy.data.cameras.new("ViewCam")
cam = bpy.data.objects.new("ViewCam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

VIEWS = [
    ("01_Facade",   (cx + R * 0.95, cy - R * 1.55, cz + R * 0.32), (cx, cy, cz + sz * 0.15), 45),
    ("02_Entree",   (cx + R * 0.10, cy - R * 1.05, cz - sz * 0.25), (cx, cy, cz - sz * 0.20), 32),
    ("03_Terrasse", (cx + R * 1.70, cy - R * 0.62, cz + R * 0.20), (cx + R * 0.55, cy, cz - sz * 0.10), 42),
    ("04_Aerienne", (cx + R * 1.25, cy - R * 1.75, cz + R * 1.55), (cx, cy, cz), 32),
    ("05_Generale", (cx - R * 1.90, cy - R * 1.45, cz + R * 0.62), (cx, cy, cz), 38),
]

for name, pos, tgt, lens in VIEWS:
    cam_data.lens = lens
    cam.location = Vector(pos)
    d = cam.location - Vector(tgt)
    cam.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(out_dir, name)
    bpy.ops.render.render(write_still=True)
    p = os.path.join(out_dir, "%s.png" % name)
    print("RENDERED=%s EXISTS=%s SIZE=%s" % (
        p, os.path.isfile(p), os.path.getsize(p) if os.path.isfile(p) else 0))

print("RENDER_ALL_DONE")

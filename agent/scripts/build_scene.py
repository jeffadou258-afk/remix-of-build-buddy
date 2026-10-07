"""
Construction Agent v2.0.0 — build_scene.py
Blender headless : construit la maquette parametrique depuis dimensions.json + program.json.

Usage :
  blender --background --factory-startup --python build_scene.py -- <project_dir> <out_blend>
"""
import bpy
import os
import sys
import json
import math

argv = sys.argv
args = argv[argv.index("--") + 1:] if "--" in argv else []
if len(args) < 2:
    print("ARGS_MISSING")
    sys.exit(2)
project_dir, out_blend = args[0], args[1]

with open(os.path.join(project_dir, "dimensions", "dimensions.json")) as f:
    dims = json.load(f)
prog = {}
pp = os.path.join(project_dir, "program", "program.json")
if os.path.isfile(pp):
    with open(pp) as f:
        prog = json.load(f)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
H = 3.0  # hauteur de niveau (hypothese de modelisation)


def mat(name, color, rough=0.5, metal=0.0, emit=None, strength=4.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit is not None:
        for k in ("Emission Color", "Emission"):
            if k in b.inputs:
                b.inputs[k].default_value = emit
                break
        if "Emission Strength" in b.inputs:
            b.inputs["Emission Strength"].default_value = strength
    return m


M_CONC = mat("Beton_blanc", (0.86, 0.85, 0.82, 1), 0.55)
M_CONC2 = mat("Beton_gris", (0.55, 0.55, 0.56, 1), 0.6)
M_WOOD = mat("Bois_terrasse", (0.42, 0.24, 0.11, 1), 0.65)
M_WOODL = mat("Bois_clin", (0.55, 0.35, 0.17, 1), 0.6)
M_GLASS = mat("Vitrage", (0.13, 0.20, 0.26, 1), 0.05, 0.55)
M_METAL = mat("Metal_fonce", (0.09, 0.09, 0.10, 1), 0.35, 0.9)
M_GRASS = mat("Pelouse", (0.16, 0.32, 0.12, 1), 0.9)
M_PATH = mat("Voirie", (0.30, 0.30, 0.31, 1), 0.8)
M_WATER = mat("Eau_piscine", (0.05, 0.35, 0.45, 1), 0.02, 0.2)
M_LED = mat("LED", (1, 0.95, 0.85, 1), 0.3, emit=(1, 0.93, 0.8, 1), strength=6)


def box(name, size, loc, material):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    o.data.materials.append(material)
    return o


# --- niveaux depuis dimensions.json -----------------------------------------
levels = [l for l in dims.get("levels", []) if l["level"] != "EXTERIEUR"]
if not levels:
    levels = [{"level": "RDC", "width_m": 13.5, "depth_m": 6.0, "surface_m2": 81.0}]

max_w = max(l["width_m"] for l in levels)
max_d = max(l["depth_m"] for l in levels)
objects = []

for i, lv in enumerate(levels):
    z0 = i * H
    objects.append(box("Volume_%s" % lv["level"], (lv["width_m"], lv["depth_m"], H),
                       (0, 0, z0 + H / 2), M_CONC if i == 0 else M_CONC))
    # bandeau vitre sur la facade sud (-Y)
    gw = min(lv["width_m"] * 0.62, 8.5)
    objects.append(box("Vitrage_%s" % lv["level"], (gw, 0.12, H * 0.72),
                       (lv["width_m"] * 0.12, -lv["depth_m"] / 2, z0 + H * 0.45), M_GLASS))
    objects.append(box("Menuiserie_%s" % lv["level"], (gw * 1.04, 0.28, 0.20),
                       (lv["width_m"] * 0.12, -lv["depth_m"] / 2, z0 + H * 0.84), M_METAL))

# --- toiture plate + acrotere -------------------------------------------------
top = len(levels) * H
objects.append(box("Toiture", (max_w + 1.6, max_d + 1.8, 0.35), (-0.5, 0, top + 0.175), M_CONC2))
objects.append(box("Acrotere", (max_w + 1.6, max_d + 1.8, 0.25), (-0.5, 0, top + 0.45), M_CONC))

# --- clins bois verticaux -----------------------------------------------------
for k in range(9):
    objects.append(box("Clin_%d" % k, (0.14, 0.16, H * 0.9),
                       (-max_w * 0.45 + k * (max_w * 0.03), -max_d / 2 - 0.06, H * 0.47), M_WOODL))

# --- auvent sur la baie -------------------------------------------------------
objects.append(box("Auvent", (min(max_w * 0.45, 5.5), 2.2, 0.16),
                   (max_w * 0.16, -max_d / 2 - 1.0, H + 0.05), M_WOODL))

# --- garage -------------------------------------------------------------------
gw2 = min(6.0, max_w * 0.45)
gx = -(max_w / 2 + gw2 / 2)
objects.append(box("Garage", (gw2, max_d, H), (gx, 0, H / 2), M_CONC))
objects.append(box("Porte_garage", (gw2 * 0.76, 0.14, H * 0.8), (gx, -max_d / 2, H * 0.4), M_METAL))

# --- terrasse couverte --------------------------------------------------------
tw, td = 8.0, max_d
tx = max_w / 2 + tw / 2
objects.append(box("Terrasse", (tw, td, 0.20), (tx, 0, 0.10), M_WOOD))
objects.append(box("Pergola", (tw, td, 0.18), (tx, 0, H + 0.09), M_WOODL))
for si, sx in enumerate((-tw * 0.47, 0.0, tw * 0.47)):
    for sj, sy in enumerate((td * 0.45, -td * 0.45)):
        objects.append(box("Poteau_%d_%d" % (si, sj), (0.18, 0.18, H),
                           (tx + sx, sy, H / 2), M_WOODL))

# --- terrain + piscine --------------------------------------------------------
BW, BD = max_w + gw2 + tw + 18.0, max_d + 20.0
objects.append(box("Terrain", (BW, BD, 0.4), (0, 4, -0.2), M_GRASS))
objects.append(box("Voirie", (BW, 4.5, 0.42), (0, -BD / 2 + 1.5, -0.19), M_PATH))
objects.append(box("Allee", (4, 8, 0.44), (gx, -max_d / 2 - 4, -0.18), M_CONC2))
objects.append(box("Piscine", (7.5, 3.2, 0.30), (tx - 1.5, -max_d / 2 - 6.5, 0.05), M_WATER))
objects.append(box("Margelle", (7.9, 3.6, 0.22), (tx - 1.5, -max_d / 2 - 6.5, -0.02), M_CONC))

# --- eclairage architectural --------------------------------------------------
for k in range(4):
    objects.append(box("Led_%d" % k, (0.9, 0.05, 0.05),
                       (-max_w * 0.3 + k * (max_w * 0.2), -max_d / 2 - 1.9, H * 0.99), M_LED))

# --- lumieres + ciel ----------------------------------------------------------
bpy.ops.object.light_add(type='SUN', location=(14, -16, 22))
sun = bpy.context.active_object
sun.data.energy = 4.5
sun.data.angle = math.radians(1.5)
sun.rotation_euler = (math.radians(52), 0, math.radians(-42))

bpy.ops.object.light_add(type='AREA', location=(-16, -14, 12))
fill = bpy.context.active_object
fill.data.energy = 900
fill.data.size = 12
fill.rotation_euler = (math.radians(58), 0, math.radians(48))

world = bpy.data.worlds.new("Sky")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.42, 0.60, 0.82, 1.0)
world.node_tree.nodes["Background"].inputs[1].default_value = 1.1

# Blender 5.2 a RENOMME les moteurs : detecter ce qui existe reellement.
_engines = [e.identifier for e in scene.render.bl_rna.properties["engine"].enum_items]
if "BLENDER_EEVEE_NEXT" in _engines:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
elif "BLENDER_EEVEE" in _engines:
    scene.render.engine = "BLENDER_EEVEE"
else:
    scene.render.engine = "CYCLES"
if scene.render.engine.startswith("BLENDER_EEVEE"):
    try:
        scene.eevee.taa_render_samples = 64
        if hasattr(scene.eevee, "use_raytracing"):
            scene.eevee.use_raytracing = True
    except Exception:
        pass
else:
    scene.cycles.samples = 48
print("ENGINE=%s" % scene.render.engine)
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.image_settings.file_format = 'PNG'

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

os.makedirs(os.path.dirname(out_blend), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=out_blend)

mesh_count = len([o for o in bpy.data.objects if o.type == 'MESH'])
print("OBJECTS=%d" % mesh_count)
print("BLEND_SAVED=%s" % out_blend)
print("SCENE_BUILD_OK")

"""
ConstructionAgent — 3D Visual Engine (REEL)
Villa Moderne Haut de Gamme — Variante B
RDC 81 m2 / Etage 69 m2 / Interieur 150 m2 / Exterieur couvert 49 m2
Execute par Blender 5.2.2 en mode headless.
"""
import bpy, os, math, sys
from mathutils import Vector

OUT_DIR = "/Users/mac/ConstructionAgent/Projets/PRJ_1701484686/3D"
RENDER_DIR = os.path.join(OUT_DIR, "Renders")
os.makedirs(RENDER_DIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def mat(name, color=(0.8, 0.8, 0.8, 1.0), rough=0.5, metal=0.0,
        transm=0.0, ior=1.45, emit=None, emit_strength=3.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    for k in ("Transmission Weight", "Transmission"):
        if k in b.inputs:
            b.inputs[k].default_value = transm
            break
    if "IOR" in b.inputs:
        b.inputs["IOR"].default_value = ior
    if emit is not None:
        for k in ("Emission Color", "Emission"):
            if k in b.inputs:
                b.inputs[k].default_value = emit
                break
        if "Emission Strength" in b.inputs:
            b.inputs["Emission Strength"].default_value = emit_strength
    return m


def box(name, size, loc, material):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    o.data.materials.append(material)
    return o


# ---------------- MATERIAUX ----------------
M_CONCRETE = mat("Beton_blanc", (0.86, 0.85, 0.82, 1), rough=0.55)
M_CONCRETE_D = mat("Beton_gris", (0.55, 0.55, 0.56, 1), rough=0.6)
M_WOOD = mat("Bois_terrasse", (0.42, 0.24, 0.11, 1), rough=0.65)
M_WOOD_L = mat("Bois_clin", (0.55, 0.35, 0.17, 1), rough=0.6)
M_GLASS = mat("Vitrage", (0.13, 0.20, 0.26, 1), rough=0.05, metal=0.55)
M_METAL = mat("Metal_fonce", (0.09, 0.09, 0.10, 1), rough=0.35, metal=0.9)
M_GRASS = mat("Pelouse", (0.16, 0.32, 0.12, 1), rough=0.9)
M_PATH = mat("Voirie", (0.30, 0.30, 0.31, 1), rough=0.8)
M_WATER = mat("Eau_piscine", (0.05, 0.35, 0.45, 1), rough=0.02, metal=0.2)
M_LED = mat("LED", (1, 0.95, 0.85, 1), rough=0.3, emit=(1, 0.93, 0.8, 1), emit_strength=6)

# ---------------- TERRAIN ----------------
box("Terrain", (46, 34, 0.4), (0, 4, -0.2), M_GRASS)
box("Voirie", (46, 4.5, 0.42), (0, -9.5, -0.19), M_PATH)
box("Allee", (4, 8, 0.44), (-9.5, -5.5, -0.18), M_CONCRETE_D)

# ---------------- RDC : 13.5 x 6.0 = 81 m2 ----------------
RDC_W, RDC_D, H = 13.5, 6.0, 3.0
box("RDC_volume", (RDC_W, RDC_D, H), (0, 0, H / 2), M_CONCRETE)

# ---------------- ETAGE : 11.5 x 6.0 = 69 m2 ----------------
ETG_W = 11.5
box("Etage_volume", (ETG_W, RDC_D, H), (-1.0, 0, H + H / 2), M_CONCRETE)

# ---------------- TOITURE PLATE + DEBORD ----------------
box("Toiture", (ETG_W + 1.6, RDC_D + 1.8, 0.35), (-1.0, 0, 2 * H + 0.175), M_CONCRETE_D)
box("Acrotere", (ETG_W + 1.6, RDC_D + 1.8, 0.25), (-1.0, 0, 2 * H + 0.45), M_CONCRETE)

# ---------------- FACADE VITREE (sud, y = -3) ----------------
# RDC : grand sejour vitre 8.5 m
box("Vitrage_RDC", (8.5, 0.12, 2.5), (2.2, -RDC_D / 2, 1.35), M_GLASS)
box("Men_baie_RDC", (9.0, 0.30, 0.20), (2.2, -RDC_D / 2, 2.7), M_METAL)
box("Vitrage_RDC_2", (2.2, 0.12, 2.5), (-3.6, -RDC_D / 2, 1.35), M_GLASS)
# Etage : bandeau vitre 7.0 m
box("Vitrage_Etage", (7.0, 0.12, 2.2), (0.5, -RDC_D / 2, H + 1.35), M_GLASS)
box("Men_baie_Etage", (7.4, 0.30, 0.20), (0.5, -RDC_D / 2, 2 * H - 0.2), M_METAL)

# ---------------- CLINS BOIS VERTICAUX ----------------
for i in range(9):
    x = -6.2 + i * 0.36
    box(f"Clin_{i}", (0.14, 0.16, 2.7), (x, -RDC_D / 2 - 0.05, 1.4), M_WOOD_L)

# ---------------- BRISE-SOLEIL / AUVENT ----------------
box("Auvent", (5.5, 2.2, 0.16), (2.2, -RDC_D / 2 - 1.0, 3.05), M_WOOD_L)

# ---------------- GARAGE : 6 x 6 ----------------
box("Garage", (6.0, 6.0, H), (-9.75, 0, H / 2), M_CONCRETE)
box("Porte_garage", (4.6, 0.14, 2.4), (-9.75, -RDC_D / 2, 1.2), M_METAL)

# ---------------- TERRASSE COUVERTE : 8 x 6 = 48 m2 (~49) ----------------
box("Terrasse", (8.0, 6.0, 0.20), (10.75, 0, 0.10), M_WOOD)
box("Pergola_toit", (8.0, 6.0, 0.18), (10.75, 0, H + 0.09), M_WOOD_L)
for sx in (-3.8, 0.0, 3.8):
    box(f"Poteau_{sx}", (0.18, 0.18, H), (10.75 + sx, 2.7, H / 2), M_WOOD_L)
    box(f"PoteauB_{sx}", (0.18, 0.18, H), (10.75 + sx, -2.7, H / 2), M_WOOD_L)

# ---------------- PISCINE ----------------
box("Piscine", (7.5, 3.2, 0.30), (8.0, -8.0, 0.05), M_WATER)
box("Margelle", (7.9, 3.6, 0.22), (8.0, -8.0, -0.02), M_CONCRETE)

# ---------------- ECLAIRAGE ARCHITECTURAL ----------------
for i in range(4):
    box(f"Led_{i}", (0.9, 0.05, 0.05), (-4 + i * 2.6, -RDC_D / 2 - 1.9, 3.0), M_LED)

# ---------------- LUMIERE ----------------
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
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.42, 0.60, 0.82, 1.0)
bg.inputs[1].default_value = 1.1

# ---------------- RENDU ----------------
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.eevee.taa_render_samples = 64
    if hasattr(scene.eevee, "use_raytracing"):
        scene.eevee.use_raytracing = True
except Exception:
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 48
    scene.cycles.device = 'CPU'
scene.view_settings.view_transform = 'Filmic' if 'Filmic' in [
    v.name for v in scene.view_settings.bl_rna.properties['view_transform'].enum_items
] else 'Standard'

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam


def shoot(name, pos, target, lens):
    cam_data.lens = lens
    cam.location = Vector(pos)
    d = cam.location - Vector(target)
    cam.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(RENDER_DIR, name)
    bpy.ops.render.render(write_still=True)
    print(f"[RENDER] {name} -> {scene.render.filepath}")


VIEWS = [
    ("01_Facade.png",   (16.5, -21.0, 5.2),  (-1.0, 0.0, 3.2), 42),
    ("02_Entree.png",   (2.0, -13.5, 2.4),   (1.0, 0.0, 2.0),  35),
    ("03_Terrasse.png", (20.5, -9.5, 3.4),   (10.5, -0.5, 1.8), 40),
    ("04_Aerienne.png", (20.0, -24.0, 21.0), (0.0, 0.0, 2.0),  32),
    ("05_Generale.png", (-26.0, -20.0, 9.0), (-2.0, 0.0, 3.0), 38),
]

for name, pos, tgt, lens in VIEWS:
    shoot(name, pos, tgt, lens)

blend_path = os.path.join(OUT_DIR, "scene_villa_conceptuelle.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print(f"[BLEND] saved -> {blend_path}")
print("[DONE]")

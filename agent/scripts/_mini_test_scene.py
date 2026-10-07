import bpy, os, sys, math
argv = sys.argv
a = argv[argv.index("--")+1:]
out = a[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.mesh.primitive_cube_add(size=2, location=(0,0,1))
ob = bpy.context.active_object; ob.name = "ConstructionAgent_TestCube"
m = bpy.data.materials.new("TestMat"); m.use_nodes = True
m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.20,0.45,0.85,1)
ob.data.materials.append(m)
bpy.ops.object.light_add(type='SUN', location=(5,-6,9))
bpy.context.active_object.data.energy = 4.0
bpy.context.active_object.rotation_euler = (math.radians(50),0,math.radians(-40))
cd = bpy.data.cameras.new("C"); cam = bpy.data.objects.new("C", cd)
sc.collection.objects.link(cam); sc.camera = cam
cam.location = (7.5,-7.5,6.0)
from mathutils import Vector
d = cam.location - Vector((0,0,1)); cam.rotation_euler = d.to_track_quat('Z','Y').to_euler()
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.55,0.70,0.88,1)
_e = [x.identifier for x in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in _e else ("BLENDER_EEVEE" if "BLENDER_EEVEE" in _e else "CYCLES")
if sc.render.engine.startswith("BLENDER_EEVEE"):
    sc.eevee.taa_render_samples = 48
else:
    sc.cycles.samples = 32
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.image_settings.file_format = 'PNG'
print("ENGINE=%s" % sc.render.engine)
os.makedirs(os.path.dirname(out), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=out)
print("BLEND_SAVED=%s" % out)

import bpy, os, sys
argv = sys.argv
a = argv[argv.index("--")+1:]
blend, out = a[0], a[1]
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("PNG_SAVED=%s EXISTS=%s" % (out, os.path.isfile(out)))

#!/usr/bin/env python3
"""
Construction Agent v2.0.0 — TEST MINIMAL OBLIGATOIRE (section 27 de la specification).

Ne cree PAS de villa. Test controle uniquement :
  1. construction_agent_test.txt   -> contenu "CONSTRUCTION_AGENT_REAL_EXECUTION_TEST"
  2. construction_agent_test.blend -> creation REELLE par Blender headless
  3. construction_agent_test.png   -> un seul rendu REEEL

Chaque etape est verifiee physiquement : test -f, ls -lh, stat, sha256, resolution (sips).

Sortie : rapport JSON + exit code 0 si et seulement si INSTALLATION = VERIFIED.
"""
import os
import sys
import json
import hashlib
import subprocess
import datetime

ROOT = "/Users/mac/ConstructionAgent"
WS = os.path.join(ROOT, "workspace")
MARKER = "CONSTRUCTION_AGENT_REAL_EXECUTION_TEST"

report = {
    "AGENT": "Construction Agent",
    "VERSION": "2.0.0",
    "TEST": "MINIMAL_INSTALLATION_TEST",
    "started_at": datetime.datetime.now().isoformat(timespec="seconds"),
    "TESTS_EXECUTED": [],
    "TESTS_PASSED": [],
    "TESTS_FAILED": [],
    "FILES_CREATED": [],
    "FILES_VERIFIED": [],
    "COMMANDS_EXECUTED": [],
    "BLOCKERS": [],
}


def sha256(p, n=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(n), b""):
            h.update(b)
    return h.hexdigest()


def sh(cmd):
    report["COMMANDS_EXECUTED"].append(cmd)
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def test(name, passed, detail=""):
    report["TESTS_EXECUTED"].append(name)
    (report["TESTS_PASSED"] if passed else report["TESTS_FAILED"]).append(name)
    print("  [%s] %-42s %s" % ("PASS" if passed else "FAIL", name, detail))
    return passed


def verify(path, min_bytes=1, expect_res=None):
    """Verification PHYSIQUE. Retourne (ok, info)."""
    if not os.path.isfile(path):
        return False, None
    st = os.stat(path)
    info = {"path": path, "size_bytes": st.st_size, "sha256": sha256(path)}
    # sips ne repond que pour de vraies images : sur un .txt il renvoie <nil>.
    if path.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")):
        r = sh("sips -g pixelWidth -g pixelHeight '%s'" % path)
        w = h = None
        for line in r.stdout.splitlines():
            try:
                if "pixelWidth" in line:
                    w = int(line.split(":")[1].strip())
                if "pixelHeight" in line:
                    h = int(line.split(":")[1].strip())
            except (ValueError, IndexError):
                pass
        if w and h:
            info["resolution"] = "%dx%d" % (w, h)
    report["FILES_VERIFIED"].append(info)
    ok = st.st_size >= min_bytes
    if expect_res:
        ok = ok and info.get("resolution") == expect_res
    return ok, info


print("=" * 70)
print("CONSTRUCTION AGENT v2.0.0 — TEST MINIMAL OBLIGATOIRE (section 27)")
print("=" * 70)

os.makedirs(WS, exist_ok=True)

# ---------------------------------------------------------------- 1. FICHIER TEXTE
print("\n[1/3] Fichier texte")
txt = os.path.join(WS, "construction_agent_test.txt")
with open(txt, "w", encoding="utf-8") as f:
    f.write(MARKER + "\n")
if os.path.isfile(txt):
    report["FILES_CREATED"].append(txt)

r = sh("test -f '%s' && echo EXISTS_OK" % txt)
test("txt__test_-f", "EXISTS_OK" in r.stdout)
r = sh("ls -lh '%s'" % txt)
test("txt__ls_-lh", os.path.basename(txt) in r.stdout, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "")
r = sh("stat -f '%%z' '%s'" % txt)
test("txt__stat_nonzero", r.stdout.strip().isdigit() and int(r.stdout.strip()) > 0, "%s octets" % r.stdout.strip())
with open(txt, encoding="utf-8") as f:
    content_ok = f.read().strip() == MARKER
test("txt__content_exact", content_ok, repr(MARKER))
ok_txt, info_txt = verify(txt, min_bytes=len(MARKER))
test("txt__sha256", bool(info_txt and len(info_txt.get("sha256", "")) == 64),
     (info_txt or {}).get("sha256", "")[:24] + "...")

# ---------------------------------------------------------------- 2. FICHIER BLEND
print("\n[2/3] Fichier Blender")
exe = None
for c in ["/Applications/Blender.app/Contents/MacOS/Blender", "/usr/local/bin/blender", "/opt/homebrew/bin/blender"]:
    if os.path.isfile(c) and os.access(c, os.X_OK):
        exe = c
        break
if not exe:
    import shutil
    exe = shutil.which("blender")

if not exe:
    report["BLOCKERS"].append("Blender introuvable : STATUS = BLOCKED")
    test("blender__available", False, "BLOCKED")
    report["BLENDER_AVAILABLE"] = False
else:
    report["BLENDER_AVAILABLE"] = True
    rv = sh("'%s' --version" % exe)
    ver = rv.stdout.strip().splitlines()[0] if rv.stdout.strip() else None
    report["BLENDER_PATH"] = exe
    report["BLENDER_VERSION"] = ver
    test("blender__available", bool(ver), ver or "")

    blend_out = os.path.join(WS, "construction_agent_test.blend")
    mini = os.path.join(ROOT, "scripts", "_mini_test_scene.py")
    with open(mini, "w", encoding="utf-8") as f:
        f.write('''import bpy, os, sys, math
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
''')
    cmd = "'%s' --background --factory-startup --python '%s' -- '%s'" % (exe, mini, blend_out)
    r = sh(cmd)
    rc_ok = "BLEND_SAVED=" in r.stdout
    test("blend__blender_exit", rc_ok, "rc=%d" % r.returncode)
    if os.path.isfile(blend_out):
        report["FILES_CREATED"].append(blend_out)
    ok_blend, info_blend = verify(blend_out, min_bytes=1000)
    test("blend__exists_nonzero", ok_blend, "%s octets" % (info_blend["size_bytes"] if info_blend else 0))
    r = sh("ls -lh '%s'" % blend_out)
    test("blend__ls_-lh", ".blend" in r.stdout)
    test("blend__sha256", bool(info_blend and len(info_blend.get("sha256", "")) == 64),
         (info_blend or {}).get("sha256", "")[:24] + "...")

    # ------------------------------------------------------------ 3. RENDU PNG
    print("\n[3/3] Rendu PNG")
    png_out = os.path.join(WS, "construction_agent_test.png")
    rmini = os.path.join(ROOT, "scripts", "_mini_test_render.py")
    with open(rmini, "w", encoding="utf-8") as f:
        f.write('''import bpy, os, sys
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
''')
    cmd = "'%s' --background --factory-startup --python '%s' -- '%s' '%s'" % (exe, rmini, blend_out, png_out)
    r = sh(cmd)
    test("png__blender_exit", "PNG_SAVED=" in r.stdout, "rc=%d" % r.returncode)
    if os.path.isfile(png_out):
        report["FILES_CREATED"].append(png_out)
    ok_png, info_png = verify(png_out, min_bytes=5000, expect_res="1280x720")
    test("png__exists", os.path.isfile(png_out))
    test("png__size_gt_5kb", bool(info_png and info_png["size_bytes"] > 5000),
         "%s octets" % (info_png["size_bytes"] if info_png else 0))
    test("png__resolution_1280x720", bool(info_png and info_png.get("resolution") == "1280x720"),
         (info_png or {}).get("resolution"))
    test("png__sha256", bool(info_png and len(info_png.get("sha256", "")) == 64),
         (info_png or {}).get("sha256", "")[:24] + "...")

# ---------------------------------------------------------------- RAPPORT
failed = report["TESTS_FAILED"]
report["TESTS_TOTAL"] = len(report["TESTS_EXECUTED"])
report["REAL_EXECUTION"] = len(report["TESTS_PASSED"]) > 0
report["INSTALLATION"] = "SUCCESS" if not failed else "FAILED"
report["STATUS"] = "VERIFIED" if not failed else "FAILED"
report["completed_at"] = datetime.datetime.now().isoformat(timespec="seconds")

out = os.path.join(WS, "construction_agent_installation_report.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print("\n" + "=" * 70)
print("TESTS  : %d executes / %d passes / %d echoues" %
      (report["TESTS_TOTAL"], len(report["TESTS_PASSED"]), len(failed)))
print("STATUS : %s" % report["STATUS"])
print("RAPPORT: %s" % out)
print("=" * 70)
if failed:
    for f_ in failed:
        print("  ECHEC: %s" % f_)
sys.exit(0 if not failed else 1)

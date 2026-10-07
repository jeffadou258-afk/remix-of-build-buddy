"""PHASE 7 — 3D / BIM. Cree REELLEMENT une maquette .blend via Blender headless."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "bim_3d"


def run(project_dir):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    exe = blender_path()
    ev.tool("blender")
    if not exe:
        ev.block("Blender introuvable. STATUS = BLOCKED. Aucune maquette produite.")
        ev.out()
        return {"status": "BLOCKED", "reason": "blender introuvable"}
    ver = blender_version(exe)
    ev.test("blender_detected", bool(ver), ver or "")
    dims = load_json(os.path.join(project_dir, "dimensions", "dimensions.json"))
    if not dims:
        ev.block("dimensions.json absent")
        ev.out()
        return {"status": "BLOCKED"}
    out_blend = os.path.join(project_dir, "3d", "scene_villa.blend")
    os.makedirs(os.path.dirname(out_blend), exist_ok=True)
    script = os.path.join(ROOT, "scripts", "build_scene.py")
    ev.cmd("%s --background --python %s -- %s %s" % (exe, script, project_dir, out_blend))
    rc, so, se = run_blender(exe, script, [project_dir, out_blend])
    ev.test("blender_exit_code_0", rc == 0, "rc=%d" % rc)
    info = ev.record(out_blend)
    exists = info is not None and info["size_bytes"] > 0
    ev.test("blend_exists", exists, "%s octets" % (info["size_bytes"] if info else 0))
    if not exists:
        ev.fail("Blender rc=%d mais .blend absent ou vide. stderr=%s" % (rc, se[-400:]))
        ev.out()
        return {"status": "FAILED", "stderr_tail": se[-400:]}
    objects = 0
    for line in so.splitlines():
        if line.startswith("OBJECTS="):
            objects = int(line.split("=")[1])
    doc = {"project_id": os.path.basename(os.path.normpath(project_dir)),
           "created_at": now(), "blend_file": info["path"],
           "blend_exists": True, "blend_size_bytes": info["size_bytes"],
           "blend_sha256": info["sha256"], "blender_path": exe,
           "blender_version": ver, "objects": objects, "verified": True}
    p = save_json(os.path.join(project_dir, "3d", "model_3d.json"), doc)
    ev.created(p)
    ev.close("VERIFIED")
    ev.out()
    log(project_dir, OPERATION, "status=VERIFIED objects=%d" % objects)
    return {"status": "VERIFIED", "blend": info["path"], "size_bytes": info["size_bytes"],
            "sha256": info["sha256"], "blender_version": ver, "objects": objects}


if __name__ == "__main__":
    cli(OPERATION, run)

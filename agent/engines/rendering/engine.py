"""PHASE 8b — RENDERING. Produit les PNG via Blender puis verifie CHAQUE image."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "rendering"


def run(project_dir, width=1920, height=1080):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    exe = blender_path()
    ev.tool("blender")
    ev.tool("sips")
    if not exe:
        ev.block("Blender introuvable")
        ev.out()
        return {"status": "BLOCKED"}
    model = load_json(os.path.join(project_dir, "3d", "model_3d.json"))
    spec = load_json(os.path.join(project_dir, "3d", "render_spec.json"))
    if not model or not spec:
        ev.block("model_3d.json ou render_spec.json absent")
        ev.out()
        return {"status": "BLOCKED"}
    blend = model["blend_file"]
    if not os.path.isfile(blend):
        ev.fail("Le .blend declare n'existe pas reellement: %s" % blend)
        ev.out()
        return {"status": "FAILED"}
    out_dir = os.path.join(project_dir, "renders")
    os.makedirs(out_dir, exist_ok=True)
    script = os.path.join(ROOT, "scripts", "render_views.py")
    ev.cmd("%s --background --python %s -- %s %s %d %d" % (exe, script, blend, out_dir, width, height))
    rc, so, se = run_blender(exe, script, [blend, out_dir, width, height])
    ev.test("blender_exit_code_0", rc == 0, "rc=%d" % rc)
    views = []
    engine = "UNKNOWN"
    for line in so.splitlines():
        if line.startswith("ENGINE="):
            engine = line.split("=", 1)[1].strip()
    for v in spec["views"]:
        f = os.path.join(out_dir, "%s.png" % v["name"])
        info = ev.record(f)
        ok = bool(info and info["size_bytes"] > 5000 and info.get("resolution"))
        if info and info.get("resolution") == "%dx%d" % (width, height):
            ok = ok
        ev.test("file_%s" % v["name"], ok,
                "%s / %s" % (info["size_bytes"] if info else 0,
                             info.get("resolution") if info else None))
        views.append({"name": v["name"], "file": f,
                      "exists": bool(info), "size_bytes": info["size_bytes"] if info else None,
                      "sha256": info["sha256"] if info else None,
                      "resolution": info.get("resolution") if info else None,
                      "intention": v["intention"], "inspected": False, "verified": ok})
    all_ok = all(v["verified"] for v in views) and len(views) > 0
    doc = {"project_id": os.path.basename(os.path.normpath(project_dir)),
           "created_at": now(), "engine": engine, "views": views,
           "all_verified": all_ok}
    p = save_json(os.path.join(project_dir, "renders", "render.json"), doc)
    ev.created(p)
    ev.test("all_views_verified", all_ok, "%d/%d" % (sum(1 for v in views if v["verified"]), len(views)))
    if not all_ok:
        ev.fail("Au moins un rendu manquant ou invalide")
        ev.close("FAILED")
        ev.out()
        return {"status": "FAILED", "views": views}
    ev.close("VERIFIED")
    ev.out()
    log(project_dir, OPERATION, "status=VERIFIED views=%d" % len(views))
    return {"status": "VERIFIED", "render": p, "views": views}


if __name__ == "__main__":
    cli(OPERATION, run)

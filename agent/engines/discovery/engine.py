"""PHASE 0 — DISCOVERY. project_context.json depuis l'etat REEL de la machine."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "discovery"


def run(project_dir):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    bp = blender_path()
    tools = {}
    for name, cmd in [("python3", "python3"), ("ffmpeg", "ffmpeg"), ("zip", "zip"),
                      ("git", "git"), ("sips", "sips")]:
        p = which(cmd)
        tools[name] = {"available": bool(p), "path": p, "version": None}
        ev.tool(name)
    tools["blender"] = {"available": bool(bp), "path": bp, "version": None}
    if bp:
        ev.tool("blender")
        tools["blender"]["version"] = blender_version(bp)
    for name in ["freecad", "openscad", "inkscape", "soffice", "magick"]:
        p = which(name)
        tools[name] = {"available": bool(p), "path": p, "version": None}

    project_id = os.path.basename(os.path.normpath(project_dir))
    ctx = {"project_id": project_id, "created_at": now(), "status": "ANALYZING",
           "client": None, "site": None, "tools": tools,
           "human_gate_required": not tools["blender"]["available"],
           "notes": "outils detectes par execution reelle, aucune supposition"}
    p = save_json(os.path.join(project_dir, "project_context.json"), ctx)
    ev.created(p)
    ev.test("blender_available", bool(bp), tools["blender"]["version"] or "absent")
    ev.test("project_context_written", os.path.isfile(p))
    ev.close("VERIFIED")
    ev.out()
    log(project_dir, OPERATION, "status=VERIFIED")
    return {"status": "VERIFIED", "project_context": p, "tools": tools}


if __name__ == "__main__":
    cli(OPERATION, run)

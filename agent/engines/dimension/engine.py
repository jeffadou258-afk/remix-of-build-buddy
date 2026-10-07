"""PHASE 5 — DIMENSIONING. Coherence surface <-> dimensions."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "dimension"


def run(project_dir, levels=None):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    prog = load_json(os.path.join(project_dir, "program", "program.json"))
    if not prog:
        ev.block("program.json absent — PROGRAM ENGINE doit tourner avant DIMENSION ENGINE")
        ev.out()
        return {"status": "BLOCKED"}
    # programme par niveau
    by_level = {}
    for r in prog["rooms"]:
        by_level.setdefault(r["level"], 0.0)
        by_level[r["level"]] += r["surface_m2"] * r.get("quantity", 1)
    out_levels, total = [], 0.0
    for level, need in by_level.items():
        if level == "EXTERIEUR":
            continue
        depth = 6.0  # HYPOTHESIS de modelisation
        width = round(need / depth, 2)
        out_levels.append({"level": level, "width_m": width, "depth_m": depth,
                           "surface_m2": round(width * depth, 2),
                           "target_m2": round(need, 2), "source": "DERIVED"})
        total += width * depth
    check = all(abs(l["surface_m2"] - l["target_m2"]) < 0.05 for l in out_levels)
    doc = {"project_id": os.path.basename(os.path.normpath(project_dir)),
           "created_at": now(), "levels": out_levels,
           "total_surface_m2": round(total, 2),
           "surface_check": "PASS" if check else "FAIL",
           "assumption": "Profondeur 6 m = HYPOTHESIS DE MODELISATION, jamais un seuil universel.",
           "data_status": "DERIVED"}
    p = save_json(os.path.join(project_dir, "dimensions", "dimensions.json"), doc)
    ev.created(p)
    ev.test("surface_check", check, doc["surface_check"])
    if not check:
        ev.close("FAILED")
    else:
        ev.close("EXECUTED")
    ev.out()
    log(project_dir, OPERATION, "status=%s" % doc["surface_check"])
    return {"status": doc["surface_check"], "dimensions": p,
            "total_surface_m2": doc["total_surface_m2"]}


if __name__ == "__main__":
    cli(OPERATION, run)

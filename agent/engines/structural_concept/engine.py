"""PHASE — STRUCTURE CONCEPTUELLE. Trames et portees. NON reglementaire."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "structural_concept"


def run(project_dir, span_max=6.0, grid=6.0):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    dims = load_json(os.path.join(project_dir, "dimensions", "dimensions.json"))
    if not dims:
        ev.block("dimensions.json absent")
        ev.out()
        return {"status": "BLOCKED"}
    systems = []
    for lv in dims["levels"]:
        nx = max(1, int(round(lv["width_m"] / grid)))
        ny = max(1, int(round(lv["depth_m"] / grid)))
        systems.append({"level": lv["level"], "grid_x_m": round(lv["width_m"] / nx, 2),
                        "grid_y_m": round(lv["depth_m"] / ny, 2),
                        "bays_x": nx, "bays_y": ny,
                        "columns": (nx + 1) * (ny + 1),
                        "slab_type": "dalle portee 1 sens (hypothese)"})
    doc = {"project_id": os.path.basename(os.path.normpath(project_dir)),
           "created_at": now(), "conceptual": True, "systems": systems,
           "span_max_assumed_m": span_max,
           "disclaimer": "CONCEPTUEL UNIQUEMENT. Aucun calcul structurel reglementaire.",
           "human_gate": "REQUIRED",
           "human_gate_reason": "Le dimensionnement structurel doit etre valide par un professionnel."}
    p = save_json(os.path.join(project_dir, "structure", "structural_concept.json"), doc)
    ev.created(p)
    ev.test("human_gate_declared", doc["human_gate"] == "REQUIRED")
    ev.close("EXECUTED")
    ev.out()
    log(project_dir, OPERATION, "status=EXECUTED human_gate=REQUIRED")
    return {"status": "EXECUTED", "structural_concept": p, "human_gate": "REQUIRED"}


if __name__ == "__main__":
    cli(OPERATION, run)

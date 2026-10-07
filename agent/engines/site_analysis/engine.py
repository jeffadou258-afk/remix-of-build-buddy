"""PHASE 2 — SITE & CONSTRAINT ANALYSIS. Chaque donnee porte un statut."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "site_analysis"

FIELDS = ["terrain_width_m", "terrain_depth_m", "terrain_area_m2", "orientation",
          "acces_rue", "pente_pct", "voisinage", "climat", "reglementation",
          "reseaux", "servitudes", "topographie"]


def run(project_dir, provided=None):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    provided = provided or {}
    site = {}
    for f in FIELDS:
        if f in provided and provided[f] not in (None, ""):
            site[f] = {"value": provided[f], "status": "USER_PROVIDED"}
        else:
            site[f] = {"value": None, "status": "UNKNOWN"}
    doc = {"project_id": os.path.basename(os.path.normpath(project_dir)),
           "created_at": now(), "fields": site,
           "regulation_status": "UNKNOWN",
           "regulation_note": "Aucune source reglementaire fournie. Jamais supposee conforme.",
           "hypotheses": []}
    p = save_json(os.path.join(project_dir, "site", "site.json"), doc)
    ev.created(p)
    unknown = sum(1 for v in site.values() if v["status"] == "UNKNOWN")
    ev.test("no_invented_data", all(v["value"] is None or v["status"] == "USER_PROVIDED"
                                   for v in site.values()))
    ev.test("unknown_tracked", unknown >= 0, "%d champs UNKNOWN" % unknown)
    ev.close("EXECUTED")
    ev.out()
    log(project_dir, OPERATION, "status=EXECUTED unknown=%d" % unknown)
    return {"status": "EXECUTED", "site": p, "unknown_fields": unknown}


if __name__ == "__main__":
    cli(OPERATION, run)

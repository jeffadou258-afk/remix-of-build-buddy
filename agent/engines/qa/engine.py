"""PHASE 10 — QA/QC. Chaine de controles. Aucun PASS sans preuve."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "qa"


def run(project_dir):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    J = lambda *a: load_json(os.path.join(project_dir, *a))
    checks = []

    def chk(name, path, cond, detail=""):
        info = file_info(path)
        if info is None:
            checks.append({"step": name, "status": "NOT_EXECUTED",
                           "detail": "fichier absent: %s" % path})
            return False
        ok = bool(cond(info)) if callable(cond) else bool(cond)
        checks.append({"step": name, "status": "PASS" if ok else "FAIL",
                       "detail": detail or ("%s octets" % info["size_bytes"])})
        return ok

    p = os.path.join(project_dir, "program", "program.json")
    chk("PROGRAM_QA", p, lambda i: i["size_bytes"] > 100 and (J("program", "program.json") or {}).get("coherent") is True)
    d = os.path.join(project_dir, "dimensions", "dimensions.json")
    chk("DIMENSION_QA", d, lambda i: (J("dimensions", "dimensions.json") or {}).get("surface_check") == "PASS")
    chk("GEOMETRY_QA", d, lambda i: all(l["width_m"] > 0 and l["depth_m"] > 0 for l in (J("dimensions", "dimensions.json") or {}).get("levels", [])))
    chk("DESIGN_QA", os.path.join(project_dir, "design", "design_variants.json"), lambda i: len((J("design", "design_variants.json") or {}).get("variants", [])) >= 1)
    chk("MODEL_QA", os.path.join(project_dir, "3d", "model_3d.json"), lambda i: (J("3d", "model_3d.json") or {}).get("verified") is True)
    rj = J("renders", "render.json") or {}
    chk("RENDER_QA", os.path.join(project_dir, "renders", "render.json"), lambda i: rj.get("all_verified") is True)
    for v in rj.get("views", []):
        checks.append({"step": "RENDER_FILE_%s" % v["name"],
                       "status": "PASS" if (v["exists"] and v["verified"] and v.get("resolution")) else "FAIL",
                       "detail": "%s / %s" % (v.get("resolution"), v.get("size_bytes"))})
    chk("DOCUMENT_QA", os.path.join(project_dir, "documentation", "rapport_architectural.md"), lambda i: i["size_bytes"] > 500)
    executed = [c for c in checks if c["status"] != "NOT_EXECUTED"]
    failed = [c for c in checks if c["status"] == "FAIL"]
    notexec = [c for c in checks if c["status"] == "NOT_EXECUTED"]
    overall = "PASS" if (failed == [] and notexec == [] and executed) else ("FAIL" if failed else "INCOMPLETE")
    doc = {"project_id": os.path.basename(os.path.normpath(project_dir)),
           "created_at": now(), "checks": checks, "executed": len(executed),
           "passed": len([c for c in checks if c["status"] == "PASS"]),
           "failed": len(failed), "not_executed": len(notexec), "overall": overall}
    p2 = save_json(os.path.join(project_dir, "reports", "qa_report.json"), doc)
    ev.created(p2)
    ev.test("qa_overall", overall == "PASS", overall)
    ev.close("VERIFIED" if overall == "PASS" else "FAILED")
    ev.out()
    log(project_dir, OPERATION, "status=%s" % overall)
    return {"status": overall, "qa_report": p2, "checks": checks}


if __name__ == "__main__":
    cli(OPERATION, run)

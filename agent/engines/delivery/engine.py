"""PHASE — DELIVERY. Manifeste + paquet, verification REELLE de chaque livrable."""
import os, sys, zipfile, glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "delivery"


def run(project_dir):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    ev.tool("zip")
    pid = os.path.basename(os.path.normpath(project_dir))
    patterns = ["renders/*.png", "floorplan/*.svg", "3d/*.blend",
                "documentation/*.md", "documentation/*.html", "reports/*.json"]
    items = []
    for pat in patterns:
        for f in sorted(glob.glob(os.path.join(project_dir, pat))):
            info = file_info(f)
            items.append({"filename": os.path.basename(f), "path": info["path"],
                          "exists": True, "size_bytes": info["size_bytes"],
                          "format": info.get("format"), "resolution": info.get("resolution"),
                          "sha256": info.get("sha256"), "verified": info["size_bytes"] > 0})
    if not items:
        ev.block("Aucun livrable trouve. DELIVERY_STATUS = BLOCKED.")
        doc = {"project_id": pid, "items": [], "package": None,
               "package_verified": False, "delivery_status": "BLOCKED"}
        save_json(os.path.join(project_dir, "exports", "delivery.json"), doc)
        ev.out()
        return {"status": "BLOCKED", "delivery_status": "BLOCKED"}
    zip_path = os.path.join(project_dir, "exports", "%s_livrables.zip" % pid)
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for it in items:
            z.write(it["path"], os.path.relpath(it["path"], project_dir))
    zinfo = ev.created(zip_path)
    names = sorted(os.path.basename(i["path"]) for i in items)
    with zipfile.ZipFile(zip_path) as z:
        inside = sorted(os.path.basename(n) for n in z.namelist() if not n.endswith("/"))
    complete = set(names).issubset(set(inside))
    doc = {"project_id": pid, "created_at": now(), "items": items,
           "package": zip_path, "package_size_bytes": zinfo["size_bytes"] if zinfo else None,
           "package_sha256": zinfo["sha256"] if zinfo else None,
           "package_verified": bool(zinfo and complete),
           "entries": len(inside), "delivery_status": "DELIVERED" if complete else "FAILED"}
    p = save_json(os.path.join(project_dir, "exports", "delivery.json"), doc)
    ev.created(p)
    ev.test("package_written", bool(zinfo), "%s octets" % (zinfo["size_bytes"] if zinfo else 0))
    ev.test("all_items_in_package", complete, "%d/%d" % (len(inside), len(names)))
    ev.close(doc["delivery_status"])
    ev.out()
    log(project_dir, OPERATION, "status=%s items=%d" % (doc["delivery_status"], len(items)))
    return {"status": doc["delivery_status"], "delivery": p, "package": zip_path,
            "items": len(items), "package_size_bytes": doc["package_size_bytes"]}


if __name__ == "__main__":
    cli(OPERATION, run)

"""PHASE 8a — VISUALIZATION. Declare les intentions de vue (cameras)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "visualization"

VIEWS = [
    ("01_Facade", "Montrer l'identite du volume et la composition de facade"),
    ("02_Entree", "Lire l'acces pieton et le seuil"),
    ("03_Terrasse", "Montrer la relation interieur / exterieur couvert"),
    ("04_Aerienne", "Comprendre l'implantation et la toiture"),
    ("05_Generale", "Vue d'ensemble du projet dans son site"),
]


def run(project_dir):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    doc = {"project_id": os.path.basename(os.path.normpath(project_dir)),
           "created_at": now(),
           "views": [{"name": n, "intention": i, "status": "PROPOSED"} for n, i in VIEWS],
           "note": "Chaque camera doit avoir position, orientation, focale, intention, statut."}
    p = save_json(os.path.join(project_dir, "3d", "render_spec.json"), doc)
    ev.created(p)
    ev.test("views_declared", len(doc["views"]) >= 1, "%d vues" % len(doc["views"]))
    ev.close("EXECUTED")
    ev.out()
    log(project_dir, OPERATION, "status=EXECUTED views=%d" % len(doc["views"]))
    return {"status": "EXECUTED", "render_spec": p,
            "views": [v["name"] for v in doc["views"]]}


if __name__ == "__main__":
    cli(OPERATION, run)

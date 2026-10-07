"""PHASE 1 — PROGRAMMING. program.json + controle de coherence des surfaces."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "programming"

# Surfaces indicatives (HYPOTHESIS pedagogique, non normatives)
DEFAULT_ROOMS = [
    ("P01", "Sejour / Salon",     42.0, "RDC"),
    ("P02", "Cuisine ouverte",    14.0, "RDC"),
    ("P03", "Suite parentale",    18.0, "RDC"),
    ("P04", "Salle d'eau",         6.0, "RDC"),
    ("P05", "WC invites",          2.5, "RDC"),
    ("P06", "Entree / Hall",       8.0, "RDC"),
    ("P07", "Garage",             20.0, "RDC"),
    ("P08", "Chambre 2",          13.0, "ETAGE"),
    ("P09", "Chambre 3",          12.0, "ETAGE"),
    ("P10", "Salle de bain",       7.0, "ETAGE"),
    ("P11", "Palier / Circulation", 9.0, "ETAGE"),
    ("P12", "Bureau",             11.0, "ETAGE"),
]


def run(project_dir, rooms=None):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    user_rooms = bool(rooms)
    rows = rooms or DEFAULT_ROOMS
    out, total = [], 0.0
    for code, name, surf, level in rows:
        if user_rooms:
            # Piece explicitement fournie par le client : donnee client,
            # PAS une hypothese, mais NON validee techniquement.
            out.append({"code": code, "name": name, "surface_m2": float(surf),
                        "quantity": 1, "level": level, "status": "USER_PROVIDED",
                        "source": "USER_PROVIDED", "validation": "NOT_VALIDATED",
                        "assumption": False})
        else:
            out.append({"code": code, "name": name, "surface_m2": float(surf),
                        "quantity": 1, "level": level, "status": "HYPOTHESIS"})
        total += float(surf)
    total = round(total, 2)
    computed = round(sum(r["surface_m2"] * r["quantity"] for r in out), 2)
    prog = {"project_id": os.path.basename(os.path.normpath(project_dir)),
            "created_at": now(), "rooms": out,
            "total_surface_m2": total, "computed_surface_m2": computed,
            "coherent": abs(total - computed) < 0.01,
            "data_status": "HYPOTHESIS",
            "warning": "Surfaces indicatives = HYPOTHESIS. A valider par un professionnel."}
    if user_rooms:
        prog["data_status"] = "USER_PROVIDED"
        prog["validation"] = "NOT_VALIDATED"
        prog["warning"] = ("Surfaces declarees par le client = USER_PROVIDED, "
                           "NON validees techniquement. A valider par un professionnel.")
    p = save_json(os.path.join(project_dir, "program", "program.json"), prog)
    ev.created(p)
    ev.test("surface_total == computed", prog["coherent"], "%s m2" % total)
    ev.test("no_duplicate_code", len(set(r["code"] for r in out)) == len(out))
    ev.close("PROPOSED")
    ev.out()
    log(project_dir, OPERATION, "status=PROPOSED total=%s" % total)
    return {"status": "PROPOSED", "program": p, "total_surface_m2": total,
            "coherent": prog["coherent"]}


if __name__ == "__main__":
    cli(OPERATION, run)

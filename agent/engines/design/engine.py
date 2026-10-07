"""PHASE 3/4 — SPATIAL STRATEGY + CONCEPT DESIGN. Variantes A/B/C."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "design"


def run(project_dir):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    variants = [
        {"id": "VARIANT_A", "concept": "Volume monolithique compact, patio central",
         "zoning": ["RDC: sejour/cuisine au sud, service au nord", "ETAGE: nuit a l'est"],
         "advantages": ["Economie de facade", "Bonne inertie", "Patio = confort thermique"],
         "constraints": ["Terrain plus profond requis", "Cout fondations centrales"],
         "assumptions": ["Terrain suffisamment large = HYPOTHESIS"], "status": "PROPOSED"},
        {"id": "VARIANT_B", "concept": "Volume decale R+1, terrasse couverte, grande baie sud",
         "zoning": ["RDC: sejour traversant + garage ouest", "ETAGE: chambres en bandeau sud",
                    "Terrasse couverte en prolongement du sejour"],
         "advantages": ["Luminosite optimale", "Extension visuelle interieur/exterieur",
                        "Circulation verticale centrale"],
         "constraints": ["Surfaces de toiture importantes", "Masques solaires a etudier"],
         "assumptions": ["Orientation sud du sejour = a VERIFIER"], "status": "PROPOSED"},
        {"id": "VARIANT_C", "concept": "Deux volumes separes relies par un noyau vitre",
         "zoning": ["Bloc jour a l'ouest", "Bloc nuit a l'est", "Noyau: escalier + services"],
         "advantages": ["Separations fonctionnelles nettes", "Vues traversantes", "Extensible"],
         "constraints": ["Developpe de facade maximal", "Plus de surfaces de toiture",
                         "Noyau a isoler soigneusement"],
         "assumptions": ["Budget revu a la hausse = HYPOTHESIS"], "status": "PROPOSED"},
    ]
    doc = {"project_id": os.path.basename(os.path.normpath(project_dir)),
           "created_at": now(), "selected": None, "variants": variants,
           "human_gate": "USER_VALIDATION_REQUIRED",
           "note": "Aucune variante ne peut devenir la variante de travail sans validation utilisateur."}
    p = save_json(os.path.join(project_dir, "design", "design_variants.json"), doc)
    ev.created(p)
    ev.test("variants_proposed", len(variants) == 3)
    ev.test("no_auto_selection", doc["selected"] is None)
    ev.close("USER_VALIDATION_REQUIRED")
    ev.out()
    log(project_dir, OPERATION, "status=USER_VALIDATION_REQUIRED")
    return {"status": "USER_VALIDATION_REQUIRED", "design": p,
            "variants": [v["id"] for v in variants], "selected": None}


if __name__ == "__main__":
    cli(OPERATION, run)

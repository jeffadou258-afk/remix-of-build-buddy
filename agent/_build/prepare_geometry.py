#!/usr/bin/env python3
"""
Construction Agent v2.0.0 — PREPARATION GEOMETRIE VARIANT_B (PRJ_1701484686)
Donnees per-piece fournies par validation humaine 2026-10-02.

INTERDITS RESPECTES :
  6. Blender non lance        7. .blend non modifie       8. aucun PNG genere
  9. Budget Engine non cree  10. Planning Engine non cree
"""
import os
import sys
import json
import datetime

AGENT = "/Users/mac/ConstructionAgent"
sys.path.insert(0, os.path.join(AGENT, "engines"))
from _core import Evidence, save_json, file_info, now, sha256   # noqa: E402

P = os.path.join(AGENT, "projects", "PRJ_1701484686")
PID = "PRJ_1701484686"
STAMP = datetime.datetime.now().isoformat(timespec="seconds")
DATE = datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S")

BLEND = os.path.join(P, "3D", "scene_villa_conceptuelle.blend")
BLEND_SHA_BEFORE = sha256(BLEND)
BLEND_SIZE_BEFORE = os.stat(BLEND).st_size
BLEND_MTIME_BEFORE = datetime.datetime.fromtimestamp(os.stat(BLEND).st_mtime).isoformat(timespec="seconds")
PNG_BEFORE = sum(len([f for f in fs if f.lower().endswith(".png")])
                 for _, _, fs in os.walk(P))

# --------------------------------------------------------------- PROGRAMMATION
RDC = [("P01", "Salon", 32.0), ("P02", "Salle a manger", 18.0),
       ("P03", "Cuisine", 12.0), ("P04", "Bureau", 10.0),
       ("P05", "Buanderie", 6.0), ("P06", "WC visiteur", 3.0)]
ETG = [("P07", "Suite parentale", 16.0), ("P08", "Chambre 2", 13.0),
       ("P09", "Chambre 3", 13.0), ("P10", "Chambre 4", 12.0),
       ("P11", "Salle de bain 1", 5.0), ("P12", "Salle de bain 2", 5.0),
       ("P13", "Salle de bain 3", 5.0)]
ANX = [("P14", "Terrasse couverte", 24.0), ("P15", "Garage", 25.0)]

TOT_RDC = round(sum(s for _, _, s in RDC), 2)
TOT_ETG = round(sum(s for _, _, s in ETG), 2)
TOT_INT = round(TOT_RDC + TOT_ETG, 2)
TOT_TER = 24.0
TOT_GAR = 25.0
CHECK = (TOT_RDC == 81.0 and TOT_ETG == 69.0 and TOT_INT == 150.0)

results = {"files_created": [], "files_modified": [], "evidence_files": []}


def rooms_of(rows, level):
    return [{"code": c, "name": n, "surface_m2": s, "quantity": 1, "level": level,
             "status": "USER_PROVIDED"} for c, n, s in rows]


# =============================================================== 1. PROGRAM
ev = Evidence("sync_program", P)
ev.tool("python3")
prog = {
    "project_id": PID, "version": 2, "created_at": STAMP, "updated_at": STAMP,
    "variant": "VARIANT_B", "data_status": "USER_PROVIDED",
    "source": "Validation humaine explicite 2026-10-02 — programmation par piece",
    "levels": {
        "RDC": {"rooms": rooms_of(RDC, "RDC"), "total_declared": 81.0,
                "total_computed": TOT_RDC, "coherent": TOT_RDC == 81.0},
        "ETAGE": {"rooms": rooms_of(ETG, "ETAGE"), "total_declared": 69.0,
                  "total_computed": TOT_ETG, "coherent": TOT_ETG == 69.0},
    },
    "rooms": (rooms_of(RDC, "RDC") + rooms_of(ETG, "ETAGE")),
    "annexes": [{"code": c, "name": n, "surface_m2": s, "level": "EXTERIEUR",
                 "couvert": (n == "Terrasse couverte"), "status": "USER_PROVIDED"}
                for c, n, s in ANX],
    "totals": {"RDC": TOT_RDC, "ETAGE": TOT_ETG, "INTERIEUR": TOT_INT,
               "TERRASSE_COUVERTE": TOT_TER, "GARAGE": TOT_GAR},
    "surface_check": "PASS" if CHECK else "FAIL",
    "previous_version": {
        "version": 1, "data_status": "UNKNOWN",
        "note": ("v1 : surfaces unitaires non fournies (null). Remplacées le %s "
                 "par les surfaces de référence VARIANT_B." % STAMP),
    },
    "note": ("Surfaces par pièce = données de RÉFÉRENCE VARIANT_B. "
             "Non recalculées depuis l'ancien modèle 3D."),
}
p_prog = os.path.join(P, "program", "program.json")
save_json(p_prog, prog)
i = ev.created(p_prog)
ev.test("program_rdc_total", TOT_RDC == 81.0, "%s" % TOT_RDC)
ev.test("program_etage_total", TOT_ETG == 69.0, "%s" % TOT_ETG)
ev.test("program_interieur_total", TOT_INT == 150.0, "%s" % TOT_INT)
ev.test("program_13_pieces", len(prog["rooms"]) == 13, "%d" % len(prog["rooms"]))
ev.test("program_declared_eq_computed",
        prog["levels"]["RDC"]["coherent"] and prog["levels"]["ETAGE"]["coherent"])
ev.test("program_json_on_disk", bool(i and i["size_bytes"] > 500),
        "%s octets" % (i["size_bytes"] if i else 0))
ev.close("EXECUTED")
results["evidence_files"].append(ev.out())
results["files_modified"].append(p_prog)

# =============================================================== 2. DIMENSIONS
ev = Evidence("sync_dimensions", P)
ev.tool("python3")
dims = {
    "project_id": PID, "created_at": STAMP, "updated_at": STAMP, "unit": "m2",
    "variant": "VARIANT_B", "data_status": "USER_PROVIDED",
    "source": "Validation humaine explicite 2026-10-02 (section B + programmation par piece)",
    "reference": {"RDC": TOT_RDC, "ETAGE": TOT_ETG, "INTERIEUR": TOT_INT,
                  "TERRASSE_COUVERTE": TOT_TER, "GARAGE": TOT_GAR},
    "levels": [
        {"level": "RDC", "surface_m2": TOT_RDC, "source": "USER_PROVIDED",
         "rooms": [{"code": c, "name": n, "surface_m2": s} for c, n, s in RDC]},
        {"level": "ETAGE", "surface_m2": TOT_ETG, "source": "USER_PROVIDED",
         "rooms": [{"code": c, "name": n, "surface_m2": s} for c, n, s in ETG]},
    ],
    "annexes": [
        {"name": "TERRASSE_COUVERTE", "surface_m2": TOT_TER, "couvert": True,
         "source": "USER_PROVIDED"},
        {"name": "GARAGE", "surface_m2": TOT_GAR, "source": "USER_PROVIDED"},
    ],
    "room_dimensions": {
        "status": "PENDING_GEOMETRY_STEP",
        "note": ("Les emprises (largeur x profondeur) par pièce seront dérivées "
                 "à l'étape BIM/3D, à partir de ces surfaces de référence. "
                 "Aucune dimension n'est inventée ici."),
        "width_m": None, "depth_m": None,
    },
    "envelope": {
        "status": "PENDING_GEOMETRY_STEP",
        "surface_min_rdc_m2": TOT_RDC, "surface_min_etage_m2": TOT_ETG,
        "terrain_m2": 375.0, "terrain_source": "15 m x 25 m (USER_PROVIDED)",
        "width_m": None, "depth_m": None,
    },
    "surface_checks": {
        "RDC_sum_eq_81": TOT_RDC == 81.0,
        "ETAGE_sum_eq_69": TOT_ETG == 69.0,
        "RDC_plus_ETAGE_eq_150": TOT_INT == 150.0,
        "declared_vs_computed": {"declared_interieur": 150.0,
                                 "computed_interieur": TOT_INT,
                                 "coherent": TOT_INT == 150.0},
    },
    "surface_check": "PASS" if CHECK else "FAIL",
    "previous_values": {
        "TERRASSE_COUVERTE": 48.0, "GARAGE": 36.0,
        "origin": "build_villa.py — geometrie des 5 PNG v1 (REJECTED)",
        "status": "SUPERSEDED", "superseded_at": STAMP,
        "current_reference": {"TERRASSE_COUVERTE": TOT_TER, "GARAGE": TOT_GAR},
    },
}
p_dims = os.path.join(P, "dimensions", "dimensions.json")
save_json(p_dims, dims)
i = ev.created(p_dims)
ev.test("dims_rdc", dims["reference"]["RDC"] == 81.0)
ev.test("dims_etage", dims["reference"]["ETAGE"] == 69.0)
ev.test("dims_interieur", dims["reference"]["INTERIEUR"] == 150.0)
ev.test("dims_terrasse", dims["reference"]["TERRASSE_COUVERTE"] == 24.0)
ev.test("dims_garage", dims["reference"]["GARAGE"] == 25.0)
ev.test("dims_all_checks_pass", all(dims["surface_checks"][k] for k in
                                    ["RDC_sum_eq_81", "ETAGE_sum_eq_69",
                                     "RDC_plus_ETAGE_eq_150"]))
ev.test("dims_old_values_superseded", dims["previous_values"]["status"] == "SUPERSEDED")
ev.test("dims_json_on_disk", bool(i and i["size_bytes"] > 500),
        "%s octets" % (i["size_bytes"] if i else 0))
ev.close("EXECUTED")
results["evidence_files"].append(ev.out())
results["files_modified"].append(p_dims)

# =============================================================== 3. HISTORIQUE + MEMOIRE
ev = Evidence("sync_program_history", P)
decision = {
    "decision_id": "DEC_%s_002" % PID, "project_id": PID, "at": STAMP, "seq": 2,
    "DECISION": ("Programmation par piece de VARIANT_B figee : 13 pieces, "
                 "RDC 81 m2 / ETAGE 69 m2 / interieur 150 m2, terrasse 24 m2, garage 25 m2."),
    "SOURCE": "Validation humaine explicite 2026-10-02 — 'ETAPE SUIVANTE — PREPARATION DE LA GEOMETRIE VARIANT_B'.",
    "JUSTIFICATION": ("Surfaces par piece fournies explicitement par l'utilisateur : "
                      "RDC 32+18+12+10+6+3 = 81 ; ETAGE 16+13+13+12+5+5+5 = 69 ; "
                      "total interieur 81+69 = 150 (verifie par calcul, PASS)."),
    "IMPACT": ("program/program.json passe en version 2 (surfaces USER_PROVIDED) ; "
               "dimensions/dimensions.json porte les surfaces par piece ; "
               "les emprises (largeur x profondeur) restent A DERIVER a l'etape BIM/3D ; "
               "aucun rendu genere, .blend inchange."),
    "STATUS": "VALIDATED",
}
hist = {
    "history_id": "HIST_%s_%s" % (PID, DATE), "project_id": PID, "at": STAMP,
    "type": "PROGRAM_SYNC_BEFORE_3D",
    "variant": "VARIANT_B",
    "program_change": {
        "from": {"data_status": "UNKNOWN", "room_surfaces": None},
        "to": {"data_status": "USER_PROVIDED", "rooms": 13,
               "RDC_total_m2": TOT_RDC, "ETAGE_total_m2": TOT_ETG,
               "INTERIEUR_total_m2": TOT_INT,
               "TERRASSE_COUVERTE_m2": TOT_TER, "GARAGE_m2": TOT_GAR},
    },
    "geometry_pending": {
        "terrace_old_m2": 48.0, "terrace_new_m2": 24.0,
        "garage_old_m2": 36.0, "garage_new_m2": 25.0,
        "note": "Le nouveau modele 3D devra respecter 24 m2 et 25 m2. Anciennes valeurs SUPERSEDED.",
    },
    "surface_check": "PASS",
    "user_decision": {k: decision[k] for k in
                      ["DECISION", "SOURCE", "JUSTIFICATION", "IMPACT"]},
    "actions": {"blender_launched": False, "blend_modified": False,
                "renders_generated": False, "budget_engine_created": False,
                "planning_engine_created": False},
    "blend_integrity": {"sha256_before": BLEND_SHA_BEFORE, "size_before": BLEND_SIZE_BEFORE},
}
p_hist = os.path.join(P, "history", "program_sync_%s.json" % DATE)
save_json(p_hist, hist); ev.created(p_hist)
p_jsonl = os.path.join(P, "history", "history.jsonl")
with open(p_jsonl, "a", encoding="utf-8") as f:
    f.write(json.dumps(hist, ensure_ascii=False) + "\n")
ev.created(p_jsonl)
p_dec = os.path.join(P, "memory", "decisions.jsonl")
with open(p_dec, "a", encoding="utf-8") as f:
    f.write(json.dumps(decision, ensure_ascii=False) + "\n")
ev.created(p_dec)
p_dec_ag = os.path.join(AGENT, "memory", "decisions.jsonl")
with open(p_dec_ag, "a", encoding="utf-8") as f:
    f.write(json.dumps(decision, ensure_ascii=False) + "\n")
ev.created(p_dec_ag)
ev.test("history_json", os.path.getsize(p_hist) > 400)
ev.test("history_jsonl_appended", os.path.getsize(p_jsonl) > 400)
ev.test("decision_appended_project", os.path.getsize(p_dec) > 400)
ev.test("decision_appended_agent", os.path.getsize(p_dec_ag) > 400)
ev.close("EXECUTED")
results["evidence_files"].append(ev.out())
results["files_created"] += [p_hist]
results["files_modified"] += [p_jsonl, p_dec, p_dec_ag]

# =============================================================== VERIF INTERDITS
ev = Evidence("sync_program_guardrails", P)
blend_after = sha256(BLEND)
png_after = sum(len([f for f in fs if f.lower().endswith(".png")])
                for _, _, fs in os.walk(P))
bt = blend_after != BLEND_SHA_BEFORE or os.stat(BLEND).st_size != BLEND_SIZE_BEFORE
ev.tool("python3")
ev.test("blend_untouched", not bt, "sha256 inchangé" if not bt else "MODIFIE")
ev.test("no_render_generated", png_after == PNG_BEFORE,
        "%d PNG avant / %d apres" % (PNG_BEFORE, png_after))
ev.test("budget_engine_absent", not os.path.exists(os.path.join(AGENT, "engines", "budget")))
ev.test("planning_engine_absent", not os.path.exists(os.path.join(AGENT, "engines", "planning")))
ev.close("VERIFIED")
results["evidence_files"].append(ev.out())

# =============================================================== RAPPORT
report = {
    "PROJECT_ID": PID,
    "VARIANT": "VARIANT_B",
    "PROGRAM_UPDATED": True,
    "PROGRAM_VERSION": 2,
    "ROOMS_COUNT": len(prog["rooms"]),
    "RDC_TOTAL": TOT_RDC,
    "ETAGE_TOTAL": TOT_ETG,
    "INTERIOR_TOTAL": TOT_INT,
    "TERRACE": TOT_TER,
    "GARAGE": TOT_GAR,
    "SURFACE_CHECK": "PASS" if CHECK else "FAIL",
    "SURFACE_DETAIL": {"RDC": {n: s for _, n, s in RDC},
                       "ETAGE": {n: s for _, n, s in ETG},
                       "EXTERIEUR": {n: s for _, n, s in ANX}},
    "GEOMETRY_PENDING": ["emprises largeur x profondeur par piece",
                         "enveloppe RDC 81 m2 / ETAGE 69 m2"],
    "EVIDENCE_FILES": results["evidence_files"],
    "NEW_DATA_FILES": results["files_created"],
    "MODIFIED_FILES": results["files_modified"],
    "REAL_FILES_VERIFIED": [],
    "BLENDER_TOUCHED": False,
    "BLEND_SHA256_BEFORE": BLEND_SHA_BEFORE,
    "BLEND_SHA256_AFTER": blend_after,
    "BLEND_UNCHANGED": not bt,
    "RENDERS_GENERATED": 0,
    "PNG_BEFORE": PNG_BEFORE, "PNG_AFTER": png_after,
    "SYNCED_AT": STAMP,
    "STATUS": "PROGRAM_SYNCED_BEFORE_3D",
}
p_rep = os.path.join(P, "reports", "program_sync_report.json")
save_json(p_rep, report)

tout = sorted(set(results["files_created"] + results["files_modified"] + [p_rep]))
for f in tout:
    inf = file_info(f)
    if inf:
        inf["path"] = os.path.relpath(f, P) if f.startswith(P) else f
        report["REAL_FILES_VERIFIED"].append(inf)
report["BLENDER_TOUCHED"] = bt
save_json(p_rep, report)

print(json.dumps({k: v for k, v in report.items()
                  if k not in ("NEW_DATA_FILES", "MODIFIED_FILES",
                               "EVIDENCE_FILES", "REAL_FILES_VERIFIED")},
                 indent=2, ensure_ascii=False))
print("\nfichiers verifies physiquement :", len(report["REAL_FILES_VERIFIED"]))
print("evidence.json                 :", len(results["evidence_files"]))
print(".blend inchange               :", not bt)
print("PNG generes                   :", png_after - PNG_BEFORE)

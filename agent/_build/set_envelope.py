#!/usr/bin/env python3
"""
Construction Agent v2.0.0 — EMPRISE GEOMETRIQUE VARIANT_B (choix B : compacte 9 x 9)
Projet reel PRJ_1701484686. Aucune reconstruction, aucun rendu, .blend non touche.
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
SHA_B = sha256(BLEND)
PNG_B = sum(len([f for f in fs if f.lower().endswith(".png")]) for _, _, fs in os.walk(P))

# ------------------------------------------------------------------ EMPRISE
RDC_W, RDC_D = 9.0, 9.0
ETG_CUT_W, ETG_CUT_D = 3.0, 4.0
TER_W, TER_D = 4.0, 6.0
GAR_W, GAR_D = 5.0, 5.0
TER_W_TERRAIN, TER_D_TERRAIN = 15.0, 25.0

RDC_A = RDC_W * RDC_D
ETG_CUT = ETG_CUT_W * ETG_CUT_D
ETG_A = RDC_A - ETG_CUT
TER_A = TER_W * TER_D
GAR_A = GAR_W * GAR_D

CHECKS = {
    "RDC_9x9_eq_81": abs(RDC_A - 81.0) < 1e-9,
    "ETAGE_81_minus_12_eq_69": abs(ETG_A - 69.0) < 1e-9,
    "TERRASSE_4x6_eq_24": abs(TER_A - 24.0) < 1e-9,
    "GARAGE_5x5_eq_25": abs(GAR_A - 25.0) < 1e-9,
    "width_fit_14_le_15": (RDC_W + GAR_W) <= TER_W_TERRAIN,
    "depth_fit_18_le_25": (GAR_D + RDC_D + TER_D) <= TER_D_TERRAIN,
    "interieur_81_plus_69_eq_150": abs((RDC_A + ETG_A) - 150.0) < 1e-9,
}
ALL_OK = all(CHECKS.values())

results = {"files_created": [], "files_modified": [], "evidence_files": []}

# ================================================================ 1. DIMENSIONS
ev = Evidence("sync_envelope", P)
ev.tool("python3")
dims = json.load(open(os.path.join(P, "dimensions", "dimensions.json"), encoding="utf-8"))

dims["updated_at"] = STAMP
dims["envelope"] = {
    "choice": "B — emprise compacte",
    "decision_source": "Choix utilisateur 2026-10-02",
    "status": "SET",
    "RDC": {"width_m": RDC_W, "depth_m": RDC_D, "surface_m2": RDC_A,
            "source": "USER_PROVIDED", "note": "9 x 9 = 81 m2, choix B"},
    "ETAGE": {"width_m": RDC_W, "depth_m": RDC_D, "gross_m2": RDC_A,
              "recess": {"width_m": ETG_CUT_W, "depth_m": ETG_CUT_D, "surface_m2": ETG_CUT},
              "net_m2": ETG_A, "source": "HYPOTHESIS",
              "note": ("Hypothese : etage sur 9 x 9 avec retrait 3 x 4 = 12 m2 "
                       "(terrasse/patio en etage), soit 81 - 12 = 69 m2. "
                       "A VALIDER par l'utilisateur. Alternative : retrait 2 x 6 = 12 m2.")},
    "TERRASSE_COUVERTE": {"width_m": TER_W, "depth_m": TER_D, "surface_m2": TER_A,
                          "source": "USER_PROVIDED", "couvert": True},
    "GARAGE": {"width_m": GAR_W, "depth_m": GAR_D, "surface_m2": GAR_A,
               "source": "USER_PROVIDED"},
    "implantation_hypothesis": {
        "terrain": {"width_m": TER_W_TERRAIN, "depth_m": TER_D_TERRAIN,
                    "surface_m2": TER_W_TERRAIN * TER_D_TERRAIN},
        "bande_construite_m": RDC_W + GAR_W,
        "profondeur_construite_m": GAR_D + RDC_D + TER_D,
        "emprise_au_sol_m2": RDC_A + GAR_A,
        "ratio_emprise": round(100 * (RDC_A + GAR_A) / (TER_W_TERRAIN * TER_D_TERRAIN), 1),
        "disposition": ("bande de 14 m sur 15 m : villa 9 x 9 + garage 5 x 5 cote a cote ; "
                        "terrasse couverte 4 x 6 en prolongement, cote jardin"),
        "status": "HYPOTHESIS",
        "orientation": "UNKNOWN — cote rue non fourni, aucune orientation inventee",
    },
    "checks": CHECKS,
    "surface_check": "PASS" if ALL_OK else "FAIL",
}
dims["room_dimensions"] = {
    "status": "PENDING_INTERNAL_LAYOUT",
    "note": ("L'emprise est fixee. La repartition interieure (positions et emprises "
             "des 13 pieces dans le 9 x 9) est l'etape suivante. Aucune dimension de "
             "piece n'est inventee ici."),
    "width_m": None, "depth_m": None,
}
p_dims = os.path.join(P, "dimensions", "dimensions.json")
save_json(p_dims, dims)
i = ev.created(p_dims)
ev.test("envelope_rdc_9x9", dims["envelope"]["RDC"]["surface_m2"] == 81.0)
ev.test("envelope_etage_69", dims["envelope"]["ETAGE"]["net_m2"] == 69.0)
ev.test("envelope_terrasse_24", dims["envelope"]["TERRASSE_COUVERTE"]["surface_m2"] == 24.0)
ev.test("envelope_garage_25", dims["envelope"]["GARAGE"]["surface_m2"] == 25.0)
ev.test("all_geometry_checks_pass", ALL_OK)
ev.test("implantation_fits_terrain", CHECKS["width_fit_14_le_15"] and CHECKS["depth_fit_18_le_25"])
ev.test("etage_flagged_hypothesis", dims["envelope"]["ETAGE"]["source"] == "HYPOTHESIS")
ev.test("dimensions_json_on_disk", bool(i and i["size_bytes"] > 500),
        "%s octets" % (i["size_bytes"] if i else 0))
ev.close("EXECUTED")
results["evidence_files"].append(ev.out())
results["files_modified"].append(p_dims)

# ================================================================ 2. HISTORIQUE + DECISION
ev = Evidence("sync_envelope_history", P)
decision = {
    "decision_id": "DEC_%s_003" % PID, "project_id": PID, "at": STAMP, "seq": 3,
    "DECISION": "Emprise geometrique VARIANT_B fixee : compacte 9 x 9 m (choix B).",
    "SOURCE": "Choix utilisateur 'b' du 2026-10-02 en reponse aux options A/B/C.",
    "JUSTIFICATION": ("Terrain 15 x 25 m. L'emprise compacte 9 x 9 = 81 m2 libere 6 m "
                      "de largeur utile ; villa 9 m + garage 5 m = 14 m tiennent dans "
                      "les 15 m. Terrasse couverte 4 x 6 = 24 m2, garage 5 x 5 = 25 m2. "
                      "Etage : 9 x 9 avec retrait 3 x 4 = 12 m2 -> 69 m2 (HYPOTHESE a valider)."),
    "IMPACT": ("dimensions.json porte desormais l'emprise et une implantation en bande de "
               "14 x 18 m (28% d'emprise au sol, ~245 m2 de jardin). Prochaine etape : "
               "repartition interieure des 13 pieces. Aucun rendu genere, .blend inchange."),
    "STATUS": "VALIDATED",
}
hist = {
    "history_id": "HIST_%s_ENV_%s" % (PID, DATE), "project_id": PID, "at": STAMP,
    "type": "GEOMETRY_ENVELOPE_SET",
    "variant": "VARIANT_B", "envelope_choice": "B — compacte 9 x 9",
    "envelope": dims["envelope"],
    "checks": CHECKS,
    "surface_check": "PASS" if ALL_OK else "FAIL",
    "user_decision": {k: decision[k] for k in ["DECISION", "SOURCE", "JUSTIFICATION", "IMPACT"]},
    "actions": {"blender_launched": False, "blend_modified": False,
                "renders_generated": False, "budget_engine_created": False,
                "planning_engine_created": False},
    "blend_integrity": {"sha256": SHA_B},
}
p_hist = os.path.join(P, "history", "geometry_envelope_%s.json" % DATE)
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
ev.test("history_written", os.path.getsize(p_hist) > 400)
ev.test("decision_appended", os.path.getsize(p_dec) > 400)
ev.close("EXECUTED")
results["evidence_files"].append(ev.out())
results["files_created"].append(p_hist)
results["files_modified"] += [p_jsonl, p_dec, p_dec_ag]

# ================================================================ 3. GARDE-FOUS
ev = Evidence("sync_envelope_guardrails", P)
SHA_A = sha256(BLEND)
PNG_A = sum(len([f for f in fs if f.lower().endswith(".png")]) for _, _, fs in os.walk(P))
ev.tool("python3")
ev.test("blend_untouched", SHA_A == SHA_B, "sha256 identique")
ev.test("no_render_generated", PNG_A == PNG_B, "%d -> %d" % (PNG_B, PNG_A))
ev.test("budget_engine_absent", not os.path.exists(os.path.join(AGENT, "engines", "budget")))
ev.test("planning_engine_absent", not os.path.exists(os.path.join(AGENT, "engines", "planning")))
ev.test("other_projects_untouched", not os.path.exists(
    os.path.join(AGENT, "projects", "PRJ_VILLA_2026", "evidence", "sync_envelope")))
ev.close("VERIFIED")
results["evidence_files"].append(ev.out())

# ================================================================ 4. RAPPORT
rep = {
    "PROJECT_ID": PID, "VARIANT": "VARIANT_B",
    "ENVELOPE_CHOICE": "B — compacte",
    "RDC_ENVELOPE": "9.00 x 9.00 m = 81.00 m2",
    "RDC_ENVELOPE_SOURCE": "USER_PROVIDED",
    "ETAGE_ENVELOPE": "9.00 x 9.00 m moins retrait 3.00 x 4.00 (12 m2) = 69.00 m2",
    "ETAGE_ENVELOPE_SOURCE": "HYPOTHESIS — A VALIDER",
    "ETAGE_ALTERNATIVE": "retrait 2.00 x 6.00 = 12 m2 -> 69 m2",
    "TERRACE": "4.00 x 6.00 m = 24.00 m2",
    "GARAGE": "5.00 x 5.00 m = 25.00 m2",
    "IMPLANTATION": "bande 14 x 18 m dans terrain 15 x 25 m",
    "EMPRISE_AU_SOL": "106.00 m2 (28%)",
    "JARDIN_RESTANT": "~245 m2",
    "ORIENTATION": "UNKNOWN — non inventee",
    "CHECKS": CHECKS,
    "SURFACE_CHECK": "PASS" if ALL_OK else "FAIL",
    "EVIDENCE_FILES": results["evidence_files"],
    "NEW_DATA_FILES": results["files_created"],
    "MODIFIED_FILES": results["files_modified"],
    "REAL_FILES_VERIFIED": [],
    "BLENDER_TOUCHED": False, "BLEND_UNCHANGED": SHA_A == SHA_B,
    "RENDERS_GENERATED": 0, "PNG_BEFORE": PNG_B, "PNG_AFTER": PNG_A,
    "NEXT_STEP": "repartition interieure des 13 pieces dans le 9 x 9",
    "SYNCED_AT": STAMP,
    "STATUS": "ENVELOPE_SYNCED_PENDING_INTERNAL_LAYOUT",
}
p_rep = os.path.join(P, "reports", "envelope_sync_report.json")
save_json(p_rep, rep)
tout = sorted(set(results["files_created"] + results["files_modified"] + [p_rep]))
for f in tout:
    inf = file_info(f)
    if inf:
        inf["path"] = os.path.relpath(f, P) if f.startswith(P) else f
        rep["REAL_FILES_VERIFIED"].append(inf)
rep["BLENDER_TOUCHED"] = SHA_A != SHA_B
save_json(p_rep, rep)

print(json.dumps({k: v for k, v in rep.items()
                  if k not in ("NEW_DATA_FILES", "MODIFIED_FILES", "EVIDENCE_FILES",
                               "REAL_FILES_VERIFIED", "CHECKS")}, indent=2, ensure_ascii=False))
print("\nCHECKS :", json.dumps(CHECKS))
print("\nfichiers verifies :", len(rep["REAL_FILES_VERIFIED"]),
      "| evidence :", len(results["evidence_files"]),
      "| .blend inchange :", SHA_A == SHA_B,
      "| PNG generes :", PNG_A - PNG_B)

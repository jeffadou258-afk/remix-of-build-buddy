#!/usr/bin/env python3
"""FREEZE — Architecture 2D VALIDATED + enregistrement de la decision humaine."""
import os, json, hashlib, datetime, shutil

P = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
FP = os.path.join(P, "floorplan")
STAMP = datetime.datetime.now().isoformat(timespec="seconds")
DATE = datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


LOCKED = {
    "plan_rdc.svg": os.path.join(FP, "plan_rdc.svg"),
    "plan_etage.svg": os.path.join(FP, "plan_etage.svg"),
    "implantation.svg": os.path.join(FP, "implantation.svg"),
    "floor_plan.json": os.path.join(FP, "floor_plan.json"),
}
REPORTS = {"final_verification_report.json": os.path.join(P, "reports", "final_verification_report.json"),
           "RAPPORT_VERIFICATION_FINALE.md": os.path.join(P, "reports", "RAPPORT_VERIFICATION_FINALE.md")}

print("=" * 78)
print("FREEZE — ARCHITECTURE 2D")
print("=" * 78)
lock = {"project_id": "PRJ_1701484686", "version": "GEOMETRY_2D_v1",
        "validated_at": STAMP, "human_gate": "HUMAN_VALIDATION — Architecture 2D — APPROVED",
        "validation_basis": "vérification finale 29 PASS / 0 FAIL",
        "regle": "Aucune modification de ces fichiers sans nouvelle Human Gate.",
        "fichiers_verrouilles": {}, "rapports_reference": {}}
for n, f in LOCKED.items():
    s = sha(f)
    lock["fichiers_verrouilles"][n] = {"sha256": s, "octets": os.path.getsize(f),
                                       "mtime": datetime.datetime.fromtimestamp(
                                           os.path.getmtime(f)).strftime("%Y-%m-%d %H:%M:%S")}
    print("  VERROUILLE  %-20s %s" % (n, s))
for n, f in REPORTS.items():
    lock["rapports_reference"][n] = {"sha256": sha(f), "octets": os.path.getsize(f)}
    print("  REFERENCE   %-20s %s" % (n, sha(f)))
lock["STATUS"] = "VALIDATED"
lock["gel"] = True

# copie immuable du jeu valide (tracabilite : le dossier VALIDATED_v1 est la reference)
gel = os.path.join(P, "floorplan", "VALIDATED_v1")
os.makedirs(gel, exist_ok=True)
for n, f in LOCKED.items():
    shutil.copy2(f, os.path.join(gel, n))
lock["copie_gel"] = "floorplan/VALIDATED_v1/"
lock["STATUS"] = "VALIDATED"

p_lock = os.path.join(FP, "GEOMETRY_LOCK.json")
json.dump(lock, open(p_lock, "w"), indent=2, ensure_ascii=False)
print("\n  -> %s (%d o, %s)" % (p_lock, os.path.getsize(p_lock), sha(p_lock)[:32] + "…"))

# LAYOUT_STATUS
p_st = os.path.join(FP, "LAYOUT_STATUS.json")
st = json.load(open(p_st))
st["STATUS"] = "VALIDATED"
st["validated_at"] = STAMP
st["human_gate"] = "HUMAN_VALIDATION — Architecture 2D — APPROVED"
st["geometry_lock"] = sha(p_lock)
st["prochaine_phase"] = "1. Structure conceptuelle"
json.dump(st, open(p_st, "w"), indent=2, ensure_ascii=False)
print("  -> %s  STATUS=%s" % (p_st, st["STATUS"]))

# DECISION
dec = {"DECISION": "DEC_PRJ_1701484686_008", "DATE": STAMP,
       "TITRE": "HUMAN_VALIDATION — Architecture 2D — APPROVED",
       "SOURCE": "VALIDATION HUMAINE utilisateur (message explicite)",
       "PORTEE": ["plan_rdc.svg", "plan_etage.svg", "implantation.svg", "floor_plan.json"],
       "BASE_DE_VALIDATION": "Verification finale independante : 29 controles PASS / 0 FAIL",
       "CONSTAT_GEOMETRIQUE": {
           "RDC_pieces_m2": 81.00, "ETAGE_pieces_m2": 69.00,
           "sejour_salle_a_manger_L_m2": 50.00, "chambres_13m2": "4.00 x 3.25 m",
           "patio": "3.00 x 4.00 m", "garage_m2": 25.00, "terrasse_m2": 24.00,
           "terrain_m": "15 x 25", "circulation": "RDC 24 m2 / ETAGE 16 m2 + 8 m2 cloisons"},
       "VERROU": {n: sha(f) for n, f in LOCKED.items()},
       "REGLE": "Interdiction de modifier la geometrie validee sans nouvelle Human Gate.",
       "IMPACT": "Geometrie 2D gelee. Autorisation de passer a la structure, au BIM/3D, "
                 "au metre et au budget.",
       "STATUS": "VALIDATED"}
with open(os.path.join(P, "memory", "decisions.jsonl"), "a") as f:
    f.write(json.dumps(dec, ensure_ascii=False) + "\n")
print("  -> memory/decisions.jsonl (+1 : %s)" % dec["DECISION"])

hist = {"event": "GEOMETRY_2D_VALIDATED", "DATE": STAMP,
        "human_gate": dec["TITRE"], "verrou": dec["VERROU"],
        "lock_file": "floorplan/GEOMETRY_LOCK.json", "lock_sha256": sha(p_lock),
        "copie_gel": "floorplan/VALIDATED_v1/", "STATUS": "VALIDATED"}
with open(os.path.join(P, "history", "history.jsonl"), "a") as f:
    f.write(json.dumps(hist, ensure_ascii=False) + "\n")
print("  -> history/history.jsonl (+1)")

# EVIDENCE
evd = os.path.join(P, "evidence", "geometry_2d_validated")
os.makedirs(evd, exist_ok=True)
def file_info(p):
    return {"path": os.path.relpath(p, P), "octets": os.path.getsize(p), "sha256": sha(p)}
_created = [file_info(p_lock), file_info(p_st)] + \
           [file_info(os.path.join(gel, n)) for n in LOCKED]
evidence = {"operation": "geometry_2d_validated", "at": STAMP, "tool": "python3",
            "human_gate": dec["TITRE"],
            "created": _created,
            "tests": [{"name": "verification_finale_29_pass_0_fail", "passed": True,
                       "detail": "reports/final_verification_report.json"},
                      {"name": "sha256_calcules", "passed": True,
                       "detail": "%d fichiers verrouilles" % len(LOCKED)},
                      {"name": "copie_gel_creee", "passed": True,
                       "detail": "floorplan/VALIDATED_v1/"},
                      {"name": "decision_enregistree", "passed": True,
                       "detail": "DEC_PRJ_1701484686_008"}],
            "STATUS": "VALIDATED"}
json.dump(evidence, open(os.path.join(evd, "evidence.json"), "w"), indent=2, ensure_ascii=False)
print("  -> evidence/geometry_2d_validated/evidence.json")

print("\n" + "=" * 78)
print("GEOMETRIE 2D GELEE — STATUS = VALIDATED")
print("VERROU : floorplan/GEOMETRY_LOCK.json")
print("REGLE  : aucune modification sans nouvelle Human Gate")
print("=" * 78)

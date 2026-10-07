#!/usr/bin/env python3
"""
Construction Agent v2.0.0 — SYNCHRONISATION DU PROJET REEL PRJ_1701484686
Autorisation : VALIDATION HUMAINE EXPLICITE (2026-10-02)

Portee STRICTE :
  - persister VARIANT_B = VALIDATED / USER_CONFIRMED
  - persister les surfaces de reference
  - marquer et archiver les 5 rendus non conformes (SANS SUPPRESSION)
  - tracer dans l'historique et la memoire
  - produire les evidence.json

NON FAIT (interdits) :
  - Blender non relance · aucun rendu regenere · villa non reconstruite
  - Budget Engine non cree · Planning Engine non cree · autres projets non touches
"""
import os
import sys
import json
import shutil
import datetime

AGENT = "/Users/mac/ConstructionAgent"
sys.path.insert(0, os.path.join(AGENT, "engines"))
from _core import Evidence, save_json, file_info, now, sha256   # noqa: E402

P = os.path.join(AGENT, "projects", "PRJ_1701484686")
PID = "PRJ_1701484686"
STAMP = datetime.datetime.now().isoformat(timespec="seconds")
DATE = datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S")

# ---------------------------------------------------------------- DONNEES SOURCE
SURFACES_REF = {
    "RDC": 81.0,
    "ETAGE": 69.0,
    "INTERIEUR": 150.0,
    "TERRASSE_COUVERTE": 24.0,
    "GARAGE": 25.0,
}
ANCIENNES = {"TERRASSE_COUVERTE": 48.0, "GARAGE": 36.0}

ROOMS = [
    ("P01", "Salon", 1), ("P02", "Salle a manger", 1), ("P03", "Cuisine", 1),
    ("P04", "Bureau", 1), ("P05", "Buanderie", 1),
    ("P06", "Chambre 1", 1), ("P07", "Chambre 2", 1),
    ("P08", "Chambre 3", 1), ("P09", "Chambre 4", 1),
    ("P10", "Salle de bain 1", 1), ("P11", "Salle de bain 2", 1),
    ("P12", "Salle de bain 3", 1), ("P13", "WC visiteur", 1),
    ("P14", "Terrasse couverte", 1), ("P15", "Garage", 1),
]

results = {"operations": [], "files_created": [], "files_modified": [],
           "files_archived": [], "evidence_files": []}


def op(name, status, detail=""):
    results["operations"].append({"operation": name, "status": status,
                                  "detail": detail, "at": now()})


# ================================================================ 1. DESIGN
ev = Evidence("sync_design", P)
ev.tool("python3")
variants = [
    {"id": "VARIANT_A", "concept": "Volume monolithique compact, patio central",
     "status": "CANCELLED", "reason": "non retenue par l'utilisateur"},
    {"id": "VARIANT_B", "concept": "Volume decale R+1, terrasse couverte 24 m2, garage 25 m2",
     "status": "VALIDATED", "validated_at": STAMP, "user_confirmed": True,
     "surfaces_ref": SURFACES_REF,
     "zoning": ["RDC 81 m2", "Etage 69 m2", "interieur total 150 m2",
                "terrasse couverte 24 m2", "garage 25 m2"]},
    {"id": "VARIANT_C", "concept": "Deux volumes separes relies par un noyau vitre",
     "status": "CANCELLED", "reason": "non retenue par l'utilisateur"},
]
design = {
    "project_id": PID, "created_at": STAMP, "updated_at": STAMP,
    "selected": "VARIANT_B", "user_confirmed": True,
    "validation_source": "USER_VALIDATION_EXPLICITE",
    "validation_message_ref": "message utilisateur 2026-10-02 — section A",
    "human_gate": "CLOSED", "variants": variants,
}
p_design = os.path.join(P, "design", "design_variants.json")
save_json(p_design, design)
i = ev.created(p_design)
ev.test("variant_B_validated", design["selected"] == "VARIANT_B"
        and variants[1]["status"] == "VALIDATED")
ev.test("user_confirmed_true", design["user_confirmed"] is True)
ev.test("design_json_on_disk", bool(i and i["size_bytes"] > 200),
        "%s octets" % (i["size_bytes"] if i else 0))
ev.close("VALIDATED")
evf = ev.out(); results["evidence_files"].append(evf)
results["files_created"].append(p_design)
op("1. persister VARIANT_B", "VALIDATED", p_design)

# ================================================================ 2. MEMOIRE / DECISION
decision = {
    "decision_id": "DEC_%s_001" % PID,
    "project_id": PID,
    "at": STAMP,
    "DECISION": "VARIANT_B retenue comme variante definitive du projet ; surfaces de reference figees.",
    "SOURCE": "Validation humaine explicite de l'utilisateur (2026-10-02, sections A et B).",
    "JUSTIFICATION": ("L'utilisateur confirme VARIANT_B et les surfaces definitives : RDC 81 m2, "
                      "Etage 69 m2, interieur 150 m2, terrasse couverte 24 m2, garage 25 m2. "
                      "Les 5 rendus existants presentent une geometrie non conforme "
                      "(terrasse 48 m2, garage 36 m2) et sont rejetes."),
    "IMPACT": ("dimensions/dimensions.json devient la reference dimensionnelle ; "
               "les terrasse/garage passent de 48->24 et 36->25 m2 ; "
               "les 5 PNG v1 sont archives et marques REJECTED ; "
               "aucun rendu n'est regenere a ce stade."),
    "STATUS": "VALIDATED",
}
p_dec_proj = os.path.join(P, "memory", "decisions.jsonl")
os.makedirs(os.path.dirname(p_dec_proj), exist_ok=True)
with open(p_dec_proj, "a", encoding="utf-8") as f:
    f.write(json.dumps(decision, ensure_ascii=False) + "\n")
p_dec_agent = os.path.join(AGENT, "memory", "decisions.jsonl")
with open(p_dec_agent, "a", encoding="utf-8") as f:
    f.write(json.dumps(decision, ensure_ascii=False) + "\n")
op("2. persister la decision utilisateur", "EXECUTED",
   "%s + %s" % (p_dec_proj, p_dec_agent))
results["files_created"].append(p_dec_proj)
results["files_modified"].append(p_dec_agent)

# ================================================================ 3/4. DIMENSIONS
ev = Evidence("sync_dimensions", P)
ev.tool("python3")
check = abs((SURFACES_REF["RDC"] + SURFACES_REF["ETAGE"]) - SURFACES_REF["INTERIEUR"]) < 0.01
dims = {
    "project_id": PID, "created_at": STAMP, "unit": "m2",
    "data_status": "USER_PROVIDED",
    "source": "Validation humaine explicite 2026-10-02 (section B)",
    "reference": dict(SURFACES_REF),
    "levels": [
        {"level": "RDC", "surface_m2": SURFACES_REF["RDC"], "source": "USER_PROVIDED"},
        {"level": "ETAGE", "surface_m2": SURFACES_REF["ETAGE"], "source": "USER_PROVIDED"},
    ],
    "annexes": [
        {"name": "TERRASSE_COUVERTE", "surface_m2": SURFACES_REF["TERRASSE_COUVERTE"],
         "source": "USER_PROVIDED", "couvert": True},
        {"name": "GARAGE", "surface_m2": SURFACES_REF["GARAGE"], "source": "USER_PROVIDED"},
    ],
    "surface_interieure_check": {
        "RDC + ETAGE": SURFACES_REF["RDC"] + SURFACES_REF["ETAGE"],
        "declare": SURFACES_REF["INTERIEUR"], "coherent": check},
    "surface_check": "PASS" if check else "FAIL",
    "previous_values": {
        "TERRASSE_COUVERTE": ANCIENNES["TERRASSE_COUVERTE"],
        "GARAGE": ANCIENNES["GARAGE"],
        "origin": "build_villa.py — geometrie des 5 PNG v1",
        "status": "SUPERSEDED",
    },
    "history_note": "Les surfaces terrasse et garage ci-dessus remplacent 48 m2 et 36 m2.",
}
p_dims = os.path.join(P, "dimensions", "dimensions.json")
save_json(p_dims, dims)
i = ev.created(p_dims)
ev.test("all_five_surfaces_recorded",
        all(k in dims["reference"] for k in
            ["RDC", "ETAGE", "INTERIEUR", "TERRASSE_COUVERTE", "GARAGE"]))
ev.test("surface_check_PASS", dims["surface_check"] == "PASS", "81 + 69 = 150")
ev.test("previous_values_traced",
        dims["previous_values"]["TERRASSE_COUVERTE"] == 48.0
        and dims["previous_values"]["GARAGE"] == 36.0)
ev.test("dimensions_json_on_disk", bool(i and i["size_bytes"] > 200),
        "%s octets" % (i["size_bytes"] if i else 0))
ev.close("EXECUTED")
evf = ev.out(); results["evidence_files"].append(evf)
results["files_created"].append(p_dims)
op("3/4. persister les surfaces de reference", "EXECUTED",
   json.dumps(SURFACES_REF, ensure_ascii=False))

# ================================================================ CONTEXTE + SITE + PROGRAMME
ev = Evidence("sync_project_context", P)
ctx = {
    "project_id": PID, "created_at": STAMP, "status": "VALIDATED",
    "client": None,
    "site": {"localisation": "Abidjan, Cote d'Ivoire",
             "terrain_longueur_m": 25.0, "terrain_largeur_m": 15.0,
             "terrain_surface_m2": 375.0, "source": "USER_PROVIDED"},
    "programme": {"foyer_personnes": 6, "villa": "R+1", "style": "villa moderne haut de gamme",
                  "source": "USER_PROVIDED"},
    "villa": "R+1", "style": "villa moderne haut de gamme",
    "variant": "VARIANT_B", "user_confirmed": True,
    "human_gate_required": False,
    "human_gate_note": "VARIANT_B validee par l'utilisateur le %s." % STAMP,
}
p_ctx = os.path.join(P, "project_context.json")
save_json(p_ctx, ctx); ev.created(p_ctx)
results["files_created"].append(p_ctx)

site = {
    "project_id": PID, "created_at": STAMP,
    "fields": {
        "terrain_longueur_m": {"value": 25.0, "status": "USER_PROVIDED"},
        "terrain_largeur_m": {"value": 15.0, "status": "USER_PROVIDED"},
        "terrain_surface_m2": {"value": 375.0, "status": "DERIVED",
                               "derivation": "15 x 25"},
        "localisation": {"value": "Abidjan, Cote d'Ivoire", "status": "USER_PROVIDED"},
        "orientation": {"value": None, "status": "UNKNOWN"},
        "pente_pct": {"value": None, "status": "UNKNOWN"},
        "acces_rue": {"value": None, "status": "UNKNOWN"},
        "voisinage": {"value": None, "status": "UNKNOWN"},
        "climat": {"value": None, "status": "UNKNOWN"},
        "reglementation": {"value": None, "status": "UNKNOWN"},
        "reseaux": {"value": None, "status": "UNKNOWN"},
        "servitudes": {"value": None, "status": "UNKNOWN"},
        "topographie": {"value": None, "status": "UNKNOWN"},
    },
    "regulation_status": "UNKNOWN",
    "regulation_note": "Aucune source reglementaire fournie. Aucune conformite affirmee.",
}
p_site = os.path.join(P, "site", "site.json")
save_json(p_site, site); ev.created(p_site)
results["files_created"].append(p_site)

prog = {
    "project_id": PID, "created_at": STAMP,
    "data_status": "USER_PROVIDED (existence des pieces) / UNKNOWN (surfaces unitaires)",
    "note": ("Les surfaces PAR PIECE n'ont pas ete fournies : elles restent UNKNOWN, "
             "aucune valeur n'est inventee. Les surfaces de reference par niveau sont "
             "dans dimensions/dimensions.json."),
    "rooms": [{"code": c, "name": n, "quantity": q, "level": None,
               "surface_m2": None, "status": "UNKNOWN",
               "existence_status": "USER_PROVIDED"} for c, n, q in ROOMS],
    "total_surface_m2": SURFACES_REF["INTERIEUR"],
    "computed_surface_m2": None,
    "coherent": None,
    "annexes_ref": {"TERRASSE_COUVERTE": SURFACES_REF["TERRASSE_COUVERTE"],
                    "GARAGE": SURFACES_REF["GARAGE"]},
}
p_prog = os.path.join(P, "program", "program.json")
save_json(p_prog, prog); ev.created(p_prog)
results["files_created"].append(p_prog)
ev.test("no_invented_room_surface",
        all(r["surface_m2"] is None for r in prog["rooms"]))
ev.test("terrain_375_recorded", site["fields"]["terrain_surface_m2"]["value"] == 375.0)
ev.close("EXECUTED")
evf = ev.out(); results["evidence_files"].append(evf)
op("contexte / site / programme", "EXECUTED",
   "terrain 375 m2, Abidjan, 15 pieces listees, surfaces unitaires UNKNOWN")

# ================================================================ 5/6. RENDUS REJETES
ev = Evidence("sync_renders_rejection", P)
ev.tool("python3")
SRC = os.path.join(P, "3D", "Renders")
DST = os.path.join(P, "history", "renders_v1_rejected")
os.makedirs(DST, exist_ok=True)
manifest = {"project_id": PID, "created_at": STAMP,
            "status": "REJECTED", "reason": (
                "Geometrie non conforme a VARIANT_B validee : terrasse 48 m2 (attendu 24), "
                "garage 36 m2 (attendu 25)."),
            "origin": "build_villa.py", "replacement": "A REGENERER (non fait a ce stade)",
            "originals_preserved": True, "files": []}
for fn in sorted(os.listdir(SRC)):
    if not fn.lower().endswith(".png"):
        continue
    sp = os.path.join(SRC, fn)
    info = file_info(sp)
    shutil.copy2(sp, os.path.join(DST, fn))       # COPIE : l'original reste en place
    dp = os.path.join(DST, fn)
    dhash = sha256(dp)
    manifest["files"].append({
        "filename": fn, "original_path": sp, "archived_path": dp,
        "size_bytes": info["size_bytes"], "resolution": info.get("resolution"),
        "sha256_original": info["sha256"], "sha256_archive": dhash,
        "integrity_ok": info["sha256"] == dhash, "status": "REJECTED"})
    ev.test("archive_%s" % fn, info["sha256"] == dhash, "sha256 identique")
    results["files_archived"].append(dp)

p_man = os.path.join(P, "history", "rejected_renders_manifest.json")
save_json(p_man, manifest); ev.created(p_man)
results["files_created"].append(p_man)

# marqueurs DANS 3D/Renders/ — les PNG restent, mais marques REJECTED
status = {"project_id": PID, "updated_at": STAMP, "status": "REJECTED_NON_CONFORMING",
          "count": len(manifest["files"]),
          "reason": manifest["reason"],
          "final_renders_of_variant_b": False,
          "originals_preserved": True,
          "manifest": p_man,
          "files": [{"filename": f["filename"], "sha256": f["sha256_original"],
                     "status": "REJECTED"} for f in manifest["files"]]}
p_st = os.path.join(SRC, "RENDERS_STATUS.json")
save_json(p_st, status); ev.created(p_st)
results["files_created"].append(p_st)

readme = (
    "# ATTENTION — CES 5 RENDUS SONT REJETES\n\n"
    "Statut : **REJECTED / NON CONFORMES** (decide le %s)\n\n"
    "Ils ne sont **PAS** les rendus finaux de VARIANT_B.\n\n"
    "| Element | Valeur dans ces PNG | Valeur de reference retenue |\n"
    "|---|---|---|\n"
    "| Terrasse couverte | 48 m2 | **24 m2** |\n"
    "| Garage | 36 m2 | **25 m2** |\n"
    "| RDC | 81 m2 | 81 m2 (conforme) |\n"
    "| Etage | 69 m2 | 69 m2 (conforme) |\n"
    "| Interieur | 150 m2 | 150 m2 (conforme) |\n\n"
    "Les fichiers originaux sont **conserves** (aucune suppression).\n"
    "Copie d'archive + empreintes : `history/renders_v1_rejected/` et\n"
    "`history/rejected_renders_manifest.json`.\n\n"
    "Aucun rendu n'a ete regenere a ce stade. Blender n'a pas ete relance.\n"
) % STAMP
p_rd = os.path.join(SRC, "LISEZ-MOI-REJETE.md")
with open(p_rd, "w", encoding="utf-8") as f:
    f.write(readme)
ev.created(p_rd)
results["files_created"].append(p_rd)

ev.test("originals_still_present",
        all(os.path.isfile(f["original_path"]) for f in manifest["files"]),
        "%d PNG conserves" % len(manifest["files"]))
ev.test("archives_created", len(os.listdir(DST)) == len(manifest["files"]),
        "%d archives" % len(manifest["files"]))
ev.close("EXECUTED")
evf = ev.out(); results["evidence_files"].append(evf)
op("5/6. rejet + archivage des 5 rendus", "EXECUTED",
   "%d fichiers, originaux conserves" % len(manifest["files"]))

# ================================================================ 7. HISTORIQUE
ev = Evidence("sync_history", P)
os.makedirs(os.path.join(P, "history"), exist_ok=True)
entry = {
    "history_id": "HIST_%s_%s" % (PID, DATE),
    "project_id": PID, "at": STAMP,
    "type": "HUMAN_VALIDATION_SYNC",
    "variant": {"value": "VARIANT_B", "status": "VALIDATED", "user_confirmed": True},
    "geometry_change": {
        "TERRASSE_COUVERTE": {"old_m2": 48.0, "new_m2": 24.0, "delta_m2": -24.0},
        "GARAGE": {"old_m2": 36.0, "new_m2": 25.0, "delta_m2": -11.0},
        "RDC": {"old_m2": 81.0, "new_m2": 81.0, "delta_m2": 0.0},
        "ETAGE": {"old_m2": 69.0, "new_m2": 69.0, "delta_m2": 0.0},
        "INTERIEUR": {"old_m2": 150.0, "new_m2": 150.0, "delta_m2": 0.0},
    },
    "user_decision": {"DECISION": decision["DECISION"], "SOURCE": decision["SOURCE"],
                      "JUSTIFICATION": decision["JUSTIFICATION"],
                      "IMPACT": decision["IMPACT"]},
    "renders_v1": {"status": "REJECTED", "count": len(manifest["files"]),
                   "archived_to": DST, "originals_preserved": True,
                   "sha256": [f["sha256_original"] for f in manifest["files"]]},
    "actions_not_performed": ["Blender non relance", "aucun rendu regenere",
                              "Budget Engine non cree", "Planning Engine non cree",
                              "autres projets non modifies"],
}
p_hist = os.path.join(P, "history", "sync_%s.json" % DATE)
save_json(p_hist, entry); ev.created(p_hist)
results["files_created"].append(p_hist)

p_jsonl = os.path.join(P, "history", "history.jsonl")
with open(p_jsonl, "a", encoding="utf-8") as f:
    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
ev.created(p_jsonl)
results["files_created"].append(p_jsonl)

ev.test("history_json_written", os.path.getsize(p_hist) > 400)
ev.test("history_jsonl_written", os.path.getsize(p_jsonl) > 400)
ev.close("EXECUTED")
evf = ev.out(); results["evidence_files"].append(evf)
op("7. historique du projet", "EXECUTED", p_hist)

# ================================================================ RAPPORT
report = {
    "PROJECT_ID": PID,
    "VARIANT": "VARIANT_B",
    "USER_CONFIRMED": True,
    "SURFACE_RDC": SURFACES_REF["RDC"],
    "SURFACE_ETAGE": SURFACES_REF["ETAGE"],
    "SURFACE_INTERIEURE": SURFACES_REF["INTERIEUR"],
    "SURFACE_TERRASSE": SURFACES_REF["TERRASSE_COUVERTE"],
    "SURFACE_GARAGE": SURFACES_REF["GARAGE"],
    "OLD_TERRASSE": ANCIENNES["TERRASSE_COUVERTE"],
    "OLD_GARAGE": ANCIENNES["GARAGE"],
    "OLD_RENDERS_STATUS": "REJECTED_NON_CONFORMING",
    "NEW_DATA_FILES": results["files_created"],
    "DECISION_LOG": {"project": p_dec_proj, "agent": p_dec_agent,
                     "entries": 1, "decision_id": decision["decision_id"]},
    "HISTORY_UPDATED": {"json": p_hist, "jsonl": p_jsonl,
                        "rejected_archive": DST},
    "EVIDENCE_FILES": results["evidence_files"],
    "REAL_FILES_VERIFIED": [],
    "SYNCED_AT": STAMP,
    "STATUS": "SYNCED_WITH_HUMAN_VALIDATION",
    "INSTRUCTIONS_RESPECTED": ["Blender NON relance", "aucun rendu regenere",
                               "villa non reconstruite", "Budget Engine NON cree",
                               "Planning Engine NON cree", "autres projets NON modifies",
                               "aucun fichier original supprime"],
}
p_rep = os.path.join(P, "reports", "sync_report.json")
save_json(p_rep, report)
op("rapport de synchronisation", "EXECUTED", p_rep)

# verification physique finale de TOUT ce qui a ete cree/modifie
tout = sorted(set(results["files_created"] + results["files_modified"]
                  + results["files_archived"]))
for f in tout:
    inf = file_info(f)
    if inf:
        inf["path"] = os.path.relpath(f, P) if f.startswith(P) else f
        report["REAL_FILES_VERIFIED"].append(inf)
save_json(p_rep, report)

print(json.dumps({k: v for k, v in report.items()
                  if k not in ("NEW_DATA_FILES", "EVIDENCE_FILES", "REAL_FILES_VERIFIED")},
                 indent=2, ensure_ascii=False))
print("\nfichiers crees/modifies/archives :", len(tout))
print("verifies physiquement           :", len(report["REAL_FILES_VERIFIED"]))
print("evidence.json                   :", len(results["evidence_files"]))
print("originaux supprimes             : 0")

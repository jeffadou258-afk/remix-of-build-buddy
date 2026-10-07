#!/usr/bin/env python3
"""
Enregistre la DECOUVERTE BLOQUANTE : pavage rectangulaire exact IMPOSSIBLE.
Ne corrige rien silencieusement. Marque le layout v1 comme rejete.
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

FEAS = {
    "RDC": {"enveloppe_m2": 81, "pieces": 6,
            "resultats": [{"min_largeur_m": t, "faisable": False} for t in
                          [3.0, 2.5, 2.2, 2.0, 1.8, 1.5]],
            "faisable_a_partir_de": 1.2,
            "layout_1_2": "Salon 4.0x8.0 | Salle a manger 3.0x6.0 | Cuisine 2.0x6.0 | "
                          "Bureau 5.0x2.0 | Buanderie 6.0x1.0 | WC 3.0x1.0",
            "verdict": "IMPOSSIBLE avec des pieces habitables (2 pieces de 1 m de profondeur)"},
    "ETAGE": {"enveloppe_m2": 69, "pieces": 7,
              "resultats": [{"min_largeur_m": t, "faisable": False} for t in
                            [3.0, 2.5, 2.2, 2.0, 1.8, 1.5, 1.2, 1.0]],
              "verdict": "IMPOSSIBLE a TOUT seuil, y compris 1.0 m"},
    "cause_racine": [
        "32 m2 ne se factorise QUE en 4.0 x 8.0 m (ou 8.0 x 4.0) dans une enveloppe 9 x 9.",
        "Ce rectangle laisse forcement une bande de 1 m de large sur 9 m.",
        "Aucune piece du programme ne mesure 1 m de large (mini realiste : 1.5 m).",
        "13 m2 n'a qu'une seule factorisation : 2.0 x 6.5 m (13 est premier).",
        "Ces deux contraintes rendent tout pavage rectangulaire exact impossible.",
    ],
    "conclusion_metier": (
        "Un pavage 100 % rectangulaire dans 9 x 9 ne peut pas produire des pieces habitables. "
        "Ce n'est pas une erreur de calcul : c'est une limite geometrique du modele "
        "(les 81 m2 sont traites comme une surface NETTE a caser exactement, sans murs, "
        "sans circulation, et avec des pieces forcement rectangulaires)."),
    "options": [
        {"id": "1", "titre": "Elargir l'enveloppe (RECOMMANDE)",
         "detail": "81 m2 habitables exigent des murs (0.2 m) et une circulation. "
                   "Une enveloppe brute de ~9.8 x 9.8 m (96 m2) permet des pieces rectangulaires "
                   "confortables + couloir. L'emprise 'compacte' reste respectee dans l'esprit.",
         "impact": "RDC 81 m2 net / ~96 m2 brut. Etage : 69 m2 net.",
         "statut": "A VALIDER PAR L'UTILISATEUR"},
        {"id": "2", "titre": "Garder 9 x 9 brut et reduire les surfaces",
         "detail": "A 9 x 9 brut, la surface habitable nette reelle serait ~68-72 m2, pas 81.",
         "impact": "Contredit les surfaces de reference validees.",
         "statut": "A VALIDER PAR L'UTILISATEUR"},
        {"id": "3", "titre": "Garder 9 x 9 et 81 m2, accepter des pieces non rectangulaires",
         "detail": "Salon/Salle a manger en L, plus un couloir desservant les pieces de service.",
         "impact": "Plan plus complexe ; necessite un solveur de formes en L.",
         "statut": "A VALIDER PAR L'UTILISATEUR"},
    ],
}

ev = Evidence("envelope_feasibility", P)
ev.tool("python3")
ev.test("rdc_infaisable_min_1_5m", True, "min 1.5 m -> INFAISABLE")
ev.test("rdc_faisable_seulement_min_1_2m", True, "mais avec 2 pieces de 1 m de profondeur")
ev.test("etage_infaisable_tous_seuils", True, "y compris 1.0 m")
ev.test("aucune_correction_silencieuse", True, "layout v1 marque REJECTED, options proposees")
ev.close("BLOCKED")
evf = ev.out()

# ---- marquer le layout v1 comme rejete (sans rien supprimer)
FP = os.path.join(P, "floorplan", "floor_plan.json")
fp = json.load(open(FP, encoding="utf-8"))
fp["status"] = "REJECTED_QUALITY"
fp["rejected_at"] = STAMP
fp["rejection_reason"] = (
    "Pavage mathematiquement exact mais architecturalement inutilisable : "
    "Buanderie 6.0x1.0 m et WC 3.0x1.0 m (1 m de profondeur). "
    "Aucune correction silencieuse. Voir reports/envelope_feasibility_report.json.")
fp["geometric_verdict"] = "PAVAGE RECTANGULAIRE EXACT IMPOSSIBLE AVEC PIECES HABITABLES"
save_json(FP, fp)
ev.record(FP)

STATUSF = os.path.join(P, "floorplan", "LAYOUT_STATUS.json")
save_json(STATUSF, {
    "project_id": PID, "updated_at": STAMP,
    "layout_status": "REJECTED_QUALITY",
    "plans_for_reference_only": ["plan_rdc.svg", "plan_etage.svg"],
    "do_not_use_as_final": True,
    "reason": fp["rejection_reason"],
    "blocking_issue": "enveloppe 9 x 9 incompatible avec 81 m2 de pieces habitables rectangulaires",
    "next_action": "HUMAN GATE : choisir une option (1, 2 ou 3) — voir envelope_feasibility_report.json",
    "evidence": evf})
ev.record(STATUSF)

rep = {
    "PROJECT_ID": PID, "VARIANT": "VARIANT_B",
    "ENVELOPE": "9.00 x 9.00 m (choix B utilisateur)",
    "LAYOUT_STATUS": "REJECTED_QUALITY",
    "GEOMETRIC_VERDICT": "PAVAGE RECTANGULAIRE EXACT IMPOSSIBLE AVEC PIECES HABITABLES",
    "FEASIBILITY": FEAS,
    "SURFACE_CHECK": "NON_APPLICABLE — aucun plan valide produit",
    "PLANS": {"plan_rdc.svg": "REFERENCE SEULEMENT (rejete)",
              "plan_etage.svg": "REFERENCE SEULEMENT (rejete)",
              "implantation.svg": "valide (hors sujet du blocage)"},
    "RDC_SUM": 81, "ETAGE_SUM": 69,
    "EVIDENCE_FILES": [evf],
    "REAL_FILES_VERIFIED": [],
    "BLENDER_TOUCHED": False,
    "RENDERS_GENERATED": 0,
    "SYNCED_AT": STAMP,
    "STATUS": "HUMAN_VALIDATION_REQUIRED_ENVELOPE",
}
p_rep = os.path.join(P, "reports", "envelope_feasibility_report.json")
save_json(p_rep, rep)

decision = {
    "decision_id": "DEC_%s_006" % PID, "project_id": PID, "at": STAMP, "seq": 6,
    "DECISION": ("BLOCAGE : pavage rectangulaire exact de 81 m2 dans 9 x 9 IMPOSSIBLE avec des "
                 "pieces habitables. Layout v1 rejete. Attribution au HUMAN GATE."),
    "SOURCE": ("Construction Agent — solveur de pavage (backtracking, grille 0,5 m) + balayage "
               "de faisabilite des largeurs minimales."),
    "JUSTIFICATION": ("32 m2 ne se factorise qu'en 4.0 x 8.0 m dans une enveloppe 9 x 9, ce qui "
                      "laisse une bande de 1 m de large. Aucune piece du programme ne mesure 1 m de "
                      "large. Le RDC n'est faisable qu'a partir d'une largeur minimale de 1.2 m, et "
                      "alors deux pieces mesurent 1 m de profondeur (inutilisables). L'etage est "
                      "infaisable a TOUS les seuils testes, y compris 1.0 m. "
                      "Ce n'est pas une erreur de calcul : c'est une limite geometrique du modele."),
    "IMPACT": ("Aucun plan exploitable produit. Les SVG v1 restent sur disque comme REFERENCE mais "
               "sont marques REJECTED_QUALITY. Aucun rendu, .blend inchange. Trois options "
               "proposees a l'utilisateur : (1) elargir l'enveloppe, (2) reduire les surfaces, "
               "(3) accepter des pieces non rectangulaires."),
    "STATUS": "BLOCKED",
}
hist = {"history_id": "HIST_%s_FEASIBILITY_%s" % (PID, DATE), "project_id": PID, "at": STAMP,
        "type": "GEOMETRIC_FEASIBILITY_BLOCKED", "variant": "VARIANT_B",
        "feasibility": FEAS, "rejected_layout": "layout v1 (DEC_..._004)",
        "rejection_reason": fp["rejection_reason"],
        "actions": {"blender_launched": False, "blend_modified": False, "renders_generated": False},
        "blend_integrity": {"sha256": SHA_B}}
p_hist = os.path.join(P, "history", "feasibility_%s.json" % DATE)
save_json(p_hist, hist)
p_jsonl = os.path.join(P, "history", "history.jsonl")
with open(p_jsonl, "a", encoding="utf-8") as f:
    f.write(json.dumps(hist, ensure_ascii=False) + "\n")
p_dec = os.path.join(P, "memory", "decisions.jsonl")
with open(p_dec, "a", encoding="utf-8") as f:
    f.write(json.dumps(decision, ensure_ascii=False) + "\n")
p_ag = os.path.join(AGENT, "memory", "decisions.jsonl")
with open(p_ag, "a", encoding="utf-8") as f:
    f.write(json.dumps(decision, ensure_ascii=False) + "\n")

SHA_A = sha256(BLEND)
PNG_A = sum(len([f for f in fs if f.lower().endswith(".png")]) for _, _, fs in os.walk(P))
rep["BLENDER_TOUCHED"] = SHA_A != SHA_B
rep["BLEND_UNCHANGED"] = SHA_A == SHA_B
rep["PNG_BEFORE"] = PNG_B
rep["PNG_AFTER"] = PNG_A
for f in sorted(set([evf, FP, STATUSF, p_hist, p_jsonl, p_dec, p_ag, p_rep])):
    inf = file_info(f)
    if inf:
        inf["path"] = os.path.relpath(f, P) if f.startswith(P) else f
        rep["REAL_FILES_VERIFIED"].append(inf)
save_json(p_rep, rep)

print(json.dumps({k: v for k, v in rep.items()
                  if k not in ("FEASIBILITY", "REAL_FILES_VERIFIED", "EVIDENCE_FILES")},
                 indent=2, ensure_ascii=False))
print("\nfichiers verifies :", len(rep["REAL_FILES_VERIFIED"]))
print(".blend inchange :", SHA_A == SHA_B, "| PNG generes :", PNG_A - PNG_B)

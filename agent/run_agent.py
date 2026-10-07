#!/usr/bin/env python3
"""
Construction Agent v2.0.0 — ORCHESTRATEUR.

Usage :
  python3 run_agent.py <project_dir> [--yes] [--until ENGINE]

Enchaine les moteurs dans l'ordre du workflow (section 5 de la specification).
S'arrete aux HUMAN GATES sauf si --yes est passe.
Un moteur qui retourne BLOCKED / FAILED interrompt la chaine (sauf --force).
"""
import os
import sys
import json
import argparse
import importlib.util

ROOT = os.path.dirname(os.path.abspath(__file__))
ENGINES_DIR = os.path.join(ROOT, "engines")

PIPELINE = [
    ("discovery",          "PHASE 0  — DECOUVERTE"),
    ("programming",        "PHASE 1  — PROGRAMMATION"),
    ("site_analysis",      "PHASE 2  — SITE & CONTRAINTES"),
    ("design",             "PHASE 3/4 — STRATEGIE SPATIALE + CONCEPT  [HUMAN GATE]"),
    ("dimension",          "PHASE 5  — DIMENSIONNEMENT"),
    ("floor_plan",         "PHASE 6  — PLANS"),
    ("structural_concept", "PHASE 6b — STRUCTURE CONCEPTUELLE        [HUMAN GATE]"),
    ("bim_3d",             "PHASE 7  — 3D / BIM"),
    ("visualization",      "PHASE 8a — INTENTIONS DE VUE"),
    ("rendering",          "PHASE 8b — RENDUS"),
    ("documentation",      "PHASE 9  — DOCUMENTATION"),
    ("qa",                 "PHASE 10 — QA/QC"),
    ("delivery",           "PHASE 11 — LIVRAISON"),
]

GATES = {"design", "structural_concept"}


def load_engine(name):
    path = os.path.join(ENGINES_DIR, name, "engine.py")
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    spec = importlib.util.spec_from_file_location("ca_engine_%s" % name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--yes", action="store_true", help="passer les human gates")
    ap.add_argument("--force", action="store_true", help="continuer malgre FAILED/BLOCKED")
    ap.add_argument("--until", default=None, help="s'arreter apres ce moteur")
    a = ap.parse_args()

    project_dir = os.path.abspath(a.project_dir)
    os.makedirs(project_dir, exist_ok=True)
    results = []

    print("=" * 68)
    print("CONSTRUCTION AGENT v2.0.0 — %s" % os.path.basename(project_dir))
    print("=" * 68)

    for name, label in PIPELINE:
        print("\n>>> %-14s %s" % (name, label))
        try:
            mod = load_engine(name)
            res = mod.run(project_dir) if name != "programming" else mod.run(project_dir)
        except Exception as e:
            res = {"status": "FAILED", "error": "%s: %s" % (type(e).__name__, e)}
        status = res.get("status", "UNKNOWN")
        res["_engine"] = name
        results.append(res)
        print("    status = %s" % status)
        details = {k: v for k, v in res.items() if k not in ("status", "views", "_engine")}
        if details:
            print("    " + json.dumps(details, ensure_ascii=False)[:300])

        if status in ("FAILED", "BLOCKED") and not a.force:
            print("\n!! CHAINE INTERROMPUE : %s = %s" % (name, status))
            break
        if name in GATES and not a.yes:
            print("\n!! HUMAN GATE a %s — validation utilisateur requise." % name)
            print("   Relancer avec --yes pour poursuivre.")
            break
        if a.until and name == a.until:
            print("\n--until %s atteint." % name)
            break

    od = os.path.join(project_dir, "reports")
    os.makedirs(od, exist_ok=True)
    out = os.path.join(od, "pipeline_run.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"agent": "construction-agent", "version": "2.0.0",
                   "project_dir": project_dir, "steps": results}, f,
                  indent=2, ensure_ascii=False)
    print("\n" + "=" * 68)
    for r in results:
        print("  %-20s %s" % (r["_engine"], r["status"]))
    print("  -> %s" % out)
    print("=" * 68)


if __name__ == "__main__":
    main()

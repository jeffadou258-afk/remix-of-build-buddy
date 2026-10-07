#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Non-regression V3.4 — capture du comportement ACTUEL (avant toute modification).

  python3 tests/regression/baseline_tool.py capture   -> ecrit baseline_v34.json
  python3 tests/regression/baseline_tool.py compare   -> compare a baseline_v34.json (exit 1 si ecart)

Capture uniquement des faits mesures (aucune valeur supposee) :
  1. empreinte sha256 de chaque fichier de donnees (projects/, memory/, schemas/,
     web/frontend/, workspace/, agent.json) -> rien n'est supprime ni modifie ;
  2. reponses de chaque route GET /api/* du serveur reel (horodatages retires) ;
  3. sortie de programming.run() sans parametre (DEFAULT_ROOMS) ;
  4. sortie de `python3 run_agent.py <tmp> --until programming` (statuts).
Le serveur doit tourner sur 127.0.0.1:8765 (web/start_web.sh ou python3 web/backend/server.py).
"""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile, urllib.request, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "baseline_v34.json")
SRV = os.environ.get("CA_SERVER", "http://127.0.0.1:8765")
DATA_DIRS = ["projects", "memory", "schemas", os.path.join("web", "frontend"), "workspace"]
DATA_FILES = ["agent.json", "AGENT_SPEC.md", "SKILL.md", "SOUL.md"]
SKIP = re.compile(r"(__pycache__|\.pyc$|\.DS_Store|/logs/|\.log$)")
GET_ROUTES = ["/api/health", "/api/project", "/api/project/status", "/api/phases", "/api/phases/01",
              "/api/budget", "/api/quantities", "/api/documents", "/api/plans", "/api/renders",
              "/api/bim", "/api/gates", "/api/bim/elements", "/api/assistant/context",
              "/api/assistant/next-step", "/api/assistant?q=fondations", "/api/glossary/poteau",
              "/api/search?q=chambre", "/api/inexistant"]
TIME_KEYS = {"at", "created_at", "started_at", "completed_at", "generated_at", "exportedAt", "now", "mtime"}
ISO = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[^\"\s]*")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def data_hashes():
    out = {}
    for d in DATA_DIRS:
        for dp, _, fs in os.walk(os.path.join(ROOT, d)):
            for f in fs:
                p = os.path.join(dp, f)
                rel = os.path.relpath(p, ROOT)
                if not SKIP.search("/" + rel):
                    out[rel] = sha(p)
    for f in DATA_FILES:
        p = os.path.join(ROOT, f)
        if os.path.isfile(p):
            out[f] = sha(p)
    return out


def strip_time(o):
    if isinstance(o, dict):
        return {k: ("<t>" if k in TIME_KEYS else strip_time(v)) for k, v in o.items()}
    if isinstance(o, list):
        return [strip_time(v) for v in o]
    if isinstance(o, str):
        return ISO.sub("<t>", o.replace(ROOT, "<ROOT>"))
    return o


def api_snapshots():
    out = {}
    for r in GET_ROUTES:
        try:
            with urllib.request.urlopen(SRV + r, timeout=30) as resp:
                code, body = resp.status, resp.read()
        except urllib.error.HTTPError as e:
            code, body = e.code, e.read()
        try:
            out[r] = {"code": code, "json": strip_time(json.loads(body.decode("utf-8")))}
        except Exception:
            out[r] = {"code": code, "sha256": hashlib.sha256(body).hexdigest()}
    return out


def programming_default():
    spec = importlib.util.spec_from_file_location("ca_prog", os.path.join(ROOT, "engines", "programming", "engine.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    tmp = tempfile.mkdtemp(prefix="ca_reg_")
    try:
        res = m.run(tmp)
        prog = json.load(open(os.path.join(tmp, "program", "program.json"), encoding="utf-8"))
        prog["project_id"] = "<tmp>"
        return {"result": {k: v for k, v in res.items() if k != "program"},
                "program": strip_time(prog),
                "DEFAULT_ROOMS": [list(r) for r in m.DEFAULT_ROOMS]}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def cli_until_programming():
    tmp = tempfile.mkdtemp(prefix="ca_reg_cli_")
    try:
        p = subprocess.run([sys.executable, os.path.join(ROOT, "run_agent.py"), tmp, "--until", "programming"],
                           capture_output=True, text=True, timeout=300)
        rep = json.load(open(os.path.join(tmp, "reports", "pipeline_run.json"), encoding="utf-8"))
        return {"returncode": p.returncode, "steps": [[s["_engine"], s["status"]] for s in rep["steps"]]}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def capture():
    return {"data_files": data_hashes(), "api": api_snapshots(),
            "programming_default": programming_default(), "cli_until_programming": cli_until_programming()}


def compare(base, cur):
    errs = []
    for f, h in base["data_files"].items():
        if f not in cur["data_files"]:
            errs.append("FICHIER SUPPRIME: " + f)
        elif cur["data_files"][f] != h:
            errs.append("FICHIER MODIFIE: " + f)
    for r, v in base["api"].items():
        if cur["api"].get(r) != v:
            errs.append("REPONSE API CHANGEE: " + r)
    for k in ("programming_default", "cli_until_programming"):
        if cur[k] != base[k]:
            errs.append("COMPORTEMENT CHANGE: " + k)
    return errs


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "compare"
    cur = capture()
    if mode == "capture":
        json.dump(cur, open(BASE, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print("baseline ecrite :", BASE, "·", len(cur["data_files"]), "fichiers ·", len(cur["api"]), "routes")
        sys.exit(0)
    errs = compare(json.load(open(BASE, encoding="utf-8")), cur)
    for e in errs:
        print("  FAIL", e)
    print("NON-REGRESSION V3.4 :", "PASS" if not errs else "FAIL (%d ecart(s))" % len(errs))
    sys.exit(1 if errs else 0)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""API multi-projets ConstructionAgent v1 (stdlib uniquement).

Separee de web/backend/server.py (V3.4), qui reste inchange.
  CA_API_KEY   (obligatoire) cle partagee avec le relais serveur de l'application
  CA_DATA_ROOT (defaut : <repo>/workspace/api_projects) un dossier par projet
  CA_API_PORT  (defaut : 8766), ecoute sur 127.0.0.1 uniquement
Chaque requete (hors /v1/health) exige : Authorization: Bearer <CA_API_KEY> et X-Owner-Id.
"""
import hmac, json, os, re, sys, threading, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline as PL  # noqa: E402

KEY = os.environ.get("CA_API_KEY", "")
DATA = os.path.abspath(os.environ.get("CA_DATA_ROOT", os.path.join(PL.ROOT, "workspace", "api_projects")))
PORT = int(os.environ.get("CA_API_PORT", "8766"))
EX = PL.EXTRACTION
PID_RE = re.compile(r"^P_[0-9a-f]{32}$")
OWNER_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
LOCKS, LOCKS_GUARD = {}, threading.Lock()
ARTIFACTS = {"context": "project_context.json", "program": "program/program.json", "site": "site/site.json",
             "design": "design/design_variants.json", "dimensions": "dimensions/dimensions.json",
             "floor_plan": "floorplan/floor_plan.json", "structure": "structure/structural_concept.json",
             "bim": "3d/model_3d.json", "render_spec": "3d/render_spec.json", "renders": "renders/render.json",
             "qa": "reports/qa_report.json", "delivery": "exports/delivery.json"}
MEMORY_FILES = ["constraints", "decisions", "assumptions"]


def lock(pid):
    with LOCKS_GUARD:
        return LOCKS.setdefault(pid, threading.Lock())


def jsonl(p):
    try:
        return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    except FileNotFoundError:
        return []


class H(BaseHTTPRequestHandler):
    server_version = "ConstructionAgentAPI/1"

    def log_message(self, *a):
        pass

    def send(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(b)

    def err(self, code, msg):
        self.send(code, {"error": {"code": code, "message": msg}})

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > 100_000:
            raise ValueError("corps trop volumineux")
        if not n:
            return {}
        d = json.loads(self.rfile.read(n).decode("utf-8"))
        if not isinstance(d, dict):
            raise ValueError("objet JSON attendu")
        return d

    def auth(self):
        tok = (self.headers.get("Authorization") or "").removeprefix("Bearer ").strip()
        if not tok or not hmac.compare_digest(tok, KEY):
            self.err(401, "cle API absente ou invalide"); return None
        owner = self.headers.get("X-Owner-Id") or ""
        if not OWNER_RE.match(owner):
            self.err(400, "X-Owner-Id absent ou invalide"); return None
        return owner

    def project(self, pid, owner):
        if not PID_RE.match(pid):
            return None
        pd = os.path.join(DATA, pid)
        meta = PL.jload(os.path.join(pd, "project.json"))
        if not meta or meta.get("owner_id") != owner:
            return None  # 404 identique : on ne revele pas l'existence d'un projet d'autrui
        return pd, meta

    def do_GET(self): self.route("GET")
    def do_POST(self): self.route("POST")
    def do_PATCH(self): self.route("PATCH")

    def route(self, method):
        path = self.path.split("?")[0].rstrip("/")
        if method == "GET" and path == "/v1/health":
            return self.send(200, {"status": "OK", "api": "v1", "engines": PL.PIPELINE, "gates": sorted(PL.GATES)})
        if not path.startswith("/v1/"):
            return self.err(404, "introuvable")
        owner = self.auth()
        if owner is None:
            return
        try:
            body = self.body() if method in ("POST", "PATCH") else {}
        except Exception as e:
            return self.err(400, "JSON invalide : %s" % e)
        parts = path.split("/")[2:]  # ["projects", pid, ...]
        try:
            if parts == ["projects"]:
                return self.create(owner, body) if method == "POST" else self.list(owner) if method == "GET" else self.err(405, "methode")
            if len(parts) >= 2 and parts[0] == "projects":
                p = self.project(parts[1], owner)
                if not p:
                    return self.err(404, "projet introuvable")
                return self.sub(method, parts[2:], parts[1], p[0], p[1], owner, body)
            return self.err(404, "introuvable")
        except Exception as e:
            return self.err(500, "erreur interne : %s" % type(e).__name__)

    # ---- projets
    def create(self, owner, body):
        title = str(body.get("title") or "").strip()[:120] or "Nouveau projet"
        pid = "P_" + uuid.uuid4().hex
        pd = os.path.join(DATA, pid)
        os.makedirs(os.path.join(pd, "memory"))
        meta = {"id": pid, "owner_id": owner, "title": title, "created_at": PL.now()}
        PL.jsave(os.path.join(pd, "project.json"), meta)
        PL.jsave(PL.state_path(pd), PL.initial_state())
        PL.jsave(PL.gates_path(pd), PL.initial_gates())
        EX._save(pd, EX.empty_inputs(pid))
        return self.send(201, {"project": meta})

    def list(self, owner):
        out = []
        if os.path.isdir(DATA):
            for pid in sorted(os.listdir(DATA)):
                m = PID_RE.match(pid) and PL.jload(os.path.join(DATA, pid, "project.json"))
                if m and m.get("owner_id") == owner:
                    out.append(dict(m, state=PL.jload(PL.state_path(os.path.join(DATA, pid)))))
        return self.send(200, {"projects": out})

    def sub(self, method, rest, pid, pd, meta, owner, body):
        r = (method, rest[0] if rest else "")
        if r == ("GET", ""):
            return self.send(200, {"project": meta, "state": PL.jload(PL.state_path(pd)), "gates": PL.jload(PL.gates_path(pd))})
        if r == ("GET", "state"):
            return self.send(200, {"state": PL.jload(PL.state_path(pd))})
        if r == ("GET", "messages"):
            return self.send(200, {"messages": jsonl(os.path.join(pd, "conversation.jsonl"))})
        if r == ("POST", "messages"):
            text = body.get("text")
            if not isinstance(text, str) or not text.strip() or len(text) > 5000:
                return self.err(400, "text requis (1 a 5000 caracteres)")
            mid = "M_" + uuid.uuid4().hex[:12]
            with lock(pid):
                with open(os.path.join(pd, "conversation.jsonl"), "a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"id": mid, "role": "user", "text": text, "at": PL.now()}, ensure_ascii=False) + "\n")
                res = EX.run(pd, text, mid)
            res.pop("inputs", None)
            return self.send(201, {"message_id": mid, "extraction": res})
        if r == ("GET", "inputs"):
            return self.send(200, {"inputs": EX.load(pd)})
        if r == ("PATCH", "inputs"):
            ch = body.get("changes")
            if not isinstance(ch, dict) or not ch:
                return self.err(400, "changes requis")
            with lock(pid):
                try:
                    d = EX.edit(pd, ch, owner)
                except ValueError as e:
                    return self.err(400, str(e))
            return self.send(200, {"inputs": d})
        if r == ("POST", "rooms"):
            name, surf, level = body.get("name"), body.get("surface_m2"), body.get("level")
            if not isinstance(name, str) or not name.strip() or len(name) > 60 \
                    or not isinstance(surf, (int, float)) or isinstance(surf, bool) or not 0 < surf < 10000 \
                    or not isinstance(level, str) or not level.strip() or len(level) > 30:
                return self.err(400, "name (texte), surface_m2 (> 0) et level (texte) requis")
            with lock(pid):
                d = EX.load(pd)
                room = {"name": name.strip(), "level": level.strip(), "surface_m2": EX._given(float(surf), None, None, "formulaire")}
                room["surface_m2"]["source"]["user_id"] = owner
                d["rooms"].append(room)
                EX._save(pd, d)
            return self.send(201, {"room": room})
        if r == ("GET", "unknowns"):
            d = EX.load(pd)
            unk = [k for k, v in d["fields"].items() if v["status"] == "UNKNOWN"]
            if d["budget"]["declared"]["status"] == "UNKNOWN":
                unk.append("budget.declared")
            return self.send(200, {"unknowns": unk, "quantities": d["quantities"]["status"],
                                   "budget_estimate": d["budget"]["estimate"]["status"]})
        if r == ("POST", "runs"):
            lk = lock(pid)
            if not lk.acquire(blocking=False):
                return self.err(409, "execution deja en cours")
            try:
                rec, why = PL.run(pd, "R_" + uuid.uuid4().hex[:12])
            finally:
                lk.release()
            return self.err(409, why) if why else self.send(200, {"run": rec})
        if r == ("GET", "history"):
            return self.send(200, {"runs": jsonl(os.path.join(pd, "runs.jsonl")), "inputs_history": EX.load(pd)["history"]})
        if r == ("GET", "gates"):
            return self.send(200, {"gates": PL.jload(PL.gates_path(pd))})
        if method == "POST" and len(rest) == 3 and rest[0] == "gates" and rest[2] == "decision":
            dec = body.get("decision")
            if dec not in ("approve", "reject"):
                return self.err(400, "decision = approve | reject")
            with lock(pid):
                g, code, why = PL.decide(pd, rest[1], dec, owner, str(body.get("comment") or "")[:1000] or None,
                                         str(body.get("variant_id") or "")[:40] or None)
            return self.err(code, why) if why else self.send(200, {"gate": g})
        if r == ("GET", "memory"):
            return self.send(200, {"memory": {m: jsonl(os.path.join(pd, "memory", m + ".jsonl")) for m in MEMORY_FILES}})
        if method == "GET" and len(rest) == 2 and rest[0] == "artifacts":
            a = rest[1]
            if a in ("budget", "quantities"):
                d = EX.load(pd)
                return self.send(200, {"artifact": d["budget"] if a == "budget" else d["quantities"]})
            if a == "bim_elements":
                return self.send(200, {"artifact": {"status": "NOT_EXECUTED", "reason": "aucun moteur ne produit la liste des elements BIM"}})
            if a not in ARTIFACTS:
                return self.err(404, "artefact inconnu")
            return self.send(200, {"artifact": PL.jload(os.path.join(pd, ARTIFACTS[a]))})
        return self.err(404, "introuvable")


if __name__ == "__main__":
    if len(KEY) < 16:
        sys.exit("CA_API_KEY absente ou trop courte (16 caracteres minimum)")
    os.makedirs(DATA, exist_ok=True)
    print("API ConstructionAgent v1 -> http://127.0.0.1:%d  (donnees : %s)" % (PORT, DATA))
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de l'API multi-projets v1 (web/api/server.py).
Demarre un serveur reel sur un port libre, avec un dossier de donnees temporaire.
Aucune donnee de la villa de test n'est lue ou ecrite."""
import json, os, shutil, socket, subprocess, sys, tempfile, time, unittest, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KEY = "test-key-0123456789"
A, B = "user-a", "user-b"


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


class Api(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = tempfile.mkdtemp(prefix="ca_api_")
        cls.port = free_port()
        env = dict(os.environ, CA_API_KEY=KEY, CA_DATA_ROOT=cls.data, CA_API_PORT=str(cls.port))
        cls.proc = subprocess.Popen([sys.executable, os.path.join(ROOT, "web", "api", "server.py")],
                                    env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            try:
                urllib.request.urlopen("http://127.0.0.1:%d/v1/health" % cls.port, timeout=1); break
            except Exception:
                time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate(); cls.proc.wait(5); shutil.rmtree(cls.data, ignore_errors=True)

    def call(self, method, path, body=None, owner=A, key=KEY):
        h = {"Content-Type": "application/json"}
        if key: h["Authorization"] = "Bearer " + key
        if owner: h["X-Owner-Id"] = owner
        req = urllib.request.Request("http://127.0.0.1:%d%s" % (self.port, path), method=method, headers=h,
                                     data=json.dumps(body).encode() if body is not None else None)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    def new(self, owner=A):
        s, d = self.call("POST", "/v1/projects", {"title": "Villa test API"}, owner)
        self.assertEqual(s, 201); return d["project"]["id"]

    # --- authentification / isolation
    def test_01_health_public(self):
        s, d = self.call("GET", "/v1/health", key=None, owner=None)
        self.assertEqual(s, 200); self.assertEqual(d["status"], "OK")

    def test_02_no_key_401(self):
        self.assertEqual(self.call("GET", "/v1/projects", key=None)[0], 401)
        self.assertEqual(self.call("GET", "/v1/projects", key="mauvaise")[0], 401)

    def test_03_no_owner_400(self):
        self.assertEqual(self.call("GET", "/v1/projects", owner=None)[0], 400)

    def test_04_isolation(self):
        pid = self.new(A)
        self.assertEqual(self.call("GET", "/v1/projects/" + pid, owner=B)[0], 404)
        self.assertNotIn(pid, [p["id"] for p in self.call("GET", "/v1/projects", owner=B)[1]["projects"]])
        self.assertEqual(self.call("GET", "/v1/projects/../../etc")[0], 404)

    # --- creation : aucun defaut
    def test_05_create_all_unknown(self):
        pid = self.new()
        s, d = self.call("GET", "/v1/projects/%s/inputs" % pid)
        self.assertEqual(s, 200)
        self.assertTrue(all(f["status"] == "UNKNOWN" for f in d["inputs"]["fields"].values()))
        self.assertEqual(d["inputs"]["budget"]["estimate"]["status"], "NOT_EXECUTED")
        st = self.call("GET", "/v1/projects/%s/state" % pid)[1]
        self.assertEqual(st["state"]["status"], "CREATED")

    # --- conversation -> extraction -> memory projet
    def test_06_message_extraction_and_memory(self):
        pid = self.new()
        s, d = self.call("POST", "/v1/projects/%s/messages" % pid,
                         {"text": "Je veux construire une villa R+1 de 4 chambres sur un terrain de 600 m²."})
        self.assertEqual(s, 201)
        self.assertEqual(sorted(d["extraction"]["user_provided"]),
                         ["bedrooms", "building_type", "levels_count", "levels_label", "plot_area_m2"])
        inp = self.call("GET", "/v1/projects/%s/inputs" % pid)[1]["inputs"]
        self.assertEqual(inp["fields"]["bedrooms"]["value"], 4)
        self.assertFalse(inp["fields"]["bedrooms"]["technically_validated"])
        self.assertEqual(len(self.call("GET", "/v1/projects/%s/messages" % pid)[1]["messages"]), 1)
        mem = self.call("GET", "/v1/projects/%s/memory" % pid)[1]["memory"]
        self.assertGreaterEqual(len(mem["constraints"]), 5)
        unk = self.call("GET", "/v1/projects/%s/unknowns" % pid)[1]["unknowns"]
        self.assertIn("location_city", unk); self.assertNotIn("bedrooms", unk)

    def test_07_edit_history_unknown(self):
        pid = self.new()
        self.call("PATCH", "/v1/projects/%s/inputs" % pid, {"changes": {"plot_area_m2": 600}})
        self.call("PATCH", "/v1/projects/%s/inputs" % pid, {"changes": {"plot_area_m2": None}})
        inp = self.call("GET", "/v1/projects/%s/inputs" % pid)[1]["inputs"]
        self.assertEqual(inp["fields"]["plot_area_m2"]["status"], "UNKNOWN")
        self.assertEqual(inp["history"][-1]["previous"]["value"], 600)
        self.assertEqual(self.call("PATCH", "/v1/projects/%s/inputs" % pid, {"changes": {"pirate": 1}})[0], 400)

    # --- execution : blocage sans programme (pas de DEFAULT_ROOMS)
    def test_08_run_blocks_without_rooms(self):
        pid = self.new()
        s, d = self.call("POST", "/v1/projects/%s/runs" % pid, {})
        self.assertEqual(s, 200)
        self.assertEqual(d["run"]["status"], "BLOCKED")
        self.assertEqual(d["run"]["stopped_at"], "programming")
        self.assertIsNone(self.call("GET", "/v1/projects/%s/artifacts/program" % pid)[1]["artifact"])

    # --- execution complete : gate design -> decision -> reprise -> gate structure
    def test_09_gates_flow(self):
        pid = self.new()
        for r in [("Salon", 36, "RDC"), ("Cuisine", 12, "RDC"), ("Chambre 1", 14, "ETAGE")]:
            s, _ = self.call("POST", "/v1/projects/%s/rooms" % pid, {"name": r[0], "surface_m2": r[1], "level": r[2]})
            self.assertEqual(s, 201)
        d = self.call("POST", "/v1/projects/%s/runs" % pid, {})[1]["run"]
        self.assertEqual(d["status"], "AWAITING_GATE"); self.assertEqual(d["stopped_at"], "design")
        prog = self.call("GET", "/v1/projects/%s/artifacts/program" % pid)[1]["artifact"]
        self.assertEqual([r["name"] for r in prog["rooms"]], ["Salon", "Cuisine", "Chambre 1"])
        self.assertEqual(prog["total_surface_m2"], 62.0)
        for r in prog["rooms"]:
            self.assertEqual((r["source"], r["validation"], r["assumption"]), ("USER_PROVIDED", "NOT_VALIDATED", False))
        self.assertEqual(self.call("POST", "/v1/projects/%s/runs" % pid, {})[0], 409)
        g = self.call("GET", "/v1/projects/%s/gates" % pid)[1]["gates"]
        self.assertEqual(g["design"]["status"], "OPEN")
        s, _ = self.call("POST", "/v1/projects/%s/gates/design/decision" % pid, {"decision": "approve", "variant_id": "VARIANT_B"})
        self.assertEqual(s, 200)
        d = self.call("POST", "/v1/projects/%s/runs" % pid, {})[1]["run"]
        self.assertEqual(d["started_at_engine"], "dimension")
        self.assertEqual(d["status"], "AWAITING_GATE"); self.assertEqual(d["stopped_at"], "structural_concept")
        mem = self.call("GET", "/v1/projects/%s/memory" % pid)[1]["memory"]
        self.assertEqual(mem["decisions"][-1]["gate"], "design")
        self.assertEqual(len(self.call("GET", "/v1/projects/%s/history" % pid)[1]["runs"]), 2)

    def test_10_reject_reruns_engine(self):
        pid = self.new()
        self.call("POST", "/v1/projects/%s/rooms" % pid, {"name": "Salon", "surface_m2": 30, "level": "RDC"})
        self.call("POST", "/v1/projects/%s/runs" % pid, {})
        self.assertEqual(self.call("POST", "/v1/projects/%s/gates/design/decision" % pid, {"decision": "reject", "comment": "non"})[0], 200)
        d = self.call("POST", "/v1/projects/%s/runs" % pid, {})[1]["run"]
        self.assertEqual(d["started_at_engine"], "design"); self.assertEqual(d["stopped_at"], "design")

    def test_11_gate_errors(self):
        pid = self.new()
        self.assertEqual(self.call("POST", "/v1/projects/%s/gates/design/decision" % pid, {"decision": "approve"})[0], 409)
        self.assertEqual(self.call("POST", "/v1/projects/%s/gates/inexistant/decision" % pid, {"decision": "approve"})[0], 404)
        self.assertEqual(self.call("POST", "/v1/projects/%s/gates/design/decision" % pid, {"decision": "peut-etre"})[0], 400)

    def test_12_budget_quantities_never_estimated(self):
        pid = self.new()
        self.call("POST", "/v1/projects/%s/messages" % pid, {"text": "Mon budget est de 80 millions FCFA."})
        b = self.call("GET", "/v1/projects/%s/artifacts/budget" % pid)[1]["artifact"]
        self.assertEqual(b["declared"]["value"]["amount"], 80000000)
        self.assertEqual(b["estimate"]["status"], "NOT_EXECUTED")
        q = self.call("GET", "/v1/projects/%s/artifacts/quantities" % pid)[1]["artifact"]
        self.assertEqual(q["status"], "UNKNOWN")
        self.assertEqual(self.call("GET", "/v1/projects/%s/artifacts/inconnu" % pid)[0], 404)

    def test_13_invalid_inputs(self):
        pid = self.new()
        self.assertEqual(self.call("POST", "/v1/projects/%s/messages" % pid, {"text": ""})[0], 400)
        self.assertEqual(self.call("POST", "/v1/projects/%s/rooms" % pid, {"name": "X", "surface_m2": -3, "level": "RDC"})[0], 400)
        self.assertEqual(self.call("POST", "/v1/projects/%s/messages" % pid, {"text": "x" * 5001})[0], 400)


if __name__ == "__main__":
    unittest.main(verbosity=2)

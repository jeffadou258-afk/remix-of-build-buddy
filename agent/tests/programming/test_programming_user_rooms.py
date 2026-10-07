"""Piece fournie par le client => USER_PROVIDED / NOT_VALIDATED / assumption=False.
Sans pieces => comportement V3.4 inchange (DEFAULT_ROOMS, HYPOTHESIS)."""
import importlib.util, json, os, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
spec = importlib.util.spec_from_file_location("ca_prog", os.path.join(ROOT, "engines", "programming", "engine.py"))
prog = importlib.util.module_from_spec(spec); spec.loader.exec_module(prog)

def run(rooms=None):
    d = tempfile.mkdtemp()
    prog.run(d, rooms=rooms)
    return json.load(open(os.path.join(d, "program", "program.json"), encoding="utf-8"))

class T(unittest.TestCase):
    def test_salon_42_user_provided(self):
        r = run([("P01", "Salon", 42, "RDC")])["rooms"][0]
        self.assertEqual(r["source"], "USER_PROVIDED")
        self.assertEqual(r["status"], "USER_PROVIDED")
        self.assertEqual(r["validation"], "NOT_VALIDATED")
        self.assertIs(r["assumption"], False)
        self.assertEqual(r["surface_m2"], 42.0)
    def test_never_hypothesis_for_user_rooms(self):
        p = run([("P01", "Salon", 42, "RDC"), ("P02", "Cuisine", 12, "RDC")])
        self.assertTrue(all(r["status"] != "HYPOTHESIS" for r in p["rooms"]))
        self.assertEqual(p["data_status"], "USER_PROVIDED")
        self.assertEqual(p["validation"], "NOT_VALIDATED")
        self.assertEqual(p["total_surface_m2"], 54.0)
        self.assertEqual(len(p["rooms"]), 2)  # aucune piece par defaut ajoutee
    def test_default_unchanged(self):
        p = run()
        self.assertEqual(len(p["rooms"]), 12)
        self.assertTrue(all(r["status"] == "HYPOTHESIS" for r in p["rooms"]))
        self.assertTrue(all("source" not in r and "assumption" not in r for r in p["rooms"]))
        self.assertEqual(p["data_status"], "HYPOTHESIS")

if __name__ == "__main__":
    unittest.main(verbosity=2)

# -*- coding: utf-8 -*-
"""Tests du module d'extraction. python3 -m unittest discover -s tests/extraction -v"""
import importlib.util, json, os, shutil, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
spec = importlib.util.spec_from_file_location("ca_extraction", os.path.join(ROOT, "engines", "extraction", "engine.py"))
X = importlib.util.module_from_spec(spec); spec.loader.exec_module(X)

PHRASE = "Je veux construire une villa R+1 de 4 chambres sur un terrain de 600 m²."


class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="ca_x_")

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def f(self):
        return X.load(self.d)["fields"]

    def test_phrase_villa_extrait_seulement_le_dit(self):
        X.run(self.d, PHRASE, "M1")
        f = self.f()
        self.assertEqual(f["building_type"]["value"], "villa")
        self.assertEqual(f["levels_label"]["value"], "R+1")
        self.assertEqual(f["levels_count"]["value"], 2)
        self.assertEqual(f["bedrooms"]["value"], 4)
        self.assertEqual(f["plot_area_m2"]["value"], 600.0)
        for k in ("building_type", "levels_label", "bedrooms", "plot_area_m2"):
            self.assertEqual(f[k]["status"], "USER_PROVIDED")
            self.assertEqual(f[k]["source"]["message_id"], "M1")

    def test_non_fourni_reste_unknown(self):
        X.run(self.d, PHRASE, "M1")
        f = self.f()
        for k in ("bathrooms", "plot_dimensions_m", "location_city", "garage", "pool", "occupants", "style"):
            self.assertEqual(f[k]["status"], "UNKNOWN", k)
            self.assertIsNone(f[k]["value"], k)

    def test_user_provided_n_est_pas_valide_techniquement(self):
        X.run(self.d, PHRASE, "M1")
        self.assertTrue(all(v["technically_validated"] is False for v in self.f().values()))
        self.assertNotIn("VERIFIED", json.dumps(X.load(self.d)))

    def test_aucune_piece_ni_surface_inventee(self):
        X.run(self.d, PHRASE, "M1")
        self.assertEqual(X.load(self.d)["rooms"], [])

    def test_budget_sans_estimation(self):
        X.run(self.d, PHRASE, "M1")
        b = X.load(self.d)["budget"]
        self.assertEqual(b["declared"]["status"], "UNKNOWN")
        self.assertEqual(b["estimate"]["status"], "NOT_EXECUTED")
        self.assertIsNone(b["estimate"]["value"])
        X.run(self.d, "Mon budget est de 45 millions FCFA.", "M2")
        b = X.load(self.d)["budget"]
        self.assertEqual(b["declared"]["value"], {"amount": 45000000, "currency": "XOF"})
        self.assertEqual(b["estimate"]["status"], "NOT_EXECUTED")

    def test_quantites_unknown(self):
        X.run(self.d, PHRASE, "M1")
        q = X.load(self.d)["quantities"]
        self.assertEqual(q["status"], "UNKNOWN"); self.assertEqual(q["items"], [])

    def test_pas_de_donnees_villa_de_test(self):
        X.run(self.d, PHRASE, "M1")
        s = json.dumps(X.load(self.d), ensure_ascii=False)
        for marker in ("PRJ_1701484686", "Villa_Test_001", "29753918", "375", "Sejour / Salon"):
            self.assertNotIn(marker, s)

    def test_surface_de_piece_explicite(self):
        X.run(self.d, "Je veux un salon de 42 m² et une cuisine de 14 m2.", "M1")
        r = X.load(self.d)["rooms"]
        self.assertEqual([(x["name"], x["surface_m2"]["value"]) for x in r], [("salon", 42.0), ("cuisine", 14.0)])
        self.assertEqual(r[0]["surface_m2"]["status"], "USER_PROVIDED")

    def test_negation(self):
        X.run(self.d, "Villa à Abidjan, sans garage, avec piscine.", "M1")
        f = self.f()
        self.assertIs(f["garage"]["value"], False); self.assertIs(f["pool"]["value"], True)
        self.assertEqual(f["location_city"]["value"], "Abidjan")

    def test_hypotheses_separees(self):
        X.run(self.d, PHRASE, "M1")
        X.add_hypothesis(self.d, "bathrooms", 3, "proposition agent", "agent")
        d = X.load(self.d)
        self.assertEqual(d["fields"]["bathrooms"]["status"], "UNKNOWN")
        self.assertEqual(d["hypotheses"][0]["status"], "HYPOTHESIS")

    def test_formulaire_corrige_et_garde_historique(self):
        X.run(self.d, PHRASE, "M1")
        X.edit(self.d, {"plot_area_m2": 650, "location_city": "Bingerville"}, "u1")
        d = X.load(self.d)
        self.assertEqual(d["fields"]["plot_area_m2"]["value"], 650)
        self.assertEqual(d["fields"]["plot_area_m2"]["source"]["origin"], "formulaire")
        self.assertEqual(d["history"][0]["previous"]["value"], 600.0)
        X.edit(self.d, {"plot_area_m2": None})
        self.assertEqual(X.load(self.d)["fields"]["plot_area_m2"]["status"], "UNKNOWN")

    def test_champ_inconnu_refuse(self):
        with self.assertRaises(ValueError):
            X.edit(self.d, {"piscine_olympique": True})

    def test_memoire_tracee(self):
        X.run(self.d, PHRASE, "M1")
        lines = open(os.path.join(self.d, "memory", "constraints.jsonl"), encoding="utf-8").read().splitlines()
        self.assertTrue(all(json.loads(l)["status"] == "USER_PROVIDED" for l in lines))
        self.assertEqual(len(lines), 5)


if __name__ == "__main__":
    unittest.main()

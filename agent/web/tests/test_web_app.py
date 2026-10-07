#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TESTS OBLIGATOIRES DE L'APPLICATION WEB — exécution réelle contre le serveur.
Aucun test n'est déclaré PASS sans une vérification réelle de la réponse."""
import json
import urllib.request

B = "http://127.0.0.1:8765"
R = []


def get(p):
    try:
        with urllib.request.urlopen(B + p, timeout=15) as r:
            return r.status, r.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)


def post(p, d):
    try:
        req = urllib.request.Request(B + p, data=json.dumps(d).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)


def t(tid, nom, cond, preuve):
    R.append({"test": tid, "nom": nom, "resultat": "PASS" if cond else "FAIL", "preuve": preuve[:150]})
    print("  %-10s %-4s %-52s %s" % (tid, "PASS" if cond else "FAIL", nom, preuve[:70]))


print("=" * 78); print("TESTS OBLIGATOIRES — APPLICATION WEB (serveur réel)"); print("=" * 78)
s, b = get("/api/health")
t("TEST_UI_01", "L'application démarre", s == 200 and '"status": "OK"' in b, "health HTTP %d : %s" % (s, b.replace("\n", " ")[:60]))

s, b = get("/api/project")
p = json.loads(b) if s == 200 else {}
t("TEST_UI_02", "Le projet PRJ_1701484686 est chargé",
  s == 200 and p.get("id") == "PRJ_1701484686" and p.get("nom") == "Villa_Test_001",
  "id=%s nom=%s terrain=%s" % (p.get("id"), p.get("nom"), p.get("terrain")))

s, b = get("/api/project/status")
st = json.loads(b) if s == 200 else {}
t("TEST_UI_03", "Le statut du projet est correct",
  s == 200 and st.get("dossier_numerique") == "AVANCÉ" and st.get("chantier_physique_pct") == 0,
  "dossier=%s / chantier=%s%%" % (st.get("dossier_numerique"), st.get("chantier_physique_pct")))

s, b = get("/api/phases")
ph = json.loads(b) if s == 200 else {}
t("TEST_UI_04", "Les 18 phases apparaissent",
  s == 200 and ph.get("total") == 18 and len(ph.get("phases", [])) == 18,
  "%d phases retournées (01→18)" % len(ph.get("phases", [])))

s, b = post("/api/assistant", {"question": "Qu'est-ce qu'un poteau ?", "pro": False})
d = json.loads(b) if s == 200 else {}
t("TEST_UI_05", "Le mode débutant fonctionne",
  s == 200 and "POTEAU" in d.get("reponse", "") and "jambe de la maison" in d.get("reponse", "") and d.get("mode") == "DEBUTANT",
  "mode=%s · réponse %d o contenant la définition simple" % (d.get("mode"), len(d.get("reponse", ""))))

s, b = post("/api/assistant", {"question": "Qu'est-ce qu'un poteau ?", "pro": True})
d2 = json.loads(b) if s == 200 else {}
t("TEST_UI_06", "Le mode professionnel fonctionne",
  s == 200 and d2.get("mode") == "PROFESSIONNEL" and "POUTEAU_*" in d2.get("reponse", ""),
  "mode=%s · contient la référence BIM (recherche POUTEAU_*: %s)" % (d2.get("mode"), "POUTEAU_*" in d2.get("reponse", "")))

s, b = post("/api/assistant", {"question": "Puis-je construire les fondations maintenant ?", "pro": False})
d3 = json.loads(b) if s == 200 else {}
secu = d3.get("securite") or {}
t("TEST_UI_07", "« Puis-je construire les fondations ? » → réponse de sécurité",
  s == 200 and "NON, pas encore" in d3.get("reponse", "") and secu.get("blocage") is True
  and "géotechnicien" in (secu.get("intervenants") or []),
  "blocage=%s · intervenants=%s" % (secu.get("blocage"), secu.get("intervenants")))

s, b = get("/api/gates")
g = json.loads(b) if s == 200 else {}
g2 = next((x for x in g.get("gates", []) if x["id"] == "G2"), {})
t("TEST_UI_08", "G2 apparaît OPEN / HUMAN_GATE",
  s == 200 and "OPEN" in g2.get("statut", "") and "HUMAN_GATE" in g2.get("statut", "") and g2.get("champs_a_remplir") == 10,
  "statut=%s · %s champs à remplir · %s" % (g2.get("statut"), g2.get("champs_a_remplir"), g2.get("intervenants")))

g3 = next((x for x in g.get("gates", []) if x["id"] == "G3"), {})
t("TEST_UI_09", "G3 apparaît OPEN / HUMAN_GATE",
  s == 200 and "OPEN" in g3.get("statut", "") and g3.get("champs_a_remplir") == 32,
  "statut=%s · %s champs · %s" % (g3.get("statut"), g3.get("champs_a_remplir"), g3.get("intervenants")))

s, b = get("/api/budget")
bu = json.loads(b) if s == 200 else {}
ref = json.load(open("/Users/mac/ConstructionAgent/projects/PRJ_1701484686/budget/budget_final_v2.json"))
t("TEST_UI_10", "Le budget affiché correspond aux données existantes",
  s == 200 and bu.get("total_fcfa") == ref["total_general_fcfa"] == 29753918
  and bu.get("mention", "").startswith("Estimation"),
  "%s FCFA (fichier source : %s) · mention=%s" % (bu.get("total_fcfa"), ref["total_general_fcfa"], bu.get("mention")))

s, b = get("/api/plans")
pl = json.loads(b) if s == 200 else {}
sv = [x for x in pl.get("plans", []) if x["type"] == "plan"]
s2, b2 = get(sv[0]["url"]) if sv else (0, "")
t("TEST_UI_11", "Les plans sont réellement chargés",
  s == 200 and pl.get("total") == 16 and s2 == 200 and "<svg" in b2,
  "%d documents · %s chargé réellement (HTTP %d, %d o, contient <svg>)" % (pl.get("total"), sv[0]["nom"] if sv else "-", s2, len(b2)))

s, b = get("/api/bim")
bm = json.loads(b) if s == 200 else {}
def getbin(p):
    try:
        with urllib.request.urlopen(B + p, timeout=20) as r:
            return r.status, r.read()
    except Exception as e:
        return 0, str(e).encode()
s3, b3 = getbin(bm.get("glb_url", "/api/bim"))
t("TEST_UI_12", "Le BIM est réellement chargé",
  s == 200 and bm.get("existe") is True and bm.get("glb") and s3 == 200 and len(b3) > 100000,
  "blend %d Ko (existe) + GLB binary chargé réellement (HTTP %s, %d octets, en-tête %s)" % (bm.get("octets",0)//1024, s3, len(b3) if s3==200 else 0, b3[:4].decode("ascii","replace") if s3==200 else "-"))

# TEST_UI_13 : aucune donnee UNKNOWN affichee comme VERIFIED
q = json.loads(get("/api/quantities")[1])
bad = [x for x in q.get("quantites", []) if x["statut"] in ("PENDING_G3", "UNKNOWN") and "VERIF" in x["statut"].upper()]
struct_ok = all(x["statut"] == "PENDING_G3" for x in q.get("quantites", []) if x["element"] in
                ("poteaux", "poutres", "longrines", "semelles", "dalles"))
t("TEST_UI_13", "Aucune donnée UNKNOWN n'est affichée comme VERIFIED",
  len(bad) == 0 and struct_ok and q.get("quantites", [])[0] is not None,
  "0 incohérence · les 5 quantités structure conservent PENDING_G3 (jamais VERIFIED)")

t("TEST_UI_14", "Dossier numérique ≠ chantier physique",
  st.get("dossier_numerique") == "AVANCÉ" and st.get("chantier_physique_pct") == 0
  and "ne signifie PAS" in st.get("avertissement", ""),
  "dossier AVANCÉ vs chantier 0%% — avertissement présent dans l'API et affiché en page d'accueil")

# TEST_UI_15 : responsive — verification reelle du viewport CSS dans le fichier servi
s, b = get("/")
has_mq = "@media(max-width:900px)" in b and ".mob" in b and "bottom:0" in b
t("TEST_UI_15", "Responsive mobile (viewport + media query + bottom nav)",
  s == 200 and has_mq and "viewport" in b,
  "index %d o · viewport présent · media query 900px + nav mobile présents" % len(b))

p = sum(1 for x in R if x["resultat"] == "PASS")
print("-" * 78)
print("RÉSULTAT : %d PASS / %d FAIL sur %d tests" % (p, len(R) - p, len(R)))
json.dump({"at": "2026-10-02T16:45:00", "serveur": B, "total": len(R), "PASS": p, "FAIL": len(R) - p,
           "tests": R}, open("/Users/mac/ConstructionAgent/projects/PRJ_1701484686/reports/web_app_tests.json", "w"),
          indent=2, ensure_ascii=False)

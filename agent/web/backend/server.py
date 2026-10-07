#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CONSTRUCTION AGENT — WEB BACKEND (v1.0.0)

Couche d'interface au-dessus des moteurs existants. NE MODIFIE RIEN.
Importe CONSTRUCTION_GUIDE_ENGINE (engines/construction_guide/engine.py)
comme unique moteur de reponse : aucun deuxieme moteur parallele.

Aucune dependance externe : http.server + json (stdlib).
Lancement :  python3 web/backend/server.py [--port 8765]
"""
import json
import threading
import os
import sys
import io
import contextlib
import argparse
import datetime
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, unquote, parse_qs

ROOT = "/Users/mac/ConstructionAgent"
PROJ = os.path.join(ROOT, "projects", "PRJ_1701484686")
sys.path.insert(0, os.path.join(ROOT, "engines", "construction_guide"))
import engine as CGE  # noqa: E402  — le moteur EXISTANT

# --- M1/M2 : PROJECT CONTEXT + NEXT STEP (module dedie, lit les fichiers reels) ---
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import assistant_core as ACORE  # noqa: E402  — lecture seule, aucune donnee inventee

_ACORE_CTX = None


def _assistant_ask(q, pro=False):
    """Reponse structuree (source, donnees, actions). Delegue au Guide Engine
    existant pour les questions pedagogiques — AUCUN moteur parallele."""
    ctx = _assistant_ctx()
    r = ACORE.answer(ctx, q, pro)
    if r.get("reponse") == "__DELEGUE_AU_GUIDE__":
        g = api_assistant(q, pro)
        r["reponse"] = g.get("reponse", "")
        r["securite"] = g.get("securite")
        r["source"] = "construction_guide_engine.ask()"
        r["statut"] = "PARTIAL"
    return r


def _assistant_ctx():
    """Contexte projet construit UNE fois depuis les fichiers reels."""
    global _ACORE_CTX
    if _ACORE_CTX is None:
        _ACORE_CTX = ACORE.ProjectContext(PROJ)
    return _ACORE_CTX

VERSION = "1.0.0"
STATUTS = ["CONNU", "CALCULE", "HYPOTHESE", "INCONNU", "VERIFIE", "HUMAN_GATE", "PENDING_VALIDATION"]


# --------------------------------------------------------------------------
def _j(p):
    f = os.path.join(PROJ, p)
    if os.path.exists(f):
        try:
            return json.load(open(f))
        except Exception:
            return None
    return None


def _dossier(p):
    d = os.path.join(PROJ, p)
    return sorted(os.listdir(d)) if os.path.isdir(d) else []


def _sha(p):
    f = os.path.join(PROJ, p)
    return hashlib.sha256(open(f, "rb").read()).hexdigest() if os.path.exists(f) else None


def _capture(fn, *a, **k):
    """Execute le moteur et capture sa sortie TEXTE REELLE (source de verite)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            fn(*a, **k)
        except Exception as e:
            print("ERREUR moteur : %s" % e)
    return buf.getvalue()


def guide(pro=False):
    g = CGE.ConstructionGuide(PROJ)
    g.pro = pro
    return g


# -------------------------------------------------------------------------- API
def api_project():
    site = _j("site/site.json") or {}
    st = _j("reports/CONTINUATION_STATE.json") or {}
    return {"id": "PRJ_1701484686", "nom": "Villa_Test_001", "localisation": "Abidjan, Côte d'Ivoire",
            "type": "Villa R+1", "terrain": "15,00 × 25,00 m = 375 m²", "surface_interieure": "150 m²",
            "chambres": 4, "occupants": 6, "variante": "A (validée)",
            "source": "site/site.json + program/ (STATUT : CONNU)",
            "chantier_physique_pct": 0,
            "avertissement": "Le dossier numerique avance ne signifie PAS que la maison est construite.",
            "programme": {"RDC": "81 m² de pièces + 24 m² circulation = 105 m²",
                          "etage": "69 m² de pièces + 16 m² circulation",
                          "exterieurs": "garage 25 m² · terrasse 24 m² · patio 12 m²"}}


def api_status():
    txt = _capture(guide().status)
    return {"statut": "OK", "source": "construction_guide_engine.status()",
            "dossier_numerique": "AVANCÉ", "chantier_physique_pct": 0,
            "avertissement": "Le dossier numérique avancé ne signifie PAS que la maison est construite.",
            "texte_brut": txt}


def api_phases():
    return {"total": 18, "phases": [
        {"id": n, "nom": nom, "objectif": obj, "explication": sim, "travaux": fait, "professionnels": qui,
         "human_gate": gate, "source": "construction_guide_engine.phases()"}
        for (n, nom, obj, sim, fait, qui, manque, gate) in CGE.phases()]}


def api_phase(pid):
    g = guide()
    txt = _capture(g.phase, pid)
    ph = [p for p in CGE.phases() if p[0] == str(pid).zfill(2)]
    if not ph:
        return {"erreur": "phase inconnue", "statut": "UNKNOWN"}
    n, nom, obj, sim, fait, qui, manque, gate = ph[0]
    return {"id": n, "nom": nom, "objectif": obj, "human_gate": gate,
            "source": "construction_guide_engine.phase(%s)" % n, "texte_brut": txt}


def api_budget():
    b = _j("budget/budget_final_v2.json")
    if not b:
        return {"statut": "UNKNOWN", "erreur": "budget indisponible"}
    return {"mention": "Estimation de travail — NON devis définitif",
            "total_fcfa": b["total_general_fcfa"],
            "independant_g3_fcfa": b["total_perimetre_independant_G3_fcfa"],
            "dependant_g3_fcfa": b["total_perimetre_dependant_G3_fcfa"],
            "ancien_budget_fcfa": b.get("ancien_budget_reference_fcfa"),
            "comparabilite": "NON comparable à périmètre identique (second œuvre et lots techniques non requantifiés)",
            "lignes": b["lignes"], "source": "budget/budget_final_v2.json",
            "sha256": _sha("budget/budget_final_v2.json")}


def api_quantities():
    m = _j("metre/metre_final_v2.json")
    if not m:
        return {"statut": "UNKNOWN"}
    q = []
    for x in m["quantites_independantes_de_G3"] + m["quantites_dependantes_de_G3"]:
        q.append({"element": x["id"], "quantite": x["quantite"], "unite": x["unite"],
                  "statut": x["statut"], "methode": x["methode"], "objets_sources": x["objets_sources"]})
    return {"quantites": q, "source": "metre/metre_final_v2.json", "sha256": _sha("metre/metre_final_v2.json")}


def api_documents():
    docs = []
    d = os.path.join(PROJ, "docs")
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            p = os.path.join("docs", f)
            docs.append({"nom": f, "chemin": p, "octets": os.path.getsize(os.path.join(PROJ, p)),
                         "statut": "EXISTE", "source": "docs/"})
    p7 = _j("reports/bloc7_plans_coupes_facades.json") or {"documents": []}
    return {"documents": docs, "plans": [{"nom": x["chemin"], "statut": x["statut"]} for x in p7["documents"]]}


def api_plans():
    out = []
    for d, typ in (("plans", "plan"), ("coupes", "coupe"), ("facades", "facade")):
        for f in _dossier(d):
            if f.endswith(".svg"):
                out.append({"nom": f, "type": typ, "url": "/files/%s/%s" % (d, f),
                            "octets": os.path.getsize(os.path.join(PROJ, d, f))})
    return {"total": len(out), "plans": out, "source": "BIM_FINAL_A3.blend (projections réelles)"}


def api_renders():
    out = [{"nom": f, "url": "/files/renders/%s" % f, "octets": os.path.getsize(os.path.join(PROJ, "renders", f))}
           for f in _dossier("renders") if f.endswith(".png")]
    return {"total": len(out), "rendus": out, "source": "3D/BIM_RENDER_A3.blend (BLENDER_EEVEE)",
            "avertissement": "MATERIALS_HYPOTHESIS · photoréalisme de présentation NON validé"}


def api_bim():
    p = os.path.join(PROJ, "3D", "BIM_FINAL_A3.blend")
    g = os.path.join(PROJ, "3D", "BIM_FINAL_A3.glb")
    d = {"fichier": "3D/BIM_FINAL_A3.blend", "existe": os.path.exists(p),
         "octets": os.path.getsize(p) if os.path.exists(p) else 0, "sha256": _sha("3D/BIM_FINAL_A3.blend"),
         "objets": 326, "source": "3D/BIM_FINAL_A3.blend"}
    if os.path.exists(g):
        d.update({"glb": "3D/BIM_FINAL_A3.glb", "glb_url": "/files/3D/BIM_FINAL_A3.glb",
                  "glb_octets": os.path.getsize(g), "glb_sha256": _sha("3D/BIM_FINAL_A3.glb")})
    else:
        d.update({"glb": None, "statut": "GLB NON EXPORTÉ — le BLEND est intact",
                  "note": "Conversion BLEND→GLB requise pour l'affichage Web."})
    return d


def api_gates():
    st = _j("reports/CONTINUATION_STATE.json") or {}
    g2 = _j("reports/G2_FICHE_COLLECTE.json") or {}
    g3 = _j("reports/G3_FICHE_COLLECTE.json") or {}
    return {"gates": [
        {"id": "G1", "objet": "Choix architectural A/B", "statut": "CLOSED", "detail": "OPTION A retenue par l'utilisateur",
         "intervenants": ["utilisateur"], "pourquoi": "Décision architecturale — tranchée"},
        {"id": "G2", "objet": "Exutoire des eaux usées", "statut": "OPEN / HUMAN_GATE",
         "detail": "9 champs de site/site.json sont UNKNOWN : aucun réseau public, fosse, regard ou pente ne peut être déterminé",
         "intervenants": ["topographe", "professionnel assainissement"],
         "pourquoi": "Sans exutoire connu, le tracé EU/EV ne peut pas être établi. L'inventer serait une faute.",
         "champs_a_remplir": len(g2.get("champs", [])), "fiche": "reports/G2_FICHE_COLLECTE.md"},
        {"id": "G3", "objet": "Validation géotechnique et dimensionnement structure", "statut": "OPEN / HUMAN_GATE",
         "detail": "7 PROPOSED / 2 HYPOTHESIS / 7 UNKNOWN. Portance 0,15 MPa = HYPOTHÈSE. 2 anomalies géométriques à arbitrer.",
         "intervenants": ["géotechnicien", "ingénieur structure"],
         "pourquoi": "Une fondation ne peut pas être coulée sur une portance supposée. Un modèle conceptuel n'autorise pas à construire.",
         "champs_a_remplir": len(g3.get("champs", [])), "fiche": "reports/G3_FICHE_COLLECTE.md"}],
        "legende_statuts": STATUTS, "source": "reports/G2_G3_FINAL_STATUS.json + fiches de collecte"}


def api_glossary(term):
    k = unquote(term).lower().strip()
    if k in CGE.GLOSSAIRE:
        d, p = CGE.GLOSSAIRE[k]
        return {"terme": k, "definition": d, "pourquoi": p, "source": "construction_guide_engine.GLOSSAIRE"}
    return {"terme": k, "statut": "UNKNOWN", "termes": sorted(CGE.GLOSSAIRE.keys())}


def api_assistant(q, pro=False):
    """Route la question vers le moteur EXISTANT — aucun moteur parallele."""
    g = guide(pro)
    txt = _capture(g.ask, q)
    # detection du statut de securite (regle §13)
    secu = None
    if "NON, pas encore" in txt:
        secu = {"blocage": True, "raison": "HYPOTHÈSE non vérifiée + G3 ouvert",
                "intervenants": ["géotechnicien", "ingénieur structure"],
                "validation_necessaire": "G3 — reports/G3_FICHE_COLLECTE.md"}
    return {"question": q, "mode": "PROFESSIONNEL" if pro else "DEBUTANT", "reponse": txt,
            "source": "construction_guide_engine.ask()", "securite": secu}


def api_search(q):
    ql = q.lower()
    out = []
    for k, (d, p) in CGE.GLOSSAIRE.items():
        if ql in k or k in ql:
            out.append({"type": "glossaire", "titre": k, "detail": d[:110]})
    for (n, nom, obj, sim, fait, qui, manque, gate) in CGE.phases():
        if ql in nom.lower() or ql in obj.lower() or ql in sim.lower():
            out.append({"type": "phase", "titre": "%s — %s" % (n, nom), "detail": obj})
    m = _j("metre/metre_final_v2.json") or {}
    for x in m.get("quantites_independantes_de_G3", []) + m.get("quantites_dependantes_de_G3", []):
        if ql in x["id"]:
            out.append({"type": "métré", "titre": x["id"], "detail": "%s %s — %s" % (x["quantite"], x["unite"], x["statut"])})
    for d in ("plans", "docs"):
        for f in _dossier(d):
            if ql.replace("é", "e").replace("è", "e") in f.lower():
                out.append({"type": d[:-1], "titre": f, "detail": "%s/%s" % (d, f)})
    return {"requete": q, "resultats": out[:40], "total": len(out)}


def api_bim_elements():
    """Metadonnees REELLES de chaque objet BIM (extraites du .blend, jamais inventees)."""
    d = _j("3D/bim_elements.json")
    if not d:
        return {"statut": "UNKNOWN", "erreur": "3D/bim_elements.json absent",
                "note": "Extraire les metadonnees depuis BIM_FINAL_A3.blend"}
    q = _qs.get("type") if False else None
    from urllib.parse import parse_qs, urlparse as _up
    return d


def api_bim_element(eid):
    """Fiche d'un element BIM par son identifiant reel."""
    d = _j("3D/bim_elements.json") or {}
    for e in d.get("elements", []):
        if e["id"] == eid:
            return dict(e, source_fichier="3D/BIM_FINAL_A3.blend",
                        correspondance_2D=("plans/P02_plan_RDC.svg" if e["niveau"] in ("RDC", "Fondation")
                                           else "plans/P03_plan_etage.svg" if e["niveau"] == "Etage"
                                           else "plans/P01_implantation.svg" if e["niveau"] == "Terrain" else None),
                        source_documentaire="docs/D02_synthese_BIM.md")
    return {"erreur": "element inconnu", "statut": "UNKNOWN", "id": eid}

# --- Verrou d acces a l assistant -------------------------------------------
# _capture() redirige sys.stdout, qui est GLOBAL. Le serveur est un
# ThreadingHTTPServer : deux requetes concurrentes corrompent la capture
# -> "Empty reply from server". On serialise l acces (cout : ~0,1 s/requete).
_ASSIST_LOCK = threading.Lock()


def _assistant_serialise(q, pro=False):
    # DIAGNOSTIC : le handler marchait en appel direct mais renvoyait
    # "Empty reply from server" via HTTP. On rend l exception VISIBLE
    # au lieu de la laisser fermer la connexion.
    try:
        with _ASSIST_LOCK:
            return api_assistant(q, pro)
    except Exception:
        import traceback
        return {"erreur": "exception dans api_assistant",
                "type": type(sys.exc_info()[1]).__name__ if False else "voir traceback",
                "traceback": traceback.format_exc()[-1800:]}


ROUTES = {
    "/api/project": lambda q: api_project(), "/api/project/status": lambda q: api_status(),
    "/api/phases": lambda q: api_phases(), "/api/budget": lambda q: api_budget(),
    "/api/quantities": lambda q: api_quantities(), "/api/documents": lambda q: api_documents(),
    "/api/plans": lambda q: api_plans(), "/api/renders": lambda q: api_renders(),
    "/api/bim": lambda q: api_bim(), "/api/gates": lambda q: api_gates(),
  # CABLE : api_assistant etait definie mais non enregistree -> 404 "route inconnue".
  # ROUTES recoit u.query = CHAINE brute (pas un dict) -> parse_qs obligatoire.
  # M1/M2 — contexte projet et prochaine etape, derives des fichiers reels.
  "/api/assistant/context": lambda q: _assistant_ctx().context(),
  # Reponse structuree + actions d'interface (§24 : assistant ACTIONNABLE).
  "/api/assistant/ask": lambda q: _assistant_serialise(
      parse_qs(q).get("q", [""])[0], parse_qs(q).get("pro", ["0"])[0] in ("1", "true", "True")),

  "/api/assistant/next-step": lambda q: ACORE.next_step(_assistant_ctx()),
  "/api/assistant": lambda q: _assistant_serialise(parse_qs(q).get("q", [""])[0],
      parse_qs(q).get("pro", ["0"])[0] in ("1", "true", "True")),
    "/api/bim/elements": lambda q: api_bim_elements(),
    "/api/health": lambda q: {"status": "OK", "version": VERSION, "moteur": "construction_guide_engine",
                              "at": datetime.datetime.now().isoformat(timespec="seconds")},
}
MIME = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "application/javascript; charset=utf-8",
        ".svg": "image/svg+xml", ".png": "image/png", ".json": "application/json; charset=utf-8",
        ".glb": "model/gltf-binary", ".md": "text/markdown; charset=utf-8"}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False, indent=1).encode("utf-8"), MIME[".json"])

    def _file(self, rel):
        """Sert un fichier du projet avec CONFINEMENT STRICT (correctif P0 path traversal).

        Resolution par realpath() puis verification par commonpath() : contrairement a
        un simple startswith(), cette logique resiste a '../', aux chemins absolus,
        aux encodages %2e%2e et aux liens symboliques pointant hors du projet
        (realpath resout les liens avant la comparaison)."""
        root = os.path.realpath(PROJ)
        raw_rel = rel.replace("\\", "/")
        # 1) REJET EXPLICITE des tentatives de remontee, AVANT toute resolution.
        #    Couvre '..', les segments vides doubles, et les encodages %2e / %2f
        #    qui ne sont pas decodes par urlparse mais qui revelent une intention
        #    de traversee. Defense en profondeur : repond 403 au lieu de 404.
        low = raw_rel.lower()
        # aucun fichier legitime du projet ne contient de caractere '%' : tout
        # pourcentage-encodage (simple ou double) est donc une intention de traversee.
        suspect = (low.startswith("/") or ".." in low or "%" in low
                   or low.startswith("~") or (len(low) > 1 and low[1] == ":"))
        if suspect:
            return self._json({"erreur": "acces refuse", "statut": "REJECTED",
                               "demande": rel, "motif": "chemin non confine"}, 403)
        # 2) CONFINEMENT REEL : realpath() resout les liens symboliques, puis
        #    commonpath() verifie l'appartenance au projet (pas un simple startswith).
        f = os.path.realpath(os.path.join(root, raw_rel))
        try:
            allowed = os.path.commonpath([root, f]) == root
        except ValueError:
            allowed = False
        if not allowed:
            return self._json({"erreur": "acces refuse", "statut": "REJECTED",
                               "demande": rel, "confine_a": os.path.basename(root)}, 403)
        if not os.path.exists(f) or not os.path.isfile(f):
            return self._json({"erreur": "fichier absent", "statut": "UNKNOWN", "demande": rel}, 404)
        ext = os.path.splitext(f)[1].lower()
        self._send(200, open(f, "rb").read(), MIME.get(ext, "application/octet-stream"))

    def do_HEAD(self):
        """HEAD : renvoie les en-tetes sans corps (necessaire pour curl -I et les navigateurs)."""
        u = urlparse(self.path)
        p = u.path
        ok = 200
        if p in ROUTES or p.startswith("/api/phases/") or p.startswith("/api/glossary/") or p.startswith("/api/search"):
            ctype = MIME[".json"]
        elif p.startswith("/files/"):
            f = os.path.join(PROJ, p[len("/files/"):])
            if os.path.exists(f) and os.path.isfile(f):
                ctype = MIME.get(os.path.splitext(f)[1].lower(), "application/octet-stream")
            else:
                ok, ctype = 404, MIME[".json"]
        elif p in ("/", "/index.html") or p.startswith("/3d") or p.startswith("/bim"):
            ctype = MIME[".html"]
        else:
            ok, ctype = 404, MIME[".json"]
        self.send_response(ok)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_GET(self):
        u = urlparse(self.path)
        p = u.path
        if p in ROUTES:
            return self._json(ROUTES[p](u.query))
        if p.startswith("/api/bim/elements/"):
            r = api_bim_element(unquote(p.split("/api/bim/elements/")[-1]))
            return self._json(r, 404 if r.get("erreur") == "element inconnu" else 200)
        if p.startswith("/api/phases/"):
            return self._json(api_phase(p.split("/")[-1]))
        if p.startswith("/api/glossary/"):
            return self._json(api_glossary(p.split("/")[-1]))
        if p.startswith("/api/search"):
            from urllib.parse import parse_qs
            return self._json(api_search(parse_qs(u.query).get("q", [""])[0]))
        if p.startswith("/files/"):
            return self._file(p[len("/files/"):])
        if p in ("/", "/index.html", "/3d", "/bim", "/projet", "/etapes", "/plans",
                 "/budget", "/documents", "/assistant", "/validations", "/gates"):
            idx = os.path.join(ROOT, "web", "frontend", "index.html")
            return self._send(200, open(idx, "rb").read(), MIME[".html"]) if os.path.exists(idx) else self._send(200, _FRONT.encode("utf-8"), MIME[".html"])
        return self._json({"erreur": "route inconnue", "statut": "UNKNOWN", "path": p}, 404)

    def do_POST(self):
        u = urlparse(self.path)
        n = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            body = {}
        if u.path == "/api/assistant":
            return self._json(api_assistant(body.get("question", ""), bool(body.get("pro"))))
        if u.path == "/api/assistant/ask":
            return self._json(_assistant_ask(body.get("question", ""), bool(body.get("pro"))))
        if u.path in ("/api/assistant/context", "/api/assistant/next-step"):
            return self._json(ROUTES[u.path](u.query))
        return self._json({"erreur": "route inconnue", "statut": "UNKNOWN"}, 404)


# le frontend est servi depuis web/frontend/ ; _FRONT est le repli embarque
_FRONT = "<html><body><h1>Construction Agent</h1><p>Frontend non trouvé dans web/frontend/.</p></body></html>"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args()
    srv = ThreadingHTTPServer((a.host, a.port), H)
    url = "http://127.0.0.1:%d" % a.port
    lan = ""
    try:
        import socket
        s_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s_.connect(("8.8.8.8", 80))
        lan = "http://%s:%d" % (s_.getsockname()[0], a.port); s_.close()
    except Exception:
        pass
    print("=" * 66)
    print("CONSTRUCTION AGENT — WEB APP v%s" % VERSION)
    print("=" * 66)
    print("URL RÉELLE (locale)  : %s" % url)
    if lan:
        print("URL RÉSEAU (LAN)     : %s" % lan)
    print("Écoute               : %s:%d" % (a.host, a.port))
    print("API health : %s/api/health" % url)
    print("Projet     : %s" % PROJ)
    print("Moteur     : engines/construction_guide/engine.py (importé, non dupliqué)")
    print("Ctrl+C pour arrêter.")
    sys.stdout.flush()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\narrêt.")
        srv.shutdown()


if __name__ == "__main__":
    main()

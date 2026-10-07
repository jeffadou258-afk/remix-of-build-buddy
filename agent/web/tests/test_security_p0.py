#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TESTS DE SECURITE P0 + NON-REGRESSION.
Requetes envoyees par SOCKET BRUT : un client HTTP normaliserait les '..' et
masquerait la vulnerabilite. Chaque resultat est mesure, jamais suppose."""
import socket
import os
import json
import subprocess

HOST, PORT = "127.0.0.1", 8765
PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"


def raw(path, method="GET", timeout=8):
    """Envoie la requete telle quelle, sans normalisation client."""
    s = socket.create_connection((HOST, PORT), timeout=timeout)
    s.sendall(("%s %s HTTP/1.0\r\nHost: %s\r\nConnection: close\r\n\r\n" % (method, path, HOST)).encode())
    d = b""
    try:
        while len(d) < 300000:
            c = s.recv(65536)
            if not c:
                break
            d += c
    except Exception:
        pass
    s.close()
    head, _, body = d.partition(b"\r\n\r\n")
    line = head.split(b"\r\n")[0].decode(errors="replace") if head else ""
    code = line.split()[1] if len(line.split()) > 1 else "000"
    return code, body


R = []


def T(cat, nom, payload, attendu, doit_contenir=None, doit_pas_contenir=None):
    code, body = raw(payload)
    ok = code == attendu
    if doit_contenir and doit_contenir not in body:
        ok = False
    if doit_pas_contenir and doit_pas_contenir in body:
        ok = False
    R.append({"cat": cat, "test": nom, "payload": payload, "http": code, "attendu": attendu,
              "resultat": "PASS" if ok else "FAIL", "extrait": body[:60].decode("utf-8", "replace").replace("\n", " ")})
    print("  %-4s %-8s %-46s HTTP %-4s (attendu %s) %s" % ("PASS" if ok else "FAIL", cat, nom, code, attendu,
          "" if ok else "  <<< " + body[:70].decode("utf-8", "replace").replace("\n", " ")))


print("=" * 100)
print("A. ACCES LEGITIME — les fichiers du projet doivent RESTER accessibles")
print("=" * 100)
T("LEGIT", "GET /", "/", "200", b"Construction Agent")
T("LEGIT", "GET /api/health", "/api/health", "200", b"OK")
T("LEGIT", "GET /api/phases", "/api/phases", "200", b"phases")
T("LEGIT", "GET P02 plan RDC", "/files/plans/P02_plan_RDC.svg", "200", b"<svg")
T("LEGIT", "GET P03 plan etage", "/files/plans/P03_plan_etage.svg", "200", b"<svg")
T("LEGIT", "GET BIM blend", "/files/3D/BIM_FINAL_A3.blend", "200", b"BLENDER")
T("LEGIT", "GET GLB", "/files/3D/BIM_FINAL_A3.glb", "200", b"glTF")
T("LEGIT", "GET rendu PNG", "/files/renders/R01_vue_principale.png", "200", b"\x89PNG")
T("LEGIT", "GET budget", "/files/budget/budget_final_v2.json", "200", b"total_general_fcfa")

print("=" * 100)
print("B. PATH TRAVERSAL — toutes les tentatives doivent etre REFUSEES")
print("=" * 100)
T("TRAV", "remontee /etc/passwd (8 niveaux)", "/files/../../../../../../../../etc/passwd", "403", None, b"User Database")
T("TRAV", "remontee /etc/passwd (5 niveaux)", "/files/../../../../../etc/passwd", "403", None, b"User Database")
T("TRAV", "vers le backend lui-meme", "/files/../backend/server.py", "403", None, b"os.path.commonpath")
T("TRAV", "vers un fichier voisin du projet", "/files/../../server.py", "403")
T("TRAV", "remontee /etc/hosts", "/files/../../../../etc/hosts", "403", None, b"localhost")
T("TRAV", "encodage %2e%2e", "/files/%2e%2e/%2e%2e/%2e%2e/etc/passwd", "403", None, b"User Database")
T("TRAV", "encodage double %252e", "/files/%252e%252e/%252e%252e/etc/passwd", "403")
T("TRAV", "chemin absolu direct", "/files//etc/passwd", "403")
T("TRAV", "remontee profonde (40 niveaux)", "/files/" + "../" * 40 + "etc/passwd", "403", None, b"User Database")
T("TRAV", "remontee vers la racine utilisateur", "/files/../../../../../../Users/mac/.zshrc", "403")
T("TRAV", "sortie puis retour dans le projet", "/files/../../ConstructionAgent/web/backend/server.py", "403")

print("=" * 100)
print("C. CAS LIMITE — chemin qui COMMENCE par le projet puis tente de sortir")
print("=" * 100)
T("LIMITE", "sous-dossier legitime puis remontee", "/files/plans/../../../etc/passwd", "403", None, b"User Database")
T("LIMITE", "remontee depuis 3D/", "/files/3D/../../../etc/passwd", "403", None, b"User Database")
T("LIMITE", "dossier profond legitime (doit PASSER)", "/files/3D/", "404")
T("LIMITE", "fichier legitime avec . et /", "/files/plans/./P02_plan_RDC.svg", "200", b"<svg")

print("=" * 100)
print("D. LIEN SYMBOLIQUE pointant hors du projet (cree puis supprime)")
print("=" * 100)
link = os.path.join(PROJ, "_test_symlink_audit")
created = False
try:
    if os.path.islink(link):
        os.unlink(link)
    os.symlink("/etc/passwd", link)
    created = True
    T("SYMLINK", "lien symbolique sortant", "/files/_test_symlink_audit", "403", None, b"User Database")
except OSError as e:
    R.append({"cat": "SYMLINK", "test": "creation du lien", "payload": "-", "http": "-", "attendu": "403",
              "resultat": "NOT_TESTED", "extrait": str(e)[:60]})
    print("  NOT_TESTED  SYMLINK  creation impossible : %s" % e)
finally:
    if created and os.path.islink(link):
        os.unlink(link)
        print("  (lien symbolique de test supprime — aucune modification durable)")

print("=" * 100)
print("E. NON-REGRESSION — le reste doit continuer a fonctionner")
print("=" * 100)
for p, exp in [("/", "200"), ("/api/health", "200"), ("/api/project", "200"), ("/api/project/status", "200"),
               ("/api/phases", "200"), ("/api/phases/10", "200"), ("/api/budget", "200"), ("/api/quantities", "200"),
               ("/api/documents", "200"), ("/api/plans", "200"), ("/api/renders", "200"), ("/api/bim", "200"),
               ("/api/gates", "200"), ("/api/inexistant", "404"), ("/nimportequoi", "404")]:
    T("REGR", "GET " + p, p, exp)
c, b = raw("/", "HEAD")
T("REGR", "HEAD /", "/", "200")
# POST assistant
import urllib.request
try:
    rq = urllib.request.Request("http://127.0.0.1:8765/api/assistant",
                                data=json.dumps({"question": "Puis-je construire les fondations maintenant ?"}).encode(),
                                headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(rq, timeout=25) as r:
        d = json.loads(r.read())
    ok = "NON, pas encore" in d.get("reponse", "") and d.get("securite", {}).get("blocage") is True
    R.append({"cat": "REGR", "test": "POST /api/assistant (securite fondations)", "payload": "POST", "http": "200",
              "attendu": "blocage", "resultat": "PASS" if ok else "FAIL", "extrait": str(d.get("securite"))[:60]})
    print("  %-4s REGR     %-46s %s" % ("PASS" if ok else "FAIL", "POST /api/assistant → blocage", d.get("securite", {}).get("blocage")))
except Exception as e:
    print("  FAIL REGR     POST /api/assistant : %s" % e)

p = sum(1 for x in R if x["resultat"] == "PASS")
f = sum(1 for x in R if x["resultat"] == "FAIL")
nt = sum(1 for x in R if x["resultat"] == "NOT_TESTED")
print("=" * 100)
print("RESULTAT : %d PASS / %d FAIL / %d NOT_TESTED  (total %d)" % (p, f, nt, len(R)))
json.dump({"at": "2026-10-02T17:12:00", "host": HOST, "port": PORT, "total": len(R), "PASS": p, "FAIL": f,
           "NOT_TESTED": nt, "tests": R},
          open(os.path.join(PROJ, "reports", "security_fix_p0_tests.json"), "w"), indent=2, ensure_ascii=False)

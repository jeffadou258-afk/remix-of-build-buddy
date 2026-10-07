"""Lanceur de production pour Render (fichier ajouté, aucune logique métier).
Réutilise tel quel le gestionnaire HTTP de web/api/server.py ; seule l'adresse
d'écoute change (0.0.0.0:$PORT, exigé par Render). HTTPS est assuré par Render.
Refuse de démarrer sans CA_API_KEY robuste."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "web", "api"))
key = os.environ.get("CA_API_KEY", "")
if len(key) < 32:
    sys.exit("CA_API_KEY absente ou trop courte (32 caractères minimum) : arrêt.")
import server  # web/api/server.py, non modifié
from http.server import ThreadingHTTPServer
port = int(os.environ.get("PORT", "10000"))
os.makedirs(server.DATA, exist_ok=True)
print("API ConstructionAgent v1 sur 0.0.0.0:%d (données : %s)" % (port, server.DATA), flush=True)
ThreadingHTTPServer(("0.0.0.0", port), server.H).serve_forever()

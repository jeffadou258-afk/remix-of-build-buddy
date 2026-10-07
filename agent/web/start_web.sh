#!/bin/bash
# ============================================================================
#  CONSTRUCTION AGENT — DÉMARRAGE DE L'APPLICATION WEB
#  PRJ_1701484686 — Villa_Test_001
#
#  Usage :   ./start_web.sh              → port 8765, toutes interfaces
#            ./start_web.sh 9000         → port personnalisé
#            ./start_web.sh --stop       → arrête le serveur
#            ./start_web.sh --standalone → ouvre la version sans serveur
#
#  Lancé DEPUIS VOTRE terminal, le serveur vit dans VOTRE session et ne
#  dépend pas de l'agent. (C'est la cause du problème initial : le serveur
#  avait été lancé comme enfant du processus de l'agent et mourait avec lui.)
# ============================================================================
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${1:-8765}"
BACKEND="$ROOT/web/backend/server.py"
PYBIN="/usr/bin/python3"
LOG="/tmp/construction_agent_web.log"

case "${1:-}" in
  --stop)
    if pkill -f "web/backend/server.py"; then echo "✔ Serveur arrêté."; else echo "· Aucun serveur en cours."; fi
    exit 0 ;;
  --standalone)
    F="$ROOT/web/frontend/Villa_Test_001_APP.html"
    [ -f "$F" ] || { echo "✘ Fichier autonome absent : $F"; exit 1; }
    echo "✔ Ouverture de la version autonome (aucun serveur requis) :"
    echo "  $F"
    open "$F" 2>/dev/null || echo "  Ouvrez ce fichier par double-clic dans votre navigateur."
    exit 0 ;;
esac

command -v "$PYBIN" >/dev/null 2>&1 || PYBIN="$(command -v python3)"
[ -f "$BACKEND" ] || { echo "✘ Backend introuvable : $BACKEND"; exit 1; }

# libérer le port si nécessaire
if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "· Port $PORT déjà utilisé — arrêt de l'ancienne instance."
  pkill -f "web/backend/server.py" ; sleep 1
fi

echo "════════════════════════════════════════════════════════════"
echo "  CONSTRUCTION AGENT — APPLICATION WEB"
echo "════════════════════════════════════════════════════════════"
echo "  Racine projet : $ROOT"
echo "  Backend       : web/backend/server.py"
echo "  Frontend      : web/frontend/index.html"
echo "  Python        : $PYBIN"
echo "  Port          : $PORT (écoute sur 127.0.0.1 — boucle locale uniquement)"
echo "════════════════════════════════════════════════════════════"
echo "  URL           : http://127.0.0.1:$PORT"
echo "  Réseau        : FERMÉ volontairement (sécurité — correctif P0 path traversal)"
echo "  Fichier seul  : ./start_web.sh --standalone"
echo "  Arrêt         : ./start_web.sh --stop"
echo "════════════════════════════════════════════════════════════"
echo "  Journal : $LOG     (Ctrl+C pour arrêter)"
echo

exec "$PYBIN" "$BACKEND" --port "$PORT" --host 127.0.0.1 2>&1 | tee "$LOG"

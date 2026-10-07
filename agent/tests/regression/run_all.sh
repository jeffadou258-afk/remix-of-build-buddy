#!/usr/bin/env bash
# Lance TOUTE la non-regression V3.4 + les tests du module d'extraction.
# Pre-requis : serveur demarre (python3 web/backend/server.py) sur 127.0.0.1:8765.
set -u
cd "$(dirname "$0")/../.."
rc=0
python3 web/tests/test_web_app.py      || rc=1
python3 web/tests/test_security_p0.py  || rc=1
python3 tests/regression/baseline_tool.py compare || rc=1
python3 -m unittest discover -s tests/extraction -v || rc=1
python3 -m unittest discover -s tests/programming -v || rc=1
echo "== GLOBAL : $([ $rc = 0 ] && echo PASS || echo FAIL)"
exit $rc

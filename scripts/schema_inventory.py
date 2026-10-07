#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inventaire du schema Supabase depuis src/integrations/supabase/types.ts.

Ne remplace pas un `supabase db dump` (qui seul donne les politiques RLS, les
triggers et les corps de fonctions SECURITY DEFINER). Sert de reference pour
verifier, apres connexion, que la base en ligne correspond a ce que le code attend.
"""
import json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src/integrations/supabase/types.ts"
OUT = ROOT / "scripts/supabase-schema-inventory.json"

src = SRC.read_text(encoding="utf-8")
pub = src[src.find("public: {"):]

# ---- Enums : chaque enum commence par "      nom:" ; les valeurs suivent (pipes, multiligne)
enums = {}
m = re.search(r"Enums:\s*\{(.*?)\n    \}", pub, re.S)
if m:
    cur = None
    for line in m.group(1).splitlines():
        head = re.match(r"^ {6}(\w+):\s*(.*)$", line)
        if head:
            cur = head.group(1)
            enums[cur] = re.findall(r'"([^"]+)"', head.group(2))
        elif cur is not None:
            enums[cur] += re.findall(r'"([^"]+)"', line)
enums = {k: v for k, v in enums.items() if v}

# ---- Tables : on isole le bloc Row de chaque table (pas Insert/Update)
tables = {}
for name in re.findall(r"\n {6}(\w+):\s*\{\n {8}Row:\s*\{", pub):
    i = pub.find("\n      %s: {\n        Row: {" % name)
    seg = pub[i:]
    j = seg.find("\n        }", seg.find("Row: {"))          # fin du bloc Row
    row = seg[:j]
    cols = [(c, t.strip()) for c, t in re.findall(r"\n {10}(\w+)\??:\s*([^\n]+)", row)]
    tables[name] = [{"name": c, "type": t} for c, t in cols]

# ---- Fonctions SQL exposées (bloc Functions, pas Tables)
fn = re.search(r"\n    Functions:\s*\{(.*?)\n    \}", pub, re.S)
functions = re.findall(r"^ {6}(\w+):\s*\{", fn.group(1), re.M) if fn else []

inv = {
    "source": "src/integrations/supabase/types.ts (genere par Supabase)",
    "project_id": "huaztikucbniycexlkem",
    "enums": enums,
    "tables": tables,
    "functions": sorted(set(functions)),
    "avertissement": ("Inventaire de TYPES uniquement. Les politiques RLS, les triggers et les corps "
                      "de fonctions SECURITY DEFINER doivent etre obtenus par `supabase db dump` "
                      "apres `supabase login` + `supabase link`."),
}
OUT.write_text(json.dumps(inv, ensure_ascii=False, indent=2), encoding="utf-8")

print("ENUMS")
for k, v in enums.items():
    print("  %-14s %s" % (k, " | ".join(v)))
print("\nTABLES")
for t, cs in sorted(tables.items()):
    print("  %-24s %2d colonnes" % (t, len(cs)))
print("\nFONCTIONS SQL (%d)" % len(inv["functions"]))
for f in inv["functions"]:
    print("   -", f)
print("\necrit ->", OUT)

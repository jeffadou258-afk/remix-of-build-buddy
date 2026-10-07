#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MODULE D'EXTRACTION — texte libre du client -> donnees structurees (inputs.json).

Regles (doctrine PREUVE > AFFIRMATION) :
  * seule une information ECRITE EXPLICITEMENT par le client est extraite -> USER_PROVIDED ;
  * USER_PROVIDED = "dit par le client", PAS "valide techniquement" (technically_validated=False) ;
  * tout le reste = UNKNOWN (value=None). Aucune valeur par defaut, aucune deduction ;
  * les hypotheses sont stockees a part (liste "hypotheses"), jamais melangees aux donnees ;
  * budget : seul le budget DECLARE est conserve ; estimation = NOT_EXECUTED (aucun moteur de chiffrage) ;
  * quantites : UNKNOWN (aucun moteur de quantification dynamique) ;
  * aucune donnee de la villa de test (PRJ_1701484686 / DEFAULT_ROOMS) n'est utilisee.
Moteur deterministe (expressions regulieres) : pas d'IA, donc pas de complement invente.

Usage : python3 engines/extraction/engine.py <project_dir> --text "..." [--message-id M1]
        python3 engines/extraction/engine.py <project_dir> --edit '{"plot_area_m2": 600}'
"""
import argparse, datetime, json, os, re, sys, unicodedata

OPERATION = "extraction"
SCHEMA = "construction-agent.inputs"
VERSION = 1

FIELDS = ["building_type", "levels_label", "levels_count", "bedrooms", "bathrooms", "plot_area_m2",
          "plot_dimensions_m", "location_city", "garage", "pool", "occupants", "style"]
CITIES = ["Abidjan", "Yamoussoukro", "Bouaké", "Bouake", "San-Pédro", "San Pedro", "Daloa", "Korhogo",
          "Man", "Gagnoa", "Grand-Bassam", "Bingerville", "Assinie", "Anyama", "Dabou", "Abobo",
          "Cocody", "Yopougon", "Marcory", "Koumassi", "Treichville", "Plateau", "Riviera", "Port-Bouët"]
WORD_NUM = {"un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7,
            "huit": 8, "neuf": 9, "dix": 10}
ROOM_WORDS = r"(salon|s[ée]jour|cuisine|chambre(?: parentale)?|suite parentale|bureau|garage|salle de bain|salle d'eau|wc|terrasse|buanderie|magasin|hall|entr[ée]e|salle [àa] manger|dressing)"
NUM = r"(\d+(?:[.,]\d+)?)"
M2 = r"\s*(?:m²|m2|mètres? carrés?|metres? carres?)"


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def _n(s):
    return float(s.replace(",", ".")) if s is not None else None


def _int(tok):
    tok = tok.lower()
    return int(tok) if tok.isdigit() else WORD_NUM.get(tok)


def _unknown():
    return {"value": None, "status": "UNKNOWN", "source": None, "technically_validated": False}


def _given(value, excerpt, message_id, origin="conversation"):
    return {"value": value, "status": "USER_PROVIDED", "technically_validated": False,
            "source": {"origin": origin, "message_id": message_id, "excerpt": excerpt, "at": now()}}


def extract(text, message_id=None):
    """Retourne uniquement les champs trouves explicitement : {champ: (valeur, extrait)}."""
    t = unicodedata.normalize("NFC", text)
    found, rooms = {}, []

    def put(k, v, m):
        found.setdefault(k, (v, m.group(0).strip()))

    m = re.search(r"\b(villa|maison|duplex|triplex|immeuble|appartement|bungalow|r[ée]sidence)\b", t, re.I)
    if m: put("building_type", m.group(1).lower(), m)
    m = re.search(r"\bR\s*\+\s*(\d+)\b", t, re.I)
    if m:
        put("levels_label", "R+%s" % m.group(1), m); put("levels_count", int(m.group(1)) + 1, m)
    else:
        m = re.search(r"\bplain[- ]pied\b", t, re.I)
        if m: put("levels_label", "plain-pied", m); put("levels_count", 1, m)
    nw = r"(\d+|un|une|deux|trois|quatre|cinq|six|sept|huit|neuf|dix)"
    m = re.search(nw + r"\s+chambres?\b", t, re.I)
    if m: put("bedrooms", _int(m.group(1)), m)
    m = re.search(nw + r"\s+(?:salles? de bains?|salles? d'eau|sdb)\b", t, re.I)
    if m: put("bathrooms", _int(m.group(1)), m)
    m = re.search(r"terrain[^.;\n]{0,25}?" + NUM + M2, t, re.I) or re.search(NUM + M2 + r"\s+de terrain", t, re.I)
    if m: put("plot_area_m2", _n(m.group(1)), m)
    m = re.search(r"terrain[^.;\n]{0,25}?" + NUM + r"\s*(?:m\s*)?[x×]\s*" + NUM + r"\s*m\b", t, re.I)
    if m: put("plot_dimensions_m", [_n(m.group(1)), _n(m.group(2))], m)
    for c in CITIES:
        m = re.search(r"\b(?:à|a|au|sur|dans|quartier)\s+(" + re.escape(c) + r")\b", t)
        if m: put("location_city", c, m); break
    m = re.search(r"\b(sans|pas de)\s+garage\b", t, re.I)
    if m: put("garage", False, m)
    else:
        m = re.search(r"\b(avec|un|une|double)\s+garage\b", t, re.I)
        if m: put("garage", True, m)
    m = re.search(r"\b(sans|pas de)\s+piscine\b", t, re.I)
    if m: put("pool", False, m)
    else:
        m = re.search(r"\b(avec|une)\s+piscine\b", t, re.I)
        if m: put("pool", True, m)
    m = re.search(r"\b(\d+)\s+(?:personnes|occupants)\b", t, re.I)
    if m: put("occupants", int(m.group(1)), m)
    m = re.search(r"\bstyle\s+([a-zà-ÿ\- ]{3,30}?)(?=[,.;\n]|$)", t, re.I)
    if m: put("style", m.group(1).strip().lower(), m)
    for m in re.finditer(ROOM_WORDS + r"[^.;,\n]{0,15}?" + NUM + M2, t, re.I):
        rooms.append({"name": m.group(1).lower(), "surface_m2": _n(m.group(2)), "excerpt": m.group(0).strip()})
    budget = None
    m = re.search(r"budget[^.;\n]{0,25}?" + NUM + r"\s*(millions?|M|milliards?)?\s*(?:de\s+)?(fcfa|f\s?cfa|xof|francs?|cfa|€|euros?)?", t, re.I)
    if m:
        amt, mult, cur = _n(m.group(1)), (m.group(2) or "").lower(), (m.group(3) or "").lower()
        amt *= 1e9 if mult.startswith("milliard") else 1e6 if mult in ("million", "millions", "m") else 1
        cur = "EUR" if cur.startswith(("€", "euro")) else "XOF" if cur else None
        budget = (round(amt), cur, m.group(0).strip())
    return found, rooms, budget


def empty_inputs(project_id):
    return {"schema": SCHEMA, "version": VERSION, "project_id": project_id, "updated_at": now(),
            "notice": "USER_PROVIDED = declare par le client, non valide techniquement. UNKNOWN = non fourni.",
            "fields": {k: _unknown() for k in FIELDS},
            "rooms": [],
            "budget": {"declared": _unknown(),
                       "estimate": {"status": "NOT_EXECUTED", "value": None,
                                    "reason": "aucun moteur reel de chiffrage"}},
            "quantities": {"status": "UNKNOWN", "items": [],
                           "reason": "aucun moteur de quantification dynamique"},
            "hypotheses": [], "history": []}


def _path(project_dir):
    return os.path.join(project_dir, "inputs.json")


def load(project_dir):
    try:
        return json.load(open(_path(project_dir), encoding="utf-8"))
    except Exception:
        return empty_inputs(os.path.basename(os.path.normpath(project_dir)))


def _save(project_dir, d):
    d["updated_at"] = now()
    os.makedirs(project_dir, exist_ok=True)
    json.dump(d, open(_path(project_dir), "w", encoding="utf-8"), indent=2, ensure_ascii=False)


def _memory(project_dir, field, entry):
    p = os.path.join(project_dir, "memory", "constraints.jsonl")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps({"at": now(), "field": field, "value": entry["value"],
                            "status": entry["status"], "source": entry["source"]}, ensure_ascii=False) + "\n")


def _set(d, project_dir, field, entry):
    old = d["fields"].get(field)
    if old and old["status"] != "UNKNOWN" and old["value"] != entry["value"]:
        d["history"].append({"field": field, "previous": old, "replaced_at": now()})
    d["fields"][field] = entry
    _memory(project_dir, field, entry)


def run(project_dir, text, message_id=None):
    d = load(project_dir)
    found, rooms, budget = extract(text, message_id)
    for k, (v, ex) in found.items():
        _set(d, project_dir, k, _given(v, ex, message_id))
    for r in rooms:
        d["rooms"].append({"name": r["name"], "surface_m2": _given(r["surface_m2"], r["excerpt"], message_id)})
    if budget:
        amt, cur, ex = budget
        d["budget"]["declared"] = _given({"amount": amt, "currency": cur}, ex, message_id)
        _memory(project_dir, "budget.declared", d["budget"]["declared"])
    _save(project_dir, d)
    return {"status": "EXTRACTED", "inputs": _path(project_dir),
            "user_provided": sorted(found) + (["budget.declared"] if budget else []),
            "unknown": [k for k in FIELDS if d["fields"][k]["status"] == "UNKNOWN"],
            "rooms_with_surface": len(rooms)}


def edit(project_dir, changes, user_id=None):
    """Correction/complement par le formulaire. value=None remet le champ a UNKNOWN."""
    d = load(project_dir)
    for k, v in changes.items():
        if k == "budget_declared":
            d["budget"]["declared"] = _unknown() if v is None else _given(v, None, None, "formulaire")
            continue
        if k not in FIELDS:
            raise ValueError("champ inconnu: %s" % k)
        entry = _unknown() if v is None else _given(v, None, None, "formulaire")
        if entry["source"]: entry["source"]["user_id"] = user_id
        _set(d, project_dir, k, entry)
    _save(project_dir, d)
    return d


def add_hypothesis(project_dir, field, value, reason, author):
    """Les hypotheses sont rangees a part ; elles ne modifient JAMAIS 'fields'."""
    d = load(project_dir)
    d["hypotheses"].append({"field": field, "value": value, "status": "HYPOTHESIS",
                            "reason": reason, "author": author, "at": now()})
    _save(project_dir, d)
    return d


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir"); ap.add_argument("--text"); ap.add_argument("--message-id")
    ap.add_argument("--edit")
    a = ap.parse_args()
    pd = os.path.abspath(a.project_dir)
    if a.edit:
        print(json.dumps(edit(pd, json.loads(a.edit)), indent=2, ensure_ascii=False))
    elif a.text:
        print(json.dumps(run(pd, a.text, a.message_id), indent=2, ensure_ascii=False))
    else:
        ap.error("--text ou --edit requis")

# -*- coding: utf-8 -*-
"""Execution des moteurs EXISTANTS pour UN projet, avec arret et reprise aux Human Gates.

Reutilise sans modification run_agent.PIPELINE, run_agent.GATES et run_agent.load_engine.
Ce fichier ne contient aucune regle metier : il transmet aux moteurs les donnees
USER_PROVIDED de inputs.json (via leurs parametres existants) et refuse de lancer
le moteur programming sans pieces fournies (sinon il utiliserait DEFAULT_ROOMS).
"""
import datetime, importlib.util, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RUN_AGENT = _load(os.path.join(ROOT, "run_agent.py"), "ca_run_agent")
EXTRACTION = _load(os.path.join(ROOT, "engines", "extraction", "engine.py"), "ca_extraction")
PIPELINE = [n for n, _ in RUN_AGENT.PIPELINE]
GATES = set(RUN_AGENT.GATES)


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def jload(p, default=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return default


def jsave(p, d):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    json.dump(d, open(tmp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    os.replace(tmp, p)


def state_path(pd):
    return os.path.join(pd, "state.json")


def gates_path(pd):
    return os.path.join(pd, "gates.json")


def initial_state():
    return {"status": "CREATED", "completed": [], "pending_gate": None, "last_run_id": None, "updated_at": now()}


def initial_gates():
    return {g: {"status": "NOT_REACHED", "opened_at": None, "decision": None} for g in PIPELINE if g in GATES}


def _engine_kwargs(name, inputs):
    """Seules les valeurs USER_PROVIDED sont transmises, via les parametres deja prevus par les moteurs."""
    f = inputs.get("fields", {})
    given = lambda k: f.get(k, {}).get("value") if f.get(k, {}).get("status") == "USER_PROVIDED" else None
    if name == "programming":
        rows = []
        for i, r in enumerate(inputs.get("rooms", [])):
            s = r.get("surface_m2", {})
            if s.get("status") != "USER_PROVIDED" or s.get("value") is None or not r.get("level"):
                return None, "piece '%s' : surface ou niveau non fourni" % r.get("name")
            rows.append(("P%02d" % (i + 1), r["name"], s["value"], r["level"]))
        if not rows:
            return None, "aucune piece fournie par le client (le moteur utiliserait DEFAULT_ROOMS)"
        return {"rooms": rows}, None
    if name == "site_analysis":
        prov = {}
        if given("plot_area_m2") is not None:
            prov["terrain_area_m2"] = given("plot_area_m2")
        dims = given("plot_dimensions_m")
        if dims:
            prov["terrain_width_m"], prov["terrain_depth_m"] = dims[0], dims[1]
        return {"provided": prov}, None
    return {}, None


def run(pd, run_id):
    st = jload(state_path(pd), initial_state())
    gates = jload(gates_path(pd), initial_gates())
    if st.get("pending_gate"):
        return None, "gate '%s' en attente de decision" % st["pending_gate"]
    inputs = EXTRACTION.load(pd)
    start = len(st["completed"])
    steps, status, stopped = [], "COMPLETED", None
    for name in PIPELINE[start:]:
        kwargs, block = _engine_kwargs(name, inputs)
        if block:
            steps.append({"engine": name, "status": "BLOCKED", "cause": block})
            status, stopped = "BLOCKED", name
            break
        try:
            res = RUN_AGENT.load_engine(name).run(pd, **kwargs)
        except Exception as e:
            res = {"status": "FAILED", "error": "%s: %s" % (type(e).__name__, e)}
        s = res.get("status", "UNKNOWN")
        steps.append({"engine": name, "status": s,
                      "details": {k: v for k, v in res.items() if k not in ("status", "views")}})
        if s in ("FAILED", "BLOCKED"):
            status, stopped = s, name
            break
        st["completed"].append(name)
        if name in GATES:
            gates[name] = {"status": "OPEN", "opened_at": now(), "decision": None}
            st["pending_gate"] = name
            status, stopped = "AWAITING_GATE", name
            break
    st.update(status=status, last_run_id=run_id, updated_at=now())
    jsave(state_path(pd), st)
    jsave(gates_path(pd), gates)
    rec = {"id": run_id, "at": now(), "started_at_engine": PIPELINE[start] if start < len(PIPELINE) else None,
           "status": status, "stopped_at": stopped, "steps": steps}
    with open(os.path.join(pd, "runs.jsonl"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec, None


def decide(pd, gate, decision, owner, comment=None, variant_id=None):
    st = jload(state_path(pd), initial_state())
    gates = jload(gates_path(pd), initial_gates())
    if gate not in gates:
        return None, 404, "gate inconnu"
    if st.get("pending_gate") != gate or gates[gate]["status"] != "OPEN":
        return None, 409, "gate non ouvert"
    entry = {"decision": decision, "by": owner, "at": now(), "comment": comment, "variant_id": variant_id}
    gates[gate] = {"status": "APPROVED" if decision == "approve" else "REJECTED",
                   "opened_at": gates[gate]["opened_at"], "decision": entry}
    st["pending_gate"] = None
    if decision == "reject":
        st["completed"] = st["completed"][:PIPELINE.index(gate)]  # le moteur sera relance
        st["status"] = "GATE_REJECTED"
    else:
        st["status"] = "GATE_APPROVED"
    st["updated_at"] = now()
    jsave(state_path(pd), st)
    jsave(gates_path(pd), gates)
    p = os.path.join(pd, "memory", "decisions.jsonl")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(entry, gate=gate), ensure_ascii=False) + "\n")
    return gates[gate], 200, None

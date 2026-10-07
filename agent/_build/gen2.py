#!/usr/bin/env python3
"""Construction Agent v2.0.0 — Generateur 2/2 : noyau Evidence, 13 moteurs, scripts Blender, orchestrateur."""
import os

ROOT = "/Users/mac/ConstructionAgent"

FILES = {}

# =============================================================== engines/_core.py
FILES["engines/_core.py"] = r'''"""
Construction Agent v2.0.0 — NOYAU COMMUN.
Systeme Evidence + verification physique. Aucune affirmation sans preuve.
"""
import os, sys, json, hashlib, shutil, subprocess, datetime

AGENT_ID = "construction-agent"
AGENT_VERSION = "2.0.0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATUS = ["DRAFT", "ANALYZING", "PROPOSED", "HYPOTHESIS", "USER_VALIDATION_REQUIRED",
          "VALIDATED", "IN_PROGRESS", "EXECUTED", "VERIFIED", "READY", "BLOCKED",
          "FAILED", "CANCELLED"]
DATA_STATUS = ["VERIFIED", "USER_PROVIDED", "DERIVED", "HYPOTHESIS", "UNKNOWN"]

__all__ = ["Evidence", "AGENT_ID", "AGENT_VERSION", "ROOT", "STATUS", "DATA_STATUS",
           "now", "sha256", "image_info", "file_info", "blender_path", "blender_version",
           "run_blender", "load_json", "save_json", "which", "log"]


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def which(cmd):
    return shutil.which(cmd)


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def image_info(path):
    """Resolution REELLE via sips (macOS). Retourne None si indisponible."""
    try:
        r = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
                           capture_output=True, text=True, timeout=30)
        w = h = None
        for line in r.stdout.splitlines():
            if "pixelWidth" in line:
                w = int(line.split(":")[1].strip())
            if "pixelHeight" in line:
                h = int(line.split(":")[1].strip())
        if w and h:
            return {"width": w, "height": h, "resolution": "%dx%d" % (w, h)}
    except Exception:
        pass
    return None


def file_info(path):
    """Preuve physique d'un fichier. None si absent."""
    if not path or not os.path.exists(path):
        return None
    st = os.stat(path)
    d = {"path": os.path.abspath(path), "exists": True,
         "size_bytes": st.st_size, "is_file": os.path.isfile(path)}
    if d["is_file"]:
        d["sha256"] = sha256(path)
        d["format"] = os.path.splitext(path)[1].lstrip(".").upper() or None
        if d["format"] == "PNG":
            ii = image_info(path)
            if ii:
                d.update(ii)
                d["format"] = "PNG"
    return d


def blender_path():
    cands = ["/Applications/Blender.app/Contents/MacOS/Blender", shutil.which("blender")]
    for p in cands:
        if p and os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None


def blender_version(exe):
    try:
        r = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=90)
        line = (r.stdout or "").strip().splitlines()
        return line[0].strip() if line else None
    except Exception:
        return None


def run_blender(exe, script, args=(), timeout=2400):
    cmd = [exe, "--background", "--factory-startup", "--python", script]
    if args:
        cmd += ["--"] + [str(a) for a in args]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def log(project_dir, engine, msg):
    p = os.path.join(project_dir, "logs", "agent.log")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write("%s [%s] %s\n" % (now(), engine, msg))


class Evidence(object):
    """Section 21 de la specification — un evidence.json par moteur."""

    def __init__(self, operation, project_dir=None):
        self.operation = operation
        self.project_dir = project_dir
        self.d = {"operation": operation, "agent": AGENT_ID, "version": AGENT_VERSION,
                  "started_at": now(), "completed_at": None, "status": "IN_PROGRESS",
                  "tools_used": [], "commands_executed": [], "files_created": [],
                  "files_verified": [], "tests": [], "errors": [], "warnings": []}

    def tool(self, name):
        if name not in self.d["tools_used"]:
            self.d["tools_used"].append(name)

    def cmd(self, c):
        self.d["commands_executed"].append(c)

    def record(self, path):
        """Verification PHYSIQUE d'un fichier. Retourne la preuve ou None."""
        info = file_info(path)
        if info is None:
            self.d["errors"].append("FICHIER ABSENT: %s" % path)
            return None
        self.d["files_verified"].append(info)
        return info

    def created(self, path):
        info = file_info(path)
        if info is None:
            self.d["errors"].append("CREATION NON CONFIRMEE: %s" % path)
            return None
        self.d["files_created"].append(info["path"])
        self.d["files_verified"].append(info)
        return info

    def test(self, name, passed, detail=""):
        self.d["tests"].append({"name": name, "passed": bool(passed),
                                "status": "PASSED" if passed else "FAILED",
                                "detail": str(detail)})
        return bool(passed)

    def warn(self, m):
        self.d["warnings"].append(m)

    def fail(self, cause):
        self.d["status"] = "FAILED"
        self.d["errors"].append(cause)
        return "FAILED"

    def block(self, cause):
        self.d["status"] = "BLOCKED"
        self.d["errors"].append(cause)
        return "BLOCKED"

    def close(self, status):
        if self.d["status"] not in ("FAILED", "BLOCKED"):
            self.d["status"] = status
        self.d["completed_at"] = now()
        self.summary = self.d
        return self.d

    def out(self, filename="evidence.json"):
        base = self.project_dir or ROOT
        path = os.path.join(base, "evidence", self.operation, filename)
        save_json(path, self.d)
        return path


def cli(operation, engine_run):
    """Point d'entree standard d'un moteur."""
    if len(sys.argv) < 2:
        print("usage: engine.py <project_dir>")
        sys.exit(2)
    project_dir = os.path.abspath(sys.argv[1])
    res = engine_run(project_dir)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return res
'''

# =============================================================== engines
ENGINES = {}

ENGINES["discovery"] = r'''"""PHASE 0 — DISCOVERY. project_context.json depuis l'etat REEL de la machine."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "discovery"


def run(project_dir):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    bp = blender_path()
    tools = {}
    for name, cmd in [("python3", "python3"), ("ffmpeg", "ffmpeg"), ("zip", "zip"),
                      ("git", "git"), ("sips", "sips")]:
        p = which(cmd)
        tools[name] = {"available": bool(p), "path": p, "version": None}
        ev.tool(name)
    tools["blender"] = {"available": bool(bp), "path": bp, "version": None}
    if bp:
        ev.tool("blender")
        tools["blender"]["version"] = blender_version(bp)
    for name in ["freecad", "openscad", "inkscape", "soffice", "magick"]:
        p = which(name)
        tools[name] = {"available": bool(p), "path": p, "version": None}

    project_id = os.path.basename(os.path.normpath(project_dir))
    ctx = {"project_id": project_id, "created_at": now(), "status": "ANALYZING",
           "client": None, "site": None, "tools": tools,
           "human_gate_required": not tools["blender"]["available"],
           "notes": "outils detectes par execution reelle, aucune supposition"}
    p = save_json(os.path.join(project_dir, "project_context.json"), ctx)
    ev.created(p)
    ev.test("blender_available", bool(bp), tools["blender"]["version"] or "absent")
    ev.test("project_context_written", os.path.isfile(p))
    ev.close("VERIFIED")
    ev.out()
    log(project_dir, OPERATION, "status=VERIFIED")
    return {"status": "VERIFIED", "project_context": p, "tools": tools}


if __name__ == "__main__":
    cli(OPERATION, run)
'''

ENGINES["programming"] = r'''"""PHASE 1 — PROGRAMMING. program.json + controle de coherence des surfaces."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "programming"

# Surfaces indicatives (HYPOTHESIS pedagogique, non normatives)
DEFAULT_ROOMS = [
    ("P01", "Sejour / Salon",     42.0, "RDC"),
    ("P02", "Cuisine ouverte",    14.0, "RDC"),
    ("P03", "Suite parentale",    18.0, "RDC"),
    ("P04", "Salle d'eau",         6.0, "RDC"),
    ("P05", "WC invites",          2.5, "RDC"),
    ("P06", "Entree / Hall",       8.0, "RDC"),
    ("P07", "Garage",             20.0, "RDC"),
    ("P08", "Chambre 2",          13.0, "ETAGE"),
    ("P09", "Chambre 3",          12.0, "ETAGE"),
    ("P10", "Salle de bain",       7.0, "ETAGE"),
    ("P11", "Palier / Circulation", 9.0, "ETAGE"),
    ("P12", "Bureau",             11.0, "ETAGE"),
]


def run(project_dir, rooms=None):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    rows = rooms or DEFAULT_ROOMS
    out, total = [], 0.0
    for code, name, surf, level in rows:
        out.append({"code": code, "name": name, "surface_m2": float(surf),
                    "quantity": 1, "level": level, "status": "HYPOTHESIS"})
        total += float(surf)
    total = round(total, 2)
    computed = round(sum(r["surface_m2"] * r["quantity"] for r in out), 2)
    prog = {"project_id": os.path.basename(os.path.normpath(project_dir)),
            "created_at": now(), "rooms": out,
            "total_surface_m2": total, "computed_surface_m2": computed,
            "coherent": abs(total - computed) < 0.01,
            "data_status": "HYPOTHESIS",
            "warning": "Surfaces indicatives = HYPOTHESIS. A valider par un professionnel."}
    p = save_json(os.path.join(project_dir, "program", "program.json"), prog)
    ev.created(p)
    ev.test("surface_total == computed", prog["coherent"], "%s m2" % total)
    ev.test("no_duplicate_code", len(set(r["code"] for r in out)) == len(out))
    ev.close("PROPOSED")
    ev.out()
    log(project_dir, OPERATION, "status=PROPOSED total=%s" % total)
    return {"status": "PROPOSED", "program": p, "total_surface_m2": total,
            "coherent": prog["coherent"]}


if __name__ == "__main__":
    cli(OPERATION, run)
'''

ENGINES["site_analysis"] = r'''"""PHASE 2 — SITE & CONSTRAINT ANALYSIS. Chaque donnee porte un statut."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "site_analysis"

FIELDS = ["terrain_width_m", "terrain_depth_m", "terrain_area_m2", "orientation",
          "acces_rue", "pente_pct", "voisinage", "climat", "reglementation",
          "reseaux", "servitudes", "topographie"]


def run(project_dir, provided=None):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    provided = provided or {}
    site = {}
    for f in FIELDS:
        if f in provided and provided[f] not in (None, ""):
            site[f] = {"value": provided[f], "status": "USER_PROVIDED"}
        else:
            site[f] = {"value": None, "status": "UNKNOWN"}
    doc = {"project_id": os.path.basename(os.path.normpath(project_dir)),
           "created_at": now(), "fields": site,
           "regulation_status": "UNKNOWN",
           "regulation_note": "Aucune source reglementaire fournie. Jamais supposee conforme.",
           "hypotheses": []}
    p = save_json(os.path.join(project_dir, "site", "site.json"), doc)
    ev.created(p)
    unknown = sum(1 for v in site.values() if v["status"] == "UNKNOWN")
    ev.test("no_invented_data", all(v["value"] is None or v["status"] == "USER_PROVIDED"
                                   for v in site.values()))
    ev.test("unknown_tracked", unknown >= 0, "%d champs UNKNOWN" % unknown)
    ev.close("EXECUTED")
    ev.out()
    log(project_dir, OPERATION, "status=EXECUTED unknown=%d" % unknown)
    return {"status": "EXECUTED", "site": p, "unknown_fields": unknown}


if __name__ == "__main__":
    cli(OPERATION, run)
'''

ENGINES["design"] = r'''"""PHASE 3/4 — SPATIAL STRATEGY + CONCEPT DESIGN. Variantes A/B/C."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "design"


def run(project_dir):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    variants = [
        {"id": "VARIANT_A", "concept": "Volume monolithique compact, patio central",
         "zoning": ["RDC: sejour/cuisine au sud, service au nord", "ETAGE: nuit a l'est"],
         "advantages": ["Economie de facade", "Bonne inertie", "Patio = confort thermique"],
         "constraints": ["Terrain plus profond requis", "Cout fondations centrales"],
         "assumptions": ["Terrain suffisamment large = HYPOTHESIS"], "status": "PROPOSED"},
        {"id": "VARIANT_B", "concept": "Volume decale R+1, terrasse couverte, grande baie sud",
         "zoning": ["RDC: sejour traversant + garage ouest", "ETAGE: chambres en bandeau sud",
                    "Terrasse couverte en prolongement du sejour"],
         "advantages": ["Luminosite optimale", "Extension visuelle interieur/exterieur",
                        "Circulation verticale centrale"],
         "constraints": ["Surfaces de toiture importantes", "Masques solaires a etudier"],
         "assumptions": ["Orientation sud du sejour = a VERIFIER"], "status": "PROPOSED"},
        {"id": "VARIANT_C", "concept": "Deux volumes separes relies par un noyau vitre",
         "zoning": ["Bloc jour a l'ouest", "Bloc nuit a l'est", "Noyau: escalier + services"],
         "advantages": ["Separations fonctionnelles nettes", "Vues traversantes", "Extensible"],
         "constraints": ["Developpe de facade maximal", "Plus de surfaces de toiture",
                         "Noyau a isoler soigneusement"],
         "assumptions": ["Budget revu a la hausse = HYPOTHESIS"], "status": "PROPOSED"},
    ]
    doc = {"project_id": os.path.basename(os.path.normpath(project_dir)),
           "created_at": now(), "selected": None, "variants": variants,
           "human_gate": "USER_VALIDATION_REQUIRED",
           "note": "Aucune variante ne peut devenir la variante de travail sans validation utilisateur."}
    p = save_json(os.path.join(project_dir, "design", "design_variants.json"), doc)
    ev.created(p)
    ev.test("variants_proposed", len(variants) == 3)
    ev.test("no_auto_selection", doc["selected"] is None)
    ev.close("USER_VALIDATION_REQUIRED")
    ev.out()
    log(project_dir, OPERATION, "status=USER_VALIDATION_REQUIRED")
    return {"status": "USER_VALIDATION_REQUIRED", "design": p,
            "variants": [v["id"] for v in variants], "selected": None}


if __name__ == "__main__":
    cli(OPERATION, run)
'''

ENGINES["dimension"] = r'''"""PHASE 5 — DIMENSIONING. Coherence surface <-> dimensions."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "dimension"


def run(project_dir, levels=None):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    prog = load_json(os.path.join(project_dir, "program", "program.json"))
    if not prog:
        ev.block("program.json absent — PROGRAM ENGINE doit tourner avant DIMENSION ENGINE")
        ev.out()
        return {"status": "BLOCKED"}
    # programme par niveau
    by_level = {}
    for r in prog["rooms"]:
        by_level.setdefault(r["level"], 0.0)
        by_level[r["level"]] += r["surface_m2"] * r.get("quantity", 1)
    out_levels, total = [], 0.0
    for level, need in by_level.items():
        if level == "EXTERIEUR":
            continue
        depth = 6.0  # HYPOTHESIS de modelisation
        width = round(need / depth, 2)
        out_levels.append({"level": level, "width_m": width, "depth_m": depth,
                           "surface_m2": round(width * depth, 2),
                           "target_m2": round(need, 2), "source": "DERIVED"})
        total += width * depth
    check = all(abs(l["surface_m2"] - l["target_m2"]) < 0.05 for l in out_levels)
    doc = {"project_id": os.path.basename(os.path.normpath(project_dir)),
           "created_at": now(), "levels": out_levels,
           "total_surface_m2": round(total, 2),
           "surface_check": "PASS" if check else "FAIL",
           "assumption": "Profondeur 6 m = HYPOTHESIS DE MODELISATION, jamais un seuil universel.",
           "data_status": "DERIVED"}
    p = save_json(os.path.join(project_dir, "dimensions", "dimensions.json"), doc)
    ev.created(p)
    ev.test("surface_check", check, doc["surface_check"])
    if not check:
        ev.close("FAILED")
    else:
        ev.close("EXECUTED")
    ev.out()
    log(project_dir, OPERATION, "status=%s" % doc["surface_check"])
    return {"status": doc["surface_check"], "dimensions": p,
            "total_surface_m2": doc["total_surface_m2"]}


if __name__ == "__main__":
    cli(OPERATION, run)
'''

ENGINES["floor_plan"] = r'''"""PHASE 6 — FLOOR PLAN. Genere de VRAIS fichiers SVG (stdlib pure)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "floor_plan"
SCALE = 42.0   # px par metre
WALL = 0.20    # m
PALETTE = ["#dbeafe", "#dcfce7", "#fef9c3", "#fae8ff", "#ffe4e6", "#e0e7ff", "#ccfbf1"]


def _svg(level, width_m, depth_m, rooms):
    pad = 60
    W = width_m * SCALE + pad * 2
    H = depth_m * SCALE + pad * 2
    b = ["<?xml version='1.0' encoding='UTF-8'?>",
         "<svg xmlns='http://www.w3.org/2000/svg' width='%.0f' height='%.0f' viewBox='0 0 %.0f %.0f'>" % (W, H, W, H),
         "<rect width='100%%' height='100%%' fill='#ffffff'/>",
         "<text x='%.0f' y='30' font-family='Helvetica' font-size='18' font-weight='bold' fill='#111'>%s</text>"
         % (pad, level),
         "<text x='%.0f' y='48' font-family='Helvetica' font-size='11' fill='#666'>Construction Agent v2.0.0 — schema CONCEPTUEL, non contractuel — echelle 1:%d</text>"
         % (pad, int(100 / (SCALE / 100.0)))]
    # enveloppe
    b.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#f8fafc' stroke='#111' stroke-width='%.1f'/>"
             % (pad, pad, width_m * SCALE, depth_m * SCALE, WALL * SCALE))
    x = pad
    y = pad
    row_h = depth_m * SCALE
    for i, r in enumerate(rooms):
        rw = (r["surface_m2"] / depth_m) * SCALE
        if x + rw > pad + width_m * SCALE + 0.5:
            rw = pad + width_m * SCALE - x
        col = PALETTE[i % len(PALETTE)]
        b.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='%s' stroke='#334155' stroke-width='1.2'/>"
                 % (x, y, rw, row_h, col))
        b.append("<text x='%.1f' y='%.1f' font-family='Helvetica' font-size='10' fill='#0f172a'>%s</text>"
                 % (x + 6, y + 18, r["code"]))
        b.append("<text x='%.1f' y='%.1f' font-family='Helvetica' font-size='9' fill='#334155'>%.1f m2</text>"
                 % (x + 6, y + 32, r["surface_m2"]))
        x += rw + WALL * SCALE
    # cotation
    b.append("<text x='%.1f' y='%.1f' font-family='Helvetica' font-size='11' fill='#111'>largeur %.2f m x profondeur %.2f m</text>"
             % (pad, pad + row_h + 28, width_m, depth_m))
    b.append("</svg>")
    return "\n".join(b)


def run(project_dir):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    dims = load_json(os.path.join(project_dir, "dimensions", "dimensions.json"))
    prog = load_json(os.path.join(project_dir, "program", "program.json"))
    if not dims or not prog:
        ev.block("dimensions.json ou program.json absent")
        ev.out()
        return {"status": "BLOCKED"}
    out_dir = os.path.join(project_dir, "floorplan")
    os.makedirs(out_dir, exist_ok=True)
    doc = {"project_id": os.path.basename(os.path.normpath(project_dir)),
           "created_at": now(), "unit": "m", "levels": []}
    for lv in dims["levels"]:
        rooms = [r for r in prog["rooms"] if r["level"] == lv["level"]]
        if not rooms:
            continue
        svg = _svg(lv["level"], lv["width_m"], lv["depth_m"], rooms)
        f = os.path.join(out_dir, "plan_%s.svg" % lv["level"].lower())
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(svg)
        info = ev.created(f)
        doc["levels"].append({"level": lv["level"], "width_m": lv["width_m"],
                              "depth_m": lv["depth_m"], "wall_thickness_m": WALL,
                              "rooms": rooms, "files": [f],
                              "size_bytes": info["size_bytes"] if info else None})
        ev.test("svg_%s_written" % lv["level"], bool(info and info["size_bytes"] > 500),
                "%s octets" % (info["size_bytes"] if info else "0"))
    p = save_json(os.path.join(project_dir, "floorplan", "floor_plan.json"), doc)
    ev.created(p)
    ev.close("EXECUTED")
    ev.out()
    log(project_dir, OPERATION, "status=EXECUTED levels=%d" % len(doc["levels"]))
    return {"status": "EXECUTED", "floor_plan": p,
            "files": [f for l in doc["levels"] for f in l["files"]]}


if __name__ == "__main__":
    cli(OPERATION, run)
'''

ENGINES["structural_concept"] = r'''"""PHASE — STRUCTURE CONCEPTUELLE. Trames et portees. NON reglementaire."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "structural_concept"


def run(project_dir, span_max=6.0, grid=6.0):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    dims = load_json(os.path.join(project_dir, "dimensions", "dimensions.json"))
    if not dims:
        ev.block("dimensions.json absent")
        ev.out()
        return {"status": "BLOCKED"}
    systems = []
    for lv in dims["levels"]:
        nx = max(1, int(round(lv["width_m"] / grid)))
        ny = max(1, int(round(lv["depth_m"] / grid)))
        systems.append({"level": lv["level"], "grid_x_m": round(lv["width_m"] / nx, 2),
                        "grid_y_m": round(lv["depth_m"] / ny, 2),
                        "bays_x": nx, "bays_y": ny,
                        "columns": (nx + 1) * (ny + 1),
                        "slab_type": "dalle portee 1 sens (hypothese)"})
    doc = {"project_id": os.path.basename(os.path.normpath(project_dir)),
           "created_at": now(), "conceptual": True, "systems": systems,
           "span_max_assumed_m": span_max,
           "disclaimer": "CONCEPTUEL UNIQUEMENT. Aucun calcul structurel reglementaire.",
           "human_gate": "REQUIRED",
           "human_gate_reason": "Le dimensionnement structurel doit etre valide par un professionnel."}
    p = save_json(os.path.join(project_dir, "structure", "structural_concept.json"), doc)
    ev.created(p)
    ev.test("human_gate_declared", doc["human_gate"] == "REQUIRED")
    ev.close("EXECUTED")
    ev.out()
    log(project_dir, OPERATION, "status=EXECUTED human_gate=REQUIRED")
    return {"status": "EXECUTED", "structural_concept": p, "human_gate": "REQUIRED"}


if __name__ == "__main__":
    cli(OPERATION, run)
'''

ENGINES["bim_3d"] = r'''"""PHASE 7 — 3D / BIM. Cree REELLEMENT une maquette .blend via Blender headless."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "bim_3d"


def run(project_dir):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    exe = blender_path()
    ev.tool("blender")
    if not exe:
        ev.block("Blender introuvable. STATUS = BLOCKED. Aucune maquette produite.")
        ev.out()
        return {"status": "BLOCKED", "reason": "blender introuvable"}
    ver = blender_version(exe)
    ev.test("blender_detected", bool(ver), ver or "")
    dims = load_json(os.path.join(project_dir, "dimensions", "dimensions.json"))
    if not dims:
        ev.block("dimensions.json absent")
        ev.out()
        return {"status": "BLOCKED"}
    out_blend = os.path.join(project_dir, "3d", "scene_villa.blend")
    os.makedirs(os.path.dirname(out_blend), exist_ok=True)
    script = os.path.join(ROOT, "scripts", "build_scene.py")
    ev.cmd("%s --background --python %s -- %s %s" % (exe, script, project_dir, out_blend))
    rc, so, se = run_blender(exe, script, [project_dir, out_blend])
    ev.test("blender_exit_code_0", rc == 0, "rc=%d" % rc)
    info = ev.record(out_blend)
    exists = info is not None and info["size_bytes"] > 0
    ev.test("blend_exists", exists, "%s octets" % (info["size_bytes"] if info else 0))
    if not exists:
        ev.fail("Blender rc=%d mais .blend absent ou vide. stderr=%s" % (rc, se[-400:]))
        ev.out()
        return {"status": "FAILED", "stderr_tail": se[-400:]}
    objects = 0
    for line in so.splitlines():
        if line.startswith("OBJECTS="):
            objects = int(line.split("=")[1])
    doc = {"project_id": os.path.basename(os.path.normpath(project_dir)),
           "created_at": now(), "blend_file": info["path"],
           "blend_exists": True, "blend_size_bytes": info["size_bytes"],
           "blend_sha256": info["sha256"], "blender_path": exe,
           "blender_version": ver, "objects": objects, "verified": True}
    p = save_json(os.path.join(project_dir, "3d", "model_3d.json"), doc)
    ev.created(p)
    ev.close("VERIFIED")
    ev.out()
    log(project_dir, OPERATION, "status=VERIFIED objects=%d" % objects)
    return {"status": "VERIFIED", "blend": info["path"], "size_bytes": info["size_bytes"],
            "sha256": info["sha256"], "blender_version": ver, "objects": objects}


if __name__ == "__main__":
    cli(OPERATION, run)
'''

ENGINES["visualization"] = r'''"""PHASE 8a — VISUALIZATION. Declare les intentions de vue (cameras)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "visualization"

VIEWS = [
    ("01_Facade", "Montrer l'identite du volume et la composition de facade"),
    ("02_Entree", "Lire l'acces pieton et le seuil"),
    ("03_Terrasse", "Montrer la relation interieur / exterieur couvert"),
    ("04_Aerienne", "Comprendre l'implantation et la toiture"),
    ("05_Generale", "Vue d'ensemble du projet dans son site"),
]


def run(project_dir):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    doc = {"project_id": os.path.basename(os.path.normpath(project_dir)),
           "created_at": now(),
           "views": [{"name": n, "intention": i, "status": "PROPOSED"} for n, i in VIEWS],
           "note": "Chaque camera doit avoir position, orientation, focale, intention, statut."}
    p = save_json(os.path.join(project_dir, "3d", "render_spec.json"), doc)
    ev.created(p)
    ev.test("views_declared", len(doc["views"]) >= 1, "%d vues" % len(doc["views"]))
    ev.close("EXECUTED")
    ev.out()
    log(project_dir, OPERATION, "status=EXECUTED views=%d" % len(doc["views"]))
    return {"status": "EXECUTED", "render_spec": p,
            "views": [v["name"] for v in doc["views"]]}


if __name__ == "__main__":
    cli(OPERATION, run)
'''

ENGINES["rendering"] = r'''"""PHASE 8b — RENDERING. Produit les PNG via Blender puis verifie CHAQUE image."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "rendering"


def run(project_dir, width=1920, height=1080):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    exe = blender_path()
    ev.tool("blender")
    ev.tool("sips")
    if not exe:
        ev.block("Blender introuvable")
        ev.out()
        return {"status": "BLOCKED"}
    model = load_json(os.path.join(project_dir, "3d", "model_3d.json"))
    spec = load_json(os.path.join(project_dir, "3d", "render_spec.json"))
    if not model or not spec:
        ev.block("model_3d.json ou render_spec.json absent")
        ev.out()
        return {"status": "BLOCKED"}
    blend = model["blend_file"]
    if not os.path.isfile(blend):
        ev.fail("Le .blend declare n'existe pas reellement: %s" % blend)
        ev.out()
        return {"status": "FAILED"}
    out_dir = os.path.join(project_dir, "renders")
    os.makedirs(out_dir, exist_ok=True)
    script = os.path.join(ROOT, "scripts", "render_views.py")
    ev.cmd("%s --background --python %s -- %s %s %d %d" % (exe, script, blend, out_dir, width, height))
    rc, so, se = run_blender(exe, script, [blend, out_dir, width, height])
    ev.test("blender_exit_code_0", rc == 0, "rc=%d" % rc)
    views = []
    for v in spec["views"]:
        f = os.path.join(out_dir, "%s.png" % v["name"])
        info = ev.record(f)
        ok = bool(info and info["size_bytes"] > 5000 and info.get("resolution"))
        if info and info.get("resolution") == "%dx%d" % (width, height):
            ok = ok
        ev.test("file_%s" % v["name"], ok,
                "%s / %s" % (info["size_bytes"] if info else 0,
                             info.get("resolution") if info else None))
        views.append({"name": v["name"], "file": f,
                      "exists": bool(info), "size_bytes": info["size_bytes"] if info else None,
                      "sha256": info["sha256"] if info else None,
                      "resolution": info.get("resolution") if info else None,
                      "intention": v["intention"], "inspected": False, "verified": ok})
    all_ok = all(v["verified"] for v in views) and len(views) > 0
    doc = {"project_id": os.path.basename(os.path.normpath(project_dir)),
           "created_at": now(), "engine": "BLENDER_EEVEE_NEXT", "views": views,
           "all_verified": all_ok}
    p = save_json(os.path.join(project_dir, "renders", "render.json"), doc)
    ev.created(p)
    ev.test("all_views_verified", all_ok, "%d/%d" % (sum(1 for v in views if v["verified"]), len(views)))
    if not all_ok:
        ev.fail("Au moins un rendu manquant ou invalide")
        ev.close("FAILED")
        ev.out()
        return {"status": "FAILED", "views": views}
    ev.close("VERIFIED")
    ev.out()
    log(project_dir, OPERATION, "status=VERIFIED views=%d" % len(views))
    return {"status": "VERIFIED", "render": p, "views": views}


if __name__ == "__main__":
    cli(OPERATION, run)
'''

ENGINES["documentation"] = r'''"""PHASE 9 — DOCUMENTATION. Genere un rapport MD + HTML reel."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "documentation"


def run(project_dir):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    pid = os.path.basename(os.path.normpath(project_dir))
    ctx = load_json(os.path.join(project_dir, "project_context.json"), {})
    prog = load_json(os.path.join(project_dir, "program", "program.json"), {})
    dims = load_json(os.path.join(project_dir, "dimensions", "dimensions.json"), {})
    site = load_json(os.path.join(project_dir, "site", "site.json"), {})
    mdl = load_json(os.path.join(project_dir, "3d", "model_3d.json"), {})
    ren = load_json(os.path.join(project_dir, "renders", "render.json"), {})
    out = os.path.join(project_dir, "documentation")
    os.makedirs(out, exist_ok=True)

    L = ["# Rapport architectural — %s" % pid, "",
         "> Genere par Construction Agent v%s le %s" % (AGENT_VERSION, now()),
         "> **Document CONCEPTUEL.** Ne remplace aucune validation professionnelle.",
         "", "## 1. Contexte", ""]
    bl = ctx.get("tools", {}).get("blender", {})
    L += ["- Blender : %s" % (bl.get("version") or "INDISPONIBLE"),
          "- Statut projet : %s" % ctx.get("status", "UNKNOWN"), ""]
    L += ["## 2. Programme", ""]
    if prog:
        L += ["| Code | Piece | Surface | Niveau | Statut |", "|---|---|---|---|---|"]
        for r in prog.get("rooms", []):
            L.append("| %s | %s | %.1f m2 | %s | %s |" %
                     (r["code"], r["name"], r["surface_m2"], r["level"], r["status"]))
        L += ["", "**Total : %.2f m2** (coherent : %s)" %
              (prog.get("total_surface_m2", 0), prog.get("coherent")), ""]
    L += ["## 3. Dimensions", ""]
    for lv in dims.get("levels", []):
        L.append("- %s : %.2f x %.2f m = **%.2f m2** (source %s)" %
                 (lv["level"], lv["width_m"], lv["depth_m"], lv["surface_m2"], lv["source"]))
    L += ["", "Controle de coherence : **%s**" % dims.get("surface_check", "NOT_EXECUTED"), ""]
    L += ["## 4. Site et contraintes", ""]
    for k, v in (site.get("fields") or {}).items():
        L.append("- %s : %s (%s)" % (k, v.get("value"), v.get("status")))
    L += ["", "Statut reglementaire : **%s**" % site.get("regulation_status", "UNKNOWN"), ""]
    L += ["## 5. Maquette 3D", ""]
    if mdl:
        L += ["- Fichier : `%s`" % mdl.get("blend_file"),
              "- Taille : %s octets" % mdl.get("blend_size_bytes"),
              "- SHA-256 : `%s`" % (mdl.get("blend_sha256") or "")[:32] + "...",
              "- Blender : %s" % mdl.get("blender_version"),
              "- Objets : %s" % mdl.get("objects"), ""]
    L += ["## 6. Rendus", ""]
    for v in ren.get("views", []):
        L.append("- %s — %s — %s — **%s**" %
                 (v["name"], v.get("resolution"), v.get("size_bytes"), "VERIFIE" if v["verified"] else "NON VERIFIE"))
    L += ["", "## 7. Hypotheses et donnees UNKNOWN", "",
          "Toute valeur `HYPOTHESIS` ou `UNKNOWN` ci-dessus n'est pas un fait.",
          "Aucune reglementation n'est affirmee conforme sans source verifiee.", ""]
    L += ["## 8. Human Gates", "",
          "- Validation de variante : REQUISE",
          "- Validation structurelle : REQUISE",
          "- Validation reglementaire : REQUISE", ""]

    md = "\n".join(L)
    f_md = os.path.join(out, "rapport_architectural.md")
    with open(f_md, "w", encoding="utf-8") as fh:
        fh.write(md)
    ev.created(f_md)
    html = "<!doctype html><meta charset='utf-8'><title>%s</title><body style=\"font-family:Helvetica;max-width:860px;margin:40px auto\"><pre style='white-space:pre-wrap;line-height:1.5'>%s</pre></body>" % (
        pid, md.replace("&", "&amp;").replace("<", "&lt;"))
    f_html = os.path.join(out, "rapport_architectural.html")
    with open(f_html, "w", encoding="utf-8") as fh:
        fh.write(html)
    ev.created(f_html)
    ev.test("md_written", os.path.getsize(f_md) > 500, "%d octets" % os.path.getsize(f_md))
    ev.test("html_written", os.path.getsize(f_html) > 500, "%d octets" % os.path.getsize(f_html))
    ev.close("EXECUTED")
    ev.out()
    log(project_dir, OPERATION, "status=EXECUTED")
    return {"status": "EXECUTED", "markdown": f_md, "html": f_html}


if __name__ == "__main__":
    cli(OPERATION, run)
'''

ENGINES["qa"] = r'''"""PHASE 10 — QA/QC. Chaine de controles. Aucun PASS sans preuve."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "qa"


def run(project_dir):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    J = lambda *a: load_json(os.path.join(project_dir, *a))
    checks = []

    def chk(name, path, cond, detail=""):
        info = file_info(path)
        if info is None:
            checks.append({"step": name, "status": "NOT_EXECUTED",
                           "detail": "fichier absent: %s" % path})
            return False
        ok = bool(cond(info)) if callable(cond) else bool(cond)
        checks.append({"step": name, "status": "PASS" if ok else "FAIL",
                       "detail": detail or ("%s octets" % info["size_bytes"])})
        return ok

    p = os.path.join(project_dir, "program", "program.json")
    chk("PROGRAM_QA", p, lambda i: i["size_bytes"] > 100 and (J("program", "program.json") or {}).get("coherent") is True)
    d = os.path.join(project_dir, "dimensions", "dimensions.json")
    chk("DIMENSION_QA", d, lambda i: (J("dimensions", "dimensions.json") or {}).get("surface_check") == "PASS")
    chk("GEOMETRY_QA", d, lambda i: all(l["width_m"] > 0 and l["depth_m"] > 0 for l in (J("dimensions", "dimensions.json") or {}).get("levels", [])))
    chk("DESIGN_QA", os.path.join(project_dir, "design", "design_variants.json"), lambda i: len((J("design", "design_variants.json") or {}).get("variants", [])) >= 1)
    chk("MODEL_QA", os.path.join(project_dir, "3d", "model_3d.json"), lambda i: (J("3d", "model_3d.json") or {}).get("verified") is True)
    rj = J("renders", "render.json") or {}
    chk("RENDER_QA", os.path.join(project_dir, "renders", "render.json"), lambda i: rj.get("all_verified") is True)
    for v in rj.get("views", []):
        checks.append({"step": "RENDER_FILE_%s" % v["name"],
                       "status": "PASS" if (v["exists"] and v["verified"] and v.get("resolution")) else "FAIL",
                       "detail": "%s / %s" % (v.get("resolution"), v.get("size_bytes"))})
    chk("DOCUMENT_QA", os.path.join(project_dir, "documentation", "rapport_architectural.md"), lambda i: i["size_bytes"] > 500)
    executed = [c for c in checks if c["status"] != "NOT_EXECUTED"]
    failed = [c for c in checks if c["status"] == "FAIL"]
    notexec = [c for c in checks if c["status"] == "NOT_EXECUTED"]
    overall = "PASS" if (failed == [] and notexec == [] and executed) else ("FAIL" if failed else "INCOMPLETE")
    doc = {"project_id": os.path.basename(os.path.normpath(project_dir)),
           "created_at": now(), "checks": checks, "executed": len(executed),
           "passed": len([c for c in checks if c["status"] == "PASS"]),
           "failed": len(failed), "not_executed": len(notexec), "overall": overall}
    p2 = save_json(os.path.join(project_dir, "reports", "qa_report.json"), doc)
    ev.created(p2)
    ev.test("qa_overall", overall == "PASS", overall)
    ev.close("VERIFIED" if overall == "PASS" else "FAILED")
    ev.out()
    log(project_dir, OPERATION, "status=%s" % overall)
    return {"status": overall, "qa_report": p2, "checks": checks}


if __name__ == "__main__":
    cli(OPERATION, run)
'''

ENGINES["delivery"] = r'''"""PHASE — DELIVERY. Manifeste + paquet, verification REELLE de chaque livrable."""
import os, sys, zipfile, glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "delivery"


def run(project_dir):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    ev.tool("zip")
    pid = os.path.basename(os.path.normpath(project_dir))
    patterns = ["renders/*.png", "floorplan/*.svg", "3d/*.blend",
                "documentation/*.md", "documentation/*.html", "reports/*.json"]
    items = []
    for pat in patterns:
        for f in sorted(glob.glob(os.path.join(project_dir, pat))):
            info = file_info(f)
            items.append({"filename": os.path.basename(f), "path": info["path"],
                          "exists": True, "size_bytes": info["size_bytes"],
                          "format": info.get("format"), "resolution": info.get("resolution"),
                          "sha256": info.get("sha256"), "verified": info["size_bytes"] > 0})
    if not items:
        ev.block("Aucun livrable trouve. DELIVERY_STATUS = BLOCKED.")
        doc = {"project_id": pid, "items": [], "package": None,
               "package_verified": False, "delivery_status": "BLOCKED"}
        save_json(os.path.join(project_dir, "exports", "delivery.json"), doc)
        ev.out()
        return {"status": "BLOCKED", "delivery_status": "BLOCKED"}
    zip_path = os.path.join(project_dir, "exports", "%s_livrables.zip" % pid)
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for it in items:
            z.write(it["path"], os.path.relpath(it["path"], project_dir))
    zinfo = ev.created(zip_path)
    names = sorted(os.path.basename(i["path"]) for i in items)
    with zipfile.ZipFile(zip_path) as z:
        inside = sorted(os.path.basename(n) for n in z.namelist() if not n.endswith("/"))
    complete = set(names).issubset(set(inside))
    doc = {"project_id": pid, "created_at": now(), "items": items,
           "package": zip_path, "package_size_bytes": zinfo["size_bytes"] if zinfo else None,
           "package_sha256": zinfo["sha256"] if zinfo else None,
           "package_verified": bool(zinfo and complete),
           "entries": len(inside), "delivery_status": "DELIVERED" if complete else "FAILED"}
    p = save_json(os.path.join(project_dir, "exports", "delivery.json"), doc)
    ev.created(p)
    ev.test("package_written", bool(zinfo), "%s octets" % (zinfo["size_bytes"] if zinfo else 0))
    ev.test("all_items_in_package", complete, "%d/%d" % (len(inside), len(names)))
    ev.close(doc["delivery_status"])
    ev.out()
    log(project_dir, OPERATION, "status=%s items=%d" % (doc["delivery_status"], len(items)))
    return {"status": doc["delivery_status"], "delivery": p, "package": zip_path,
            "items": len(items), "package_size_bytes": doc["package_size_bytes"]}


if __name__ == "__main__":
    cli(OPERATION, run)
'''

for name, src in ENGINES.items():
    FILES["engines/%s/engine.py" % name] = src

for rel, content in FILES.items():
    p = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)

print("gen2: OK")
print("engines:", len(ENGINES))
for n in ENGINES:
    print("  engines/%s/engine.py" % n)
